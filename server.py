from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import requests
from functools import wraps
from datetime import datetime

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DB_NAME = 'petfinder.db'

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create pets table
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
    
    # Create table for pet photos
    c.execute('''
        CREATE TABLE IF NOT EXISTS pet_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pet_id) REFERENCES pets(id)
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
    """Helper function to process pet data and handle nested objects"""
    if not isinstance(pet_data, dict):
        return None
        
    try:
        if 'id' not in pet_data:
            return None
            
        # Process nested objects
        for field in ['breed', 'category', 'gender', 'size']:
            if isinstance(pet_data.get(field), dict):
                pet_data[field] = pet_data[field].get('name')
            
        # Handle location/address
        if 'location' not in pet_data and 'address' in pet_data:
            pet_data['location'] = pet_data['address']
            
        # Get photo
        photo_response = requests.get(
            f'https://animals.admhmao.ru/pets-api/open/{photo_type}-photo/{pet_data["id"]}/files'
        )
        photo_response.raise_for_status()
        photo_ids = photo_response.json()
        
        if photo_ids and isinstance(photo_ids, list) and len(photo_ids) > 0:
            pet_data['photo_url'] = f'https://animals.admhmao.ru/pets-api/open/{photo_type}-photo/{pet_data["id"]}/files/{photo_ids[0]}'
        else:
            pet_data['photo_url'] = None

        # Clean up any remaining [object Object] strings
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
        
        # Parse and validate response
        try:
            pets_data = response.json()
        except ValueError as e:
            return jsonify({'error': 'Invalid JSON response from API'}), 500
            
        # Handle both possible response formats (direct list or paginated object)
        if isinstance(pets_data, dict) and 'content' in pets_data:
            pets = pets_data['content']
        elif isinstance(pets_data, list):
            pets = pets_data
        else:
            return jsonify({'error': 'Unexpected API response format'}), 500
            
        # Process each pet
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
            
        # Handle both possible response formats (direct list or paginated object)
        if isinstance(pets_data, dict) and 'content' in pets_data:
            pets = pets_data['content']
        elif isinstance(pets_data, list):
            pets = pets_data
        else:
            return jsonify({'error': 'Unexpected API response format'}), 500
            
        # Process each pet
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
        
        # Insert pet record
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
        
        # Save photos
        for photo in photos:
            if photo and allowed_file(photo.filename):
                filename = secure_filename(f"{pet_id}_{photo.filename}")
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                
                cursor.execute('''
                    INSERT INTO pet_photos (pet_id, photo_path)
                    VALUES (?, ?)
                ''', (pet_id, filename))
        
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
        
        # Get pet details
        cursor.execute('''
            SELECT p.*, u.email as user_email
            FROM pets p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        ''', (pet_id,))
        
        pet = cursor.fetchone()
        if not pet:
            return jsonify({'error': 'Pet not found'}), 404
            
        # Get pet photos
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
        
        # Check if pet belongs to user
        cursor.execute('SELECT user_id FROM pets WHERE id = ?', (pet_id,))
        pet = cursor.fetchone()
        
        if not pet:
            return jsonify({'error': 'Pet not found'}), 404
        if pet['user_id'] != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get photos to delete
        cursor.execute('SELECT photo_path FROM pet_photos WHERE pet_id = ?', (pet_id,))
        photos = cursor.fetchall()
        
        # Delete photos from filesystem
        for photo in photos:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], photo['photo_path']))
            except OSError:
                pass  # Ignore errors if file doesn't exist
                
        # Delete from database
        cursor.execute('DELETE FROM pet_photos WHERE pet_id = ?', (pet_id,))
        cursor.execute('DELETE FROM pets WHERE id = ?', (pet_id,))
        
        db.commit()
        return jsonify({'message': 'Pet deleted successfully'}), 200
        
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

# Initialize the database when the application starts
with app.app_context():
    try:
        init_db()
        print("Database initialized successfully")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        try:
            os.makedirs(UPLOAD_FOLDER)
            print(f"Created upload folder: {UPLOAD_FOLDER}")
        except OSError as e:
            print(f"Error creating upload folder: {e}")
            raise

    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)

