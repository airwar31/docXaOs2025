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
from config.settings import active_config
from backend.core.similar_pet_detector import SimilarPetDetector
from backend.utils.translate_utils import translate_size, translate_fur, translate_gender, translate_category, translate_tail, translate_ears

API_TOKEN = active_config.TELEGRAM_API_TOKEN
try:
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    print("Bot and dispatcher initialized successfully")
except Exception as e:
    print(f"Error initializing bot or dispatcher: {e}")
    raise

DB_NAME = active_config.DB_NAME
UPLOAD_FOLDER = active_config.UPLOAD_FOLDER

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


