from typing import Dict
from config import active_config

def translate_attribute(attribute_value: str, translation_dict: Dict[str, str]) -> str:
    """Translate attribute values using the provided dictionary"""
    if not attribute_value:
        return translation_dict.get('UNKNOWN', 'Не указан')
        
    # Convert to uppercase for case-insensitive matching
    upper_value = attribute_value.upper()
    
    if upper_value in translation_dict:
        return translation_dict[upper_value]
        
    for key, value in translation_dict.items():
        if key in upper_value:
            return value
            
    return attribute_value

def translate_size(size_value: str) -> str:
    return translate_attribute(size_value, active_config.SIZE_TRANSLATIONS)

def translate_fur(fur_value: str) -> str:
    return translate_attribute(fur_value, active_config.FUR_TRANSLATIONS)

def translate_gender(gender_value: str) -> str:
    return translate_attribute(gender_value, active_config.GENDER_TRANSLATIONS)

def translate_category(category_value: str) -> str:
    return translate_attribute(category_value, active_config.CATEGORY_TRANSLATIONS)

def translate_tail(tail_value: str) -> str:
    return translate_attribute(tail_value, active_config.TAIL_TRANSLATIONS)

def translate_ears(ears_value: str) -> str:
    return translate_attribute(ears_value, active_config.EARS_TRANSLATIONS)
