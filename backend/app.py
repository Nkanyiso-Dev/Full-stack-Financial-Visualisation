import os
from io import BytesIO
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import openpyxl

app = Flask(__name__)
CORS(app)

# === Configuration ===
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "MyStrongPass123!")
DB_NAME = os.getenv("DB_NAME", "finance_db")
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "finance_test_db")


# === Database Connection ===
def get_db_connection(testing=False):
    """Return a MySQL connection. Uses test DB if testing=True."""
    db_name = TEST_DB_NAME if testing else DB_NAME
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=db_name,
            autocommit=True
        )
        return conn
    except mysql.connector.Error as e:
        if not app.config.get("TESTING"):
            print(f"DB connection error ({db_name}): {e}")
        return None


# === Upload Excel File ===
@app.route('/api/finances/upload/<int:user_id>/<int:year>', methods=['POST'])
def upload_file(user_id, year):
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    # Validate Excel file
    try:
        file_bytes = file.read()
        workbook = openpyxl.load_workbook(BytesIO(file_bytes))
        sheet = workbook.active
    except Exception:
        return jsonify({"error": "Invalid Excel file format"}), 400

    testing = app.config.get('TESTING', False)
    conn = get_db_connection(testing=testing)
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    inserted, skipped = 0, 0

    try:
        for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row or len(row) < 2:
                skipped += 1
                continue

            month, amount = row[0], row[1]
            if month is None or amount is None:
                skipped += 1
                continue

            try:
                amount = float(amount)
            except Exception:
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
        if not app.config.get("TESTING"):
            print(f"DB insert error: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "message": "Upload processed",
        "inserted": inserted,
        "skipped": skipped
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
