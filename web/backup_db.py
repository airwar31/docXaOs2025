import os
import shutil
from app import app

def backup_database():
    # Get the database file path
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    # Create backup path
    backup_path = db_path + '.backup'
    
    # If database exists, create a backup
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"Created backup at {backup_path}")
    else:
        print("No existing database found to backup")

if __name__ == '__main__':
    backup_database()