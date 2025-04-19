from PIL import Image
import numpy as np
from io import BytesIO
import requests
import json
import os
from typing import List, Tuple, Optional, Dict, Any

class ImageProcessor:
    def __init__(self):
        self.target_size = (224, 224)
        self.similarity_threshold = 0.7

    def load_image(self, image_path_or_url: str) -> Optional[Image.Image]:
        try:
            if image_path_or_url.startswith(('http://', 'https://')):
                response = requests.get(image_path_or_url)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
            else:
                return Image.open(image_path_or_url)
        except Exception as e:
            print(f"Error loading image from {image_path_or_url}: {e}")
            return None

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image = image.resize(self.target_size)
        
        img_array = np.array(image)
        img_array = img_array.astype('float32') / 255.0
        
        return img_array

    def extract_features(self, image_path: str) -> Optional[List[float]]:
        try:
            image = self.load_image(image_path)
            if image is None:
                return None
                
            processed_image = self.preprocess_image(image)
            
            features = []
            
            for channel in range(3):
                histogram = np.histogram(
                    processed_image[:,:,channel],
                    bins=32,
                    range=(0, 1)
                )[0]
                histogram = histogram.astype('float32') / histogram.sum()
                features.extend(histogram.tolist())
            
            for channel in range(3):
                channel_data = processed_image[:,:,channel]
                features.extend([
                    float(channel_data.mean()),
                    float(channel_data.std()),
                    float(np.median(channel_data)),
                ])
            
            return features
            
        except Exception as e:
            print(f"Error extracting features from {image_path}: {e}")
            return None

    def calculate_similarity(self, features1: List[float], features2: List[float]) -> float:
        try:
            f1 = np.array(features1)
            f2 = np.array(features2)
            
            similarity = np.dot(f1, f2) / (np.linalg.norm(f1) * np.linalg.norm(f2))
            
            return float(similarity)
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def find_matches(
        self,
        target_features: List[float],
        candidate_features: List[Tuple[int, List[float]]],
        threshold: float = None
    ) -> List[Tuple[int, float]]:
        if threshold is None:
            threshold = self.similarity_threshold
            
        matches = []
        for candidate_id, features in candidate_features:
            similarity = self.calculate_similarity(target_features, features)
            if similarity >= threshold:
                matches.append((candidate_id, similarity))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def compare_with_external_images(
        self,
        local_image_path: str,
        external_images: List[Dict[str, Any]],
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        if threshold is None:
            threshold = self.similarity_threshold
            
        matches = []
        
        local_features = self.extract_features(local_image_path)
        if not local_features:
            return matches
            
        for ext_image in external_images:
            try:
                ext_features = self.extract_features(ext_image['photo_url'])
                if not ext_features:
                    continue
                    
                similarity = self.calculate_similarity(local_features, ext_features)
                
                if similarity >= threshold:
                    match_info = {
                        'external_id': ext_image['id'],
                        'similarity_score': similarity,
                        'photo_url': ext_image['photo_url'],
                        'breed': ext_image.get('breed'),
                        'category': ext_image.get('category'),
                        'location': ext_image.get('location'),
                        'contact_info': ext_image.get('contact_info')
                    }
                    matches.append(match_info)
                    
            except Exception as e:
                print(f"Error processing external image {ext_image.get('id')}: {e}")
                continue
        
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches