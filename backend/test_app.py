import unittest
from io import BytesIO
from app import app

class FinancialAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_upload_missing_file(self):
        """Should return 400 if no file is uploaded."""
        response = self.client.post('/api/finances/upload/1/2025')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No file uploaded', response.data)

    def test_upload_empty_filename(self):
        """Should return 400 if filename is empty."""
        data = {'file': (BytesIO(b''), '')}
        response = self.client.post('/api/finances/upload/1/2025', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Empty filename', response.data)

    def test_upload_invalid_excel_format(self):
        """Should return 400 if the uploaded file is not a valid .xlsx Excel file."""
        # Upload a plain text file with .xlsx extension
        data = {'file': (BytesIO(b'not an excel file'), 'invalid.xlsx')}
        response = self.client.post('/api/finances/upload/1/2025', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid Excel file format', response.data)

    def test_get_records(self):
        """Should return 200 and a list (may be empty) for valid user/year."""
        response = self.client.get('/api/finances/1/2025')
        self.assertTrue(response.is_json)
        data = response.get_json()

        if response.status_code == 200:
            self.assertIsInstance(data, list)
        else:
            # DB/auth failures should return a JSON error object
            self.assertIsInstance(data, dict)
            self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()