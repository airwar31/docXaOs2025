from requests import get
import os

# Create images directory if it doesn't exist
images_dir = 'images'
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

url_lost = 'https://animals.admhmao.ru/pets-api/open/lost?sort=placementDate,desc&sort=id'
url_find = 'https://animals.admhmao.ru/pets-api/open/found?sort=placementDate,desc&sort=id'
response = get(url_lost).json()

photos = []

for animal in response['content']:
    id = animal['id']

    photos_by_animals = get(f'https://animals.admhmao.ru/pets-api/open/lost-photo/{id}/files').json()

    for photo in photos_by_animals:
        image = get(f'https://animals.admhmao.ru/pets-api/open/lost-photo/{id}/files/{photo["id"]}').content
        with open(f'images/{id}-{photo["id"]}.jpg', 'wb') as img:
            img.write(image)

response = get(url_find).json()

for animal in response['content']:
    id = animal['id']

    photos_by_animals = get(f'https://animals.admhmao.ru/pets-api/open/found-photo/{id}/files').json()

    for photo in photos_by_animals:
        image = get(f'https://animals.admhmao.ru/pets-api/open/found-photo/{id}/files/{photo["id"]}').content
        with open(f'images/{id}-{photo["id"]}.jpg', 'wb') as img:
            img.write(image)