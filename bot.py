"""
Pet Finding Application - Telegram Bot Interface

This module implements a Telegram bot for finding lost pets and matching found pets
with their owners. It provides an interactive chat interface for users to submit
search requests and receive notifications about matches.

Features:
- Interactive search request creation
- Image processing and matching
- Integration with GIS "Домашние животные" API
- Real-time notifications

Author: Your Name
License: MIT
"""

import os
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from datetime import datetime
import requests
from PIL import Image
import numpy as np
import io
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import Model
import tensorflow as tf
import aiohttp
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize ResNet50 model for image processing
base_model = ResNet50(weights='imagenet')
model = Model(inputs=base_model.input, outputs=base_model.get_layer('avg_pool').output)

# Bot initialization
API_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7237195300:AAFo-56TNpLaxOl28k49_8htoJCVQfE13sU')
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

class SearchStates(StatesGroup):
    """State machine for managing conversation flow."""
    waiting_for_search_type = State()
    waiting_for_photo = State()
    waiting_for_breed = State()
    waiting_for_category = State()
    waiting_for_gender = State()
    waiting_for_size = State()
    waiting_for_hair = State()
    waiting_for_location = State()
    waiting_for_chip = State()

# Temporary storage for user data
user_data = {}

@router.message(F.text.in_({'/start', '/help'}))
async def send_welcome(message: Message):
    """Handle /start and /help commands."""
    welcome_text = (
        "Привет! Я бот для поиска потерянных животных.\n"
        "Выберите действие:\n"
        "/search_lost - Я потерял животное\n"
        "/search_found - Я нашел животное\n"
        "/my_searches - Мои поиски\n"
        "/cancel - Отменить текущее действие"
    )
    await message.reply(welcome_text)

@router.message(F.text == '/search_lost')
async def search_lost(message: Message, state: FSMContext):
    """Start the lost pet search process."""
    user_data[message.from_user.id] = {'search_type': 'lost'}
    await state.set_state(SearchStates.waiting_for_photo)
    await message.reply("Пожалуйста, отправьте фотографию потерянного животного")

@router.message(F.text == '/search_found')
async def search_found(message: Message, state: FSMContext):
    """Start the found pet search process."""
    user_data[message.from_user.id] = {'search_type': 'found'}
    await state.set_state(SearchStates.waiting_for_photo)
    await message.reply("Пожалуйста, отправьте фотографию найденного животного")

@router.message(F.text == '/cancel')
async def cancel_handler(message: Message, state: FSMContext):
    """Cancel the current operation and reset the state."""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.reply('Действие отменено')

