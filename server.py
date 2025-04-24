from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import requests
import json
from filter_utils import filter_matches_api_animal
from functools import wraps
from datetime import datetime
from image_processor import ImageProcessor
from translate_utils import translate_size, translate_fur, translate_tail, translate_ears
from task_scheduler import TaskScheduler
from telegram_bot import start_bot, notify_match, stop_bot, notify_similar_pet
from animal_api import AnimalAPI
import asyncio
from similar_pet_detector import SimilarPetDetector


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_NAME = 'petfinder.db'


image_processor = ImageProcessor()
similar_pet_detector = SimilarPetDetector(DB_NAME, UPLOAD_FOLDER)
task_scheduler = None

telegram_bot_task = None


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            telegram_chat_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notification_preferences JSON
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('lost', 'found')),
            breed TEXT,
            category TEXT NOT NULL CHECK(category IN ('dog', 'cat')),
            gender TEXT,
            color TEXT,
            district TEXT,
            chip TEXT,
            sterilization TEXT,
            special_marks TEXT,
            size TEXT,
            fur TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS pet_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS image_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id INTEGER NOT NULL,
            features BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (photo_id) REFERENCES pet_photos(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            search_params JSON,
            last_check_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_id INTEGER NOT NULL,
            external_pet_id INTEGER NOT NULL,
            similarity_score FLOAT NOT NULL,
            is_archived BOOLEAN DEFAULT 0,
            matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (search_id) REFERENCES searches(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def process_pet_data(pet_data, photo_type='lost'):
    if not isinstance(pet_data, dict):
        return None
        
    try:
        if 'id' not in pet_data:
            return None
            
        for field in ['breed', 'category', 'gender', 'size']:
            if isinstance(pet_data.get(field), dict):
                pet_data[field] = pet_data[field].get('name')
            
        if 'location' not in pet_data and 'address' in pet_data:
            pet_data['location'] = pet_data['address']
            
        photo_response = requests.get(
            f'https://animals.admhmao.ru/pets-api/open/{photo_type}-photo/{pet_data["id"]}/files'
        )
        photo_response.raise_for_status()
        photo_ids = photo_response.json()
        
        if photo_ids and isinstance(photo_ids, list) and len(photo_ids) > 0:
            pet_data['photo_url'] = f'https://animals.admhmao.ru/pets-api/open/{photo_type}-photo/{pet_data["id"]}/files/{photo_ids[0]}'
        else:
            pet_data['photo_url'] = None

        for key, value in pet_data.items():
            if str(value) == '[object Object]':
                pet_data[key] = None
                
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        print(f"Error processing pet {pet_data.get('id')}: {str(e)}")
        pet_data['photo_url'] = None
        
    return pet_data

@app.route('/')
def index():
    return send_from_directory('.', 'pet-finder.html')

@app.route('/pet-finder.css')
def pet_finder_css():
    return send_from_directory('.', 'pet-finder.css')

@app.route('/pet-finder.js')
def pet_finder_js():
    return send_from_directory('.', 'pet-finder.js')

@app.route('/createPetCard.js')
def create_pet_card_js():
    return send_from_directory('.', 'createPetCard.js')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    try:
        db = get_db()
        hashed_password = generate_password_hash(password)
        db.execute('INSERT INTO users (email, password) VALUES (?, ?)',
                  (email, hashed_password))
        db.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400
    finally:
        db.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    db.close()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        return jsonify({'message': 'Login successful'}), 200
    
    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id']
        }), 200
    return jsonify({
        'authenticated': False,
        'user_id': None
    }), 200

