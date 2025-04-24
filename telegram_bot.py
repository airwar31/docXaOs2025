try:
    from aiogram import Bot, Dispatcher
    from aiogram import types
    from aiogram.filters import Command
    from aiogram import F
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.enums.parse_mode import ParseMode
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.client.default import DefaultBotProperties
except ImportError as e:
    print(f"Error importing aiogram components: {e}")
    raise

import sqlite3
import os
import json
import asyncio
from datetime import datetime
from similar_pet_detector import SimilarPetDetector

API_TOKEN = ('7237195300:AAFo-56TNpLaxOl28k49_8htoJCVQfE13sU')
try:

    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    print("Bot and dispatcher initialized successfully")
except Exception as e:
    print(f"Error initializing bot or dispatcher: {e}")
    raise

DB_NAME = 'petfinder.db'
UPLOAD_FOLDER = 'uploads'

class UserStates(StatesGroup):
    awaiting_email = State()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.reply(
        "Добро пожаловать в сервис поиска животных!\n"
        "Для подписки на уведомления, пожалуйста, укажите ваш email, "
        "который вы использовали при регистрации на сайте."
    )
    await state.set_state(UserStates.awaiting_email)

@dp.message(UserStates.awaiting_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text.strip().lower()
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute(
                'UPDATE users SET telegram_chat_id = ? WHERE email = ?',
                (str(message.chat.id), email)
            )
            
            cursor.execute(
                '''UPDATE users SET notification_preferences = json_set(
                    COALESCE(notification_preferences, '{}'),
                    '$.telegram_enabled', true
                ) WHERE email = ?''',
                (email,)
            )
            
            db.commit()
            await message.reply(
                "Отлично! Вы успешно подписались на уведомления.\n"
                "Теперь вы будете получать уведомления о возможных совпадениях.\n\n"
                "Используйте команду /my_pets чтобы увидеть ваших питомцев и найти похожих."
            )
        else:
            await message.reply(
                "Извините, но этот email не зарегистрирован в системе.\n"
                "Пожалуйста, сначала зарегистрируйтесь на сайте."
            )
    except sqlite3.Error as e:
        await message.reply("Произошла ошибка при обработке запроса. Попробуйте позже.")
        print(f"Database error: {e}")
    finally:
        db.close()
        await state.clear()

@dp.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: types.Message):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            '''UPDATE users SET 
                notification_preferences = json_set(
                    COALESCE(notification_preferences, '{}'),
                    '$.telegram_enabled', false
                )
            WHERE telegram_chat_id = ?''',
            (str(message.chat.id),)
        )
        
        if cursor.rowcount > 0:
            db.commit()
            await message.reply("Вы успешно отписались от уведомлений.")
        else:
            await message.reply("Вы не были подписаны на уведомления.")
            
    except sqlite3.Error as e:
        await message.reply("Произошла ошибка при обработке запроса. Попробуйте позже.")
        print(f"Database error: {e}")
    finally:
        db.close()

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            '''SELECT email, notification_preferences 
            FROM users WHERE telegram_chat_id = ?''',
            (str(message.chat.id),)
        )
        user = cursor.fetchone()
        
        if user:
            prefs = json.loads(user['notification_preferences'] or '{}')
            status = "включены" if prefs.get('telegram_enabled', False) else "отключены"
            await message.reply(
                f"Email: {user['email']}\n"
                f"Уведомления: {status}"
            )
        else:
            await message.reply(
                "Вы не привязали свой Telegram к аккаунту.\n"
                "Используйте команду /start для привязки."
            )
            
    except sqlite3.Error as e:
        await message.reply("Произошла ошибка при обработке запроса. Попробуйте позже.")
        print(f"Database error: {e}")
    finally:
        db.close()

