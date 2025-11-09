import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "MyStrongPass123!"
}

def test_setup_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS finance_test_db;")
    cursor.execute("USE finance_test_db;")

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100)
        );
    """)

    # Create financial_records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            year INT,
            month VARCHAR(20),
            amount DECIMAL(10, 2),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ finance_test_db setup complete with required tables.")

if __name__ == "__main__":
    test_setup_db()
