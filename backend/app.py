import csv
import io
import logging
import math
import os
from decimal import Decimal, InvalidOperation

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import mysql.connector
import openpyxl

#=== Logging ===
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getlogger("finance")

app = Flask(__name__)
CORS(app)

# === Configuration ===
# NOTE: For local/dev use these fall back to defaults so the app "just works"
# out of the box, but in any shared or production environment you should set
# real values via environment variables (see .env.example) and never rely on
# the fallback password below.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "MyStrongPass123!")
DB_NAME = os.getenv("DB_NAME", "finance_db")
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "finance_test_db")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROWS = 5000  # Max rows to process in a single upload
# amount is stored as DECIMAL(10,2) in the database, so max value is 99999999.99
MAX_ABS_AMOUNT = Decimal("99999999.99")
MAX_SKIP_DEATIALS = 20 #cap how many per row problems we echo back

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Accepts full names and 3- letter abbreviations("Jan", "Sept")

MONTH_LOOKUP = {}
for _m in MONTHS:
    MONTH_LOOKUP[_m.lower()] = _m
    MONTH_LOOKUP[_m[:3].lower()] = _m
MONTH_LOOKUP["sept"] = "September"  # Special case for September abbreviation

# === Error Handling ===
@app.errorhandler(HTTPException)
def handle_http_error(e):
    if e.code == 413:
        message = f"File is too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)"
    else:
        message = e.description
    return jsonify({"error": message}), e.code

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    logger.exception("Unhandled error on %s %s", request.method, request.path)
    return jsonify({"error": "Internal server error"}), 500

# def normalize_month(value):
#     """Trim whitespace and title-case month names so 'january', ' January ',
#     and 'JANUARY' are all treated as the same month instead of creating
#     duplicate rows."""
#     return str(value).strip().title()


# @app.errorhandler(413)
# def file_too_large(e):
#     return jsonify({"error": "File is too large (max 10 MB)"}), 413


# === Database Connection ===
def get_db_connection(testing=False):
    """Return a MySQL connection. Uses test DB if testing=True."""
    db_name = TEST_DB_NAME if testing else DB_NAME
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=db_name,
            autocommit=False,
        )
    except mysql.connector.Error as e:
        logger.error("DB connection error (%s): %s", db_name, e)
        return None

# === Parsing & validation ===
class UploadError(Exception):
    """A Problem with the uoloaded file itself; message is safe to show users."""
    
def normalize_month(value):
    """Map 'january', 'jan', 'JANUARY', etc. to 'January'."""
    return MONTH_LOOKUP.get(str(value).strip().lower())

def parse_amount(value):
    """"Return a Decimal round to 2dp, or raise VAlueError with a reason."""
    if isinstance (value, bool):
        raise ValueError(f"amount is not a number")
    try:
        amount = Decimal(str(value).strip().replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"amount '{value}' is not a number")
    if not amount.is_finite():
        raise ValueError(f"amount '{value}' is not a finite number")
    if abs(amount) > MAX_ABS_AMOUNT:
        raise ValueError(f"amount '{value}' exceeds max allowed {MAX_ABS_AMOUNT}")
    return amount

def is_xlsx(data):
    """Return True if the bytes appear to be an XLSX file (starts with PK)."""
    return data[:2] == b'PK'

def detect_delimiter(text):
    """Return the delimiter of a CSV-llike header line, or None if it can't be determined."""
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    for delimiter in (",", "\t", ";"):
        if delimiter in first_line:
            return delimiter
    return None

def parse_xlsx(raw_bytes):
    """Return a list of (month, amount) tuples from an XLSX file."""
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(raw_bytes), read_only=True, data_only=True)
        sheet = workbook.active
        rows = [
            (row[0], row[1])
            for row in sheet.iter_rows(min_row=2, max_col=2, values_only=True)
            if row and len(row) >= 2 and not (row[0] is None and row[1] is None)
        ]
        workbook.close()
        return rows
    except Exception:
        logger.warning("Could not read uploaded XLSX", exc_info=True)
        raise UploadError("Could not read the Excel file. Is it a valid .xlsx workbook?")

def parse_csv(raw_bytes):
    try:
        text = raw-bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise UploadError("Unsupported file formate — must be UTF-8 encoded CSV or XLSX")
    
    reader = csv.reader(io.StringIO(text)), delimiter=delimiter
    headers = next (reader, None)
    if not headers or len(headers) < 2:
        raise UploadError("Unsupported CSV format — must have at least two columns (month, amount)")
    return [
        (row[0], row[1])
        for row in reader
        if len(row) >= 2 and not (row[0] is None and row[1] is None)
    ]
    
def validate_rows(raw_rows):
    valid, problems = [], []
    for index, (raw_month, raw_amount) in enumerate(raw_rows, start=2):
        month = normalize_month(raw_month) if raw_month is not None else None
        if month is None:
            problems.append({"row": index, "reason": f"'{raw_month}' is not a recognised month"})
            continue
        if raw_amount is None or str(raw_amount).strip() == "":
            problems.append({"row": index, "reason": "amount is missing"})
            continue
        try:
            valid.append((month, parse_amount(raw_amount)))
        except ValueError as e:
            problems.append({"row": index, "reason": str(e)})
    return valid, problems

