import requests
import json

def get_all_found_animals(api_url="https://animals.admhmao.ru/pets-api/open/found", page_size=8):
    try:
        all_animals = []
        page = 0
        while True:
            url = f"{api_url}?sort=placementDate,desc&sort=id,desc&page={page}&size={page_size}"
            response = requests.get(url)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            animals = data.get("content", [])
            all_animals.extend(animals)

            if data.get("last"):
                break

            page += 1
            print(f"Загружена страница {page + 1}")

        return all_animals

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")
        return None

if __name__ == "__main__":
    animals = get_all_found_animals()

    if animals:
        print(f"Всего найдено {len(animals)} животных.")

        for i, animal in enumerate(animals):
            print(f"\nЖивотное {i+1}:")
            for key, value in animal.items():
                if isinstance(value, dict):
                    print(f" {key.capitalize()}:")
                    for inner_key, inner_value in value.items():
                        print(f"    {inner_key.capitalize()}: {inner_value}")
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    print(f" {key.capitalize()}:")
                    for j, item in enumerate(value):
                        print(f"    Элемент {j+1}:")
                        for inner_key, inner_value in item.items():
                            print(f"      {inner_key.capitalize()}: {inner_value}")
                else:
                    print(f" {key.capitalize()}: {value}")
    else:
        print("Не удалось получить данные о животных.")

