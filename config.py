import os
from datetime import timedelta

class Config:
    # Generate a secure random secret key
    SECRET_KEY = os.environ.get('SECRET_KEY', ' *y5@8wyGEq5p*c*Aj&FcJE*n#DVMv5=T')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///pets.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder configuration
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    
    # API Configuration
    API_BASE_URL = 'https://animals.admhmao.ru/pets-api/open'
    
    # Image similarity threshold
    IMAGE_SIMILARITY_THRESHOLD = 0.7
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CHECK_INTERVAL_SECONDS = 3600  # Check every hour
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@petfinder.com')
