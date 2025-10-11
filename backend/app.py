from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import openpyxl

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="", 
        database="finance_db"
    )

@app.route('/api/finances/upload/<int:user_id>/<int:year>', methods=['POST'])
def upload_file(user_id, year):
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
    except Exception as e:
        print(f"Excel load error: {e}")
        return jsonify({"error": "Invalid Excel file format"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    inserted = 0
    skipped = 0

    try:
        for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if row is None or len(row) < 2:
                skipped += 1
                continue
            month, amount = row
            if not isinstance(month, (str, int)) or not isinstance(amount, (int, float)):
                skipped += 1
                continue

            # Check for duplicate
            cursor.execute("""
                SELECT 1 FROM financial_records
                WHERE user_id = %s AND year = %s AND month = %s
            """, (user_id, year, month))
            if cursor.fetchone():
                skipped += 1
                continue

            cursor.execute("""
                INSERT INTO financial_records (user_id, year, month, amount)
                VALUES (%s, %s, %s, %s)
            """, (user_id, year, month, amount))
            inserted += 1

        conn.commit()
        print(f"Upload: {inserted} inserted, {skipped} skipped for user {user_id}, year {year}")
    except Exception as e:
        conn.rollback()
        print(f"Database error: {e}")
        return jsonify({"error": "Database error occurred"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "message": "Upload successful",
        "inserted": inserted,
        "skipped": skipped
    }), 201

@app.route('/api/finances/<int:user_id>/<int:year>', methods=['GET'])
def get_records(user_id, year):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT u.name, f.month, f.amount
            FROM financial_records f
            JOIN users u ON f.user_id = u.user_id
            WHERE f.user_id = %s AND f.year = %s
        """, (user_id, year))
        records = cursor.fetchall()
    except Exception as e:
        print(f"Data retrieval error: {e}")
        return jsonify({"error": "Database error occurred"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(records), 200

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)