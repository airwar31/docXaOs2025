import os
import sys
import argparse
import logging
import asyncio
import sqlite3
import threading
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
file_handler = logging.FileHandler('petfinder.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger('petfinder')

import atexit
def close_handlers():
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.FileHandler):
            handler.close()
atexit.register(close_handlers)

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from config.settings import active_config
    from backend.bots.telegram_bot import bot, dp
    from backend.core.similar_pet_detector import SimilarPetDetector
    from backend.api.animal_api import AnimalAPI
    from backend.utils.translate_utils import translate_size, translate_fur, translate_gender, translate_category, translate_tail, translate_ears
    
    from flask import Flask, send_from_directory, request, jsonify, session, make_response
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please install required packages: pip install flask aiogram opencv-python")
    sys.exit(1)

# Use configuration from config/settings.py
DB_NAME = active_config.DB_NAME
UPLOAD_FOLDER = active_config.UPLOAD_FOLDER
HOST = active_config.SERVER_HOST
API_PORT = active_config.API_PORT
FRONTEND_PORT = active_config.FRONTEND_PORT
SESSION_LIFETIME = active_config.SESSION_LIFETIME
ALLOWED_EXTENSIONS = active_config.ALLOWED_EXTENSIONS

os.makedirs(os.path.join(project_root, UPLOAD_FOLDER), exist_ok=True)

def create_app():
    flask_app = Flask(__name__, 
                     static_folder='frontend/static',
                     static_url_path='/static')
    flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    flask_app.config['SECRET_KEY'] = active_config.SECRET_KEY
    flask_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=SESSION_LIFETIME)
    return flask_app

app = create_app()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 6

