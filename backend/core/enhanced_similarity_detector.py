import os
import cv2
import numpy as np
import sqlite3
import requests
from typing import List, Dict, Any, Optional, Tuple
import json
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.api.animal_api import AnimalAPI

class EnhancedSimilarityDetector:
    def __init__(self, db_name: str, upload_folder: str, 
                 similarity_threshold: float = 0.7,
                 text_weight: float = 0.4, 
                 image_weight: float = 0.6):
        self.db_name = db_name
        self.upload_folder = upload_folder
        self.similarity_threshold = similarity_threshold
        self.text_weight = text_weight
        self.image_weight = image_weight
        
        self.sift = cv2.SIFT_create()
        
        self.tfidf_vectorizer = TfidfVectorizer(
            analyzer='word',
            stop_words='english',
            lowercase=True,
            max_features=1000
        )
        
    def get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _extract_sift_descriptors(self, img_path: str) -> Optional[np.ndarray]:
        try:
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"Could not read image: {img_path}")
                return None
                
            keypoints, des = self.sift.detectAndCompute(img, None)
            if des is None or len(des) == 0:
                print(f"No descriptors found in image: {img_path}")
                return None
                
            return des
            
        except Exception as e:
            print(f"Error extracting SIFT descriptors from {img_path}: {e}")
            return None
    
    def _calculate_image_similarity(self, desc1: np.ndarray, desc2: np.ndarray) -> float:
        try:
            if desc1 is None or desc2 is None:
                return 0.0
                
            if len(desc1) < len(desc2):
                query_desc, train_desc = desc1, desc2
            else:
                query_desc, train_desc = desc2, desc1
                
            nn = NearestNeighbors(n_neighbors=1, algorithm='auto').fit(train_desc)
            
            distances, _ = nn.kneighbors(query_desc)
            
            avg_distance = np.mean(distances)
            if avg_distance == 0:
                return 1.0
                
            similarity = 1.0 / (1.0 + avg_distance)
            return float(similarity)
            
        except Exception as e:
            print(f"Error calculating image similarity: {e}")
            return 0.0
    
    def _create_pet_description(self, pet: Dict[str, Any]) -> str:
        description_parts = []
        
        if pet.get('type'):
            description_parts.append(f"Type: {pet['type']}")
        if pet.get('category'):
            description_parts.append(f"Category: {pet['category']}")
        
        if pet.get('breed'):
            description_parts.append(f"Breed: {pet['breed']}")
        if pet.get('gender'):
            description_parts.append(f"Gender: {pet['gender']}")
        if pet.get('size'):
            description_parts.append(f"Size: {pet['size']}")
        if pet.get('fur'):
            description_parts.append(f"Fur: {pet['fur']}")
        
        if pet.get('color'):
            description_parts.append(f"Color: {pet['color']}")
        if pet.get('tail'):
            description_parts.append(f"Tail: {pet['tail']}")
        if pet.get('ears'):
            description_parts.append(f"Ears: {pet['ears']}")
        
        if pet.get('special_marks'):
            description_parts.append(f"Special marks: {pet['special_marks']}")
        if pet.get('additional_info'):
            description_parts.append(f"Additional info: {pet['additional_info']}")
        
        return " ".join(description_parts)
    
    def _calculate_text_similarity(self, desc1: str, desc2: str) -> float:
        try:
            if not desc1 or not desc2:
                return 0.0
                
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([desc1, desc2])
            
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            print(f"Error calculating text similarity: {e}")
            return 0.0
    
    def _calculate_combined_similarity(self, text_similarity: float, image_similarity: float) -> float:
        return (self.text_weight * text_similarity) + (self.image_weight * image_similarity)
    
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
                pet_dict['photo_url'] = f"/uploads/{pet_dict['photos'][0]}"
            else:
                pet_dict['photos'] = []
                pet_dict['photo_url'] = "/static/images/noPhotoAnimals.png"
                
            return pet_dict
            
        except Exception as e:
            print(f"Error getting pet details for {pet_id}: {e}")
            return None
    
    def _download_image_from_url(self, url: str, max_retries: int = 2) -> Optional[np.ndarray]:
        retries = 0
        while retries <= max_retries:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, timeout=10, headers=headers)
                
                if response.status_code == 404:
                    print(f"Image not found (404) at URL: {url}")
                    return None
                elif response.status_code == 403:
                    print(f"Access forbidden (403) to image at URL: {url}")
                    return None
                elif response.status_code >= 500:
                    if retries < max_retries:
                        print(f"Server error ({response.status_code}) for URL: {url}. Retrying ({retries+1}/{max_retries})...")
                        retries += 1
                        continue
                    else:
                        print(f"Server error ({response.status_code}) for URL: {url} after {max_retries} retries")
                        return None
                
                response.raise_for_status()
                
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    print(f"URL does not point to an image (Content-Type: {content_type}): {url}")
                    return None
                
                image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                
                img = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    img_color = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                    if img_color is not None:
                        img = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
                    else:
                        print(f"Could not decode image from URL: {url}")
                        return None
                
                if img.size == 0 or img.shape[0] == 0 or img.shape[1] == 0:
                    print(f"Downloaded image is empty from URL: {url}")
                    return None
                    
                return img
                
            except requests.exceptions.Timeout:
                if retries < max_retries:
                    print(f"Timeout downloading image from URL: {url}. Retrying ({retries+1}/{max_retries})...")
                    retries += 1
                else:
                    print(f"Timeout downloading image from URL: {url} after {max_retries} retries")
                    return None
                    
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error downloading image from URL {url}: {e}")
                return None
                
            except requests.exceptions.ConnectionError:
                if retries < max_retries:
                    print(f"Connection error downloading image from URL: {url}. Retrying ({retries+1}/{max_retries})...")
                    retries += 1
                else:
                    print(f"Connection error downloading image from URL: {url} after {max_retries} retries")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error downloading image from URL {url}: {e}")
                return None
                
            except Exception as e:
                print(f"Unexpected error downloading image from URL {url}: {e}")
                return None
    
    def _compare_with_api_pets(self, new_pet_id: int, new_pet: Dict[str, Any], 
                              new_pet_description: str, new_descriptors: np.ndarray) -> List[Dict[str, Any]]:
        similar_api_pets = []
        
        try:
            try:
                api_pets = AnimalAPI.get_all_animals()
            except Exception as api_err:
                print(f"Error fetching pets from API: {api_err}")
                return []
            
            if not api_pets:
                print("No API pets found to compare")
                return []
                
            print(f"Comparing pet {new_pet_id} with {len(api_pets)} API pets")
            
            for api_pet in api_pets:
                try:
                    if not isinstance(api_pet, dict):
                        print(f"Skipping invalid API pet (not a dictionary): {type(api_pet)}")
                        continue
                        
                    try:
                        pet_info = AnimalAPI.extract_animal_info(api_pet)
                    except Exception as extract_err:
                        print(f"Error extracting info from API pet: {extract_err}")
                        continue
                    
                    if not pet_info or not isinstance(pet_info, dict):
                        print("Invalid pet info returned from API")
                        continue
                    
                    if 'id' not in pet_info or not pet_info['id']:
                        print("API pet missing ID, skipping")
                        continue
                    
                    api_pet_description = self._create_pet_description(pet_info)
                    
                    text_similarity = self._calculate_text_similarity(new_pet_description, api_pet_description)
                    
                    max_image_similarity = 0.0
                    
                    photos = pet_info.get('photos', [])
                    if isinstance(photos, list) and photos and new_descriptors is not None:
                        for photo_url in photos:
                            if not isinstance(photo_url, str) or not photo_url:
                                continue
                                
                            img = self._download_image_from_url(photo_url)
                            if img is None:
                                continue
                                
                            try:
                                keypoints, api_descriptors = self.sift.detectAndCompute(img, None)
                                if api_descriptors is None or len(api_descriptors) == 0:
                                    continue
                                    
                                image_similarity = self._calculate_image_similarity(new_descriptors, api_descriptors)
                                max_image_similarity = max(max_image_similarity, image_similarity)
                            except Exception as img_err:
                                print(f"Error processing image from URL {photo_url}: {img_err}")
                                continue
                    
                    combined_similarity = self._calculate_combined_similarity(text_similarity, max_image_similarity)
                    
                    if combined_similarity >= self.similarity_threshold:
                        pet_info['similarity_score'] = combined_similarity
                        pet_info['text_similarity'] = text_similarity
                        pet_info['image_similarity'] = max_image_similarity
                        pet_info['from_api'] = True
                        
                        if 'user_email' not in pet_info:
                            pet_info['user_email'] = pet_info.get('email', 'No email provided')
                        
                        similar_api_pets.append(pet_info)
                        print(f"Found similar API pet with ID {pet_info.get('id')} with combined similarity {combined_similarity:.2f} "
                               f"(text: {text_similarity:.2f}, image: {max_image_similarity:.2f})")
                
                except Exception as e:
                    print(f"Error comparing with API pet: {e}")
                    continue
                    
            return similar_api_pets
            
        except Exception as e:
            print(f"Error in _compare_with_api_pets: {e}")
            return []
    

























