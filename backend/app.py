from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import openpyxl

app = Flask(__name__)
CORS(app)

# Database connection helper
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",   # keep empty if no password
        database="finance_db"
    )

# File Upload Endpoint
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
        return jsonify({"error": f"Invalid file format: {str(e)}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # skip header row
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row is None or len(row) < 2:
                continue  # skip empty/invalid rows
            month, amount = row
            cursor.execute("""
                INSERT INTO financial_records (user_id, year, month, amount)
                VALUES (%s, %s, %s, %s)
            """, (user_id, year, month, amount))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Upload successful"}), 201

# Data Retrieval Endpoint
@app.route('/api/finances/<int:user_id>/<int:year>', methods=['GET'])
def get_records(user_id, year):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.name, f.month, f.amount
        FROM financial_records f
        JOIN users u ON f.user_id = u.user_id
        WHERE f.user_id = %s AND f.year = %s
    """, (user_id, year))

    records = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(records), 200

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
