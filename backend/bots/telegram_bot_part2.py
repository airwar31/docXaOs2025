from backend.bots.telegram_bot import dp, bot, get_db, Command, F, types, InlineKeyboardBuilder, SimilarPetDetector, DB_NAME, UPLOAD_FOLDER
from backend.bots.telegram_bot import translate_size, translate_fur, translate_gender, translate_category, translate_tail, translate_ears
import json
import sqlite3
import asyncio

@dp.message(Command("my_pets"))
async def cmd_my_pets(message: types.Message):
    """Show the user's pets with buttons to find similar pets"""
    try:
        db = get_db()
        cursor = db.cursor()
        
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
            
        for pet in pets:
            pet_dict = dict(pet)
            
            if pet_dict['size']:
                pet_dict['size'] = translate_size(pet_dict['size'])
            
            if pet_dict['fur']:
                pet_dict['fur'] = translate_fur(pet_dict['fur'])
            
            if pet_dict['gender']:
                pet_dict['gender'] = translate_gender(pet_dict['gender'])
            
            if pet_dict['tail']:
                pet_dict['tail'] = translate_tail(pet_dict['tail'])
            
            if pet_dict['ears']:
                pet_dict['ears'] = translate_ears(pet_dict['ears'])
            
            builder = InlineKeyboardBuilder()
            builder.button(
                text="Найти похожих животных", 
                callback_data=f"find_similar:{pet_dict['id']}"
            )
            
            pet_type = "Пропавший" if pet_dict['type'] == 'lost' else "Найденный"
            pet_category = translate_category(pet_dict['category']) if pet_dict['category'] else "Неизвестно"
            
            message_text = (
                f"<b>{pet_type} {pet_category}</b>\n"
                f"Порода: {pet_dict['breed']}\n"
                f"Пол: {pet_dict['gender']}\n"
                f"Размер: {pet_dict['size']}\n"
                f"Шерсть: {pet_dict['fur']}\n"
                f"Место: {pet_dict['location']}\n"
                f"Особые приметы: {pet_dict.get('special_marks', 'Не указаны')}"
            )
            
            await message.answer(message_text, reply_markup=builder.as_markup())
            
    except sqlite3.Error as e:
        await message.reply("Произошла ошибка при обработке запроса. Попробуйте позже.")
        print(f"Database error in my_pets: {e}")
    finally:
        db.close()

