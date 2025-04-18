# web/app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from db.models import db, User, SearchRequest, SearchMatch, Notification
import os
import requests
from datetime import datetime
import json
from PIL import Image
import numpy as np
from werkzeug.utils import secure_filename
import threading
import time
from functools import wraps

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['SECRET_KEY'] = 'dasdqwdqwWQIDH218124iwadhWOiqwfodvkjwev'  # Change to a real secret key
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize migrations
    from flask_migrate import Migrate
    migrate = Migrate(app, db)
    
    return app

app = create_app()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def background_search():
    with app.app_context():
        while True:
            try:
                # Получаем все активные запросы на поиск
                active_requests = SearchRequest.query.filter_by(is_active=True).all()
                
                for request in active_requests:
                    try:
                        last_search = request.last_search_date or request.created_at
                        
                        # Поиск в разных разделах API
                        sources = [
                            ('lost', 'https://animals.admhmao.ru/pets-api/open/lost'),
                            ('found', 'https://animals.admhmao.ru/pets-api/open/found'),
                            ('find_home', 'https://animals.admhmao.ru/pets-api/open/find-home')
                        ]
                
                        for source_type, base_url in sources:
                            try:
                                # Получаем новые записи с момента последнего поиска
                                params = {
                                    'sort': 'placementDate,desc',
                                    'sort': 'id,desc',
                                    'page': 0,
                                    'size': 100
                                }
                                
                                response = requests.get(base_url, params=params)
                                if response.status_code == 200:
                                    animals = response.json()
                                    
                                    for animal in animals:
                                        try:
                                            # Проверяем дату создания записи
                                            animal_date = datetime.fromisoformat(animal.get('placementDate', '').replace('Z', '+00:00'))
                                            if animal_date > last_search:
                                                # Получаем фотографии животного
                                                photos_url = f"{base_url}-photo/{animal['id']}/files"
                                                photos_response = requests.get(photos_url)
                                                
                                                if photos_response.status_code == 200:
                                                    photos = photos_response.json()
                                                    
                                                    # Сравниваем фотографии
                                                    for photo in photos:
                                                        try:
                                                            similarity = compare_images(request.image_path, photo['url'])
                                                            
                                                            if similarity > 0.7:  # Пороговое значение схожести
                                                                # Создаем запись о совпадении
                                                                match = SearchMatch(
                                                                    search_request_id=request.id,
                                                                    external_id=str(animal['id']),
                                                                    source=source_type,
                                                                    similarity_score=similarity,
                                                                    external_data=json.dumps(animal)
                                                                )
                                                                db.session.add(match)
                                                                
                                                                # Создаем уведомление
                                                                notification = Notification(
                                                                    user_id=request.user_id,
                                                                    search_match_id=match.id,
                                                                    type='in_app',
                                                                    content=f'Найдено потенциальное совпадение для вашего поиска!'
                                                                )
                                                                db.session.add(notification)
                                                        except Exception as e:
                                                            print(f"Error processing photo: {str(e)}")
                                                            continue
                                        except Exception as e:
                                            print(f"Error processing animal: {str(e)}")
                                            continue
                            except Exception as e:
                                print(f"Error processing source {source_type}: {str(e)}")
                                continue
                        
                        request.last_search_date = datetime.utcnow()
                        db.session.commit()
                    except Exception as e:
                        print(f"Error processing request {request.id}: {str(e)}")
                        continue
            except Exception as e:
                print(f"Error in background search: {str(e)}")
            finally:
                time.sleep(3600)  # Проверяем раз в час

def compare_images(image1_path, image2_url):
    # Загружаем первое изображение
    img1 = Image.open(image1_path)
    img1 = img1.resize((224, 224))  # Стандартный размер для сравнения
    img1_array = np.array(img1)
    
    # Загружаем второе изображение по URL
    response = requests.get(image2_url)
    img2 = Image.open(response.raw)
    img2 = img2.resize((224, 224))
    img2_array = np.array(img2)
    
    # Простое сравнение по пикселям (в реальном приложении нужно использовать более сложные методы)
    similarity = np.mean(img1_array == img2_array)
    return similarity


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        
        # Проверяем, существует ли пользователь
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Этот email уже зарегистрирован')
            return redirect(url_for('register'))
        
        new_user = User(email=email)
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        flash('Регистрация успешна!')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            session['user_id'] = user.id
            flash('Вход выполнен успешно!')
            return redirect(url_for('index'))
        else:
            flash('Пользователь не найден')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
