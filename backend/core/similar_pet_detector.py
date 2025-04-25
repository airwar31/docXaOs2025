import os
import cv2
import numpy as np
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('similar_pet_detector.log')
    ]
)
logger = logging.getLogger('similar_pet_detector')

class SimilarPetDetector:
    def __init__(self, db_name: str, upload_folder: str, similarity_threshold: float = 0.7):

        self.db_name = db_name
        self.upload_folder = upload_folder
        self.similarity_threshold = similarity_threshold
        self.sift = cv2.SIFT_create()
        
    def get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
        
    def build_index(self) -> List[Dict[str, Any]]:

        db = self.get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT p.id, p.user_id, p.type, p.breed, p.category, p.location, pp.photo_path, u.email as user_email
            FROM pets p
            JOIN users u ON p.user_id = u.id
            JOIN pet_photos pp ON p.id = pp.pet_id
        ''')
        
        pets = cursor.fetchall()
        db.close()
        
        pet_index = []
        
        for pet in pets:
            try:
                img_path = os.path.join(self.upload_folder, pet['photo_path'])
                if not os.path.exists(img_path):
                    logger.warning(f"Image not found: {img_path}")
                    continue
                    
                descriptors = self._extract_sift_descriptors(img_path)
                if descriptors is None:
                    continue
                    
                pet_info = dict(pet)
                pet_info['descriptors'] = descriptors
                pet_index.append(pet_info)
                
            except Exception as e:
                logger.error(f"Error processing pet {pet['id']}: {e}")
                continue
                
        logger.info(f"Built index with {len(pet_index)} pets")
        return pet_index
        
    def find_similar_pets(self, new_pet_id: int) -> List[Dict[str, Any]]:

        db = self.get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT pp.photo_path
            FROM pet_photos pp
            WHERE pp.pet_id = ?
        ''', (new_pet_id,))
        
        new_pet_photos = cursor.fetchall()
        
        if not new_pet_photos:
            logger.warning(f"No photos found for pet {new_pet_id}")
            db.close()
            return []
            
        cursor.execute('''
            SELECT p.id, p.user_id, p.type, p.breed, p.category, p.location, pp.photo_path, u.email as user_email
            FROM pets p
            JOIN users u ON p.user_id = u.id
            JOIN pet_photos pp ON p.id = pp.pet_id
            WHERE p.id != ?
        ''', (new_pet_id,))
        
        existing_pets = cursor.fetchall()
        db.close()
        
        if not existing_pets:
            logger.info(f"No existing pets to compare with pet {new_pet_id}")
            return []
            
        similar_pets = []
        
        for new_photo in new_pet_photos:
            new_img_path = os.path.join(self.upload_folder, new_photo['photo_path'])
            if not os.path.exists(new_img_path):
                logger.warning(f"New pet image not found: {new_img_path}")
                continue
                
            new_descriptors = self._extract_sift_descriptors(new_img_path)
            if new_descriptors is None:
                continue
                
            for pet in existing_pets:
                try:
                    img_path = os.path.join(self.upload_folder, pet['photo_path'])
                    if not os.path.exists(img_path):
                        continue
                        
                    pet_descriptors = self._extract_sift_descriptors(img_path)
                    if pet_descriptors is None:
                        continue
                        
                    similarity = self._calculate_similarity(new_descriptors, pet_descriptors)
                    
                    if similarity >= self.similarity_threshold:
                        similar_pet = dict(pet)
                        similar_pet['similarity_score'] = similarity
                        # Add photo_url for the frontend
                        similar_pet['photo_url'] = f"/uploads/{similar_pet['photo_path']}"
                        similar_pets.append(similar_pet)
                        logger.info(f"Found similar pet: {pet['id']} with similarity {similarity:.2f}")
                        
                except Exception as e:
                    logger.error(f"Error comparing with pet {pet['id']}: {e}")
                    continue
                    
        unique_pets = {}
        for pet in similar_pets:
            pet_id = pet['id']
            if pet_id not in unique_pets or pet['similarity_score'] > unique_pets[pet_id]['similarity_score']:
                unique_pets[pet_id] = pet
                
        result = list(unique_pets.values())
        result.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return result
        
    def _extract_sift_descriptors(self, img_path: str) -> Optional[np.ndarray]:
        try:
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                logger.warning(f"Could not read image: {img_path}")
                return None
                
            _, des = self.sift.detectAndCompute(img, None)
            if des is None or len(des) == 0:
                logger.warning(f"No descriptors found in image: {img_path}")
                return None
                
            avg_des = np.mean(des, axis=0)
            return avg_des
            
        except Exception as e:
            logger.error(f"Error extracting SIFT descriptors from {img_path}: {e}")
            return None
            
    def _calculate_similarity(self, desc1: np.ndarray, desc2: np.ndarray) -> float:
        try:
            similarity = np.dot(desc1, desc2) / (np.linalg.norm(desc1) * np.linalg.norm(desc2))
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
            
    def get_pet_details(self, pet_id: int) -> Optional[Dict[str, Any]]:
        try:
            db = self.get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT p.*, u.email as user_email, GROUP_CONCAT(pp.photo_path) as photos
                FROM pets p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN pet_photos pp ON p.id = pp.pet_id
                WHERE p.id = ?
                GROUP BY p.id
            ''', (pet_id,))
            
            pet = cursor.fetchone()
            db.close()
            
            if not pet:
                return None
                
            pet_dict = dict(pet)
            if pet_dict['photos']:
                pet_dict['photos'] = pet_dict['photos'].split(',')
                # Set photo_url to the first photo's path for use in the frontend
                pet_dict['photo_url'] = f"/uploads/{pet_dict['photos'][0]}"
            else:
                pet_dict['photos'] = []
                # Set a default photo URL instead of None
                pet_dict['photo_url'] = "/static/images/noPhotoAnimals.png"
                
            return pet_dict
            
        except Exception as e:
            logger.error(f"Error getting pet details for {pet_id}: {e}")
            return None





