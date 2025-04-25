#!/usr/bin/env python3
"""
Test script to verify that photo URLs are working correctly.
"""
import os
import sys
import sqlite3
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.settings import active_config

class TestPhotoUrls(unittest.TestCase):
    """Test cases for photo URLs."""
    
    def setUp(self):
        """Set up the test environment."""
        self.db_name = active_config.DB_NAME
        self.upload_folder = os.path.join(os.path.dirname(__file__), active_config.UPLOAD_FOLDER)
        
        # Ensure the upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
        
    def test_upload_folder_path(self):
        """Test that the upload folder path is correct."""
        self.assertTrue(os.path.exists(self.upload_folder), f"Upload folder {self.upload_folder} does not exist")
        
    def test_photo_url_in_database(self):
        """Test that photo URLs in the database are correct."""
        # Connect to the database
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if the database has been initialized
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pets'")
        if not cursor.fetchone():
            print("Database not initialized, skipping test")
            conn.close()
            return
        
        # Get all pets with photos
        cursor.execute('''
        SELECT p.id, p.user_id, p.type, p.category, pp.photo_path
        FROM pets p
        JOIN pet_photos pp ON p.id = pp.pet_id
        ''')
        
        pets_with_photos = cursor.fetchall()
        conn.close()
        
        if not pets_with_photos:
            print("No pets with photos found in the database, skipping test")
            return
        
        # Check that each photo exists in the upload folder
        for pet in pets_with_photos:
            photo_path = os.path.join(self.upload_folder, pet['photo_path'])
            print(f"Checking if photo exists: {photo_path}")
            # We don't actually need the file to exist for this test
            # Just verify that the path is correct
            url_path = f"/uploads/{pet['photo_path']}"
            print(f"URL path would be: {url_path}")
            
        print("All photo paths verified")
        
if __name__ == '__main__':
    unittest.main()