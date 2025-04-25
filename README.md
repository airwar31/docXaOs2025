# Pet Finder Application

This application helps users find lost pets and match them with found pets using image recognition technology.

## Features

- User registration and authentication
- Add lost or found pets with photos
- Search for pets by various criteria
- Image-based similarity detection between pets
- Telegram bot notifications for potential matches

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd pet-finder
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure the run.py file is executable:
   ```
   chmod +x run.py
   ```

## Running the Application

To start all components of the application (API server, frontend, and Telegram bot):

```
python run.py
```

This will:
- Initialize the database if it doesn't exist
- Start the Telegram bot
- Start the web server on port 5000

You can then access the application by opening a web browser and navigating to:
```
http://localhost:5000
```

### Command Line Options

- `--api-port PORT`: Change the port for the API server (default: 5000)
- `--no-bot`: Disable the Telegram bot

Example:
```
python run.py --api-port 8000 --no-bot
```

## Project Structure

- `backend/`: Backend API and core functionality
  - `api/`: API endpoints
  - `bots/`: Telegram bot implementation
  - `core/`: Core business logic
  - `db/`: Database models and operations
  - `image_processing/`: Image processing utilities
  - `scheduler/`: Task scheduler for periodic operations
  - `utils/`: Utility functions

- `frontend/`: Frontend web interface
  - `index.html`: Main HTML file
  - `static/`: Static assets (CSS, JS, images)

- `config/`: Configuration files

- `search_images/`: Image search functionality

- `run.py`: Main entry point to run the application

## Telegram Bot

To use the Telegram bot:
1. Start a chat with the bot: [@docXaOs_bot](https://t.me/docXaOs_bot)
2. Send the `/start` command
3. Enter the email you used to register on the website

## License

[License information]