@login_required
def search():
    if 'image' not in request.files:
        flash('Не загружено изображение')
        return redirect(url_for('index'))
    
    file = request.files['image']
    if file.filename == '':
        flash('Не выбрано изображение')
        return redirect(url_for('index'))
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Получаем данные из формы
    search_type = request.form.get('search_type')  # 'lost' или 'found'
    breed = request.form.get('breed')
    category = request.form.get('category')
    gender = request.form.get('gender')
    size = request.form.get('size')
    fur = request.form.get('fur')
    location = request.form.get('location')
    chip_number = request.form.get('chip_number')
    description = request.form.get('description')
    contact_info = request.form.get('contact_info')
    
    # Создаем новый запрос на поиск
    new_request = SearchRequest(
        user_id=session['user_id'],
        request_type=search_type,
        image_path=file_path,
        breed=breed,
        category=category,
        gender=gender,
        size=size,
        fur=fur,
        location=location,
        chip_number=chip_number,
        description=description,
        contact_info=contact_info
    )
    
    db.session.add(new_request)
    db.session.commit()
    
    # Выполняем немедленный поиск
    search_results = search_animals(new_request)
    
    return render_template('results.html', results=search_results)

def search_animals(search_request):
    results = []
    
    # Определяем API endpoints в зависимости от типа поиска
    if search_request.request_type == 'lost':
        endpoints = [
            ('found', 'https://animals.admhmao.ru/pets-api/open/found'),
            ('find_home', 'https://animals.admhmao.ru/pets-api/open/find-home')
        ]
    else:  # found
        endpoints = [
            ('lost', 'https://animals.admhmao.ru/pets-api/open/lost'),
            ('find_home', 'https://animals.admhmao.ru/pets-api/open/find-home')
        ]
    
    for source_type, base_url in endpoints:
        params = {
            'sort': 'placementDate,desc',
            'sort': 'id,desc',
            'page': 0,
            'size': 100
        }
        
        # Добавляем параметры фильтрации
        if search_request.category:
            params['category'] = search_request.category
        if search_request.location:
            params['location'] = search_request.location
        
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            animals = response.json()
            
            for animal in animals:
                # Проверяем совпадение параметров
                if (search_request.breed and search_request.breed.lower() != animal.get('breed', '').lower()):
                    continuevbb
                    continue
                if (search_request.size and search_request.size.lower() != animal.get('size', '').lower()):
                    continue
                if (search_request.fur and search_request.fur.lower() != animal.get('fur', '').lower()):
                    continue
                if (search_request.chip_number and search_request.chip_number != animal.get('chipNumber')):
                    continue
                
                # Получаем фотографии животного
                photos_url = f"{base_url}-photo/{animal['id']}/files"
                photos_response = requests.get(photos_url)
                
                if photos_response.status_code == 200:
                    photos = photos_response.json()
                    max_similarity = 0
                    
                    # Сравниваем со всеми фотографиями
                    for photo in photos:
                        similarity = compare_images(search_request.image_path, photo['url'])
                        max_similarity = max(max_similarity, similarity)
                    
                    if max_similarity > 0.7:  # Пороговое значение схожести
                        animal['similarity'] = max_similarity
                        animal['source'] = source_type
                        results.append(animal)
    
    # Сортируем результаты по схожести
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results

@app.route('/my-searches')
@login_required
def my_searches():
    user_searches = SearchRequest.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_searches.html', searches=user_searches)

@app.route('/search/<int:search_id>')
@login_required
def search_details(search_id):
    search = SearchRequest.query.get_or_404(search_id)
    if search.user_id != session['user_id']:
        flash('Доступ запрещен')
        return redirect(url_for('my_searches'))
    
    matches = SearchMatch.query.filter_by(search_request_id=search_id).all()
    return render_template('search_details.html', search=search, matches=matches)

if __name__ == '__main__':
    # Create and configure the app
    app = create_app()
    
    # Запускаем фоновый поиск в отдельном потоке
    background_thread = threading.Thread(target=background_search)
    background_thread.daemon = True
    background_thread.start()
    
    app.run(debug=True)










