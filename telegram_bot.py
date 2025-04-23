try:
    from aiogram import Bot, Dispatcher
    from aiogram import types
    from aiogram.filters import Command
    from aiogram import F
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.enums.parse_mode import ParseMode
except ImportError as e:
    print(f"Error importing aiogram components: {e}")
    raise

import sqlite3
import os
import json
import asyncio
from datetime import datetime
API_TOKEN = ('7237195300:AAFo-56TNpLaxOl28k49_8htoJCVQfE13sU')
try:
    # In aiogram 3.x, parse_mode can be passed directly to Bot constructor
    bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    print("Bot and dispatcher initialized successfully")
except Exception as e:
    print(f"Error initializing bot or dispatcher: {e}")
    raise

DB_NAME = 'petfinder.db'

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
                "Теперь вы будете получать уведомления о возможных совпадениях."
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
    """
    Notify a user when a similar pet to their pet is posted.
    
    Args:
        user_id: ID of the user to notify
        original_pet: Dictionary with information about the user's pet
        new_pet: Dictionary with information about the newly posted pet
        similarity_score: Similarity score between the two pets (0.0 to 1.0)
    
    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            'SELECT telegram_chat_id, notification_preferences FROM users WHERE id = ?',
            (user_id,)
        )
        user = cursor.fetchone()
        
        if user and user['telegram_chat_id']:
            # Check if user has enabled telegram notifications
            prefs = json.loads(user['notification_preferences'] or '{}')
            if not prefs.get('telegram_enabled', False):
                return False
                
            # Format pet types for display
            original_type = "Пропавший" if original_pet.get('type') == 'lost' else "Найденный"
            new_type = "Пропавший" if new_pet.get('type') == 'lost' else "Найденный"
            
            # Create message
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
        # Start polling
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







