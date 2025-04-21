import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class AnimalAPI:
    """
    Class for interacting with the external animal API.
    Provides methods to fetch animal data and extract relevant information.
    """
    BASE_URL = "https://animals.admhmao.ru/pets-api/open"
    
    @staticmethod
    def get_all_animals(animal_type: str = "all", size: int = 10) -> List[Dict]:
        endpoints = {
            "lost": {"url": "/lost", "params": {"size": size, "sort": "placementDate,desc"}},
            "found": {"url": "/found", "params": {"size": size, "sort": "placementDate,desc"}},
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
                response_data = response.json()
                
                if isinstance(response_data, dict) and "content" in response_data:
                    data = response_data.get("content", [])
                    pagination = {
                        "totalPages": response_data.get("totalPages", 1),
                        "totalElements": response_data.get("totalElements", len(data)),
                        "size": response_data.get("size", size),
                        "number": response_data.get("number", 0)
                    }
                else:
                    data = response_data
                    pagination = {}
                
                print(f"Успешно загружено {len(data)} животных типа {api_type}")
                for animal in data:
                    animal['api_type'] = api_type
                    animal['pagination'] = pagination
                    animals.append(animal)
                    
            except Exception as e:
                print(f"Ошибка при загрузке {api_type}: {str(e)}")
        
        return animals

    @staticmethod
    def extract_animal_info(animal: Dict) -> Dict:
        info = {
            "id": animal.get("id", "N/A"),
            "category": {
                "lost": "Пропавшие",
                "found": "Найденные",
                "find-home": "Ищут дом"
            }.get(animal.get("api_type"), "Неизвестно"),
            "type": None,
            "gender": None,
            "breed": None,
            "color": None,
            "district": None,
            "chip": None,
            "sterilization": None,
            "special_marks": None,
            "date": None,
            "photos": [],
            "shelter": None,
            "aviary": None,
            "description": None,
            "size": None,
            "fur": None,
            "location": None,
            "age": None,
            "contact_info": None,
            "tail": None,
            "ears": None,
            "weight": None,
            "coordinates": None,
            "municipality": None,
            "additional_info": None,
            "petName": None,
            "foundDate": None,
            "placementDate": None,
            "phone": None
        }

        # Extract basic information directly from the animal object
        info["petName"] = animal.get("petName")
        info["phone"] = animal.get("phone")
        info["foundDate"] = animal.get("foundDate")
        info["placementDate"] = animal.get("placementDate")
        info["location"] = animal.get("location")
        info["additional_info"] = animal.get("additionalInfo")
        info["age"] = animal.get("age")

        # Extract characters information
        characters = animal.get("characters", {})
        if isinstance(characters, dict):
            pet_category = characters.get("petCategory")
            if pet_category:
                info["type"] = {
                    "DOG": "Собака",
                    "CAT": "Кошка",
                    "OTHER": "Другое"
                }.get(pet_category, pet_category)
            
            if "gender" in characters:
                info["gender"] = "Мальчик" if characters["gender"] else "Девочка"
            
            info["color"] = characters.get("color")
            info["special_marks"] = characters.get("specialSigns")
            info["size"] = characters.get("petSize") 
            info["fur"] = characters.get("hair")  
            info["tail"] = characters.get("tail")  
            info["ears"] = characters.get("ears")  
            info["weight"] = characters.get("weight")
        
        # Extract breed information
        breed = animal.get("breed")
        if breed:
            if isinstance(breed, dict):
                info["breed"] = breed.get("name")
                info["breed_aggressive"] = breed.get("isAggressive")
            else:
                info["breed"] = str(breed)
        
        # Extract municipality and coordinates
        municipality = animal.get("dicMunicipality")
        if municipality and isinstance(municipality, dict):
            info["municipality"] = municipality.get("name")
            
            coordinates = municipality.get("coordinate")
            if coordinates and isinstance(coordinates, dict):
                info["coordinates"] = {
                    "lat": coordinates.get("coordY"),
                    "lng": coordinates.get("coordX")
                }
            
            if "showOkrug" in municipality and isinstance(municipality["showOkrug"], dict):
                info["district"] = municipality["showOkrug"].get("name")
        
        # Set contact information
        if info["phone"]:
            info["contact_info"] = f"Телефон: {info['phone']}"
        
        # Set date information
        info["date"] = info["placementDate"] or info["foundDate"]
        
        # Get photos
        if animal.get("id") and animal.get("api_type"):
            info["photos"] = AnimalAPI.get_animal_photos(animal["id"], animal["api_type"])
        
        # Set default values for missing information
        display_messages = {
            "type": "Не указан",
            "gender": "Не указан",
            "breed": "Не указана",
            "color": "Не указан",
            "district": "Не указан",
            "chip": "Нет данных",
            "sterilization": "Нет данных",
            "special_marks": "Нет",
            "date": "Не указана",
            "shelter": "Не указано",
            "aviary": "Не указан",
            "size": "Не указан",
            "fur": "Не указана",
            "location": "Не указано",
            "age": "Не указан",
            "contact_info": "Контактная информация отсутствует",
            "tail": "Не указан",
            "ears": "Не указаны",
            "weight": "Не указан",
            "municipality": "Не указан",
            "additional_info": "Нет дополнительной информации",
            "petName": "Без имени",
            "foundDate": "Не указана",
            "placementDate": "Не указана",
            "phone": "Не указан"
        }
        
        for key, default_msg in display_messages.items():
            if info[key] is None:
                info[key] = default_msg
        
        # Build description from available information
        description_parts = []
        if info["breed"] != "Не указана":
            description_parts.append(f"Порода: {info['breed']}")
        if info["type"] != "Не указан":
            description_parts.append(f"Категория: {info['type']}")
        if info["gender"] != "Не указан":
            description_parts.append(f"Пол: {info['gender']}")
        if info["size"] != "Не указан":
            description_parts.append(f"Размер: {info['size']}")
        if info["fur"] != "Не указана":
            description_parts.append(f"Шерсть: {info['fur']}")
        if info["tail"] != "Не указан":
            description_parts.append(f"Хвост: {info['tail']}")
        if info["ears"] != "Не указаны":
            description_parts.append(f"Уши: {info['ears']}")
        if info["weight"] != "Не указан":
            description_parts.append(f"Вес: {info['weight']}")
        if info["date"] != "Не указана":
            description_parts.append(f"Дата: {info['date']}")
        if info["district"] != "Не указан":
            description_parts.append(f"Район: {info['district']}")
        if info["municipality"] != "Не указан":
            description_parts.append(f"Муниципалитет: {info['municipality']}")
        if info["location"] != "Не указано":
            description_parts.append(f"Место: {info['location']}")
        if info["age"] != "Не указан":
            description_parts.append(f"Возраст: {info['age']}")
        if info["special_marks"] != "Нет":
            description_parts.append(f"Особые приметы: {info['special_marks']}")
        if info["additional_info"] != "Нет дополнительной информации":
            description_parts.append(f"Дополнительная информация: {info['additional_info']}")
            
        if description_parts:
            info["description"] = ". ".join(description_parts)
        else:
            info["description"] = "Описание отсутствует"
        
        return info
        
    @staticmethod
    def get_animal_photos(animal_id: int, api_type: str) -> List[str]:
        """
        Get photo URLs for an animal.
        
        Args:
            animal_id: ID of the animal
            api_type: Type of animal ("lost", "found", "find-home")
            
        Returns:
            List of photo URLs
        """
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
        except Exception as e:
            print(f"Error fetching photos for animal {animal_id}: {e}")
            
        return []

def display_animals(animals: List[Dict]):
    """
    Display information about animals in a formatted way.
    
    Args:
        animals: List of animal dictionaries
    """
    if not animals:
        print("\nЖивотные не найдены")
        return
    
    print(f"\n{'='*50}")
    print(f"ИНФОРМАЦИЯ О ЖИВОТНЫХ (ВСЕГО: {len(animals)})")
    print(f"{'='*50}\n")
    
    for i, animal in enumerate(animals, 1):
        info = AnimalAPI.extract_animal_info(animal)
        
        animal_info = [
            f"Животное #{i}",
            f"Категория: {info['category']}",
            f"ID: {info['id']}",
            f"Имя: {info['petName']}",
            f"Тип: {info['type']}",
            f"Пол: {info['gender']}",
            f"Порода: {info['breed']}",
            f"Окрас: {info['color']}",
            f"Район: {info['district']}",
            f"Телефон: {info['phone']}",
            f"Место: {info['location']}",
            f"Дата размещения: {info['placementDate']}",
            f"Дата находки: {info['foundDate']}",
            f"Особые приметы: {info['special_marks']}",
            f"Дополнительная информация: {info['additional_info']}"
        ]
        
        if info['category'] == "Ищут дом":
            animal_info.extend([
                f"Приют: {info['shelter']}",
                f"Вольер: {info['aviary']}"
            ])
        
        print("\n".join(animal_info))
        
        if info["photos"]:
            print("\nФотографии:")
            for j, photo in enumerate(info["photos"][:3], 1):
                print(f"{j}. {photo}")
        else:
            print("\nФотографии отсутствуют")
        
        print()

if __name__ == "__main__":
    print("Начинаем загрузку данных...\n")
    
    animals = AnimalAPI.get_all_animals(animal_type="all", size=10)
    
    display_animals(animals)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"animals_full_data_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(animals, f, ensure_ascii=False, indent=2)
    
    print(f"\nПолные данные сохранены в файл: {filename}")