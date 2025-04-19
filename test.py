import requests
import json
from datetime import datetime
from typing import List, Dict

class AnimalAPI:
    BASE_URL = "https://animals.admhmao.ru/pets-api/open"
    
    @staticmethod
    def get_all_animals(animal_type: str = "all", size: int = 10) -> List[Dict]:
        endpoints = {
            "lost": {"url": "/lost", "params": {"size": size, "sort": "id,desc"}},
            "found": {"url": "/found", "params": {"size": size, "sort": "id,desc"}},
            "find-home": {"url": "/find-home", "params": {"size": size}}
        }
        
        animals = []
        for api_type, config in endpoints.items():
            if animal_type != "all" and api_type != animal_type:
                continue
                
            url = f"{AnimalAPI.BASE_URL}{config['url']}"
            try:
                response = requests.get(url, params=config['params'], timeout=10)
                response.raise_for_status()
                data = response.json().get("content", [])
                
                print(f"Успешно загружено {len(data)} животных типа {api_type}")
                for animal in data:
                    animal['api_type'] = api_type
                    animals.append(animal)
                    
            except Exception as e:
                print(f"Ошибка при загрузке {api_type}: {str(e)}")
        
        return animals

    @staticmethod
    def extract_animal_info(animal: Dict) -> Dict:
        """Улучшенный метод извлечения информации с проверкой всех полей"""
        info = {
            "id": animal.get("id", "N/A"),
            "category": {
                "lost": "Пропавшие",
                "found": "Найденные",
                "find-home": "Ищут дом"
            }.get(animal.get("api_type"), "Неизвестно"),
            "type": "Не указан",
            "gender": "Не указан",
            "breed": "Не указана",
            "color": "Не указан",
            "district": "Не указан",
            "chip": "Нет данных",
            "sterilization": "Нет данных",
            "special_marks": "Нет",
            "date": "Не указана",
            "photos": [],
            "shelter": "Не указано",
            "aviary": "Не указан"
        }

        # Обработка для find-home
        if animal.get("api_type") == "find-home":
            animal_data = animal.get("animal", {})
            characters = animal_data.get("characters", {})
            
            # Тип животного
            if isinstance(characters, dict):
                pet_category = characters.get("petCategory")
                if pet_category:
                    info["type"] = {
                        "DOG": "Собака",
                        "CAT": "Кошка",
                        "OTHER": "Другое"
                    }.get(pet_category, pet_category)
            
            # Пол
            if isinstance(characters, dict) and "gender" in characters:
                info["gender"] = "Мальчик" if characters["gender"] else "Девочка"
            
            # Порода
            breed = animal_data.get("breed")
            if breed:
                if isinstance(breed, dict):
                    info["breed"] = breed.get("name", "Не указана")
                else:
                    info["breed"] = str(breed)
            
            # Окрас и особые приметы
            if isinstance(characters, dict):
                info["color"] = characters.get("color", "Не указан")
                info["special_marks"] = characters.get("specialSigns", "Нет")
            
            # Чип и стерилизация
            info["chip"] = "Да" if animal_data.get("chip") else "Нет"
            info["sterilization"] = "Да" if animal_data.get("sterilization") else "Нет"
            
            # Район
            if animal_data.get("catchMunicipality"):
                if isinstance(animal_data["catchMunicipality"], dict):
                    info["district"] = animal_data["catchMunicipality"].get("name", "Не указан")
            
            # Дата
            info["date"] = animal.get("shelterArrival") or animal_data.get("cardDate") or "Не указана"
            
            # Приют
            if animal.get("shelter"):
                if isinstance(animal["shelter"], dict):
                    org_info = animal["shelter"].get("organizationInformation", {})
                    if isinstance(org_info, dict):
                        info["shelter"] = org_info.get("name", "Не указано")
            
            # Вольер
            info["aviary"] = animal.get("aviary", "Не указан")
        
        # Обработка для lost и found
        else:
            info["type"] = animal.get("animalType", "Не указан")
            info["gender"] = animal.get("gender", "Не указан")
            
            breed = animal.get("breed")
            if breed:
                if isinstance(breed, dict):
                    info["breed"] = breed.get("name", "Не указана")
                else:
                    info["breed"] = str(breed)
            
            info["color"] = animal.get("color", "Не указан")
            info["date"] = animal.get("placementDate", "Не указана")
        
        # Фотографии для всех типов
        if animal.get("id") and animal.get("api_type"):
            info["photos"] = AnimalAPI.get_animal_photos(animal["id"], animal["api_type"])
        
        return info

    @staticmethod
    def get_animal_photos(animal_id: int, api_type: str) -> List[str]:
        """Получает фотографии с проверкой ошибок"""
        endpoints = {
            "lost": "/lost-photo",
            "found": "/found-photo", 
            "find-home": "/find-home"
        }
        
        if api_type not in endpoints:
            return []
        
        url = f"{AnimalAPI.BASE_URL}{endpoints[api_type]}/{animal_id}/files"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            photos = response.json()
            
            if isinstance(photos, list):
                return [f"{url}/{photo['id']}" for photo in photos 
                       if isinstance(photo, dict) and 'id' in photo]
        except:
            pass
            
        return []

def display_animals(animals: List[Dict]):
    """Улучшенный вывод информации о животных"""
    if not animals:
        print("\nЖивотные не найдены")
        return
    
    print(f"\n{'='*50}")
    print(f"ИНФОРМАЦИЯ О ЖИВОТНЫХ (ВСЕГО: {len(animals)})")
    print(f"{'='*50}\n")
    
    for i, animal in enumerate(animals, 1):
        info = AnimalAPI.extract_animal_info(animal)
        
        # Формируем строку с основной информацией
        animal_info = [
            f"Животное #{i}",
            f"Категория: {info['category']}",
            f"ID: {info['id']}",
            f"Тип: {info['type']}",
            f"Пол: {info['gender']}",
            f"Порода: {info['breed']}",
            f"Окрас: {info['color']}",
            f"Район: {info['district']}",
            f"Чип: {info['chip']}",
            f"Стерилизация: {info['sterilization']}",
            f"Особые приметы: {info['special_marks']}",
            f"Дата: {info['date']}"
        ]
        
        # Добавляем дополнительную информацию для "Ищут дом"
        if info['category'] == "Ищут дом":
            animal_info.extend([
                f"Приют: {info['shelter']}",
                f"Вольер: {info['aviary']}"
            ])
        
        # Выводим основную информацию
        print("\n".join(animal_info))
        
        # Фотографии
        if info["photos"]:
            print("\nФотографии:")
            for j, photo in enumerate(info["photos"][:3], 1):
                print(f"{j}. {photo}")
        else:
            print("\nФотографии отсутствуют")
        
        # Добавляем пустую строку между животными вместо разделителей
        print()

if __name__ == "__main__":
    print("Начинаем загрузку данных...\n")
    
    # Получаем данные
    animals = AnimalAPI.get_all_animals(animal_type="all", size=10)
    
    # Выводим информацию
    display_animals(animals)
    
    # Сохраняем полные данные
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"animals_full_data_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(animals, f, ensure_ascii=False, indent=2)
    
    print(f"\nПолные данные сохранены в файл: {filename}")