import unittest
import requests
import json
import os
import sys
import sqlite3
from server import app, init_db, DB_NAME
import tempfile

class CategoryValidationTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['DB_NAME'] = self.db_path
        self.client = app.test_client()
        
        with app.app_context():
            init_db()
            
        # Create a test user
        self.client.post('/api/register', 
                         data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
                         content_type='application/json')
        
        # Login
        response = self.client.post('/api/login',
                                   data=json.dumps({'email': 'test@example.com', 'password': 'password'}),
                                   content_type='application/json')
        
        # Create test directory for uploads if it doesn't exist
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
            
        # Create a test image file
        with open('uploads/test_image.jpg', 'w') as f:
            f.write('test image content')

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        if os.path.exists('uploads/test_image.jpg'):
            os.unlink('uploads/test_image.jpg')

    def test_valid_dog_category(self):
        """Test that 'dog' is a valid category"""
        data = {
            'type': 'lost',
            'category': 'dog',
            'breed': 'Test Breed',
            'gender': 'MALE',
            'color': 'Brown',
            'district': 'Test District',
            'chip': 'No',
            'sterilization': 'No',
            'special_marks': 'None',
            'size': 'MEDIUM',
            'fur': 'SHORTHAIR',
            'location': 'Test Location'
        }
        
        with open('uploads/test_image.jpg', 'rb') as img:
            response = self.client.post(
                '/api/pets',
                data={**data, 'photos': (img, 'test_image.jpg')},
                content_type='multipart/form-data'
            )
            
        self.assertEqual(response.status_code, 201)
        self.assertIn('pet_id', response.json)

    def test_valid_cat_category(self):
        """Test that 'cat' is a valid category"""
        data = {
            'type': 'lost',
            'category': 'cat',
            'breed': 'Test Breed',
            'gender': 'FEMALE',
            'color': 'White',
            'district': 'Test District',
            'chip': 'No',
            'sterilization': 'No',
            'special_marks': 'None',
            'size': 'LITTLE',
            'fur': 'LONGHAIR',
            'location': 'Test Location'
        }
        
        with open('uploads/test_image.jpg', 'rb') as img:
            response = self.client.post(
                '/api/pets',
                data={**data, 'photos': (img, 'test_image.jpg')},
                content_type='multipart/form-data'
            )
            
        self.assertEqual(response.status_code, 201)
        self.assertIn('pet_id', response.json)

    def test_invalid_category(self):
        """Test that categories other than 'dog' or 'cat' are invalid"""
        data = {
            'type': 'lost',
            'category': 'OTHER',  # Invalid category
            'breed': 'Test Breed',
            'gender': 'MALE',
            'color': 'Brown',
            'district': 'Test District',
            'chip': 'No',
            'sterilization': 'No',
            'special_marks': 'None',
            'size': 'MEDIUM',
            'fur': 'SHORTHAIR',
            'location': 'Test Location'
        }
        
        with open('uploads/test_image.jpg', 'rb') as img:
            response = self.client.post(
                '/api/pets',
                data={**data, 'photos': (img, 'test_image.jpg')},
                content_type='multipart/form-data'
            )
            
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Invalid category. Must be "dog" or "cat"')

if __name__ == '__main__':
    unittest.main()