# db/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    searches = db.relationship('SearchRequest', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

class SearchRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    request_type = db.Column(db.String(20), nullable=False)  # 'lost' или 'found'
    image_path = db.Column(db.String(256))  # Путь к изображению
    breed = db.Column(db.String(50))
    category = db.Column(db.String(20))  # Собака или кошка
    gender = db.Column(db.String(10))
    size = db.Column(db.String(20))
    fur = db.Column(db.String(20))
    location = db.Column(db.String(100))
    chip_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_search_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    contact_info = db.Column(db.String(200))
    matches = db.relationship('SearchMatch', backref='search_request', lazy=True)

class SearchMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_request_id = db.Column(db.Integer, db.ForeignKey('search_request.id'))
    external_id = db.Column(db.String(50))  # ID из внешней системы
    source = db.Column(db.String(50))  # 'lost', 'found', или 'find_home'
    similarity_score = db.Column(db.Float)
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_notified = db.Column(db.Boolean, default=False)
    external_data = db.Column(db.JSON)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    search_match_id = db.Column(db.Integer, db.ForeignKey('search_match.id'))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(20))  # 'email' или 'web'
    status = db.Column(db.String(20))  # 'sent', 'delivered', 'failed'
    content = db.Column(db.Text)