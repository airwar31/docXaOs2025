import os
from app import app
from migrations import init_migrations

# Get the database file path
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

# Remove the database file if it exists
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Removed existing database at {db_path}")

# Create new database with current schema using migrations
with app.app_context():
    init_migrations()
    print("Created new database with updated schema using migrations")
