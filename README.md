# Pet Finding Application

This application helps users find lost pets or report found pets through both a web interface and a Telegram bot. It uses machine learning for image similarity matching and integrates with an external pet registry API.

## Features

- Dual interface: Web application and Telegram bot
- Image-based pet matching using ResNet50
- Integration with GIS "Домашние животные" API
- Automated background matching with Celery tasks
- User authentication and search history
- Real-time notifications for new matches

## Components

### 1. Web Application (`app.py`)
- Flask-based web interface
- User registration and authentication
- Search request management
- Image processing and matching

### 2. Telegram Bot (`bot.py`)
- Interactive chat interface
- Step-by-step search process
- Photo processing and matching
- Real-time notifications

### 3. Background Tasks (`cel.py`)
- Periodic checking for new matches
- Automated notifications
- Search request updates

## Technical Stack

- **Backend Framework**: Flask
- **Database**: SQLAlchemy with SQLite (for both application data and task queue)
- **Machine Learning**: TensorFlow with ResNet50
- **Task Queue**: Celery with SQLAlchemy broker
- **Bot Framework**: aiogram
- **Image Processing**: PIL, NumPy

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
- `SECRET_KEY` for Flask
- `TELEGRAM_BOT_TOKEN` for the bot
- `DATABASE_URL` (optional, defaults to SQLite)

3. Initialize the database:
```bash
flask db upgrade
```

4. Start Celery worker:
```bash
celery -A cel worker --loglevel=info
```

5. Run the application:
```bash
python app.py
```

6. Run the Telegram bot:
```bash
c
```

## Project Structure

```
.
├── app.py              # Web application main file
├── bot.py             # Telegram bot implementation
├── cel.py             # Celery tasks
├── index.html         # HTML templates
└── static/            # Static files
    └── uploads/       # Uploaded images
```

## API Integration

The application integrates with the GIS "Домашние животные" API for:
- Lost pet listings
- Found pet listings
- Pet photos

## Image Processing

Pet matching uses ResNet50 for feature extraction:
1. Images are resized to 224x224
2. Features are extracted using ResNet50
3. Cosine similarity is used for matching
4. Threshold of 0.7 for positive matches

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

