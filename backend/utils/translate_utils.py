def translate_size(size_value: str) -> str:

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
    GENDER_TRANSLATIONS = {
        'MALE': 'Мальчик',
        'FEMALE': 'Девочка',
        'UNKNOWN': 'Не указан'
    }
    
    return _translate_attribute(gender_value, GENDER_TRANSLATIONS)

def translate_category(category_value: str) -> str:

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
    
    if isinstance(category_value, str):
        if category_value.lower() == "dog":
            return "Собака"
        elif category_value.lower() == "собака":
            return "Собака"
        elif category_value.lower() == "cat":
            return "Кошка"
        elif category_value.lower() == "кошка":
            return "Кошка"
    
    return _translate_attribute(category_value, CATEGORY_TRANSLATIONS)

def translate_tail(tail_value: str) -> str:

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

    TYPE_TRANSLATIONS = {
        'LOST': 'Пропавшие',
        'FOUND': 'Найденный',
        'FIND-HOME': 'Ищут дом',
        'ПРОПАВШИЕ': 'Пропавшие',
        'НАЙДЕННЫЕ': 'Найденный',
        'НАЙДЕННЫЙ': 'Найденный',
        'ИЩУТ ДОМ': 'Ищут дом',
        'ПРОПАВШИЙ': 'Пропавшие',
        'UNKNOWN': 'Найденный' 
    }

    if isinstance(type_value, str):
        if type_value.lower() == "lost":
            return "Пропавшие"
        elif type_value.lower() == "пропавшие" or type_value.lower() == "пропавший":
            return "Пропавшие"
        elif type_value.lower() == "found" or type_value.lower() == "найденный" or type_value.lower() == "найденные":
            return "Найденный"
    
    return _translate_attribute(type_value, TYPE_TRANSLATIONS)

def _translate_attribute(attribute_value: str, translation_dict: dict) -> str:

    if not attribute_value:
        return translation_dict.get('UNKNOWN', 'Не указан')
    
    if not isinstance(attribute_value, str):
        attribute_value = str(attribute_value)
    
    upper_value = attribute_value.upper()
    
    if upper_value in translation_dict:
        return translation_dict[upper_value]
    
    lower_value = attribute_value.lower()
    for key, value in translation_dict.items():
        if key.lower() == lower_value:
            return value
    
    for key, value in translation_dict.items():
        if key in upper_value:
            return value
            
    return attribute_value




















