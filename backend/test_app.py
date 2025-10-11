import unittest
import json
from app import app, db, FinancialRecord

class FinancialAppTestCase(unittest.TestCase):
    def setUp(self):
        """
        Set up a clean test environment before each test.
        - Uses in-memory SQLite database so we don't affect production.
        - Creates tables and inserts one dummy financial record.
        """
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            test_record = FinancialRecord(description="Test record", amount=100.0)
            db.session.add(test_record)
            db.session.commit()

    def tearDown(self):
        """
        Clean up after each test.
        Drops all tables so every test starts fresh.
        """
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_records(self):
        """
        Test the GET /records endpoint.
        - Expects 200 OK response.
        - Verifies the dummy record we inserted is returned.
        """
        response = self.app.get('/records')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1) 
        self.assertEqual(data[0]['description'], "Test record")
        self.assertEqual(data[0]['amount'], 100.0)

    def test_add_record(self):
        """
        Test the POST /records endpoint.
        - Sends a new record in JSON format.
        - Expects 201 Created response.
        - Verifies that the new record is stored in the DB.
        """
        response = self.app.post(
            '/records',
            data=json.dumps({'description': 'New record', 'amount': 250.0}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        
        get_response = self.app.get('/records')
        data = json.loads(get_response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[1]['description'], 'New record')
        self.assertEqual(data[1]['amount'], 250.0)

    def test_add_invalid_record(self):
        """
        Test adding an invalid record (missing amount).
        - Expects a 400 Bad Request or similar error.
        - This shows how QA catches bugs / error handling issues.
        """
        response = self.app.post(
            '/records',
            data=json.dumps({'description': 'Broken record'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)  

if __name__ == '__main__':
    unittest.main()
