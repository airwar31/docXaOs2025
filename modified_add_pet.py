@app.route('/api/pets', methods=['POST'])
@login_required
def add_pet():
    if 'photos' not in request.files:
        return jsonify({'error': 'No photos provided'}), 400
        
    photos = request.files.getlist('photos')
    if not photos or photos[0].filename == '':
        return jsonify({'error': 'No photos selected'}), 400

    data = request.form.to_dict()
    
    if 'type' not in data or data['type'] not in ['lost', 'found']:
        return jsonify({'error': 'Invalid type. Must be "lost" or "found"'}), 400
    if 'category' not in data or data['category'] not in ['dog', 'cat']:
        return jsonify({'error': 'Invalid category. Must be "dog" or "cat"'}), 400
        
    data.setdefault('breed', 'Не указан')
    data.setdefault('gender', 'Не указан')
    data.setdefault('color', 'Не указан')
    data.setdefault('district', 'Не указан')
    data.setdefault('chip', 'Нет данных')
    data.setdefault('sterilization', 'Нет данных')
    data.setdefault('special_marks', 'Нет')
    data.setdefault('size', 'Не указан')
    data.setdefault('fur', 'Не указан')
    data.setdefault('location', 'Не указан')

    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO pets (
                user_id, type, breed, category, gender, color, district,
                chip, sterilization, special_marks, size, fur, location
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data['type'],
            data['breed'],
            data['category'],
            data['gender'],
            data['color'],
            data['district'],
            data['chip'],
            data['sterilization'],
            data['special_marks'],
            data['size'],
            data['fur'],
            data['location']
        ))
        
        pet_id = cursor.lastrowid
        
        for photo in photos:
            if photo and allowed_file(photo.filename):
                filename = secure_filename(f"{pet_id}_{photo.filename}")
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                
                cursor.execute('''
                    INSERT INTO pet_photos (pet_id, photo_path)
                    VALUES (?, ?)
                ''', (pet_id, filename))
                photo_id = cursor.lastrowid
                
                features = image_processor.extract_features(photo_path)
                if features:
                    cursor.execute('''
                        INSERT INTO image_features (photo_id, features)
                        VALUES (?, ?)
                    ''', (photo_id, json.dumps(features)))
        
        search_params = {
            'breed': data['breed'],
            'category': data['category'],
            'gender': data['gender'],
            'color': data['color'],
            'district': data['district'],
            'chip': data['chip'],
            'sterilization': data['sterilization'],
            'special_marks': data['special_marks'],
            'size': data['size'],
            'fur': data['fur'],
            'location': data['location']
        }
        
        cursor.execute('''
            INSERT INTO searches (pet_id, search_params, last_check_time)
            VALUES (?, ?, datetime('now'))
        ''', (pet_id, json.dumps(search_params)))
        
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
        
        db.commit()
        return jsonify({
            'message': 'Pet added successfully',
            'pet_id': pet_id
        }), 201
        
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()