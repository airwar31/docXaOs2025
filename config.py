import os
class Config:
    SECRET_KEY = os.urandom(24)
    UPLOAD_FOLDER = 'static/uploads'
    DB_NAME = 'petfinder.db'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ANIMAL_API_BASE_URL = "https://animals.admhmao.ru/pets-api/open"
    
    TELEGRAM_API_TOKEN = '7237195300:AAFo-56TNpLaxOl28k49_8htoJCVQfE13sU'
    
    # Translation dictionaries for pet attributes
    SIZE_TRANSLATIONS = {
        'LITTLE': 'Маленький',
        'AVERAGE': 'Средний',
        'MEDIUM': 'Средний',
        'LARGE': 'Большой',
        'GIANT': 'Огромный',
        'TINY': 'Крошечный',
        'BIG': 'Большой',
        'UNKNOWN': 'Не указан'
    }
    
    FUR_TRANSLATIONS = {
        'SHORTHAIR': 'Короткошерстный',
        'MEDIUMHAIRED':"Среднешерстный",
        'LONGHAIR': 'Длинношерстный',
        'WIREHAIR': 'Жесткошерстный',
        'CURLY': 'Кудрявый',
        'HAIRLESS': 'Бесшерстный',
        'UNKNOWN': 'Не указан'
    }
    
    GENDER_TRANSLATIONS = {
        'MALE': 'Мальчик',
        'FEMALE': 'Девочка',
        'UNKNOWN': 'Не указан'
    }
    
    CATEGORY_TRANSLATIONS = {
        'DOG': 'Собака',
        'CAT': 'Кошка',
        'OTHER': 'Другое',
        'UNKNOWN': 'Не указан'
    }
    TAIL_TRANSLATIONS = {
        'RAISED': 'Поднятый',
        'LONG': 'Длинный',
        'STRAIGHT': 'Прямой',
        'SHORT': 'Короткий',
        'DOCKED': 'Купированный',
        'UNKNOWN': 'Не указан'
    }
    
    EARS_TRANSLATIONS = {
        'SHORT': 'Короткие',
        'STANDS': 'Стоячие',
        'FLOPPY': 'Висячие',
        'HANGING': 'Висячие',
        'DOCKED': 'Купированные',
        'NOT_DOCKED': 'Некупированные',
        'HALF_LIES': 'Полулежачие',
        'LIES': 'Лежачие',
        'UNKNOWN': 'Не указаны'
    }

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


