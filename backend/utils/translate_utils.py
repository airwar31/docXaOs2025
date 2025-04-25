"""
Utility functions for translating animal attributes from API responses to human-readable format.
These functions are used to standardize and translate various animal characteristics.
"""

def translate_size(size_value: str) -> str:
    """
    Translate animal size values to standardized format.
    
    Args:
        size_value: The original size value from the API
        
    Returns:
        Translated size in human-readable format
    """
    SIZE_TRANSLATIONS = {
        'LITTLE': 'Маленький',
        'AVERAGE': 'Средний',
        'MEDIUM': 'Средний',
        'LARGE': 'Большой',
        'GIANT': 'Огромный',
        'TINY': 'Крошечный',
        'BIG': 'Большой',
        'SMALL': 'Маленький',
        'EXTRA_LARGE': 'Очень большой',
        'UNKNOWN': 'Не указан'
    }
    
    return _translate_attribute(size_value, SIZE_TRANSLATIONS)

def translate_fur(fur_value: str) -> str:
    """
    Translate animal fur/hair values to standardized format.
    
    Args:
        fur_value: The original fur/hair value from the API
        
    Returns:
        Translated fur description in human-readable format
    """
    FUR_TRANSLATIONS = {
        'SHORTHAIR': 'Короткошерстный',
        'MEDIUMHAIRED': 'Среднешерстный',
        'LONGHAIR': 'Длинношерстный',
        'WIREHAIR': 'Жесткошерстный',
        'CURLY': 'Кудрявый',
        'HAIRLESS': 'Бесшерстный',
        'SHORT': 'Короткая',
        'MEDIUM': 'Средней длины',
        'LONG': 'Длинная',
        'WIRE': 'Жесткая',
        'UNKNOWN': 'Не указан'
    }
    
    return _translate_attribute(fur_value, FUR_TRANSLATIONS)

def translate_gender(gender_value: str) -> str:
    """
    Translate animal gender values to standardized format.
    
    Args:
        gender_value: The original gender value from the API
        
    Returns:
        Translated gender in human-readable format
    """
    GENDER_TRANSLATIONS = {
        'MALE': 'Мальчик',
        'FEMALE': 'Девочка',
        'UNKNOWN': 'Не указан'
    }
    
    return _translate_attribute(gender_value, GENDER_TRANSLATIONS)

def translate_category(category_value: str) -> str:
    """
    Translate animal category values to standardized format.
    
    Args:
        category_value: The original category value from the API
        
    Returns:
        Translated category in human-readable format
    """
    CATEGORY_TRANSLATIONS = {
        'DOG': 'Собака',
        'CAT': 'Кошка',
        'OTHER': 'Другое',
        'BIRD': 'Птица',
        'RODENT': 'Грызун',
        'REPTILE': 'Рептилия',
        'AMPHIBIAN': 'Амфибия',
        'FISH': 'Рыба',
        'ARTHROPOD': 'Членистоногое',
        'UNKNOWN': 'Не указан',
        # Add Russian translations
        'СОБАКА': 'Собака',
        'КОШКА': 'Кошка',
        'ДРУГОЕ': 'Другое',
        'ПТИЦА': 'Птица',
        'ГРЫЗУН': 'Грызун',
        'РЕПТИЛИЯ': 'Рептилия',
        'АМФИБИЯ': 'Амфибия',
        'РЫБА': 'Рыба',
        'ЧЛЕНИСТОНОГОЕ': 'Членистоногое'
    }
    
    return _translate_attribute(category_value, CATEGORY_TRANSLATIONS)

def translate_tail(tail_value: str) -> str:
    """
    Translate animal tail values to standardized format.
    
    Args:
        tail_value: The original tail value from the API
        
    Returns:
        Translated tail description in human-readable format
    """
    TAIL_TRANSLATIONS = {
        'RAISED': 'Поднятый',
        'LONG': 'Длинный',
        'STRAIGHT': 'Прямой',
        'SHORT': 'Короткий',
        'DOCKED': 'Купированный',
        'NONE': 'Отсутствует',
        'UNKNOWN': 'Не указан'
    }
    
    return _translate_attribute(tail_value, TAIL_TRANSLATIONS)

def translate_ears(ears_value: str) -> str:
    """
    Translate animal ears values to standardized format.
    
    Args:
        ears_value: The original ears value from the API
        
    Returns:
        Translated ears description in human-readable format
    """
    EARS_TRANSLATIONS = {
        'SHORT': 'Короткие',
        'STANDS': 'Стоячие',
        'FLOPPY': 'Висячие',
        'HANGING': 'Висячие',
        'DOCKED': 'Купированные',
        'NOT_DOCKED': 'Некупированные',
        'HALF_LIES': 'Полулежачие',
        'LIES': 'Лежачие',
        'ERECT': 'Стоячие',
        'SEMI_ERECT': 'Полустоячие',
        'DROOPING': 'Висячие',
        'FOLDED': 'Сложенные',
        'CROPPED': 'Купированные',
        'UNKNOWN': 'Не указаны'
    }
    
    return _translate_attribute(ears_value, EARS_TRANSLATIONS)

def translate_pet_type(type_value: str) -> str:
    """
    Translate pet type values (lost, found, etc.) to standardized format.
    
    Args:
        type_value: The original type value
        
    Returns:
        Translated type in human-readable format
    """
    TYPE_TRANSLATIONS = {
        'LOST': 'Пропавшие',
        'FOUND': 'Найденные',
        'FIND-HOME': 'Ищут дом',
        'ПРОПАВШИЕ': 'Пропавшие',
        'НАЙДЕННЫЕ': 'Найденные',
        'ИЩУТ ДОМ': 'Ищут дом',
        'ПРОПАВШИЙ': 'Пропавшие',
        'НАЙДЕННЫЙ': 'Найденные',
        'UNKNOWN': 'Неизвестно'
    }
    
    return _translate_attribute(type_value, TYPE_TRANSLATIONS)

def _translate_attribute(attribute_value: str, translation_dict: dict) -> str:
    """
    Helper function to translate attribute values using a translation dictionary.
    
    Args:
        attribute_value: The original attribute value
        translation_dict: Dictionary mapping original values to translated values
        
    Returns:
        Translated attribute value
    """
    if not attribute_value:
        return translation_dict.get('UNKNOWN', 'Не указан')
    
    upper_value = attribute_value.upper()
    
    if upper_value in translation_dict:
        return translation_dict[upper_value]
        
    for key, value in translation_dict.items():
        if key in upper_value:
            return value
            
    return attribute_value














