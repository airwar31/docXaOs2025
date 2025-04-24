# Check for similar pets and send notifications
try:
    similar_pets = similar_pet_detector.find_similar_pets(pet_id)
    
    if similar_pets:
        # Get details of the newly added pet
        new_pet_details = similar_pet_detector.get_pet_details(pet_id)
        
        # Get the current user's notification preferences
        cursor.execute(
            'SELECT notification_preferences, telegram_chat_id FROM users WHERE id = ?',
            (session['user_id'],)
        )
        current_user = cursor.fetchone()
        
        # Send notification to the current user about similar pets found
        if current_user and current_user['telegram_chat_id']:
            notification_prefs = json.loads(current_user['notification_preferences'] or '{}')
            if notification_prefs.get('telegram_enabled', False):
                for similar_pet in similar_pets:
                    try:
                        # Get the similar pet details
                        similar_pet_details = similar_pet_detector.get_pet_details(similar_pet['id'])
                        
                        if similar_pet_details and new_pet_details:
                            # Send notification to current user about the similar pet
                            asyncio.run(notify_similar_pet(
                                session['user_id'],
                                new_pet_details,
                                similar_pet_details,
                                similar_pet['similarity_score']
                            ))
                            print(f"Sent notification to current user {session['user_id']} about similar pet {similar_pet['id']}")
                    except Exception as e:
                        print(f"Error sending notification to current user about similar pet {similar_pet['id']}: {e}")
        
        # Send notifications to owners of similar pets
        for similar_pet in similar_pets:
            try:
                # Get the original pet details
                original_pet = similar_pet_detector.get_pet_details(similar_pet['id'])
                
                if original_pet and new_pet_details:
                    # Send notification asynchronously
                    asyncio.run(notify_similar_pet(
                        original_pet['user_id'],
                        original_pet,
                        new_pet_details,
                        similar_pet['similarity_score']
                    ))
                    print(f"Sent notification about similar pet to user {original_pet['user_id']}")
            except Exception as e:
                print(f"Error sending notification for similar pet {similar_pet['id']}: {e}")
except Exception as e:
    print(f"Error checking for similar pets: {e}")