@router.message(SearchStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Process the uploaded pet photo and extract features."""
    try:
        # Get the largest photo version
        photo = message.photo[-1]
        file_id = photo.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Download and process the photo
        photo_bytes = await bot.download_file(file_path)
        img = Image.open(io.BytesIO(photo_bytes.read())).resize((224, 224))
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        image_vector = model.predict(img_array)
        
        # Store the image vector
        user_data[message.from_user.id]['image_vector'] = image_vector
        
        await state.set_state(SearchStates.waiting_for_breed)
        await message.reply(
            "Фото получено. Теперь укажите дополнительные параметры "
            "(можно пропустить, отправив /skip):\n"
            "Порода животного:"
        )
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        await message.reply(
            "Произошла ошибка при обработке фотографии. "
            "Пожалуйста, попробуйте еще раз или используйте другое фото."
        )
        await state.clear()

@router.message(SearchStates.waiting_for_breed)
async def process_breed(message: Message, state: FSMContext):
    """Process the pet breed information."""
    if message.text.lower() != '/skip':
        user_data[message.from_user.id]['breed'] = message.text
    
    await state.set_state(SearchStates.waiting_for_category)
    await message.reply("Категория (собака/кошка):")

@router.message(SearchStates.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    """Process the pet category information."""
    if message.text.lower() != '/skip':
        user_data[message.from_user.id]['category'] = message.text
    
    await state.set_state(SearchStates.waiting_for_gender)
    await message.reply("Пол животного:")

@router.message(SearchStates.waiting_for_gender)
async def process_gender(message: Message, state: FSMContext):
    """Process the pet gender information."""
    if message.text.lower() != '/skip':
        user_data[message.from_user.id]['gender'] = message.text
    
    await state.set_state(SearchStates.waiting_for_size)
    await message.reply("Размер животного (маленький, средний, большой):")

@router.message(SearchStates.waiting_for_size)
async def process_size(message: Message, state: FSMContext):
    """Process the pet size information."""
    if message.text.lower() != '/skip':
        user_data[message.from_user.id]['size'] = message.text
    
    await state.set_state(SearchStates.waiting_for_hair)
    await message.reply("Тип шерсти:")

@router.message(SearchStates.waiting_for_hair)
async def process_hair(message: Message, state: FSMContext):
    """Process the pet hair type information."""
    if message.text.lower() != '/skip':
        user_data[message.from_user.id]['hair'] = message.text
    
    await state.set_state(SearchStates.waiting_for_location)
    await message.reply("Населенный пункт:")

@router.message(SearchStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext):
    """Process the location information."""
    if message.text.lower() != '/skip':
        user_data[message.from_user.id]['location'] = message.text
    
    await state.set_state(SearchStates.waiting_for_chip)
    await message.reply("Номер чипа (если известен):")

@router.message(SearchStates.waiting_for_chip)
async def process_chip(message: Message, state: FSMContext):
    """Process the chip number and start the search."""
    if message.text.lower() != '/skip':
        user_data[message.from_user.id]['chip_number'] = message.text
    
    await state.clear()
    await message.reply("Идет поиск совпадений...")
    
    try:
        # Perform the search
        search_data = user_data[message.from_user.id]
        results = await search_in_gis(search_data)
        
        if results:
            for result in results:
                # Format the result message
                msg = format_result_message(result)
                
                # Try to send photo if available
                try:
                    photo_url = get_photo_url(result, search_data['search_type'])
                    if photo_url:
                        await bot.send_photo(message.from_user.id, photo_url, caption=msg)
                    else:
                        await message.reply(msg)
                except Exception as e:
                    logger.error(f"Error sending photo: {e}")
                    await message.reply(msg)
        else:
            await message.reply(
                "Совпадений не найдено. "
                "Мы уведомим вас, если появятся новые объявления."
            )
    except Exception as e:
        logger.error(f"Error in search process: {e}")
        await message.reply(
            "Произошла ошибка при поиске. "
            "Пожалуйста, попробуйте позже."
        )

async def search_in_gis(search_data):
    """
    Search for matching pets in the GIS API.
    
    Args:
        search_data: Dictionary containing search parameters
        
    Returns:
        list: List of matching animals
    """
    api_url = (
        "https://animals.admhmao.ru/pets-api/open/found"
        if search_data['search_type'] == 'lost'
        else "https://animals.admhmao.ru/pets-api/open/lost"
    )
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                response.raise_for_status()
                data = await response.json()
                animals = data.get('content', [])
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return []
    
    results = []
    for animal in animals:
        if not matches_criteria(animal, search_data):
            continue
            
        if 'image_vector' in search_data:
            if not await matches_image(animal, search_data):
                continue
                
        results.append(animal)
    
    return results

def matches_criteria(animal, search_data):
    """Check if an animal matches the search criteria."""
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
        if field in search_data and search_data[field]:
            if not compare(search_data[field], animal.get(field, '')):
                return False
    return True

async def matches_image(animal, search_data):
    """Check if an animal's image matches the search image."""
    try:
        photo_url = get_photo_url(animal, search_data['search_type'])
        if not photo_url:
            return False
            
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url) as response:
                response.raise_for_status()
                content = await response.read()
                
        img = Image.open(io.BytesIO(content)).resize((224, 224))
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        compare_vector = model.predict(img_array)
        
        similarity = cosine_similarity(search_data['image_vector'], compare_vector)
        return similarity >= 0.7
        
    except Exception as e:
        logger.error(f"Image comparison failed: {e}")
        return False

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    return np.dot(vec1, vec2.T) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def format_result_message(result):
    """Format the search result message."""
    return (
        f"Найдено совпадение:\n"
        f"ID: {result.get('id')}\n"
        f"Категория: {result.get('category')}\n"
        f"Порода: {result.get('breed')}\n"
        f"Пол: {result.get('gender')}\n"
        f"Размер: {result.get('size')}\n"
        f"Шерсть: {result.get('hair')}\n"
        f"Местоположение: {result.get('location')}\n"
        f"Дата: {result.get('placementDate')}\n"
        f"Контакты: {result.get('contacts')}"
    )

def get_photo_url(animal, search_type):
    """Get the URL of the animal's photo."""
    animal_id = animal.get('id')
    if not animal_id:
        return None
        
    base_url = "https://animals.admhmao.ru/pets-api/open"
    endpoint = "found" if search_type == 'lost' else "lost"
    return f"{base_url}/{endpoint}-photo/{animal_id}/files"

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())