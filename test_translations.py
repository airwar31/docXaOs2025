import unittest
from translate_utils import translate_size, translate_fur, translate_tail, translate_ears

class TestTranslations(unittest.TestCase):
    def test_size_translations(self):
        self.assertEqual(translate_size("BIG"), "Большой")
        self.assertEqual(translate_size("LARGE"), "Большой")
        self.assertEqual(translate_size("LITTLE"), "Маленький")
        self.assertEqual(translate_size("MEDIUM"), "Средний")
        self.assertEqual(translate_size("AVERAGE"), "Средний")
        self.assertEqual(translate_size("GIANT"), "Огромный")
        self.assertEqual(translate_size("TINY"), "Крошечный")
        self.assertEqual(translate_size(""), "Не указан")
        self.assertEqual(translate_size(None), "Не указан")
        
    def test_fur_translations(self):
        self.assertEqual(translate_fur("LONGHAIR"), "Длинношерстный")
        self.assertEqual(translate_fur("MEDIUMHAIRED"), "Среднешерстный")        
        self.assertEqual(translate_fur("SHORTHAIR"), "Короткошерстный")
        self.assertEqual(translate_fur("WIREHAIR"), "Жесткошерстный")
        self.assertEqual(translate_fur("CURLY"), "Кудрявый")
        self.assertEqual(translate_fur("HAIRLESS"), "Бесшерстный")
        self.assertEqual(translate_fur(""), "Не указан")
        self.assertEqual(translate_fur(None), "Не указан")
        
    def test_tail_translations(self):
        self.assertEqual(translate_tail("RAISED"), "Поднятый")
        self.assertEqual(translate_tail("STRAIGHT"), "Прямой")
        self.assertEqual(translate_tail("LONG"), "Длинный")
        self.assertEqual(translate_tail("SHORT"), "Короткий")
        self.assertEqual(translate_tail("DOCKED"), "Купированный")
        self.assertEqual(translate_tail(""), "Не указан")
        self.assertEqual(translate_tail(None), "Не указан")
        
    def test_ears_translations(self):
        self.assertEqual(translate_ears("SHORT"), "Короткие")
        self.assertEqual(translate_ears("STANDS"), "Стоячие")
        self.assertEqual(translate_ears("FLOPPY"), "Висячие")
        self.assertEqual(translate_ears("HANGING"), "Висячие")
        self.assertEqual(translate_ears("DOCKED"), "Купированные")
        self.assertEqual(translate_ears("NOT_DOCKED"), "Некупированные")
        self.assertEqual(translate_ears("HALF_LIES"), "Полулежачие")
        self.assertEqual(translate_ears("LIES"), "Лежачие")
        self.assertEqual(translate_ears(""), "Не указаны")
        self.assertEqual(translate_ears(None), "Не указаны")

if __name__ == "__main__":
    # Run the unit tests
    unittest.main(exit=False)



