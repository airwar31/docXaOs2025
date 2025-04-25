"""
Tests for the translate_utils module.
"""
import unittest
from backend.utils.translate_utils import (
    translate_size, translate_fur, translate_gender, 
    translate_category, translate_tail, translate_ears
)

class TestTranslateUtils(unittest.TestCase):
    """Test cases for the translate_utils module."""
    
    def test_translate_size(self):
        """Test the translate_size function."""
        self.assertEqual(translate_size('LITTLE'), 'Маленький')
        self.assertEqual(translate_size('AVERAGE'), 'Средний')
        self.assertEqual(translate_size('MEDIUM'), 'Средний')
        self.assertEqual(translate_size('LARGE'), 'Большой')
        self.assertEqual(translate_size('GIANT'), 'Огромный')
        self.assertEqual(translate_size('TINY'), 'Крошечный')
        self.assertEqual(translate_size('BIG'), 'Большой')
        self.assertEqual(translate_size('UNKNOWN'), 'Не указан')
        self.assertEqual(translate_size(None), 'Не указан')
        self.assertEqual(translate_size(''), 'Не указан')
        
    def test_translate_fur(self):
        """Test the translate_fur function."""
        self.assertEqual(translate_fur('SHORTHAIR'), 'Короткошерстный')
        self.assertEqual(translate_fur('MEDIUMHAIRED'), 'Среднешерстный')
        self.assertEqual(translate_fur('LONGHAIR'), 'Длинношерстный')
        self.assertEqual(translate_fur('WIREHAIR'), 'Жесткошерстный')
        self.assertEqual(translate_fur('CURLY'), 'Кудрявый')
        self.assertEqual(translate_fur('HAIRLESS'), 'Бесшерстный')
        self.assertEqual(translate_fur('UNKNOWN'), 'Не указан')
        self.assertEqual(translate_fur(None), 'Не указан')
        self.assertEqual(translate_fur(''), 'Не указан')
        
    def test_translate_gender(self):
        """Test the translate_gender function."""
        self.assertEqual(translate_gender('MALE'), 'Мальчик')
        self.assertEqual(translate_gender('FEMALE'), 'Девочка')
        self.assertEqual(translate_gender('UNKNOWN'), 'Не указан')
        self.assertEqual(translate_gender(None), 'Не указан')
        self.assertEqual(translate_gender(''), 'Не указан')
        
    def test_translate_category(self):
        """Test the translate_category function."""
        self.assertEqual(translate_category('DOG'), 'Собака')
        self.assertEqual(translate_category('CAT'), 'Кошка')
        self.assertEqual(translate_category('OTHER'), 'Другое')
        self.assertEqual(translate_category('UNKNOWN'), 'Не указан')
        self.assertEqual(translate_category(None), 'Не указан')
        self.assertEqual(translate_category(''), 'Не указан')
        
    def test_translate_tail(self):
        """Test the translate_tail function."""
        self.assertEqual(translate_tail('RAISED'), 'Поднятый')
        self.assertEqual(translate_tail('LONG'), 'Длинный')
        self.assertEqual(translate_tail('STRAIGHT'), 'Прямой')
        self.assertEqual(translate_tail('SHORT'), 'Короткий')
        self.assertEqual(translate_tail('DOCKED'), 'Купированный')
        self.assertEqual(translate_tail('UNKNOWN'), 'Не указан')
        self.assertEqual(translate_tail(None), 'Не указан')
        self.assertEqual(translate_tail(''), 'Не указан')
        
    def test_translate_ears(self):
        """Test the translate_ears function."""
        self.assertEqual(translate_ears('SHORT'), 'Короткие')
        self.assertEqual(translate_ears('STANDS'), 'Стоячие')
        self.assertEqual(translate_ears('FLOPPY'), 'Висячие')
        self.assertEqual(translate_ears('HANGING'), 'Висячие')
        self.assertEqual(translate_ears('DOCKED'), 'Купированные')
        self.assertEqual(translate_ears('NOT_DOCKED'), 'Некупированные')
        self.assertEqual(translate_ears('HALF_LIES'), 'Полулежачие')
        self.assertEqual(translate_ears('LIES'), 'Лежачие')
        self.assertEqual(translate_ears('UNKNOWN'), 'Не указаны')
        self.assertEqual(translate_ears(None), 'Не указаны')
        self.assertEqual(translate_ears(''), 'Не указаны')
        
    def test_case_insensitivity(self):
        """Test that the translation functions are case-insensitive."""
        self.assertEqual(translate_size('little'), 'Маленький')
        self.assertEqual(translate_fur('shorthair'), 'Короткошерстный')
        self.assertEqual(translate_gender('male'), 'Мальчик')
        self.assertEqual(translate_category('dog'), 'Собака')
        self.assertEqual(translate_tail('raised'), 'Поднятый')
        self.assertEqual(translate_ears('short'), 'Короткие')
        
    def test_partial_match(self):
        """Test that the translation functions can handle partial matches."""
        self.assertEqual(translate_size('LITTLE_DOG'), 'Маленький')
        self.assertEqual(translate_fur('SHORTHAIR_CAT'), 'Короткошерстный')
        
if __name__ == '__main__':
    unittest.main()