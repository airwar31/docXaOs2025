"""
Configuration settings for the Pet Finder application.
This module contains configuration settings used throughout the application.
"""
import os

class Config:
    # API configuration
    ANIMAL_API_BASE_URL = "https://animals.admhmao.ru/pets-api/open"
    API_TIMEOUT = 10
    
    # Security configuration
    SECRET_KEY = os.urandom(24)
    
    # Database configuration
    DB_NAME = 'petfinder.db'
    
    # Upload configuration
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Server configuration
    SERVER_HOST = '0.0.0.0'
    API_PORT = 5000
    FRONTEND_PORT = 8080
    
    # Session configuration
    SESSION_LIFETIME = 30  # days
    
    # Logging configuration
    LOGGING_LEVEL = 'INFO'
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_FILE = 'petfinder.log'
    
    # Similarity detection configuration
    SIMILARITY_THRESHOLD = 0.7
    
    # Telegram configuration
    TELEGRAM_API_TOKEN = '7237195300:AAFo-56TNpLaxOl28k49_8htoJCVQfE13sU'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    DB_NAME = 'test_petfinder.db'

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

active_config = config_map.get('development', DevelopmentConfig)

