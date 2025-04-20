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
            "additional_info": None
        }

        characters = animal.get("characters", {})
        if not characters and "animal" in animal:
            characters = animal.get("animal", {}).get("characters", {})

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
        
        breed = animal.get("breed")
        if breed:
            if isinstance(breed, dict):
                info["breed"] = breed.get("name")

                info["breed_aggressive"] = breed.get("isAggressive")
            else:
                info["breed"] = str(breed)
        
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
        
        info["phone"] = animal.get("phone")
        info["location"] = animal.get("location")
        info["date"] = animal.get("placementDate") or animal.get("lostDate")
        info["age"] = animal.get("age")
        info["additional_info"] = animal.get("additionalInfo")
        
        if info["phone"]:
            info["contact_info"] = f"Телефон: {info['phone']}"
        
        if animal.get("api_type") == "find-home":
            animal_data = animal.get("animal", {})
            
            if not info["type"]:
                if isinstance(animal_data.get("characters"), dict):
                    pet_category = animal_data["characters"].get("petCategory")
                    if pet_category:
                        info["type"] = {
                            "DOG": "Собака",
                            "CAT": "Кошка",
                            "OTHER": "Другое"
                        }.get(pet_category, pet_category)
            
            if not info["breed"] and animal_data.get("breed"):
                if isinstance(animal_data["breed"], dict):
                    info["breed"] = animal_data["breed"].get("name")
                else:
                    info["breed"] = str(animal_data["breed"])
            
            if animal.get("shelter"):
                if isinstance(animal["shelter"], dict):
                    org_info = animal["shelter"].get("organizationInformation", {})
                    if isinstance(org_info, dict):
                        info["shelter"] = org_info.get("name")
                        contact_phone = org_info.get("phone")
                        contact_email = org_info.get("email")
                        if contact_phone or contact_email:
                            contacts = []
                            if contact_phone:
                                contacts.append(f"Телефон: {contact_phone}")
                            if contact_email:
                                contacts.append(f"Email: {contact_email}")
                            info["contact_info"] = ", ".join(contacts)
            
            info["aviary"] = animal.get("aviary")
            
            if not info["location"]:
                info["location"] = animal_data.get("location") or animal.get("location")
            
            if not info["date"]:
                info["date"] = animal.get("shelterArrival") or animal_data.get("cardDate")
        
        else:
            if not info["type"]:
                info["type"] = animal.get("animalType")
            
            if not info["gender"]:
                info["gender"] = animal.get("gender")
            
            if not info["color"]:
                info["color"] = animal.get("color")
            
            if not info["district"] and animal.get("district"):
                info["district"] = animal.get("district")
            
            info["chip"] = animal.get("chip")
            info["sterilization"] = animal.get("sterilization")
            
            if not info["special_marks"]:
                info["special_marks"] = animal.get("special_marks")
            
            if not info["size"]:
                info["size"] = animal.get("size")
            
            if not info["fur"]:
                info["fur"] = animal.get("fur")
            
            if not info["contact_info"]:
                contact_phone = animal.get("phone")
                contact_email = animal.get("email")
                if contact_phone or contact_email:
                    contacts = []
                    if contact_phone:
                        contacts.append(f"Телефон: {contact_phone}")
                    if contact_email:
                        contacts.append(f"Email: {contact_email}")
                    info["contact_info"] = ", ".join(contacts)
        
        if animal.get("id") and animal.get("api_type"):
            info["photos"] = AnimalAPI.get_animal_photos(animal["id"], animal["api_type"])
        
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
            "additional_info": "Нет дополнительной информации"
        }
        
        for key, default_msg in display_messages.items():
            if info[key] is None:
                info[key] = default_msg
        
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
            f"Описание: {info['description']}"
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









