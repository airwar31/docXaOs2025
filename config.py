import os
class Config:
    SECRET_KEY = os.urandom(24)
    UPLOAD_FOLDER = 'static/uploads'
    DB_NAME = 'petfinder.db'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ANIMAL_API_BASE_URL = "https://animals.admhmao.ru/pets-api/open"
    
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
