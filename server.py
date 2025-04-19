from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import requests
import json
from functools import wraps
from datetime import datetime
from image_processor import ImageProcessor
from task_scheduler import TaskScheduler
from telegram_bot import start_bot, notify_match
import asyncio


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_NAME = 'petfinder.db'


image_processor = ImageProcessor()
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
            last_login TIMESTAMP,
            notification_preferences JSON
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('lost', 'found')),
            breed TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('dog', 'cat')),
            gender TEXT NOT NULL CHECK(gender IN ('male', 'female')),
            size TEXT NOT NULL,
            fur TEXT NOT NULL,
            location TEXT NOT NULL,
            chip_number TEXT,
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

@app.route('/api/pets/lost', methods=['GET'])
def get_lost_pets():
    page = request.args.get('page', 0, type=int)
    size = request.args.get('size', 8, type=int)
    
    try:
        response = requests.get(
            f'https://animals.admhmao.ru/pets-api/open/lost',
            params={
                'sort': ['placementDate,desc', 'id,desc'],
                'page': page,
                'size': size
            }
        )
        response.raise_for_status()
        
        try:
            pets_data = response.json()
        except ValueError as e:
            return jsonify({'error': 'Invalid JSON response from API'}), 500
            
        if isinstance(pets_data, dict) and 'content' in pets_data:
            pets = pets_data['content']
        elif isinstance(pets_data, list):
            pets = pets_data
        else:
            return jsonify({'error': 'Unexpected API response format'}), 500
            
        processed_pets = []
        for pet in pets:
            processed_pet = process_pet_data(pet, 'lost')
            if processed_pet:
                processed_pets.append(processed_pet)
        
        return jsonify(processed_pets)
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pets/found', methods=['GET'])
def get_found_pets():
    page = request.args.get('page', 0, type=int)
    size = request.args.get('size', 8, type=int)
    
    try:
        response = requests.get(
            f'https://animals.admhmao.ru/pets-api/open/found',
            params={
                'sort': ['placementDate,desc', 'id,desc'],
                'page': page,
                'size': size
            }
        )
        response.raise_for_status()
        
        # Parse and validate response
        try:
            pets_data = response.json()
        except ValueError as e:
            return jsonify({'error': 'Invalid JSON response from API'}), 500
            
        if isinstance(pets_data, dict) and 'content' in pets_data:
            pets = pets_data['content']
        elif isinstance(pets_data, list):
            pets = pets_data
        else:
            return jsonify({'error': 'Unexpected API response format'}), 500
            
        processed_pets = []
        for pet in pets:
            processed_pet = process_pet_data(pet, 'found')
            if processed_pet:
                processed_pets.append(processed_pet)
        
        return jsonify(processed_pets)
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pets', methods=['POST'])
@login_required
def add_pet():
    if 'photos' not in request.files:
        return jsonify({'error': 'No photos provided'}), 400
        
    photos = request.files.getlist('photos')
    if not photos or photos[0].filename == '':
        return jsonify({'error': 'No photos selected'}), 400

    # Validate form data
    required_fields = ['type', 'breed', 'category', 'gender', 'size', 'fur', 'location']
    data = request.form.to_dict()
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
            
    # Validate type and category
    if data['type'] not in ['lost', 'found']:
        return jsonify({'error': 'Invalid type. Must be "lost" or "found"'}), 400
    if data['category'] not in ['dog', 'cat']:
        return jsonify({'error': 'Invalid category. Must be "dog" or "cat"'}), 400
    if data['gender'] not in ['male', 'female']:
        return jsonify({'error': 'Invalid gender. Must be "male" or "female"'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO pets (user_id, type, breed, category, gender, size, fur, location, chip_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data['type'],
            data['breed'],
            data['category'],
            data['gender'],
            data['size'],
            data['fur'],
            data['location'],
            data.get('chip_number')
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
            'size': data['size'],
            'fur': data['fur'],
            'location': data['location'],
            'chip_number': data.get('chip_number')
        }
        
        cursor.execute('''
            INSERT INTO searches (pet_id, search_params, last_check_time)
            VALUES (?, ?, datetime('now'))
        ''', (pet_id, json.dumps(search_params)))
        
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














