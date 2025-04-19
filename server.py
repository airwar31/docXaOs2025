from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
DB_NAME = 'petfinder.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
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
        return jsonify({'authenticated': True}), 200
    return jsonify({'authenticated': False}), 200

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)