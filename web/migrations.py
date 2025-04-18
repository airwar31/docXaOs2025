from flask_migrate import Migrate
from flask import Flask
from db.models import db
import os

def init_migrations(app):
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Set the application instance for Flask CLI
    app.config['FLASK_APP'] = 'web.app'
    
    # Get absolute paths
    app_root = os.path.abspath(os.path.dirname(__file__))
    migrations_dir = os.path.join(app_root, '..', 'migrations')
    
    # Create migrations directory if it doesn't exist
    if not os.path.exists(migrations_dir):
        print("Migrations directory already exists at:", migrations_dir)
    
    print("Flask-Migrate initialized successfully")

if __name__ == '__main__':
    from app import app
    init_migrations(app)



