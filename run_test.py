import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:

    from animal_requests import AnimalAPI
    
    test_json = {
      "content": [
        {
          "id": 32,
          "phone": "9825040795",
          "placementDate": "2025-04-07",
          "foundDate": "2025-04-02",
          "location": "ул Майская 6",
          "petName": "ч/б",
          "coordinate": None,
          "characters": {
            "gender": False,
            "petSize": "AVERAGE",
            "hair": "SHORTHAIR",
            "tail": None,
            "ears": None,
            "petCategory": "CAT",
            "color": "чернобелый",
            "specialSigns": "Контактное лицо Виктория Викторовна +79825040795",
            "weight": None
          },
          "breed": None,
          "dicMunicipality": {
            "id": 197,
            "name": "г Сургут",
            "coordinate": {
              "coordX": 73.3962,
              "coordY": 61.2541
            },
            "okato": 71136000000,
            "okrug": {
              "id": 100,
              "oktmo": 71876000,
              "name": "город Сургут",
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
              "id": 100,
              "oktmo": 71876000,
              "name": "город Сургут",
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
          "additionalInfo": "Контактное лицо Виктория Викторовна +79825040795"
        }
      ]
    }
    
    test_animal = test_json["content"][0]
    test_animal["api_type"] = "found"
    
    print("Testing AnimalAPI.extract_animal_info with the provided JSON structure...")
    info = AnimalAPI.extract_animal_info(test_animal)
    
    print("\nExtracted animal info:")
    for key, value in info.items():
        if key != "photos" and value and value != "Не указан" and value != "Не указана" and value != "Нет" and value != "Нет данных":
            print(f"{key}: {value}")
    
    print("\nTest executed successfully!")
except Exception as e:
    print(f"Error during test: {str(e)}")