@dp.callback_query(F.data.startswith("find_similar:"))
async def process_find_similar(callback_query: types.CallbackQuery):
    try:
        pet_id = int(callback_query.data.split(":")[1])
        
        await callback_query.answer()
        
        await callback_query.message.answer("Ищем похожих животных...")
        
        similar_pet_detector = SimilarPetDetector(DB_NAME, UPLOAD_FOLDER)
        
        similar_pets = similar_pet_detector.find_similar_pets(pet_id)
        
        if not similar_pets:
            await callback_query.message.answer(
                "К сожалению, похожих животных не найдено."
            )
            return
            
        original_pet = similar_pet_detector.get_pet_details(pet_id)
        
        if not original_pet:
            await callback_query.message.answer(
                "Произошла ошибка при получении информации о вашем питомце."
            )
            return
            
        await callback_query.message.answer(
            f"Найдено {len(similar_pets)} похожих животных:"
        )
        
        for similar_pet in similar_pets:
            pet_details = similar_pet
            
            if not pet_details:
                continue
                
            if pet_details['size']:
                pet_details['size'] = translate_size(pet_details['size'])
            
            if pet_details['fur']:
                pet_details['fur'] = translate_fur(pet_details['fur'])
            
            if pet_details['gender']:
                pet_details['gender'] = translate_gender(pet_details['gender'])
            
            if pet_details['tail']:
                pet_details['tail'] = translate_tail(pet_details['tail'])
            
            if pet_details['ears']:
                pet_details['ears'] = translate_ears(pet_details['ears'])
                
            pet_type = "Пропавший" if pet_details['type'] == 'lost' else "Найденный"
            pet_category = translate_category(pet_details['category']) if pet_details['category'] else "Неизвестно"
            
            combined_percent = int(similar_pet['similarity_score'] * 100)
            
            text_similarity = similar_pet.get('text_similarity', None)
            image_similarity = similar_pet.get('image_similarity', None)
            
            source = "внешнего API" if similar_pet.get('from_api', False) else "базы данных"
            
            similarity_text = f"Общее сходство: {combined_percent}%"
            if text_similarity is not None and image_similarity is not None:
                text_percent = int(text_similarity * 100)
                image_percent = int(image_similarity * 100)
                similarity_text += f"\nСходство по описанию: {text_percent}%\nСходство по фото: {image_percent}%"
            
            message_text = (
                f"<b>{pet_type} {pet_category}</b> (из {source})\n"
                f"Порода: {pet_details['breed']}\n"
                f"Пол: {pet_details['gender']}\n"
                f"Размер: {pet_details['size']}\n"
                f"Шерсть: {pet_details['fur']}\n"
                f"Место: {pet_details['location']}\n"
                f"Особые приметы: {pet_details.get('special_marks', 'Не указаны')}\n"
                f"Контакт: {pet_details['user_email']}\n\n"
                f"<b>{similarity_text}</b>"
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
            text_similarity = match_data.get('text_similarity', None)
            image_similarity = match_data.get('image_similarity', None)
            
            combined_percent = int(match_data.get('similarity_score', 0) * 100)
            
            source = "внешнего API" if match_data.get('from_api', False) else "базы данных"
            
            similarity_details = f"Общее сходство: {combined_percent}%"
            if text_similarity is not None and image_similarity is not None:
                text_percent = int(text_similarity * 100)
                image_percent = int(image_similarity * 100)
                similarity_details += f"\nСходство по описанию: {text_percent}%\nСходство по фото: {image_percent}%"
            
            message = (
                "🔍 Найдено возможное совпадение!\n\n"
                f"Порода: {match_data.get('breed', 'Не указана')}\n"
                f"Категория: {match_data.get('category', 'Не указана')}\n"
                f"Место: {match_data.get('location', 'Не указано')}\n"
                f"Источник: {source}\n"
                f"{similarity_details}\n\n"
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
            
            text_similarity = new_pet.get('text_similarity', 0.0)
            image_similarity = new_pet.get('image_similarity', 0.0)
            
            combined_percent = int(similarity_score * 100)
            text_percent = int(text_similarity * 100) if text_similarity else None
            image_percent = int(image_similarity * 100) if image_similarity else None
            
            similarity_details = f"Общее сходство: {combined_percent}%"
            if text_percent is not None and image_percent is not None:
                similarity_details += f"\nСходство по описанию: {text_percent}%\nСходство по фото: {image_percent}%"
            
            source = "внешнего API" if new_pet.get('from_api', False) else "базы данных"
            
            message = (
                "🔍 Найден похожий питомец!\n\n"
                f"На сайте появился питомец, похожий на вашего {original_pet.get('category', 'питомца')}.\n\n"
                f"Ваш питомец ({original_type}):\n"
                f"Порода: {original_pet.get('breed', 'Не указана')}\n"
                f"Категория: {original_pet.get('category', 'Не указана')}\n"
                f"Место: {original_pet.get('location', 'Не указано')}\n\n"
                f"Похожий питомец ({new_type}) из {source}:\n"
                f"Порода: {new_pet.get('breed', 'Не указана')}\n"
                f"Категория: {new_pet.get('category', 'Не указана')}\n"
                f"Место: {new_pet.get('location', 'Не указано')}\n"
                f"Контакт: {new_pet.get('user_email', 'Не указан')}\n\n"
                f"{similarity_details}\n\n"
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