@dp.message(Command("my_pets"))
async def cmd_my_pets(message: types.Message):
    """Show the user's pets with buttons to find similar pets"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # First, get the user ID from the telegram_chat_id
        cursor.execute(
            'SELECT id FROM users WHERE telegram_chat_id = ?',
            (str(message.chat.id),)
        )
        user = cursor.fetchone()
        
        if not user:
            await message.reply(
                "Вы не привязали свой Telegram к аккаунту.\n"
                "Используйте команду /start для привязки."
            )
            db.close()
            return
            
        user_id = user['id']
        
        cursor.execute('''
            SELECT p.*, GROUP_CONCAT(pp.photo_path) as photos
            FROM pets p
            LEFT JOIN pet_photos pp ON p.id = pp.pet_id
            WHERE p.user_id = ?
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''', (user_id,))
        
        pets = cursor.fetchall()
        
        if not pets:
            await message.reply(
                "У вас пока нет добавленных питомцев.\n"
                "Добавьте питомца на сайте, чтобы использовать эту функцию."
            )
            db.close()
            return
            
        # Send a message for each pet with a button to find similar pets
        for pet in pets:
            pet_dict = dict(pet)
            
            # Create a keyboard with a button to find similar pets
            builder = InlineKeyboardBuilder()
            builder.button(
                text="Найти похожих животных", 
                callback_data=f"find_similar:{pet_dict['id']}"
            )
            
            # Format pet type and category
            pet_type = "Пропавший" if pet_dict['type'] == 'lost' else "Найденный"
            pet_category = "Собака" if pet_dict['category'] == 'dog' else "Кошка"
            
            # Create the message text
            message_text = (
                f"<b>{pet_type} {pet_category}</b>\n"
                f"Порода: {pet_dict['breed']}\n"
                f"Пол: {pet_dict['gender']}\n"
                f"Размер: {pet_dict['size']}\n"
                f"Шерсть: {pet_dict['fur']}\n"
                f"Место: {pet_dict['location']}\n"
                f"Особые приметы: {pet_dict['special_marks']}"
            )
            
            # Send the message with the button
            await message.answer(message_text, reply_markup=builder.as_markup())
            
    except sqlite3.Error as e:
        await message.reply("Произошла ошибка при обработке запроса. Попробуйте позже.")
        print(f"Database error in my_pets: {e}")
    finally:
        db.close()

@dp.callback_query(F.data.startswith("find_similar:"))
async def process_find_similar(callback_query: types.CallbackQuery):
    """Handle the button click to find similar pets"""
    try:
        # Extract the pet ID from the callback data
        pet_id = int(callback_query.data.split(":")[1])
        
        # Answer the callback query to stop the loading animation
        await callback_query.answer()
        
        # Send a message that we're searching
        await callback_query.message.answer("Ищем похожих животных...")
        
        # Initialize the SimilarPetDetector
        similar_pet_detector = SimilarPetDetector(DB_NAME, UPLOAD_FOLDER)
        
        # Find similar pets
        similar_pets = similar_pet_detector.find_similar_pets(pet_id)
        
        if not similar_pets:
            await callback_query.message.answer(
                "К сожалению, похожих животных не найдено."
            )
            return
            
        # Get the original pet details
        original_pet = similar_pet_detector.get_pet_details(pet_id)
        
        if not original_pet:
            await callback_query.message.answer(
                "Произошла ошибка при получении информации о вашем питомце."
            )
            return
            
        # Send a message with information about each similar pet
        await callback_query.message.answer(
            f"Найдено {len(similar_pets)} похожих животных:"
        )
        
        for similar_pet in similar_pets:
            # Get detailed information about the similar pet
            pet_details = similar_pet_detector.get_pet_details(similar_pet['id'])
            
            if not pet_details:
                continue
                
            # Format pet type and category
            pet_type = "Пропавший" if pet_details['type'] == 'lost' else "Найденный"
            pet_category = "Собака" if pet_details['category'] == 'dog' else "Кошка"
            
            # Calculate similarity percentage
            similarity_percent = int(similar_pet['similarity_score'] * 100)
            
            # Create the message text
            message_text = (
                f"<b>{pet_type} {pet_category}</b> (Сходство: {similarity_percent}%)\n"
                f"Порода: {pet_details['breed']}\n"
                f"Пол: {pet_details['gender']}\n"
                f"Размер: {pet_details['size']}\n"
                f"Шерсть: {pet_details['fur']}\n"
                f"Место: {pet_details['location']}\n"
                f"Особые приметы: {pet_details['special_marks']}\n"
                f"Контакт: {pet_details['user_email']}"
            )
            
            await callback_query.message.answer(message_text)
            
    except Exception as e:
        await callback_query.message.answer(
            "Произошла ошибка при поиске похожих животных. Попробуйте позже."
        )
        print(f"Error finding similar pets: {e}")

async def send_notification(chat_id: str, message_text: str):
    try:
        await bot.send_message(chat_id, message_text)
        return True
    except Exception as e:
        print(f"Error sending notification to {chat_id}: {e}")
        return False

async def notify_match(user_id: int, match_data: dict):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT telegram_chat_id FROM users WHERE id = ?',
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user and user['telegram_chat_id']:
            message = (
                "🔍 Найдено возможное совпадение!\n\n"
                f"Порода: {match_data.get('breed', 'Не указана')}\n"
                f"Категория: {match_data.get('category', 'Не указана')}\n"
                f"Место: {match_data.get('location', 'Не указано')}\n"
                f"Сходство: {int(match_data.get('similarity_score', 0) * 100)}%\n\n"
                "Для просмотра деталей перейдите на сайт."
            )
            
            await send_notification(user['telegram_chat_id'], message)
            return True
    except sqlite3.Error as e:
        print(f"Database error in notify_match: {e}")
    except Exception as e:
        print(f"Error in notify_match: {e}")
    finally:
        db.close()
    return False

async def notify_no_match(user_id: int, pet_data: dict):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT telegram_chat_id FROM users WHERE id = ?',
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user and user['telegram_chat_id']:
            message = (
                "🔍 Подтверждение поиска\n\n"
                "К сожалению, мы не нашли совпадений для вашего питомца:\n"
                f"Тип: {pet_data.get('type', 'Не указан')}\n"
                f"Порода: {pet_data.get('breed', 'Не указана')}\n"
                f"Категория: {pet_data.get('category', 'Не указана')}\n\n"
                "Мы будем продолжать поиск и уведомим вас, если найдем совпадение."
            )
            
            await send_notification(user['telegram_chat_id'], message)
            return True
    except sqlite3.Error as e:
        print(f"Database error in notify_no_match: {e}")
    except Exception as e:
        print(f"Error in notify_no_match: {e}")
    finally:
        db.close()
    return False

async def notify_similar_pet(user_id: int, original_pet: dict, new_pet: dict, similarity_score: float):

    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT telegram_chat_id, notification_preferences FROM users WHERE id = ?',
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user and user['telegram_chat_id']:

            prefs = json.loads(user['notification_preferences'] or '{}')
            if not prefs.get('telegram_enabled', False):
                return False
                
            original_type = "Пропавший" if original_pet.get('type') == 'lost' else "Найденный"
            new_type = "Пропавший" if new_pet.get('type') == 'lost' else "Найденный"
            
            message = (
                "🔍 Найден похожий питомец!\n\n"
                f"На сайте появился питомец, похожий на вашего {original_pet.get('category', 'питомца')}.\n\n"
                f"Ваш питомец ({original_type}):\n"
                f"Порода: {original_pet.get('breed', 'Не указана')}\n"
                f"Категория: {original_pet.get('category', 'Не указана')}\n"
                f"Место: {original_pet.get('location', 'Не указано')}\n\n"
                f"Похожий питомец ({new_type}):\n"
                f"Порода: {new_pet.get('breed', 'Не указана')}\n"
                f"Категория: {new_pet.get('category', 'Не указана')}\n"
                f"Место: {new_pet.get('location', 'Не указано')}\n"
                f"Контакт: {new_pet.get('user_email', 'Не указан')}\n\n"
                f"Сходство: {int(similarity_score * 100)}%\n\n"
                "Для просмотра деталей перейдите на сайт."
            )
            
            await send_notification(user['telegram_chat_id'], message)
            return True
    except sqlite3.Error as e:
        print(f"Database error in notify_similar_pet: {e}")
    except Exception as e:
        print(f"Error in notify_similar_pet: {e}")
    finally:
        if 'db' in locals():
            db.close()
    return False

async def start_bot():
    try:
        print("Starting Telegram bot...")

        await dp.start_polling(bot, skip_updates=True)
        return True
    except Exception as e:
        print(f"Error starting bot: {e}")
        return False

async def stop_bot():
    try:
        print("Stopping Telegram bot...")
        await bot.session.close()
        return True
    except Exception as e:
        print(f"Error stopping bot: {e}")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Unexpected error: {e}")









