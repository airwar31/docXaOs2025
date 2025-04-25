import os
import cv2
import numpy as np
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
import json
from backend.core.enhanced_similarity_detector import EnhancedSimilarityDetector

class SimilarPetDetector:
    def __init__(self, db_name: str, upload_folder: str, similarity_threshold: float = 0.7):

        self.db_name = db_name
        self.upload_folder = upload_folder
        self.similarity_threshold = similarity_threshold
        self.sift = cv2.SIFT_create()
        
        self.enhanced_detector = EnhancedSimilarityDetector(
            db_name=db_name,
            upload_folder=upload_folder,
            similarity_threshold=similarity_threshold
        )
        
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
                    print(f"Image not found: {img_path}")
                    continue
                    
                descriptors = self._extract_sift_descriptors(img_path)
                if descriptors is None:
                    continue
                    
                pet_info = dict(pet)
                pet_info['descriptors'] = descriptors
                pet_index.append(pet_info)
                
            except Exception as e:
                print(f"Error processing pet {pet['id']}: {e}")
                continue
                
        print(f"Built index with {len(pet_index)} pets")
        return pet_index
        
    def find_similar_pets(self, new_pet_id: int) -> List[Dict[str, Any]]:

        similar_pets = self.enhanced_detector.find_similar_pets(new_pet_id)
        
        for pet in similar_pets:
            if 'photo_url' not in pet and 'photos' in pet and pet['photos']:
                pet['photo_url'] = f"/uploads/{pet['photos'][0]}"
        
        return similar_pets
        
    def _extract_sift_descriptors(self, img_path: str) -> Optional[np.ndarray]:
        try:
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"Could not read image: {img_path}")
                return None
                
            _, des = self.sift.detectAndCompute(img, None)
            if des is None or len(des) == 0:
                print(f"No descriptors found in image: {img_path}")
                return None
                
            avg_des = np.mean(des, axis=0)
            return avg_des
            
        except Exception as e:
            print(f"Error extracting SIFT descriptors from {img_path}: {e}")
            return None
            
    def _calculate_similarity(self, desc1: np.ndarray, desc2: np.ndarray) -> float:
        try:
            similarity = np.dot(desc1, desc2) / (np.linalg.norm(desc1) * np.linalg.norm(desc2))
            return float(similarity)
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
            
    def get_pet_details(self, pet_id: int) -> Optional[Dict[str, Any]]:
        return self.enhanced_detector.get_pet_details(pet_id)







