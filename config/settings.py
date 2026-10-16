import os
import secrets
from pathlib import Path

# Load .env file if python-dotenv is installed and file exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

class Config:
    ANIMAL_API_BASE_URL = os.getenv("ANIMAL_API_BASE_URL", "https://animals.admhmao.ru/pets-api/open")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
    
    # Secret key for sessions. Fallback to stable secret from env or auto-generated token
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(24))
    
    DB_NAME = os.getenv("DB_NAME", "petfinder.db")
    
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "5000"))
    FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "8080"))
    
    SESSION_LIFETIME = int(os.getenv("SESSION_LIFETIME", "30"))
    
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_FILE = os.getenv("LOGGING_FILE", "petfinder.log")
    
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    
    # Telegram Bot Token (obtain from @BotFather)
    TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN", "")

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

env_mode = os.getenv("FLASK_ENV", "development").lower()
active_config = config_map.get(env_mode, DevelopmentConfig)
