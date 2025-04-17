from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.models import Model
from celery import Celery

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

# Initialize Celery
celery = Celery('tasks')

# Initialize ResNet50 model for feature extraction
base_model = ResNet50(weights='imagenet')
model = Model(inputs=base_model.input, outputs=base_model.get_layer('avg_pool').output)

def init_extensions(app):
    """Initialize Flask extensions with the app"""
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    mail.init_app(app)
    
    # Configure Celery
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask