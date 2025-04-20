from animal_api import AnimalAPI
import json
print("Testing AnimalAPI.get_all_animals...")
animals = AnimalAPI.get_all_animals(animal_type="lost", size=2)
print(f"Retrieved {len(animals)} animals")
if animals:
    print("\nTesting AnimalAPI.get_animal_photos...")
    animal_id = animals[0].get("id")
    photos = AnimalAPI.get_animal_photos(animal_id, "lost")
    print(f"Retrieved {len(photos)} photos for animal {animal_id}")
print("\nTesting AnimalAPI.extract_animal_info with new JSON structure...")
test_animal = {
    "id": 85,
    "phone": "9044670390",
    "placementDate": "2025-03-10",
    "lostDate": "2025-03-10",
    "location": "ул. Садовая 13.",
    "petName": "Василиса",
    "coordinate": None,
    "characters": {
        "gender": False,
        "petSize": "AVERAGE",
        "hair": "SHORTHAIR",
        "tail": "STRAIGHT",
        "ears": "SHORT",
        "petCategory": "DOG",
        "color": "Светлая с рыжими и черными пятнами",
        "specialSigns": None,
        "weight": None
    },
    "breed": {
        "id": 92,
        "name": "Метис",
        "isAggressive": False
    },
    "age": 8,
    "additionalInfo": "Без ошейника, шустрая.",
    "dicMunicipality": {
        "id": 193,
        "name": "г Мегион",
        "coordinate": {
            "coordX": 76.098187,
            "coordY": 61.033157
        },
        "okato": 71133000000,
        "okrug": {
            "id": 97,
            "oktmo": 71873000,
            "name": "город Мегион",
            "dicTypeMo": {
                "id": 2,
                "name": "Городской округ"
            },
            "okrug": {
                "id": 2,
                "oktmo": 71800000,
                "name": "Ханты-Мансийский автономный округ - Югра",
                "dicTypeMo": {
                    "id": 5,
                    "name": "Субъект"
                },
                "okrug": None,
                "firstOrder": False
            },
            "firstOrder": True
        },
        "showOkrug": {
            "id": 97,
            "oktmo": 71873000,
            "name": "город Мегион",
            "dicTypeMo": {
                "id": 2,
                "name": "Городской округ"
            },
            "okrug": {
                "id": 2,
                "oktmo": 71800000,
                "name": "Ханты-Мансийский автономный округ - Югра",
                "dicTypeMo": {
                    "id": 5,
                    "name": "Субъект"
                },
                "okrug": None,
                "firstOrder": False
            },
            "firstOrder": True
        }
    },
    "api_type": "lost"
}

info = AnimalAPI.extract_animal_info(test_animal)

print("\nExtracted animal info:")
for key, value in info.items():
    if key != "photos" and value and value != "Не указан" and value != "Не указана" and value != "Нет" and value != "Нет данных":
        print(f"{key}: {value}")

print("\nTest completed successfully!")