def init_database():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            telegram_chat_id TEXT,
            notification_preferences TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            breed TEXT,
            gender TEXT,
            size TEXT,
            fur TEXT,
            tail TEXT,
            ears TEXT,
            location TEXT,
            chip_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pet_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            FOREIGN KEY (pet_id) REFERENCES pets (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet1_id INTEGER NOT NULL,
            pet2_id INTEGER NOT NULL,
            similarity_score REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet1_id) REFERENCES pets (id),
            FOREIGN KEY (pet2_id) REFERENCES pets (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        sys.exit(1)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email и пароль обязательны"}), 400
            
        email = data['email']
        password = data['password']
        
        if not validate_email(email):
            return jsonify({"error": "Неверный формат email"}), 400
            
        if not validate_password(password):
            return jsonify({"error": "Пароль должен содержать не менее 6 символов"}), 400
            
        password_hash = hash_password(password)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return jsonify({"error": "Пользователь с таким email уже существует"}), 400
                
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            conn.commit()
            
            return jsonify({"message": "Регистрация успешна"}), 201
            
        except sqlite3.Error as e:
            logger.error(f"Database error during registration: {e}")
            return jsonify({"error": "Произошла ошибка при регистрации"}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return jsonify({"error": "Произошла ошибка при регистрации"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email и пароль обязательны"}), 400
            
        email = data['email']
        password = data['password']
        
        password_hash = hash_password(password)
        
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT id, email FROM users WHERE email = ? AND password_hash = ?",
                (email, password_hash)
            )
            user = cursor.fetchone()
            
            if not user:
                return jsonify({"error": "Неверный email или пароль"}), 401
                
            session.permanent = True
            session['user_id'] = user['id']
            session['email'] = user['email']
            
            return jsonify({
                "message": "Вход выполнен успешно",
                "user_id": user['id'],
                "email": user['email']
            }), 200
            
        except sqlite3.Error as e:
            logger.error(f"Database error during login: {e}")
            return jsonify({"error": "Произошла ошибка при входе в систему"}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({"error": "Произошла ошибка при входе в систему"}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({"message": "Выход выполнен успешно"}), 200
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({"error": "Произошла ошибка при выходе из системы"}), 500

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    try:
        if 'user_id' in session:
            return jsonify({
                "authenticated": True,
                "user_id": session['user_id'],
                "email": session.get('email')
            }), 200
        else:
            return jsonify({"authenticated": False}), 200
    except Exception as e:
        logger.error(f"Error checking authentication: {e}")
        return jsonify({"error": "Произошла ошибка при проверке аутентификации"}), 500

@app.route('/api/notification-preferences', methods=['GET', 'PUT'])
def notification_preferences():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Требуется аутентификация"}), 401
            
        user_id = session['user_id']
        
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if request.method == 'GET':
            try:
                cursor.execute(
                    "SELECT notification_preferences FROM users WHERE id = ?",
                    (user_id,)
                )
                user = cursor.fetchone()
                
                if not user or not user['notification_preferences']:
                    return jsonify({
                        "telegram_enabled": False,
                        "frequency": 1,
                        "min_similarity": 0.7
                    }), 200
                    
                preferences = json.loads(user['notification_preferences'])
                return jsonify(preferences), 200
                
            except sqlite3.Error as e:
                logger.error(f"Database error getting notification preferences: {e}")
                return jsonify({"error": "Произошла ошибка при получении настроек уведомлений"}), 500
            finally:
                conn.close()
                
        elif request.method == 'PUT':
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({"error": "Отсутствуют данные"}), 400
                    
                preferences_json = json.dumps(data)
                
                cursor.execute(
                    "UPDATE users SET notification_preferences = ? WHERE id = ?",
                    (preferences_json, user_id)
                )
                conn.commit()
                
                return jsonify({"message": "Настройки уведомлений обновлены"}), 200
                
            except sqlite3.Error as e:
                logger.error(f"Database error updating notification preferences: {e}")
                return jsonify({"error": "Произошла ошибка при обновлении настроек уведомлений"}), 500
            finally:
                conn.close()
                
    except Exception as e:
        logger.error(f"Error with notification preferences: {e}")
        return jsonify({"error": "Произошла ошибка при работе с настройками уведомлений"}), 500

@app.route('/api/pets', methods=['GET', 'POST'])
def pets():
    if request.method == 'GET':
        try:
            animal_type = request.args.get('type', 'all')
            page = int(request.args.get('page', 0))
            size = int(request.args.get('size', 10))
            search = request.args.get('search', '')
            category_filter = request.args.get('category', '')
            gender_filter = request.args.get('gender', '')
            size_filter = request.args.get('size_filter', '')
            fur_filter = request.args.get('fur', '')
            
            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT p.*, u.email as user_email, GROUP_CONCAT(pp.photo_path) as photos
            FROM pets p
            JOIN users u ON p.user_id = u.id
            LEFT JOIN pet_photos pp ON p.id = pp.pet_id
            GROUP BY p.id
            ''')
            
            pets = [dict(row) for row in cursor.fetchall()]
            for pet in pets:
                if pet['photos']:
                    pet['photos'] = pet['photos'].split(',')
                    # Set photo_url to the first photo's path for use in the frontend
                    pet['photo_url'] = f"/uploads/{pet['photos'][0]}"
                else:
                    pet['photos'] = []
                    # Set a default photo URL instead of None
                    pet['photo_url'] = "/static/images/noPhotoAnimals.png"
                
                if pet['size']:
                    pet['size_original'] = pet['size']
                    pet['size'] = translate_size(pet['size'])
                
                if pet['fur']:
                    pet['fur_original'] = pet['fur']
                    pet['fur'] = translate_fur(pet['fur'])
                
                if pet['gender']:
                    pet['gender_original'] = pet['gender']
                    pet['gender'] = translate_gender(pet['gender'])
                
                if pet['type']:
                    pet['type_original'] = pet['type']
                    pet['type'] = translate_category(pet['type'])
                
                if pet['tail']:
                    pet['tail_original'] = pet['tail']
                    pet['tail'] = translate_tail(pet['tail'])
                
                if pet['ears']:
                    pet['ears_original'] = pet['ears']
                    pet['ears'] = translate_ears(pet['ears'])
                    
            conn.close()
            
            api_animals = []
            try:
                logger.info("Fetching pets from external API...")
                api_animals = AnimalAPI.get_all_animals(animal_type=animal_type, size=size, page=page)
                
                if api_animals:
                    processed_animals = []
                    for animal in api_animals:
                        animal_info = AnimalAPI.extract_animal_info(animal)
                        processed_animals.append(animal_info)
                    
                    filtered_animals = []
                    for animal in processed_animals:
                        # Apply search filter
                        if search and not any(search.lower() in str(value).lower() for value in animal.values() if isinstance(value, (str, int, float))):
                            continue
                        
                        # Apply category filter
                        if category_filter and animal.get('type_original', '').lower() != category_filter.lower():
                            continue
                        
                        # Apply gender filter
                        if gender_filter and animal.get('gender_original', '').lower() != gender_filter.lower():
                            continue
                        
                        # Apply size filter
                        if size_filter and animal.get('size_original', '').lower() != size_filter.lower():
                            continue
                        
                        # Apply fur filter
                        if fur_filter and animal.get('fur_original', '').lower() != fur_filter.lower():
                            continue
                        
                        filtered_animals.append(animal)
                    
                    # Combine database pets and API pets
                    combined_pets = pets + filtered_animals
                    
                    # Apply pagination to combined results
                    start_idx = page * size
                    end_idx = start_idx + size
                    
                    # Make sure we have enough data for the requested page
                    if start_idx < len(combined_pets):
                        paginated_pets = combined_pets[start_idx:end_idx]
                        return jsonify(paginated_pets)
                    else:
                        # If the requested page is beyond our data, return an empty list
                        # This should not happen with our updated AnimalAPI.get_all_animals method
                        logger.warning(f"Requested page {page} is beyond available data (total items: {len(combined_pets)})")
                        return jsonify([])
                
            except Exception as api_error:
                logger.error(f"Error fetching animals from external API: {api_error}")
            
            # If API fetch failed or returned no results, return just the database pets
            return jsonify(pets)
        except Exception as e:
            logger.error(f"Error getting pets: {e}")
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            # Check if the user is authenticated
            if 'user_id' not in session:
                return jsonify({"error": "Требуется аутентификация"}), 401
                
            user_id = session['user_id']
            
            # Get form data
            type = request.form.get('type')
            category = request.form.get('category')
            breed = request.form.get('breed')
            gender = request.form.get('gender')
            size = request.form.get('size')
            fur = request.form.get('fur')
            tail = request.form.get('tail')
            ears = request.form.get('ears')
            location = request.form.get('location')
            chip_number = request.form.get('chip_number')
            
            # Validate required fields
            if not type or not category:
                return jsonify({"error": "Тип и категория животного обязательны"}), 400
                
            # Connect to the database
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            try:
                # Insert the new pet
                cursor.execute('''
                INSERT INTO pets (user_id, type, category, breed, gender, size, fur, tail, ears, location, chip_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, type, category, breed, gender, size, fur, tail, ears, location, chip_number))
                
                pet_id = cursor.lastrowid
                
                # Handle photo uploads
                if 'photos' in request.files:
                    photos = request.files.getlist('photos')
                    
                    for photo in photos:
                        if photo and photo.filename:
                            # Generate a unique filename
                            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}"
                            photo_path = os.path.join(project_root, UPLOAD_FOLDER, filename)
                            
                            # Save the photo
                            photo.save(photo_path)
                            
                            # Save the photo path in the database
                            cursor.execute('''
                            INSERT INTO pet_photos (pet_id, photo_path)
                            VALUES (?, ?)
                            ''', (pet_id, filename))
                
                conn.commit()
                
                return jsonify({
                    "message": "Питомец успешно добавлен",
                    "pet_id": pet_id
                }), 201
                
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database error adding pet: {e}")
                return jsonify({"error": "Произошла ошибка при добавлении питомца"}), 500
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error adding pet: {e}")
            return jsonify({"error": "Произошла ошибка при добавлении питомца"}), 500

@app.route('/api/pets/<int:pet_id>', methods=['GET'])
def get_pet(pet_id):
    """API endpoint to get a specific pet."""
    try:
        detector = SimilarPetDetector(DB_NAME, UPLOAD_FOLDER)
        pet = detector.get_pet_details(pet_id)
        
        if pet:
            if pet['size']:
                pet['size_original'] = pet['size']
                pet['size'] = translate_size(pet['size'])
            
            if pet['fur']:
                pet['fur_original'] = pet['fur']
                pet['fur'] = translate_fur(pet['fur'])
            
            if pet['gender']:
                pet['gender_original'] = pet['gender']
                pet['gender'] = translate_gender(pet['gender'])
            
            if pet['type']:
                pet['type_original'] = pet['type']
                pet['type'] = translate_category(pet['type'])
            
            if pet['tail']:
                pet['tail_original'] = pet['tail']
                pet['tail'] = translate_tail(pet['tail'])
            
            if pet['ears']:
                pet['ears_original'] = pet['ears']
                pet['ears'] = translate_ears(pet['ears'])
                
            return jsonify(pet)
        else:
            return jsonify({"error": "Pet not found"}), 404
    except Exception as e:
        logger.error(f"Error getting pet {pet_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pets/<int:pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    """API endpoint to delete a specific pet."""
    try:
        # Check if the user is authenticated
        if 'user_id' not in session:
            return jsonify({"error": "Требуется аутентификация"}), 401
            
        user_id = session['user_id']
        
        # Connect to the database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        try:
            # Check if the pet exists and belongs to the current user
            cursor.execute('''
            SELECT id FROM pets WHERE id = ? AND user_id = ?
            ''', (pet_id, user_id))
            
            pet = cursor.fetchone()
            
            if not pet:
                # Check if the pet exists at all
                cursor.execute('SELECT id FROM pets WHERE id = ?', (pet_id,))
                if cursor.fetchone():
                    # Pet exists but doesn't belong to the current user
                    return jsonify({"error": "У вас нет прав на удаление этого питомца"}), 403
                else:
                    # Pet doesn't exist
                    return jsonify({"error": "Питомец не найден"}), 404
            
            # Get the photo paths before deleting them from the database
            cursor.execute('SELECT photo_path FROM pet_photos WHERE pet_id = ?', (pet_id,))
            photos = cursor.fetchall()
            
            # Delete the photos from the file system
            for photo in photos:
                photo_path = os.path.join(UPLOAD_FOLDER, photo[0])
                try:
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                except Exception as e:
                    logger.error(f"Error deleting photo file {photo_path}: {e}")
            
            # Delete the photo records from the database
            cursor.execute('DELETE FROM pet_photos WHERE pet_id = ?', (pet_id,))
            
            # Delete any matches involving this pet
            cursor.execute('DELETE FROM matches WHERE pet1_id = ? OR pet2_id = ?', (pet_id, pet_id))
            
            # Delete the pet
            cursor.execute('DELETE FROM pets WHERE id = ?', (pet_id,))
            
            # Commit the transaction
            conn.commit()
            
            return jsonify({"message": "Питомец успешно удален"}), 200
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error deleting pet {pet_id}: {e}")
            return jsonify({"error": "Произошла ошибка при удалении питомца"}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error deleting pet {pet_id}: {e}")
        return jsonify({"error": "Произошла ошибка при удалении питомца"}), 500

@app.route('/api/similar/<int:pet_id>', methods=['GET'])
def find_similar(pet_id):
    try:
        threshold = float(request.args.get('threshold', 0.7))
        detector = SimilarPetDetector(DB_NAME, UPLOAD_FOLDER, similarity_threshold=threshold)
        similar_pets = detector.find_similar_pets(pet_id)
        
        for pet in similar_pets:
            if pet['size']:
                pet['size_original'] = pet['size']
                pet['size'] = translate_size(pet['size'])
            
            if pet['fur']:
                pet['fur_original'] = pet['fur']
                pet['fur'] = translate_fur(pet['fur'])
            
            if pet['gender']:
                pet['gender_original'] = pet['gender']
                pet['gender'] = translate_gender(pet['gender'])
            
            if pet['type']:
                pet['type_original'] = pet['type']
                pet['type'] = translate_category(pet['type'])
            
            if pet['tail']:
                pet['tail_original'] = pet['tail']
                pet['tail'] = translate_tail(pet['tail'])
            
            if pet['ears']:
                pet['ears_original'] = pet['ears']
                pet['ears'] = translate_ears(pet['ears'])
        
        return jsonify(similar_pets)
    except Exception as e:
        logger.error(f"Error finding similar pets for {pet_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve frontend files."""
    if path == "" or path == "index.html":
        return send_from_directory('frontend', 'index.html')
    
    frontend_path = os.path.join('frontend', path)
    if os.path.exists(frontend_path) and not os.path.isdir(frontend_path):
        directory, file = os.path.split(frontend_path)
        return send_from_directory(directory, file)
    
    return send_from_directory('frontend', 'index.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(project_root, UPLOAD_FOLDER), filename)

async def start_bot():
    try:
        logger.info("Starting Telegram bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")

def run_bot():
    asyncio.run(start_bot())

# Main function
def main():
    """Main entry point for the application."""
    global app
    
    parser = argparse.ArgumentParser(description='Pet Finder Application')
    parser.add_argument('--api-port', type=int, default=API_PORT, help='Port for the API server')
    parser.add_argument('--no-bot', action='store_true', help='Disable Telegram bot')
    args = parser.parse_args()
    
    # Initialize database
    init_database()
    
    # Start Telegram bot in a separate thread if enabled
    if not args.no_bot:
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Bot and dispatcher initialized successfully")
    
    # Start the Flask app
    logger.info(f"Starting API server on port {args.api_port}...")
    app.run(host=HOST, port=args.api_port, debug=False)

if __name__ == '__main__':
    main()




































