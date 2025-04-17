from flask import current_app
from datetime import datetime, timedelta
import requests
from PIL import Image
import numpy as np
import io
from flask_mail import Message
from extensions import db, model, celery, mail
from models import SearchRequest
from tensorflow.keras.applications.resnet50 import preprocess_input

from config import Config
def get_api_data(endpoint, params=None):
    url = f"{Config.API_BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('content', [])
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"API request failed for {endpoint}: {e}")
        return []

def process_image(image_url):
    """Helper function to process image and get feature vector."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).resize((224, 224))
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        return model.predict(img_array)
    except Exception as e:
        current_app.logger.error(f"Image processing failed: {e}")
        return None

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    return np.dot(vec1, vec2.T) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

@celery.task
def check_for_matches():
    """Periodic task to check for matches for all active searches."""
    searches = SearchRequest.query.filter_by(active=True).all()
    
    for search in searches:
        # Get the last check date
        last_check = search.last_check_date or datetime.min
        
        # Update last check date
        search.last_check_date = datetime.now()
        db.session.commit()
        
        # Search in all three sections
        sections = [
            ('lost', 'placementDate'),
            ('found', 'placementDate'),
            ('find-home', 'shelterArrival')
        ]
        
        matches = []
        for endpoint, date_field in sections:
            # Skip if searching in the same section as the request
            if (endpoint == 'lost' and search.search_type == 'lost') or \
               (endpoint == 'found' and search.search_type == 'found'):
                continue
            
            # Get animals added since last check
            params = {
                'sort': f"{date_field},desc",
                'sort': 'id,desc',
                'page': 0,
                'size': 50
            }
            
            animals = get_api_data(endpoint, params)
            
            for animal in animals:
                # Check if animal was added after last check
                animal_date = datetime.fromisoformat(animal.get(date_field).replace('Z', '+00:00'))
                if animal_date <= last_check:
                    continue
                
                # Check basic criteria match
                if not matches_criteria(animal, search):
                    continue
                
                # Get animal photos
                photos = get_api_data(f"{endpoint}-photo/{animal['id']}/files")
                if not photos:
                    continue
                
                # Compare images if search has image
                if search.image_vector is not None:
                    photo_url = f"{Config.API_BASE_URL}/{endpoint}-photo/{animal['id']}/files/{photos[0]['id']}"
                    compare_vector = process_image(photo_url)
                    if compare_vector is None:
                        continue
                    
                    similarity = cosine_similarity(search.image_vector, compare_vector)
                    if similarity < Config.IMAGE_SIMILARITY_THRESHOLD:
                        continue
                
                # If we got here, we have a match
                matches.append({
                    'animal': animal,
                    'section': endpoint,
                    'similarity': similarity if search.image_vector is not None else None
                })
        
        # If matches found, send notification
        if matches:
            send_match_notification.delay(search.id, matches)

def matches_criteria(animal, search):
    """Check if animal matches search criteria."""
    criteria = [
        ('breed', lambda x, y: x.lower() == y.lower()),
        ('category', lambda x, y: x.lower() == y.lower()),
        ('gender', lambda x, y: x.lower() == y.lower()),
        ('size', lambda x, y: x.lower() == y.lower()),
        ('hair', lambda x, y: x.lower() == y.lower()),
        ('location', lambda x, y: x.lower() in y.lower()),
        ('chip_number', lambda x, y: x == y)
    ]
    
    for field, compare in criteria:
        search_value = getattr(search, field)
        if search_value and not compare(search_value, animal.get(field, '')):
            return False
    return True

@celery.task
def send_match_notification(search_id, matches):
    """Send email notification about matches."""
    search = SearchRequest.query.get(search_id)
    if not search or not search.user:
        return
    
    # Prepare email content
    subject = "Найдены потенциальные совпадения!"
    body = "Мы нашли следующие потенциальные совпадения для вашего поиска:\n\n"
    
    for match in matches:
        animal = match['animal']
        section = match['section']
        similarity = match['similarity']
        
        body += f"Раздел: {section}\n"
        body += f"Описание: {animal.get('description', 'Нет описания')}\n"
        if similarity:
            body += f"Схожесть изображения: {similarity:.2%}\n"
        body += f"Контактная информация: {animal.get('contactInfo', 'Нет контактной информации')}\n"
        body += f"Дата размещения: {animal.get('placementDate', 'Не указана')}\n"
        body += "\n---\n\n"
    
    # Send email
    msg = Message(
        subject=subject,
        sender=Config.MAIL_DEFAULT_SENDER,
        recipients=[search.user.email],
        body=body
    )
    
    with mail.connect() as conn:
        conn.send(msg)

# Schedule periodic task
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        Config.CHECK_INTERVAL_SECONDS,
        check_for_matches.s(),
        name='check-for-matches'
    )


















