from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import requests
from datetime import datetime
import os
import io
from PIL import Image
import numpy as np
from tensorflow.keras.applications.resnet50 import preprocess_input
import tensorflow as tf
from config import Config
from extensions import db, login_manager, mail, model, init_extensions
from models import User, SearchRequest

# Flask application initialization
app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
init_extensions(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        new_user = User(
            email=email,
            password=generate_password_hash(password, method='sha256'),
            name=name
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    searches = SearchRequest.query.filter_by(user_id=current_user.id).order_by(SearchRequest.last_check_date.desc()).all()
    return render_template('dashboard.html', user=current_user, searches=searches)

@app.route('/new_search', methods=['GET', 'POST'])
@login_required
def new_search():
    """Handle creation of new pet search requests."""
    if request.method == 'POST':
        search_type = request.form['search_type']
        image = request.files.get('image')
        notify = request.form.get('notify_on_match', 'true') == 'true'
        
        search_data = {
            'breed': request.form.get('breed'),
            'category': request.form.get('category'),
            'gender': request.form.get('gender'),
            'size': request.form.get('size'),
            'hair': request.form.get('hair'),
            'location': request.form.get('location'),
            'chip_number': request.form.get('chip_number')
        }
        
        # Process and save image if provided
        image_path = None
        image_vector = None
        if image:
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            
            # Generate image vector using ResNet50
            img = Image.open(image_path).resize((224, 224))
            img_array = np.array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            image_vector = model.predict(img_array)
        
        # Create new search request
        new_search = SearchRequest(
            user_id=current_user.id,
            search_type=search_type,
            image_path=image_path,
            image_vector=image_vector,
            last_check_date=datetime.now(),
            active=True,
            notify_on_match=notify,
            **search_data
        )
        db.session.add(new_search)
        db.session.commit()
        
        # Search for matches
        results = search_matches(new_search)
        
        if not results and notify:
            flash('No matches found. We will notify you when we find potential matches.', 'info')
        
        return render_template('search_results.html', results=results, search=new_search)
    
    return render_template('new_search.html')

@app.route('/search/<int:search_id>/toggle_active', methods=['POST'])
@login_required
def toggle_search_active(search_id):
    """Toggle the active status of a search."""
    search = SearchRequest.query.get_or_404(search_id)
    if search.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    search.active = not search.active
    db.session.commit()
    
    status = 'activated' if search.active else 'deactivated'
    flash(f'Search {status} successfully', 'success')
    return redirect(url_for('dashboard'))

def search_matches(search_request):
    """Search for matches across all three sections."""
    sections = [
        ('lost', 'placementDate'),
        ('found', 'placementDate'),
        ('find-home', 'shelterArrival')
    ]
    
    results = []
    for endpoint, date_field in sections:
        # Skip if searching in the same section as the request
        if (endpoint == 'lost' and search_request.search_type == 'lost') or \
           (endpoint == 'found' and search_request.search_type == 'found'):
            continue
        
        api_url = f"{app.config['API_BASE_URL']}/{endpoint}"
        params = {
            'sort': f"{date_field},desc",
            'sort': 'id,desc',
            'page': 0,
            'size': 50
        }
        
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            animals = response.json().get('content', [])
        except requests.exceptions.RequestException as e:
            app.logger.error(f"API request failed for {endpoint}: {e}")
            continue
        
        for animal in animals:
            if not matches_criteria(animal, search_request):
                continue
                
            if search_request.image_vector is not None:
                similarity = matches_image(animal, search_request, endpoint)
                if similarity is None or similarity < app.config['IMAGE_SIMILARITY_THRESHOLD']:
                    continue
                animal['similarity'] = similarity
            
            animal['section'] = endpoint
            results.append(animal)
    
    return results

def matches_criteria(animal, search_request):
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
        search_value = getattr(search_request, field)
        if search_value and not compare(search_value, animal.get(field, '')):
            return False
    return True

def matches_image(animal, search_request, endpoint):
    """Compare images and return similarity score if successful, None if failed."""
    animal_id = animal.get('id')
    photos_url = f"{app.config['API_BASE_URL']}/{endpoint}-photo/{animal_id}/files"
    
    try:
        photos_response = requests.get(photos_url)
        photos_response.raise_for_status()
        photos = photos_response.json()
        
        if not photos:
            return None
            
        photo_id = photos[0].get('id')
        photo_url = f"{photos_url}/{photo_id}"
        
        photo_response = requests.get(photo_url, stream=True)
        photo_response.raise_for_status()
        
        img = Image.open(io.BytesIO(photo_response.content)).resize((224, 224))
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        compare_vector = model.predict(img_array)
        
        return cosine_similarity(search_request.image_vector, compare_vector)
        
    except (requests.exceptions.RequestException, IOError) as e:
        app.logger.error(f"Image processing failed for {endpoint}/{animal_id}: {e}")
        return None

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    return float(np.dot(vec1.flatten(), vec2.flatten()) / 
                (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)









