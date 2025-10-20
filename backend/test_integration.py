import unittest
import mysql.connector
from io import BytesIO
import openpyxl
from app import app, get_db_connection

def create_test_db():
    """Ensure the test database exists."""
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="MyStrongPass123!"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS finance_test_db;")
    conn.commit()
    cursor.close()
    conn.close()

class FinanceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run once before all tests."""
        create_test_db()  # Ensure test DB exists

        cls.conn = get_db_connection(testing=True)
        cls.cursor = cls.conn.cursor()

        # Create tables for testing
        cls.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100)
            );
        """)
        cls.cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                year INT,
                month VARCHAR(20),
                amount DECIMAL(10, 2),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        cls.conn.commit()

        # Insert a test user
        cls.cursor.execute("INSERT INTO users (name) VALUES ('Test User')")
        cls.conn.commit()
        cls.user_id = cls.cursor.lastrowid

        app.config['TESTING'] = True
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.cursor.execute("DROP TABLE IF EXISTS financial_records;")
        cls.cursor.execute("DROP TABLE IF EXISTS users;")
        cls.conn.commit()
        cls.cursor.close()
        cls.conn.close()

    def test_full_upload_and_fetch(self):
        """Should upload Excel file and retrieve same data."""
        # Create a valid in-memory Excel file
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(["Month", "Amount"])
        sheet.append(["January", 1000])
        sheet.append(["February", 2000])

        excel_file = BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)

        # Upload to API
        response = self.client.post(
            f'/api/finances/upload/{self.user_id}/2025',
            data={'file': (excel_file, 'test_data.xlsx')},
            content_type='multipart/form-data'
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn('inserted', response.get_json())

        # Retrieve records
        response = self.client.get(f'/api/finances/{self.user_id}/2025')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertTrue(any(r['month'] == 'January' for r in data))

if __name__ == '__main__':
    unittest.main()
