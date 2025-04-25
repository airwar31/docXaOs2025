import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config.settings import active_config
from backend.utils.translate_utils import translate_size, translate_fur, translate_gender, translate_category, translate_tail, translate_ears, translate_pet_type

class AnimalAPI:
    BASE_URL = active_config.ANIMAL_API_BASE_URL
    
    @staticmethod
    def get_all_animals(animal_type: str = "all", size: int = 10, page: int = 0) -> List[Dict]:
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
                # First request to get total pages
                initial_params = config['params'].copy()
                initial_params["page"] = 0
                response = requests.get(url, params=initial_params, timeout=10)
                response.raise_for_status()
                response_data = response.json()
                
                if isinstance(response_data, dict) and "content" in response_data:
                    # Get total pages from the response
                    total_pages = response_data.get("totalPages", 1)
                    
                    # Fetch all pages up to the current page + 1 to ensure we have enough data
                    pages_to_fetch = min(total_pages, page + 2)  # Fetch up to page+1 to ensure we have enough data
                    
                    for current_page in range(pages_to_fetch):
                        page_params = config['params'].copy()
                        page_params["page"] = current_page
                        
                        page_response = requests.get(url, params=page_params, timeout=10)
                        page_response.raise_for_status()
                        page_data = page_response.json()
                        
                        if isinstance(page_data, dict) and "content" in page_data:
                            data = page_data.get("content", [])
                            pagination = {
                                "totalPages": page_data.get("totalPages", 1),
                                "totalElements": page_data.get("totalElements", len(data)),
                                "size": page_data.get("size", size),
                                "number": page_data.get("number", 0)
                            }
                            
                            print(f"Успешно загружено {len(data)} животных типа {api_type}, страница {current_page+1}")
                            for animal in data:
                                animal['api_type'] = api_type
                                animal['pagination'] = pagination
                                animals.append(animal)
                        else:
                            print(f"Неверный формат ответа для {api_type}, страница {current_page+1}")
                else:
                    # Handle non-paginated response
                    data = response_data if isinstance(response_data, list) else []
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
    def translate_attribute(attribute_value: str, translation_dict: Dict[str, str]) -> str:
        if not attribute_value:
            return translation_dict.get('UNKNOWN', 'Не указан')
        upper_value = attribute_value.upper()
        
        if upper_value in translation_dict:
            return translation_dict[upper_value]
            
        for key, value in translation_dict.items():
            if key in upper_value:
                return value
                
        return attribute_value
        
    @staticmethod
    def extract_animal_info(animal: Dict) -> Dict:
        info = {
            "id": animal.get("id", "N/A"),
            "category": translate_pet_type(animal.get("api_type", "UNKNOWN")),
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

        info["petName"] = animal.get("petName")
        info["phone"] = animal.get("phone")
        info["foundDate"] = animal.get("foundDate")
        info["placementDate"] = animal.get("placementDate")
        info["location"] = animal.get("location")
        info["additional_info"] = animal.get("additionalInfo")
        info["age"] = animal.get("age")

        characters = animal.get("characters", {})
        if isinstance(characters, dict):
            pet_category = characters.get("petCategory")
            if pet_category:
                info["type_original"] = pet_category
                info["type"] = translate_category(pet_category)
            
            if "gender" in characters:
                gender_value = "MALE" if characters["gender"] else "FEMALE"
                info["gender_original"] = gender_value
                info["gender"] = translate_gender(gender_value)
            
            info["color"] = characters.get("color")
            info["special_marks"] = characters.get("specialSigns")
            
            size_value = characters.get("petSize")
            if size_value:
                info["size_original"] = size_value
                info["size"] = translate_size(size_value)
            
            fur_value = characters.get("hair")
            if fur_value:
                info["fur_original"] = fur_value
                info["fur"] = translate_fur(fur_value)
                
            tail_value = characters.get("tail")
            if tail_value:
                info["tail_original"] = tail_value
                info["tail"] = translate_tail(tail_value)
                
            ears_value = characters.get("ears")
            if ears_value:
                info["ears_original"] = ears_value
                info["ears"] = translate_ears(ears_value)
                
            info["weight"] = characters.get("weight")
        
        breed = animal.get("breed")
        if breed:
            if isinstance(breed, dict):
                info["breed_original"] = breed.get("name")
                info["breed"] = breed.get("name")
                info["breed_aggressive"] = breed.get("isAggressive")
            else:
                info["breed_original"] = str(breed)
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
        
        # Use phone number as contact info if available
        if info["phone"]:
            info["contact_info"] = f"Телефон: {info['phone']}"
        
        info["date"] = info["placementDate"] or info["foundDate"]
        
        if animal.get("id") and animal.get("api_type"):
            info["photos"] = AnimalAPI.get_animal_photos(animal["id"], animal["api_type"])
            # If no photos were found, ensure photo_url is set to a default image
            if not info["photos"]:
                info["photo_url"] = "/static/images/noPhotoAnimals.png"
            else:
                # Set photo_url to the first photo for use in the frontend
                info["photo_url"] = info["photos"][0]
        else:
            info["photos"] = []
            info["photo_url"] = "/static/images/noPhotoAnimals.png"
        
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
        except Exception as e:
            print(f"Error fetching photos for animal {animal_id}: {e}")
            
        return []




















