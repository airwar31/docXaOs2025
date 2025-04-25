import os
import sys
import argparse
import logging
import asyncio
import sqlite3
import threading
import hashlib
import json
import atexit
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, request, jsonify, session, make_response

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
file_handler = logging.FileHandler('petfinder.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger('petfinder')

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
    import backend.bots.telegram_bot_part2
    from backend.core.similar_pet_detector import SimilarPetDetector
    from backend.api.animal_api import AnimalAPI
    from backend.utils.translate_utils import translate_size, translate_fur, translate_gender, translate_category, translate_tail, translate_ears
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please install required packages: pip install flask aiogram opencv-python")
    sys.exit(1)

# Allow overriding the database name for testing
DB_NAME = os.environ.get('TEST_DB_NAME', active_config.DB_NAME)
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
        with sqlite3.connect(DB_NAME) as conn:
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
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
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
        
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
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
        
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if request.method == 'GET':
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
                
            elif request.method == 'PUT':
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
        logger.error(f"Database error with notification preferences: {e}")
        return jsonify({"error": "Произошла ошибка при работе с настройками уведомлений"}), 500
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
            
            with sqlite3.connect(DB_NAME) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build the SQL query with filters
                query = '''
                SELECT p.*, u.email as user_email, GROUP_CONCAT(pp.photo_path) as photos
                FROM pets p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN pet_photos pp ON p.id = pp.pet_id
                '''
                
                # Add WHERE clause if filters are applied
                where_clauses = []
                query_params = []
                
                # Filter by animal type if specified
                if animal_type != 'all':
                    where_clauses.append("p.type = ?")
                    query_params.append(animal_type)
                
                # Filter by category if specified
                if category_filter:
                    where_clauses.append("LOWER(p.type) = LOWER(?)")
                    query_params.append(category_filter)
                
                # Filter by gender if specified
                if gender_filter:
                    where_clauses.append("LOWER(p.gender) = LOWER(?)")
                    query_params.append(gender_filter)
                
                # Filter by size if specified
                if size_filter:
                    where_clauses.append("LOWER(p.size) = LOWER(?)")
                    query_params.append(size_filter)
                
                # Filter by fur if specified
                if fur_filter:
                    where_clauses.append("LOWER(p.fur) = LOWER(?)")
                    query_params.append(fur_filter)
                
                # Add the WHERE clause to the query if there are any conditions
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                # Add GROUP BY clause
                query += " GROUP BY p.id"
                
                # Execute the query with parameters
                cursor.execute(query, query_params)
                
                pets = [dict(row) for row in cursor.fetchall()]
                
                # Apply text search filter if specified
                if search:
                    filtered_pets = []
                    for pet in pets:
                        if any(search.lower() in str(value).lower() for value in pet.values() if isinstance(value, (str, int, float))):
                            filtered_pets.append(pet)
                    pets = filtered_pets
                
                # Process pet data
                for pet in pets:
                    if pet['photos']:
                        pet['photos'] = pet['photos'].split(',')
                        pet['photo_url'] = f"/uploads/{pet['photos'][0]}"
                    else:
                        pet['photos'] = []
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
            
            api_animals = []
            try:
                logger.info("Fetching pets from external API...")
                api_animals = AnimalAPI.get_all_animals(animal_type=animal_type, size=size, page=page)
                
                if api_animals:
                    processed_animals = [AnimalAPI.extract_animal_info(animal) for animal in api_animals]
                    
                    filtered_animals = []
                    for animal in processed_animals:
                        if search and not any(search.lower() in str(value).lower() for value in animal.values() if isinstance(value, (str, int, float))):
                            continue
                        
                        if category_filter and animal.get('type_original', '').lower() != category_filter.lower():
                            continue
                        
                        if gender_filter and animal.get('gender_original', '').lower() != gender_filter.lower():
                            continue
                        
                        if size_filter and animal.get('size_original', '').lower() != size_filter.lower():
                            continue
                        
                        if fur_filter and animal.get('fur_original', '').lower() != fur_filter.lower():
                            continue
                        
                        filtered_animals.append(animal)
                    
                    combined_pets = pets + filtered_animals
                    
                    start_idx = page * size
                    end_idx = start_idx + size
                    
                    if start_idx < len(combined_pets):
                        paginated_pets = combined_pets[start_idx:end_idx]
                        return jsonify(paginated_pets)
                    else:
                        logger.warning(f"Requested page {page} is beyond available data (total items: {len(combined_pets)})")
                        return jsonify([])
                
            except Exception as api_error:
                logger.error(f"Error fetching animals from external API: {api_error}")
            
            # Apply pagination to local pets if API fetch failed
            start_idx = page * size
            end_idx = start_idx + size
            
            if start_idx < len(pets):
                paginated_pets = pets[start_idx:end_idx]
                return jsonify(paginated_pets)
            else:
                logger.warning(f"Requested page {page} is beyond available data (total items: {len(pets)})")
                return jsonify([])
                
        except Exception as e:
            logger.error(f"Error getting pets: {e}")
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            if 'user_id' not in session:
                return jsonify({"error": "Требуется аутентификация"}), 401
                
            user_id = session['user_id']
            
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
            
            if not type or not category:
                return jsonify({"error": "Тип и категория животного обязательны"}), 400
                
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO pets (user_id, type, category, breed, gender, size, fur, tail, ears, location, chip_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, type, category, breed, gender, size, fur, tail, ears, location, chip_number))
                
                pet_id = cursor.lastrowid
                
                if 'photos' in request.files:
                    photos = request.files.getlist('photos')
                    
                    for photo in photos:
                        if photo and photo.filename:
                            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}"
                            photo_path = os.path.join(project_root, UPLOAD_FOLDER, filename)
                            
                            photo.save(photo_path)
                            
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
            logger.error(f"Database error adding pet: {e}")
            return jsonify({"error": "Произошла ошибка при добавлении питомца"}), 500
        except Exception as e:
            logger.error(f"Error adding pet: {e}")
            return jsonify({"error": "Произошла ошибка при добавлении питомца"}), 500

