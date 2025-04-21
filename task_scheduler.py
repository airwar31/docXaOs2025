from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import sqlite3
import json
import requests
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from image_processor import ImageProcessor
from telegram_bot import notify_match, notify_no_match
import os

EMAIL_NOTIFICATIONS_AVAILABLE = False

class TaskScheduler:
    def __init__(self, app, db_name: str):
        self.app = app
        self.db_name = db_name
        self.image_processor = ImageProcessor()
        self.scheduler = BackgroundScheduler(timezone=pytz.UTC)
        self.scheduler.start()
        
        self.scheduler.add_job(
            func=self.process_active_searches,
            trigger=IntervalTrigger(minutes=15, timezone=pytz.UTC),
            id='process_searches',
            name='Process active searches',
            replace_existing=True
        )

    def get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def fetch_external_pets(self, last_check_time: datetime) -> List[Dict[str, Any]]:
        pets = []
        
        try:
            response = requests.get(
                'https://animals.admhmao.ru/pets-api/open/lost',
                params={
                    'sort': ['placementDate,desc', 'id,desc'],
                    'page': 0,
                    'size': 100
                }
            )
            response.raise_for_status()
            lost_pets = response.json()
            
            response = requests.get(
                'https://animals.admhmao.ru/pets-api/open/found',
                params={
                    'sort': ['placementDate,desc', 'id,desc'],
                    'page': 0,
                    'size': 100
                }
            )
            response.raise_for_status()
            found_pets = response.json()
            
            response = requests.get(
                'https://animals.admhmao.ru/pets-api/open/find-home',
                params={
                    'sort': ['shelterArrival,desc', 'id,desc'],
                    'page': 0,
                    'size': 100
                }
            )
            response.raise_for_status()
            find_home_pets = response.json()
            
            all_pets = []
            
            if isinstance(lost_pets, dict) and 'content' in lost_pets:
                all_pets.extend(self.process_external_pets(lost_pets['content'], 'lost'))
            elif isinstance(lost_pets, list):
                all_pets.extend(self.process_external_pets(lost_pets, 'lost'))
            
            if isinstance(found_pets, dict) and 'content' in found_pets:
                all_pets.extend(self.process_external_pets(found_pets['content'], 'found'))
            elif isinstance(found_pets, list):
                all_pets.extend(self.process_external_pets(found_pets, 'found'))
            
            if isinstance(find_home_pets, dict) and 'content' in find_home_pets:
                all_pets.extend(self.process_external_pets(find_home_pets['content'], 'find-home'))
            elif isinstance(find_home_pets, list):
                all_pets.extend(self.process_external_pets(find_home_pets, 'find-home'))
            
            if last_check_time:
                pets = [
                    pet for pet in all_pets
                    if ('placement_date' in pet and
                        datetime.fromisoformat(pet['placement_date']) > last_check_time) or
                       ('card_date' in pet and
                        datetime.fromisoformat(pet['card_date']) > last_check_time)
                ]
            else:
                pets = all_pets
                
        except Exception as e:
            print(f"Error fetching external pets: {e}")
            
        return pets

    def process_external_pets(self, pets: List[Dict], pet_type: str) -> List[Dict]:
        processed_pets = []
        
        for pet in pets:
            try:
                if not isinstance(pet, dict) or 'id' not in pet:
                    continue
                    
                try:
                    if pet_type == 'find-home':
                        photo_response = requests.get(
                            f'https://animals.admhmao.ru/pets-api/open/{pet_type}/{pet["id"]}/files'
                        )
                    else:
                        photo_response = requests.get(
                            f'https://animals.admhmao.ru/pets-api/open/{pet_type}-photo/{pet["id"]}/files'
                        )
                    photo_response.raise_for_status()
                    photo_ids = photo_response.json()
                    
                    if photo_ids and isinstance(photo_ids, list) and len(photo_ids) > 0:
                        if pet_type == 'find-home':
                            photo_url = f'https://animals.admhmao.ru/pets-api/open/{pet_type}/{pet["id"]}/files/{photo_ids[0]}'
                        else:
                            photo_url = f'https://animals.admhmao.ru/pets-api/open/{pet_type}-photo/{pet["id"]}/files/{photo_ids[0]}'
                    else:
                        continue
                        
                except requests.RequestException:
                    continue
                
                processed_pet = {
                    'id': pet['id'],
                    'type': pet_type,
                    'photo_url': photo_url,
                    'breed': pet.get('breed', {}).get('name') if isinstance(pet.get('breed'), dict) else pet.get('breed'),
                    'category': pet.get('category', {}).get('name') if isinstance(pet.get('category'), dict) else pet.get('category'),
                    'location': pet.get('location') or pet.get('address'),
                    'contact_info': pet.get('contactInfo')
                }
                
                if pet_type == 'find-home':
                    processed_pet['card_date'] = pet.get('cardDate') or pet.get('shelterArrival') or datetime.now().isoformat()
                else:
                    processed_pet['placement_date'] = pet.get('placementDate') or pet.get('created_at') or datetime.now().isoformat()
                
                processed_pets.append(processed_pet)
                
            except Exception as e:
                print(f"Error processing external pet {pet.get('id')}: {e}")
                continue
                
        return processed_pets

    def process_active_searches(self):
        with self.app.app_context():
            try:
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
                
                for search in searches:
                    try:
                        last_check = datetime.fromisoformat(search['last_check_time']) if search['last_check_time'] else None
                        
                        external_pets = self.fetch_external_pets(last_check)
                        
                        if not external_pets:
                            continue
                            
                        photo_path = os.path.join(self.app.config['UPLOAD_FOLDER'], search['photo_path'])
                        
                        matches = self.image_processor.compare_with_external_images(
                            photo_path,
                            external_pets,
                            threshold=0.7
                        )
                        
                        if matches:
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
                                    
                                    notification_prefs = json.loads(search['notification_preferences'] or '{}')
                                    
                                    if search['telegram_chat_id'] and notification_prefs.get('telegram_enabled', False):
                                        notify_match(search['user_id'], match)
                        else:
                            if last_check is None:
                                notification_prefs = json.loads(search['notification_preferences'] or '{}')
                                pet_data = {
                                    'type': search['type'],
                                    'breed': search['breed'],
                                    'category': search['category']
                                }
                                
                                if search['telegram_chat_id'] and notification_prefs.get('telegram_enabled', False):
                                    try:
                                        notify_no_match(search['user_id'], pet_data)
                                    except Exception as e:
                                        print(f"Error sending no-match Telegram notification: {e}")
                        
                        cursor.execute('''
                            UPDATE searches
                            SET last_check_time = datetime('now')
                            WHERE id = ?
                        ''', (search['id'],))
                        
                        db.commit()
                        
                    except Exception as e:
                        print(f"Error processing search {search['id']}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error in process_active_searches: {e}")
            finally:
                db.close()

    def shutdown(self):
        self.scheduler.shutdown()




