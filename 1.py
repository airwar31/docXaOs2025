import requests
import json

def get_all_found_animals(api_url="https://animals.admhmao.ru/pets-api/open/found", page_size=8):
    try:
        all_animals = []
        page = 0
        while True:
            url = f"{api_url}?sort=placementDate,desc&sort=id,desc&page={page}&size={page_size}"
            response = requests.get(url)
            response.raise_for_status() # Проверка на ошибки HTTP
            data = response.json()

            animals = data.get("content", [])
            if not animals: # Если список животных пуст, значит, больше нет данных
                break
            all_animals.extend(animals)

            if data.get("last"): # Если это последняя страница, выходим из цикла
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
            animal_id = animal.get("id")

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

            if animal_id:
                photos_url = f"https://animals.admhmao.ru/pets-api/open/found-photo/{animal_id}/files"
                try:
                    response = requests.get(photos_url)
                    response.raise_for_status()
                    photos_data = response.json()

                    if photos_data:
                        print(" Ссылки на фото:")
                        for photo in photos_data:
                            photo_url = photo.get("url")
                            if photo_url:
                                print(f" {photo_url}")
                    else:
                        print(" Фото не найдены.")

                except requests.exceptions.RequestException as e:
                    print(f" Ошибка при получении фото: {e}")
    else:
        print("Не удалось получить данные о животных.")

