import json
import unittest
import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
from flask import Flask

from app import create_app

# Mark all tests in this module with the 'upload' marker
pytestmark = pytest.mark.upload


class TestUploadEndpoint(unittest.TestCase):
    def setUp(self):
        """Set up test client and app context"""
        self.app = create_app(testing=True)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create test file data
        self.test_file_content = b"Test ontology content"
        self.test_file = (BytesIO(self.test_file_content), "ontology.txt")
    
    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
    
    @patch('app.routes.main.extract_markdown_to_json')  # Updated function name
    @patch('app.routes.main.load_query_engine')
    @patch('os.path.join')
    @patch('werkzeug.utils.secure_filename')
    def test_upload_file_success(self, mock_secure_filename, mock_path_join, 
                                mock_load_query_engine, mock_extract):
        """Test successful file upload"""
        # Configure mocks
        mock_secure_filename.return_value = "ontology.txt"
        mock_path_join.side_effect = lambda *args: '/'.join(args)
        mock_load_query_engine.return_value = True
        
        # Mock file saving
        with patch('app.routes.main.open', mock_open()) as mock_file:
            with patch('os.path.exists') as mock_exists:
                mock_exists.return_value = True
                
                # Make request to endpoint
                response = self.client.post(
                    '/upload',
                    data={
                        'ontology_file': self.test_file
                    },
                    content_type='multipart/form-data'
                )
                
                # Check response
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertEqual(data['filename'], 'ontology.txt')
                
                # Verify extract_markdown_to_json was called
                mock_extract.assert_called_once()
                mock_load_query_engine.assert_called_once()
    
    def test_upload_file_no_file(self):
        """Test file upload with no file"""
        # Make request to endpoint with no file
        response = self.client.post(
            '/upload',
            data={},
            content_type='multipart/form-data'
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No file part')
    
    def test_upload_file_empty_filename(self):
        """Test file upload with empty filename"""
        # Make request to endpoint with empty filename
        response = self.client.post(
            '/upload',
            data={
                'ontology_file': (BytesIO(b""), "")
            },
            content_type='multipart/form-data'
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No selected file')
    
    @patch('app.routes.main.extract_markdown_to_json')  # Updated function name
    def test_upload_file_processing_error(self, mock_extract):
        """Test file upload with processing error"""
        # Configure mock to raise exception
        mock_extract.side_effect = Exception("Processing error")
        
        # Make request to endpoint
        with patch('werkzeug.utils.secure_filename') as mock_secure_filename:
            mock_secure_filename.return_value = "ontology.txt"
            
            with patch('app.routes.main.open', mock_open()) as mock_file:
                with patch('os.path.join') as mock_path_join:
                    mock_path_join.side_effect = lambda *args: '/'.join(args)
                    
                    response = self.client.post(
                        '/upload',
                        data={
                            'ontology_file': self.test_file
                        },
                        content_type='multipart/form-data'
                    )
                    
                    # Check response
                    self.assertEqual(response.status_code, 500)
                    data = json.loads(response.data)
                    self.assertIn('error', data)
                    self.assertIn('Processing error', data['error'])


if __name__ == '__main__':
    unittest.main()