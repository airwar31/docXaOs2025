from flask_login import UserMixin
from extensions import db

class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    searches = db.relationship('SearchRequest', backref='user', lazy=True)

class SearchRequest(db.Model):
    """Model for storing pet search requests and their parameters."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    search_type = db.Column(db.String(20))  # lost/found
    breed = db.Column(db.String(100))
    category = db.Column(db.String(20))  # dog/cat
    gender = db.Column(db.String(10))
    size = db.Column(db.String(10))
    hair = db.Column(db.String(20))
    location = db.Column(db.String(100))
    chip_number = db.Column(db.String(50))
    image_path = db.Column(db.String(200))
    image_vector = db.Column(db.PickleType)
    last_check_date = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    notify_on_match = db.Column(db.Boolean, default=True)