from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR
import sqlite3
import json
import requests
import pytz
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.image_processing.image_processor import ImageProcessor
from backend.bots.telegram_bot import notify_match, notify_no_match
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('task_scheduler.log')
    ]
)
logger = logging.getLogger('task_scheduler')



class TaskScheduler:
    def __init__(self, app, db_name: str):
        self.app = app
        self.db_name = db_name
        self.image_processor = ImageProcessor()
        self.scheduler = BackgroundScheduler(timezone=pytz.UTC)
        
        self.scheduler.add_listener(self._handle_job_error, EVENT_JOB_ERROR)
        
        try:
            self.scheduler.start()
            logger.info("Task scheduler started successfully")
            
            self.scheduler.add_job(
                func=self.process_active_searches,
                trigger=IntervalTrigger(minutes=15, timezone=pytz.UTC),
                id='process_searches',
                name='Process active searches',
                replace_existing=True
            )
            logger.info("Added job: process_active_searches (every 15 minutes)")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def _handle_job_error(self, event):
        logger.error(f"Error executing job {event.job_id}: {event.exception}")

    def get_db(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def fetch_external_pets(self, last_check_time: datetime) -> List[Dict[str, Any]]:
        pets = []
        
        try:
            endpoints = [
                {'url': 'https://animals.admhmao.ru/pets-api/open/lost', 'type': 'lost'},
                {'url': 'https://animals.admhmao.ru/pets-api/open/found', 'type': 'found'},
                {'url': 'https://animals.admhmao.ru/pets-api/open/find-home', 'type': 'find-home'}
            ]
            
            all_pets = []
            
            for endpoint in endpoints:
                try:
                    params = {
                        'sort': ['placementDate,desc', 'id,desc'] if endpoint['type'] != 'find-home' else ['shelterArrival,desc', 'id,desc'],
                        'page': 0,
                        'size': 100
                    }
                    
                    response = requests.get(endpoint['url'], params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if isinstance(data, dict) and 'content' in data:
                        all_pets.extend(self.process_external_pets(data['content'], endpoint['type']))
                    elif isinstance(data, list):
                        all_pets.extend(self.process_external_pets(data, endpoint['type']))
                        
                    logger.info(f"Successfully fetched {len(all_pets)} pets from {endpoint['type']}")
                    
                except requests.RequestException as e:
                    logger.error(f"Error fetching from {endpoint['url']}: {e}")
                    continue
            
            if last_check_time:
                pets = [
                    pet for pet in all_pets
                    if ('placement_date' in pet and
                        datetime.fromisoformat(pet['placement_date']) > last_check_time) or
                       ('card_date' in pet and
                        datetime.fromisoformat(pet['card_date']) > last_check_time)
                ]
                logger.info(f"Filtered to {len(pets)} pets newer than {last_check_time}")
            else:
                pets = all_pets
                
        except Exception as e:
            logger.error(f"Error in fetch_external_pets: {e}")
            
        return pets

    def process_external_pets(self, pets: List[Dict], pet_type: str) -> List[Dict]:
        processed_pets = []
        
        for pet in pets:
            try:
                if not isinstance(pet, dict) or 'id' not in pet:
                    continue
                
                photo_url = self._get_pet_photo_url(pet, pet_type)
                if not photo_url:
                    continue
                
                processed_pet = {
                    'id': pet['id'],
                    'type': pet_type,
                    'photo_url': photo_url,
                    'breed': self._extract_breed(pet),
                    'category': self._extract_category(pet),
                    'location': pet.get('location') or pet.get('address'),
                    'contact_info': pet.get('contactInfo')
                }
                
                if pet_type == 'find-home':
                    processed_pet['card_date'] = pet.get('cardDate') or pet.get('shelterArrival') or datetime.now().isoformat()
                else:
                    processed_pet['placement_date'] = pet.get('placementDate') or pet.get('created_at') or datetime.now().isoformat()
                
                processed_pets.append(processed_pet)
                
            except Exception as e:
                logger.error(f"Error processing external pet {pet.get('id')}: {e}")
                continue
                
        logger.info(f"Processed {len(processed_pets)} pets of type {pet_type}")
        return processed_pets
    
    def _get_pet_photo_url(self, pet: Dict, pet_type: str) -> Optional[str]:

        try:
            if pet_type == 'find-home':
                photo_response = requests.get(
                    f'https://animals.admhmao.ru/pets-api/open/{pet_type}/{pet["id"]}/files',
                    timeout=5
                )
            else:
                photo_response = requests.get(
                    f'https://animals.admhmao.ru/pets-api/open/{pet_type}-photo/{pet["id"]}/files',
                    timeout=5
                )
                
            photo_response.raise_for_status()
            photo_ids = photo_response.json()
            
            if photo_ids and isinstance(photo_ids, list) and len(photo_ids) > 0:
                if pet_type == 'find-home':
                    return f'https://animals.admhmao.ru/pets-api/open/{pet_type}/{pet["id"]}/files/{photo_ids[0]}'
                else:
                    return f'https://animals.admhmao.ru/pets-api/open/{pet_type}-photo/{pet["id"]}/files/{photo_ids[0]}'
        except requests.RequestException as e:
            logger.debug(f"Could not fetch photos for pet {pet.get('id')}: {e}")
        except Exception as e:
            logger.error(f"Error getting photo URL for pet {pet.get('id')}: {e}")
            
        return None
    
    def _extract_breed(self, pet: Dict) -> str:
        breed = pet.get('breed')
        if isinstance(breed, dict) and 'name' in breed:
            return breed['name']
        elif breed:
            return str(breed)
        return None
    
    def _extract_category(self, pet: Dict) -> str:
        category = pet.get('category')
        if isinstance(category, dict) and 'name' in category:
            return category['name']
        elif category:
            return str(category)
        return None

    def process_active_searches(self):
        with self.app.app_context():
            try:
                logger.info("Starting to process active searches")
                db = self.get_db()
                cursor = db.cursor()
                
                cursor.execute('''
                    SELECT s.*, p.*, u.id as user_id, u.notification_preferences, u.email,
                           pp.photo_path, u.telegram_chat_id
                    FROM searches s
                    JOIN pets p ON s.pet_id = p.id
                    JOIN users u ON p.user_id = u.id
                    JOIN pet_photos pp ON p.id = pp.pet_id
                    WHERE s.is_active = 1
                ''')
                
                searches = cursor.fetchall()
                logger.info(f"Found {len(searches)} active searches to process")
                
                for search in searches:
                    try:
                        self._process_single_search(db, cursor, search)
                    except Exception as e:
                        logger.error(f"Error processing search {search['id']}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error in process_active_searches: {e}")
            finally:
                if 'db' in locals():
                    db.close()
                logger.info("Finished processing active searches")
    
    def _process_single_search(self, db, cursor, search):
        search_id = search['id']
        logger.info(f"Processing search {search_id} for pet {search['pet_id']}")
        
        last_check = datetime.fromisoformat(search['last_check_time']) if search['last_check_time'] else None
        
        external_pets = self.fetch_external_pets(last_check)
        
        if not external_pets:
            logger.info(f"No new external pets found for search {search_id}")
            self._update_last_check_time(db, cursor, search_id)
            return
            
        photo_path = os.path.join(self.app.config['UPLOAD_FOLDER'], search['photo_path'])
        if not os.path.exists(photo_path):
            logger.error(f"Photo not found at {photo_path} for search {search_id}")
            self._update_last_check_time(db, cursor, search_id)
            return
        
        matches = self.image_processor.compare_with_external_images(
            photo_path,
            external_pets,
            threshold=0.7
        )
        
        if matches:
            logger.info(f"Found {len(matches)} potential matches for search {search_id}")
            self._process_matches(db, cursor, search, matches)
        else:
            logger.info(f"No matches found for search {search_id}")
            self._handle_no_matches(search)
        
        self._update_last_check_time(db, cursor, search_id)
    
    def _process_matches(self, db, cursor, search, matches):

        for match in matches:
            cursor.execute('''
                SELECT id FROM matches
                WHERE search_id = ? AND external_pet_id = ?
            ''', (search['id'], match['external_id']))
            
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO matches (
                        search_id, external_pet_id, similarity_score
                    ) VALUES (?, ?, ?)
                ''', (
                    search['id'],
                    match['external_id'],
                    match['similarity_score']
                ))
                
                db.commit()
                logger.info(f"Inserted new match for search {search['id']}, external pet {match['external_id']}")
                
                self._send_match_notification(search, match)
    
    def _handle_no_matches(self, search):
        if search['last_check_time'] is None:
            notification_prefs = json.loads(search['notification_preferences'] or '{}')
            pet_data = {
                'type': search['type'],
                'breed': search['breed'],
                'category': search['category']
            }
            
            if search['telegram_chat_id'] and notification_prefs.get('telegram_enabled', False):
                try:
                    notify_no_match(search['user_id'], pet_data)
                    logger.info(f"Sent no-match notification for search {search['id']}")
                except Exception as e:
                    logger.error(f"Error sending no-match notification: {e}")
    
    def _send_match_notification(self, search, match):
        notification_prefs = json.loads(search['notification_preferences'] or '{}')
        
        if search['telegram_chat_id'] and notification_prefs.get('telegram_enabled', False):
            try:
                notify_match(search['user_id'], match)
                logger.info(f"Sent match notification to user {search['user_id']}")
            except Exception as e:
                logger.error(f"Error sending match notification: {e}")
    
    def _update_last_check_time(self, db, cursor, search_id):
        try:
            cursor.execute('''
                UPDATE searches
                SET last_check_time = datetime('now')
                WHERE id = ?
            ''', (search_id,))
            
            db.commit()
            logger.debug(f"Updated last_check_time for search {search_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating last_check_time for search {search_id}: {e}")
            db.rollback()

    def shutdown(self):
        try:
            logger.info("Shutting down task scheduler")
            self.scheduler.shutdown(wait=False)
            logger.info("Task scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down task scheduler: {e}")