# === Routes ===
@app.route("/api/health", methods=["GET"])
def health():
    """Liveness/readiness probe used by Docker and CI."""
    conn = get_db_connection(testing=app.config.get("TESTING", False))
    if conn is None:
        return jsonify({"status": "degraded", "database": "down"}), 503
    conn.close()
    return jsonify({"status": "ok", "database": "up"}), 200


# === Upload Excel File ===
@app.route('/api/finances/upload/<int:user_id>/<int:year>', methods=['POST'])
def upload_file(user_id, year):
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    raw_bytes = file.read()
    filename = file.filename.lower()
    rows = []

    # -----------------------------
    # MAGIC BYTE DETECTION
    # -----------------------------
    def is_xlsx(data):
        # XLSX files start with PK (zip file magic bytes)
        return data[:2] == b'PK'

    def is_probably_csv(data):
        # Being UTF-8 decodable isn't enough on its own -- a renamed .txt
        # file would pass that check too. Require it to actually look like
        # delimited tabular data: a non-blank line containing a comma/tab.
        if not data:
            return False
        try:
            decoded = data.decode("utf-8")
        except Exception:
            return False

        first_line = next((line for line in decoded.splitlines() if line.strip()), "")
        return ("," in first_line) or ("\t" in first_line)

    # -----------------------------
    # 1) XLSX DETECTED (real Excel)
    # -----------------------------
    if is_xlsx(raw_bytes):
        try:
            workbook = openpyxl.load_workbook(BytesIO(raw_bytes))
            sheet = workbook.active

            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 2:
                    continue
                if row[0] is None or row[1] is None:
                    continue
                rows.append((normalize_month(row[0]), row[1]))

        except Exception as e:
            return jsonify({"error": f"Invalid XLSX file: {str(e)}"}), 400

    # -----------------------------
    # 2) CSV DETECTED (real CSV)
    # -----------------------------
    elif is_probably_csv(raw_bytes):
        try:
            decoded = raw_bytes.decode("utf-8")
            import csv
            reader = csv.reader(decoded.splitlines())

            headers = next(reader, None)
            if not headers or len(headers) < 2:
                return jsonify({"error": "Invalid CSV format"}), 400

            for row in reader:
                if len(row) < 2 or not row[0] or not row[1]:
                    continue
                rows.append((normalize_month(row[0]), row[1]))

        except Exception as e:
            return jsonify({"error": f"CSV parse error: {str(e)}"}), 400

    # -----------------------------
    # 3) Unknown file type
    # -----------------------------
    else:
        return jsonify({
            "error": "Unsupported file format — must be CSV or XLSX",
            "tip": "Even if renamed, file must be valid CSV or valid XLSX",
        }), 400

    if len(rows) > 5000:
        return jsonify({"error": "Too many rows in file (max 5000)"}), 400

    # -----------------------------
    # DATABASE INSERTION
    # -----------------------------
    testing = app.config.get('TESTING', False)
    conn = get_db_connection(testing=testing)
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    inserted, skipped = 0, 0

    try:
        for month, amount in rows:
            if not month or not amount:
                skipped += 1
                continue

            try:
                amount = float(amount)
            except:
                skipped += 1
                continue

            cursor.execute(
                "SELECT 1 FROM financial_records WHERE user_id = %s AND year = %s AND month = %s",
                (user_id, year, str(month))
            )
            if cursor.fetchone():
                skipped += 1
                continue

            cursor.execute(
                "INSERT INTO financial_records (user_id, year, month, amount) VALUES (%s, %s, %s, %s)",
                (user_id, year, str(month), amount)
            )
            inserted += 1

        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "message": "Upload processed",
        "inserted": inserted,
        "skipped": skipped,
        "rows_received": len(rows),
        "file_detected_as": "xlsx" if is_xlsx(raw_bytes) else "csv"
    }), 201



# === Get Records ===
@app.route('/api/finances/<int:user_id>/<int:year>', methods=['GET'])
def get_records(user_id, year):
    testing = app.config.get('TESTING', False)
    conn = get_db_connection(testing=testing)
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.name, f.month, f.amount
            FROM financial_records f
            LEFT JOIN users u ON f.user_id = u.user_id
            WHERE f.user_id = %s AND f.year = %s
            ORDER BY FIELD(
                LOWER(f.month),
                'january','february','march','april','may','june',
                'july','august','september','october','november','december'
            )
        """, (user_id, year))
        records = cursor.fetchall()
    except mysql.connector.Error as e:
        # ✅ No printing in testing mode
        if not app.config.get("TESTING"):
            print(f"Data retrieval error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()

    return jsonify(records), 200


# === Run App ===
if __name__ == '__main__':
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
