"""
Tests for the photo handling functionality.
"""
import unittest
import os
import sys
import sqlite3
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.core.similar_pet_detector import SimilarPetDetector
from backend.api.animal_api import AnimalAPI

class TestPhotoHandling(unittest.TestCase):
    """Test cases for the photo handling functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for uploads
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test database
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create the necessary tables
        self.cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            breed TEXT,
            gender TEXT,
            size TEXT,
            fur TEXT,
            tail TEXT,
            ears TEXT,
            location TEXT,
            chip_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE pet_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            FOREIGN KEY (pet_id) REFERENCES pets (id)
        )
        ''')
        
        # Insert a test user
        self.cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ('test@example.com', 'hash')
        )
        self.user_id = self.cursor.lastrowid
        
        # Insert a test pet with a photo
        self.cursor.execute(
            "INSERT INTO pets (user_id, type, category) VALUES (?, ?, ?)",
            (self.user_id, 'DOG', 'dog')
        )
        self.pet_with_photo_id = self.cursor.lastrowid
        
        # Insert a photo for the pet
        self.cursor.execute(
            "INSERT INTO pet_photos (pet_id, photo_path) VALUES (?, ?)",
            (self.pet_with_photo_id, 'test_photo.jpg')
        )
        
        # Insert a test pet without a photo
        self.cursor.execute(
            "INSERT INTO pets (user_id, type, category) VALUES (?, ?, ?)",
            (self.user_id, 'CAT', 'cat')
        )
        self.pet_without_photo_id = self.cursor.lastrowid
        
        self.conn.commit()
        
        # Create the detector
        self.detector = SimilarPetDetector(self.db_path, self.temp_dir)
        
    def tearDown(self):
        """Clean up the test environment."""
        self.conn.close()
        shutil.rmtree(self.temp_dir)
        
    def test_get_pet_details_with_photo(self):
        """Test that get_pet_details returns the correct photo URL for a pet with a photo."""
        pet = self.detector.get_pet_details(self.pet_with_photo_id)
        self.assertIsNotNone(pet)
        self.assertEqual(pet['photos'], ['test_photo.jpg'])
        self.assertEqual(pet['photo_url'], '/uploads/test_photo.jpg')
        
    def test_get_pet_details_without_photo(self):
        """Test that get_pet_details returns a default photo URL for a pet without a photo."""
        pet = self.detector.get_pet_details(self.pet_without_photo_id)
        self.assertIsNotNone(pet)
        self.assertEqual(pet['photos'], [])
        self.assertEqual(pet['photo_url'], '/static/images/noPhotoAnimals.png')
        
    def test_animal_api_extract_info_with_photo(self):
        """Test that AnimalAPI.extract_animal_info returns the correct photo URL for an animal with a photo."""
        animal = {
            'id': 1,
            'api_type': 'lost',
            'breed': 'Labrador',
            'location': 'Moscow'
        }
        
        # Mock the get_animal_photos method to return a photo
        with patch.object(AnimalAPI, 'get_animal_photos', return_value=['http://example.com/photo.jpg']):
            info = AnimalAPI.extract_animal_info(animal)
            self.assertEqual(info['photos'], ['http://example.com/photo.jpg'])
            self.assertEqual(info['photo_url'], 'http://example.com/photo.jpg')
            
    def test_animal_api_extract_info_without_photo(self):
        """Test that AnimalAPI.extract_animal_info returns a default photo URL for an animal without a photo."""
        animal = {
            'id': 1,
            'api_type': 'lost',
            'breed': 'Labrador',
            'location': 'Moscow'
        }
        
        # Mock the get_animal_photos method to return an empty list
        with patch.object(AnimalAPI, 'get_animal_photos', return_value=[]):
            info = AnimalAPI.extract_animal_info(animal)
            self.assertEqual(info['photos'], [])
            self.assertEqual(info['photo_url'], '/static/images/noPhotoAnimals.png')
            
    def test_animal_api_extract_info_without_id(self):
        """Test that AnimalAPI.extract_animal_info returns a default photo URL for an animal without an ID."""
        animal = {
            'breed': 'Labrador',
            'location': 'Moscow'
        }
        
        info = AnimalAPI.extract_animal_info(animal)
        self.assertEqual(info['photos'], [])
        self.assertEqual(info['photo_url'], '/static/images/noPhotoAnimals.png')
        
if __name__ == '__main__':
    unittest.main()