@app.route('/api/pets/<int:pet_id>', methods=['GET'])
def get_pet(pet_id):
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
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Требуется аутентификация"}), 401
            
        user_id = session['user_id']
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM pets WHERE id = ? AND user_id = ?', (pet_id, user_id))
            pet = cursor.fetchone()
            
            if not pet:
                cursor.execute('SELECT id FROM pets WHERE id = ?', (pet_id,))
                if cursor.fetchone():
                    return jsonify({"error": "У вас нет прав на удаление этого питомца"}), 403
                else:
                    return jsonify({"error": "Питомец не найден"}), 404
            
            cursor.execute('SELECT photo_path FROM pet_photos WHERE pet_id = ?', (pet_id,))
            photos = cursor.fetchall()
            
            for photo in photos:
                photo_path = os.path.join(UPLOAD_FOLDER, photo[0])
                try:
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                except Exception as e:
                    logger.error(f"Error deleting photo file {photo_path}: {e}")
            
            cursor.execute('DELETE FROM pet_photos WHERE pet_id = ?', (pet_id,))
            cursor.execute('DELETE FROM matches WHERE pet1_id = ? OR pet2_id = ?', (pet_id, pet_id))
            cursor.execute('DELETE FROM pets WHERE id = ?', (pet_id,))
            
            conn.commit()
            
            return jsonify({"message": "Питомец успешно удален"}), 200
            
    except sqlite3.Error as e:
        logger.error(f"Database error deleting pet {pet_id}: {e}")
        return jsonify({"error": "Произошла ошибка при удалении питомца"}), 500
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

def main():
    global app
    
    parser = argparse.ArgumentParser(description='Pet Finder Application')
    parser.add_argument('--api-port', type=int, default=API_PORT, help='Port for the API server')
    parser.add_argument('--no-bot', action='store_true', help='Disable Telegram bot')
    args = parser.parse_args()
    
    init_database()
    
    if not args.no_bot:
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Bot and dispatcher initialized successfully")
    
    logger.info(f"Starting API server on port {args.api_port}...")
    app.run(host=HOST, port=args.api_port, debug=False)

if __name__ == '__main__':
    main()















































