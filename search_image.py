import os
import cv2
import numpy as np
from sklearn.neighbors import NearestNeighbors

class SIFTImageSearch:
    def __init__(self, image_dir):
        self.image_dir = image_dir
        self.image_paths = []
        self.descriptors = []
        self.sift = cv2.SIFT_create()
        self.knn = NearestNeighbors(n_neighbors=5, metric='euclidean')
        
    def build_index(self):
        # Сбор всех изображений в директории
        self.image_paths = [os.path.join(self.image_dir, f) 
                          for f in os.listdir(self.image_dir) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # Извлечение дескрипторов для каждого изображения
        for img_path in self.image_paths:
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            _, des = self.sift.detectAndCompute(img, None)
            if des is not None:
                # Берем среднее всех дескрипторов для изображения
                avg_des = np.mean(des, axis=0)
                self.descriptors.append(avg_des)
            else:
                self.descriptors.append(np.zeros(128))  # Размерность SIFT дескриптора
        
        # Построение индекса для поиска ближайших соседей
        self.knn.fit(self.descriptors)
    
    def search_similar(self, query_img_path, k=5):
        # Обработка запросного изображения
        query_img = cv2.imread(query_img_path, cv2.IMREAD_GRAYSCALE)
        _, des = self.sift.detectAndCompute(query_img, None)
        
        if des is None:
            return []
        
        avg_des = np.mean(des, axis=0).reshape(1, -1)
        
        # Поиск k ближайших соседей
        distances, indices = self.knn.kneighbors(avg_des, n_neighbors=k)
        
        # Возврат результатов
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            results.append({
                'image_path': self.image_paths[idx],
                'distance': dist
            })
        
        return results