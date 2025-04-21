from PIL import Image
import numpy as np
from io import BytesIO
import requests
import json
import os
import logging
from typing import List, Tuple, Optional, Dict, Any
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_processor.log')
    ]
)
logger = logging.getLogger('image_processor')

class ImageProcessor:
    """
    Class for processing images and extracting features for similarity comparison.
    """
    def __init__(self):
        """Initialize the ImageProcessor with default settings."""
        self.target_size = (224, 224)  # Standard size for processing
        self.similarity_threshold = 0.7  # Default threshold for similarity matching
        self.feature_cache = {}  # Cache for image features
        
    @lru_cache(maxsize=100)
    def load_image(self, image_path_or_url: str) -> Optional[Image.Image]:
        try:
            if image_path_or_url.startswith(('http://', 'https://')):
                response = requests.get(image_path_or_url, timeout=10)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
            else:
                return Image.open(image_path_or_url)
        except Exception as e:
            logger.error(f"Error loading image from {image_path_or_url}: {e}")
            return None

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image to target size
        image = image.resize(self.target_size)
        
        # Convert to numpy array and normalize
        img_array = np.array(image)
        img_array = img_array.astype('float32') / 255.0
        
        return img_array

    def extract_features(self, image_path: str) -> Optional[List[float]]:
        # Check if features are already in cache
        if image_path in self.feature_cache:
            logger.debug(f"Using cached features for {image_path}")
            return self.feature_cache[image_path]
            
        try:
            image = self.load_image(image_path)
            if image is None:
                return None
                
            processed_image = self.preprocess_image(image)
            
            features = []
            
            # Extract color histograms for each channel
            for channel in range(3):
                histogram = np.histogram(
                    processed_image[:,:,channel],
                    bins=32,
                    range=(0, 1)
                )[0]
                histogram = histogram.astype('float32') / histogram.sum()
                features.extend(histogram.tolist())
            
            # Extract statistical features for each channel
            for channel in range(3):
                channel_data = processed_image[:,:,channel]
                features.extend([
                    float(channel_data.mean()),
                    float(channel_data.std()),
                    float(np.median(channel_data)),
                ])
            
            # Cache the features
            self.feature_cache[image_path] = features
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features from {image_path}: {e}")
            return None

    def calculate_similarity(self, features1: List[float], features2: List[float]) -> float:
        """
        Calculate cosine similarity between two feature vectors.
        
        Args:
            features1: First feature vector
            features2: Second feature vector
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            f1 = np.array(features1)
            f2 = np.array(features2)
            
            # Calculate cosine similarity
            similarity = np.dot(f1, f2) / (np.linalg.norm(f1) * np.linalg.norm(f2))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def find_matches(
        self,
        target_features: List[float],
        candidate_features: List[Tuple[int, List[float]]],
        threshold: float = None
    ) -> List[Tuple[int, float]]:
        """
        Find matches for target features among candidates.
        
        Args:
            target_features: Feature vector to match
            candidate_features: List of (id, features) tuples
            threshold: Minimum similarity threshold (default: self.similarity_threshold)
            
        Returns:
            List of (id, similarity) tuples for matches above threshold
        """
        if threshold is None:
            threshold = self.similarity_threshold
            
        matches = []
        for candidate_id, features in candidate_features:
            similarity = self.calculate_similarity(target_features, features)
            if similarity >= threshold:
                matches.append((candidate_id, similarity))
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def compare_with_external_images(
        self,
        local_image_path: str,
        external_images: List[Dict[str, Any]],
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Compare a local image with external images to find matches.
        
        Args:
            local_image_path: Path to local image file
            external_images: List of external image dictionaries
            threshold: Minimum similarity threshold (default: self.similarity_threshold)
            
        Returns:
            List of match dictionaries
        """
        if threshold is None:
            threshold = self.similarity_threshold
            
        matches = []
        
        # Extract features from local image
        local_features = self.extract_features(local_image_path)
        if not local_features:
            logger.error(f"Could not extract features from local image: {local_image_path}")
            return matches
        
        # Process external images in batches for better performance
        batch_size = 10
        for i in range(0, len(external_images), batch_size):
            batch = external_images[i:i+batch_size]
            
            for ext_image in batch:
                try:
                    # Extract features from external image
                    ext_features = self.extract_features(ext_image['photo_url'])
                    if not ext_features:
                        continue
                        
                    # Calculate similarity
                    similarity = self.calculate_similarity(local_features, ext_features)
                    
                    # Add to matches if above threshold
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
                        logger.debug(f"Found match with similarity {similarity:.2f} for external ID {ext_image['id']}")
                        
                except Exception as e:
                    logger.error(f"Error processing external image {ext_image.get('id')}: {e}")
                    continue
        
        # Sort matches by similarity (highest first)
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches
        
    def clear_cache(self):
        """Clear the feature cache to free memory."""
        self.feature_cache.clear()
        logger.info("Feature cache cleared")