@app.route('/api/pets', methods=['GET'])
def get_pets():
    animal_type = request.args.get('type', 'all')
    page = request.args.get('page', 0, type=int)
    size = request.args.get('size', 8, type=int)
    
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    filter_category = request.args.get('category', '').strip()
    filter_gender = request.args.get('gender', '').strip()
    filter_size = request.args.get('size_filter', '').strip()  # Using size_filter to avoid conflict with page size
    filter_fur = request.args.get('fur', '').strip()
    filter_color = request.args.get('color', '').strip()
    filter_district = request.args.get('district', '').strip()
    filter_special_marks = request.args.get('special_marks', '').strip()
    
    try:
        # Get animals from external API - fetch all without pagination
        api_animals = []
        if animal_type != 'db_only':  # Add a new option to fetch only from DB
            # Use a large size to get all animals from API without pagination
            api_animals = AnimalAPI.get_all_animals(animal_type=animal_type, size=1000, page=0)
            
            processed_api_animals = []
            for animal in api_animals:
                processed_animal = AnimalAPI.extract_animal_info(animal)
                
                # Apply filters to API animals
                if not filter_matches_api_animal(processed_animal, search_query, filter_category, 
                                               filter_gender, filter_size, filter_fur, 
                                               filter_color, filter_district, filter_special_marks):
                    continue
                    
                processed_api_animals.append(processed_animal)
        else:
            processed_api_animals = []
        
        # Get animals from database with server-side filtering
        db_animals = []
        if animal_type in ['all', 'lost', 'found', 'db_only']:
            db = get_db()
            cursor = db.cursor()
            
            # Build the query based on the animal type and filters
            query = '''
                SELECT p.*, u.email as user_email, GROUP_CONCAT(pp.photo_path) as photos
                FROM pets p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN pet_photos pp ON p.id = pp.pet_id
                WHERE 1=1
            '''
            
            params = []
            
            # Filter by animal type
            if animal_type not in ['all', 'db_only']:
                query += ' AND p.type = ?'
                params.append(animal_type)
            
            # Apply search query to multiple fields
            if search_query:
                query += ''' AND (
                    p.breed LIKE ? OR 
                    p.location LIKE ? OR 
                    p.district LIKE ? OR 
                    p.special_marks LIKE ? OR
                    p.color LIKE ?
                )'''
                search_param = f'%{search_query}%'
                params.extend([search_param, search_param, search_param, search_param, search_param])
            
            # Apply filters
            if filter_category:
                query += ' AND p.category = ?'
                params.append(filter_category)
                
            if filter_gender:
                query += ' AND p.gender = ?'
                params.append(filter_gender)
                
            if filter_size:
                query += ' AND p.size LIKE ?'
                params.append(f'%{filter_size}%')
                
            if filter_fur:
                query += ' AND p.fur LIKE ?'
                params.append(f'%{filter_fur}%')
                
            if filter_color:
                query += ' AND p.color LIKE ?'
                params.append(f'%{filter_color}%')
                
            if filter_district:
                query += ' AND p.district LIKE ?'
                params.append(f'%{filter_district}%')
                
            if filter_special_marks:
                query += ' AND p.special_marks LIKE ?'
                params.append(f'%{filter_special_marks}%')
                
            query += ' GROUP BY p.id ORDER BY p.created_at DESC'
            
            cursor.execute(query, params)
            db_pets = cursor.fetchall()
            
            # Process database pets to match the format expected by the frontend
            for pet in db_pets:
                pet_dict = dict(pet)
                
                # Process photos
                if pet_dict['photos']:
                    pet_dict['photos'] = pet_dict['photos'].split(',')
                else:
                    pet_dict['photos'] = []
                
                # Add source information
                pet_dict['source'] = 'database'
                
                # Format the pet data to match the structure expected by the frontend
                formatted_pet = {
                    'id': pet_dict['id'],
                    'user_id': pet_dict['user_id'],
                    'category': 'Пропавшие' if pet_dict['type'] == 'lost' else 'Найденные',
                    'type': pet_dict['category'],  # 'dog' or 'cat'
                    'gender': pet_dict['gender'],
                    'breed': pet_dict['breed'],
                    'color': pet_dict['color'],
                    'district': pet_dict['district'],
                    'chip': pet_dict['chip'],
                    'sterilization': pet_dict['sterilization'],
                    'special_marks': pet_dict['special_marks'],
                    'size': pet_dict['size'],
                    'fur': pet_dict['fur'],
                    'location': pet_dict['location'],
                    'photos': pet_dict['photos'],
                    'contact_info': f"Email: {pet_dict['user_email']}",
                    'description': f"Порода: {pet_dict['breed']}. Пол: {pet_dict['gender']}. Размер: {pet_dict['size']}. Шерсть: {pet_dict['fur']}. Особые приметы: {pet_dict['special_marks']}",
                    'created_at': pet_dict['created_at']
                }
                
                db_animals.append(formatted_pet)
            
            db.close()
        
        # Combine animals from both sources - API animals first, then database animals
        all_animals = processed_api_animals + db_animals
        
        # Apply pagination to the combined list
        start_idx = page * size
        end_idx = start_idx + size
        paginated_animals = all_animals[start_idx:end_idx] if start_idx < len(all_animals) else []
        
        return jsonify(paginated_animals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pets', methods=['POST'])
@login_required
def add_pet():
    if 'photos' not in request.files:
        return jsonify({'error': 'No photos provided'}), 400
        
    photos = request.files.getlist('photos')
    if not photos or photos[0].filename == '':
        return jsonify({'error': 'No photos selected'}), 400

    data = request.form.to_dict()
    
    if 'type' not in data or data['type'] not in ['lost', 'found']:
        return jsonify({'error': 'Invalid type. Must be "lost" or "found"'}), 400
    if 'category' not in data or data['category'] not in ['dog', 'cat']:
        return jsonify({'error': 'Invalid category. Must be "dog" or "cat"'}), 400
        
    data.setdefault('breed', 'Не указан')
    data.setdefault('gender', 'Не указан')
    data.setdefault('color', 'Не указан')
    data.setdefault('district', 'Не указан')
    data.setdefault('chip', 'Нет данных')
    data.setdefault('sterilization', 'Нет данных')
    data.setdefault('special_marks', 'Нет')
    data.setdefault('size', 'Не указан')
    data.setdefault('fur', 'Не указан')
    data.setdefault('location', 'Не указан')

    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO pets (
                user_id, type, breed, category, gender, color, district,
                chip, sterilization, special_marks, size, fur, location
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data['type'],
            data['breed'],
            data['category'],
            data['gender'],
            data['color'],
            data['district'],
            data['chip'],
            data['sterilization'],
            data['special_marks'],
            data['size'],
            data['fur'],
            data['location']
        ))
        
        pet_id = cursor.lastrowid
        
        for photo in photos:
            if photo and allowed_file(photo.filename):
                filename = secure_filename(f"{pet_id}_{photo.filename}")
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                
                cursor.execute('''
                    INSERT INTO pet_photos (pet_id, photo_path)
                    VALUES (?, ?)
                ''', (pet_id, filename))
                photo_id = cursor.lastrowid
                
                features = image_processor.extract_features(photo_path)
                if features:
                    cursor.execute('''
                        INSERT INTO image_features (photo_id, features)
                        VALUES (?, ?)
                    ''', (photo_id, json.dumps(features)))
        
        search_params = {
            'breed': data['breed'],
            'category': data['category'],
            'gender': data['gender'],
            'color': data['color'],
            'district': data['district'],
            'chip': data['chip'],
            'sterilization': data['sterilization'],
            'special_marks': data['special_marks'],
            'size': data['size'],
            'fur': data['fur'],
            'location': data['location']
        }
        
        cursor.execute('''
            INSERT INTO searches (pet_id, search_params, last_check_time)
            VALUES (?, ?, datetime('now'))
        ''', (pet_id, json.dumps(search_params)))
        
        # Check for similar pets and send notifications
        try:
            similar_pets = similar_pet_detector.find_similar_pets(pet_id)
            
            if similar_pets:
                # Get details of the newly added pet
                
                # Get the current user's notification preferences
                cursor.execute(
                    'SELECT notification_preferences, telegram_chat_id FROM users WHERE id = ?',
                    (session['user_id'],)
                )
                current_user = cursor.fetchone()
                
                # Send notification to the current user about similar pets found
                if current_user and current_user['telegram_chat_id']:
                    notification_prefs = json.loads(current_user['notification_preferences'] or '{}')
                    if notification_prefs.get('telegram_enabled', False):
                        for similar_pet in similar_pets:
                            try:
                                # Get the similar pet details
                                similar_pet_details = similar_pet_detector.get_pet_details(similar_pet['id'])
                                
                                if similar_pet_details and new_pet_details:
                                    # Send notification to current user about the similar pet
                                    asyncio.run(notify_similar_pet(
                                        session['user_id'],
                                        new_pet_details,
                                        similar_pet_details,
                                        similar_pet['similarity_score']
                                    ))
                                    print(f"Sent notification to current user {session['user_id']} about similar pet {similar_pet['id']}")
                            except Exception as e:
                                print(f"Error sending notification to current user about similar pet {similar_pet['id']}: {e}")
                new_pet_details = similar_pet_detector.get_pet_details(pet_id)
                
                # Send notifications to owners of similar pets
                for similar_pet in similar_pets:
                    try:
                        # Get the original pet details
                        original_pet = similar_pet_detector.get_pet_details(similar_pet['id'])
                        
                        if original_pet and new_pet_details:
                            # Send notification asynchronously
                            asyncio.run(notify_similar_pet(
                                original_pet['user_id'],
                                original_pet,
                                new_pet_details,
                                similar_pet['similarity_score']
                            ))
                            print(f"Sent notification about similar pet to user {original_pet['user_id']}")
                    except Exception as e:
                        print(f"Error sending notification for similar pet {similar_pet['id']}: {e}")
        except Exception as e:
            print(f"Error checking for similar pets: {e}")
        
        db.commit()
        return jsonify({
            'message': 'Pet added successfully',
            'pet_id': pet_id
        }), 201
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/pets/<int:pet_id>', methods=['GET'])
def get_pet(pet_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT p.*, u.email as user_email
            FROM pets p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        ''', (pet_id,))
        
        pet = cursor.fetchone()
        if not pet:
            return jsonify({'error': 'Pet not found'}), 404
            
        cursor.execute('SELECT photo_path FROM pet_photos WHERE pet_id = ?', (pet_id,))
        photos = cursor.fetchall()
        
        pet_dict = dict(pet)
        pet_dict['photos'] = [photo['photo_path'] for photo in photos]
        
        return jsonify(pet_dict)
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/pets/<int:pet_id>', methods=['DELETE'])
@login_required
def delete_pet(pet_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT user_id FROM pets WHERE id = ?', (pet_id,))
        pet = cursor.fetchone()
        
        if not pet:
            return jsonify({'error': 'Pet not found'}), 404
        if pet['user_id'] != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        cursor.execute('SELECT photo_path FROM pet_photos WHERE pet_id = ?', (pet_id,))
        photos = cursor.fetchall()
        
        for photo in photos:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo['photo_path']))
            except OSError:
                pass
                
        cursor.execute('DELETE FROM pet_photos WHERE pet_id = ?', (pet_id,))
        cursor.execute('DELETE FROM pets WHERE id = ?', (pet_id,))
        
        db.commit()
        return jsonify({'message': 'Pet deleted successfully'}), 200
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/notification-preferences', methods=['GET', 'PUT'])
@login_required
def notification_preferences():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT notification_preferences FROM users WHERE id = ?', (session['user_id'],))
        prefs = cursor.fetchone()
        return jsonify(json.loads(prefs['notification_preferences'] or '{}'))
        
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            if 'telegram_enabled' not in data:
                data['telegram_enabled'] = False
                
            cursor.execute('''
                UPDATE users 
                SET notification_preferences = ?
                WHERE id = ?
            ''', (json.dumps(data), session['user_id']))
            db.commit()
            return jsonify({'message': 'Preferences updated successfully'})
        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

@app.route('/api/searches', methods=['GET'])
@login_required
def get_searches():
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT s.*, p.type, p.category, p.breed, p.location,
                   m.id as match_id, m.external_pet_id, m.similarity_score, m.matched_at
            FROM searches s
            JOIN pets p ON s.pet_id = p.id
            LEFT JOIN matches m ON s.id = m.search_id AND m.is_archived = 0
            WHERE p.user_id = ?
            ORDER BY s.created_at DESC
        ''', (session['user_id'],))
        
        searches = cursor.fetchall()
        result = []
        
        for search in searches:
            search_dict = dict(search)
            search_dict['search_params'] = json.loads(search_dict['search_params'])
            result.append(search_dict)
            
        return jsonify(result)
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/searches/<int:search_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_search(search_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT s.id
            FROM searches s
            JOIN pets p ON s.pet_id = p.id
            WHERE s.id = ? AND p.user_id = ?
        ''', (search_id, session['user_id']))
        
        if not cursor.fetchone():
            return jsonify({'error': 'Search not found or unauthorized'}), 404
            
        if request.method == 'PUT':
            data = request.get_json()
            cursor.execute('''
                UPDATE searches
                SET is_active = ?, search_params = ?
                WHERE id = ?
            ''', (data.get('is_active', True), json.dumps(data.get('search_params', {})), search_id))
            
        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM matches WHERE search_id = ?', (search_id,))
            cursor.execute('DELETE FROM searches WHERE id = ?', (search_id,))
            
        db.commit()
        return jsonify({'message': 'Search updated successfully'})
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/matches', methods=['GET'])
@login_required
def get_matches():
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT m.*, s.pet_id, p.type, p.category, p.breed, p.location
            FROM matches m
            JOIN searches s ON m.search_id = s.id
            JOIN pets p ON s.pet_id = p.id
            WHERE p.user_id = ? AND m.is_archived = 0
            ORDER BY m.matched_at DESC
        ''', (session['user_id'],))
        
        matches = cursor.fetchall()
        result = []
        
        for match in matches:
            match_dict = dict(match)
            result.append(match_dict)
            
        return jsonify(result)
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/matches/<int:match_id>', methods=['PUT'])
@login_required
def update_match(match_id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT m.id
            FROM matches m
            JOIN searches s ON m.search_id = s.id
            JOIN pets p ON s.pet_id = p.id
            WHERE m.id = ? AND p.user_id = ?
        ''', (match_id, session['user_id']))
        
        if not cursor.fetchone():
            return jsonify({'error': 'Match not found or unauthorized'}), 404
            
        data = request.get_json()
        cursor.execute('''
            UPDATE matches
            SET is_archived = ?
            WHERE id = ?
        ''', (data.get('is_archived', False), match_id))
        
        db.commit()
        return jsonify({'message': 'Match updated successfully'})
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/my-pets', methods=['GET'])
@login_required
def get_my_pets():
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT p.*, GROUP_CONCAT(pp.photo_path) as photos
            FROM pets p
            LEFT JOIN pet_photos pp ON p.id = pp.pet_id
            WHERE p.user_id = ?
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''', (session['user_id'],))
        
        pets = cursor.fetchall()
        result = []
        
        for pet in pets:
            pet_dict = dict(pet)
            if pet_dict['photos']:
                pet_dict['photos'] = pet_dict['photos'].split(',')
            else:
                pet_dict['photos'] = []
            result.append(pet_dict)
            
        return jsonify(result)
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

with app.app_context():
    try:
        init_db()
        print("Database initialized successfully")
        
        task_scheduler = TaskScheduler(app, DB_NAME)
        print("Task scheduler initialized successfully")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        telegram_bot_task = loop.create_task(start_bot())
        print("Telegram bot initialized successfully")
        
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise
    except Exception as e:
        print(f"Error initializing services: {e}")
        raise

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        try:
            os.makedirs(UPLOAD_FOLDER)
            print(f"Created upload folder: {UPLOAD_FOLDER}")
        except OSError as e:
            print(f"Error creating upload folder: {e}")
            raise

    try:
        app.run(host='localhost', port=5000, debug=True)
    finally:
        if task_scheduler:
            task_scheduler.shutdown()
        if telegram_bot_task:
            telegram_bot_task.cancel()





















