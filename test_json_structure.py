from animal_requests import AnimalAPI
import json

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
  ],
  "pageable": {
    "sort": {
      "sorted": True,
      "unsorted": False,
      "empty": False
    },
    "pageNumber": 0,
    "pageSize": 1,
    "offset": 0,
    "paged": True,
    "unpaged": False
  },
  "totalPages": 24,
  "totalElements": 24,
  "last": False,
  "numberOfElements": 1,
  "size": 1,
  "number": 0,
  "sort": {
    "sorted": True,
    "unsorted": False,
    "empty": False
  },
  "first": True,
  "empty": False
}

test_animal = test_json["content"][0]
test_animal["api_type"] = "found"

print("Testing AnimalAPI.extract_animal_info with the provided JSON structure...")
info = AnimalAPI.extract_animal_info(test_animal)

print("\nExtracted animal info:")
for key, value in info.items():
    if key != "photos" and value and value != "Не указан" and value != "Не указана" and value != "Нет" and value != "Нет данных":
        print(f"{key}: {value}")

html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Pet Card with JSON Structure</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .pets-grid {
            display: grid;
            grid-template-columns: repeat(1, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }

        .pet-card {
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
            cursor: pointer;
            position: relative;
        }

        .pet-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        .pet-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 4px;
            margin-bottom: 10px;
        }

        .pet-summary {
            margin: 10px 0;
            padding: 10px;
            background-color: #f8f8f8;
            border-radius: 4px;
        }
        
        .pet-summary p {
            margin: 5px 0;
            line-height: 1.4;
        }
        
        .pet-summary strong {
            color: #444;
            font-weight: 600;
        }

        .pet-details {
            margin: 10px 0;
            padding: 10px;
            background-color: #f8f8f8;
            border-radius: 4px;
        }

        .pet-details p {
            margin: 5px 0;
            line-height: 1.4;
        }

        .pet-details strong {
            color: #444;
            font-weight: 600;
        }

        .pet-card h3 {
            margin-top: 10px;
            margin-bottom: 5px;
            color: #333;
            font-size: 18px;
            text-align: center;
        }
        
        .pet-card .pet-image {
            border-radius: 4px 4px 0 0;
        }
        
        /* Add a visual indicator that the card is clickable */
        .pet-card:after {
            content: "Нажмите для подробностей";
            position: absolute;
            bottom: 5px;
            right: 5px;
            background-color: rgba(76, 175, 80, 0.8);
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.2s;
        }
        
        .pet-card:hover:after {
            opacity: 1;
        }

        .pet-card .hidden-details {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Pet Card with JSON Structure</h1>
        <div id="petsGrid" class="pets-grid">
            <!-- Pet card will be added here -->
        </div>
    </div>

    <script src="createPetCard.js"></script>
    <script>
        // Global variable for testing
        const currentUserId = null;

        // Test data from the request
        const testPet = {
            "id": 32,
            "phone": "9825040795",
            "placementDate": "2025-04-07",
            "foundDate": "2025-04-02",
            "location": "ул Майская 6",
            "petName": "ч/б",
            "coordinate": null,
            "characters": {
                "gender": false,
                "petSize": "AVERAGE",
                "hair": "SHORTHAIR",
                "tail": null,
                "ears": null,
                "petCategory": "CAT",
                "color": "чернобелый",
                "specialSigns": "Контактное лицо Виктория Викторовна +79825040795",
                "weight": null
            },
            "breed": null,
            "dicMunicipality": {
                "id": 197,
                "name": "г Сургут",
                "coordinate": {
                    "coordX": 73.3962,
                    "coordY": 61.2541
                },
                "okato": 71136000000,
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
                        "okrug": null,
                        "firstOrder": false
                    },
                    "firstOrder": true
                }
            },
            "additionalInfo": "Контактное лицо Виктория Викторовна +79825040795",
            "api_type": "found"
        };

        // Add pet card to the grid
        window.addEventListener('load', function() {
            const petsGrid = document.getElementById('petsGrid');
            const card = createPetCard(testPet);
            petsGrid.appendChild(card);
        });
    </script>
</body>
</html>
"""

with open("/workspace/test_json_structure.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("\nCreated test_json_structure.html for testing the createPetCard.js with the provided JSON structure")
print("Test completed successfully!")
