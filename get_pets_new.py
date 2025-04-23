"""
This file contains the updated get_pets function that includes both API and database animals.
Replace the existing get_pets function in server.py with this one.
"""

@app.route('/api/pets', methods=['GET'])
def get_pets():
    animal_type = request.args.get('type', 'all')
    page = request.args.get('page', 0, type=int)
    size = request.args.get('size', 8, type=int)
    
    try:
        # Get animals from external API
        api_animals = []
        if animal_type != 'db_only':  # Add a new option to fetch only from DB
            api_animals = AnimalAPI.get_all_animals(animal_type=animal_type, size=size, page=page)
            
            processed_api_animals = []
            for animal in api_animals:
                processed_animal = AnimalAPI.extract_animal_info(animal)
                processed_api_animals.append(processed_animal)
        else:
            processed_api_animals = []
        
        # Get animals from database
        db_animals = []
        if animal_type in ['all', 'lost', 'found', 'db_only']:
            db = get_db()
            cursor = db.cursor()
            
            # Build the query based on the animal type
            query = '''
                SELECT p.*, u.email as user_email, GROUP_CONCAT(pp.photo_path) as photos
                FROM pets p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN pet_photos pp ON p.id = pp.pet_id
            '''
            
            params = []
            if animal_type not in ['all', 'db_only']:
                query += ' WHERE p.type = ?'
                params.append(animal_type)
                
            query += ' GROUP BY p.id ORDER BY p.created_at DESC'
            
            cursor.execute(query, params)
            db_pets = cursor.fetchall()
            
            # Process database pets to match the format expected by the frontend
            for pet in db_pets:
                pet_dict = dict(pet)
                
                # Process photos
                if pet_dict['photos']:
                    pet_dict['photos'] = pet_dict['photos'].split(',')
                else:
                    pet_dict['photos'] = []
                
                # Add source information
                pet_dict['source'] = 'database'
                
                # Format the pet data to match the structure expected by the frontend
                formatted_pet = {
                    'id': pet_dict['id'],
                    'user_id': pet_dict['user_id'],
                    'category': 'Пропавшие' if pet_dict['type'] == 'lost' else 'Найденные',
                    'type': pet_dict['category'],  # 'dog' or 'cat'
                    'gender': pet_dict['gender'],
                    'breed': pet_dict['breed'],
                    'color': pet_dict['color'],
                    'district': pet_dict['district'],
                    'chip': pet_dict['chip'],
                    'sterilization': pet_dict['sterilization'],
                    'special_marks': pet_dict['special_marks'],
                    'size': pet_dict['size'],
                    'fur': pet_dict['fur'],
                    'location': pet_dict['location'],
                    'photos': pet_dict['photos'],
                    'contact_info': f"Email: {pet_dict['user_email']}",
                    'description': f"Порода: {pet_dict['breed']}. Пол: {pet_dict['gender']}. Размер: {pet_dict['size']}. Шерсть: {pet_dict['fur']}. Особые приметы: {pet_dict['special_marks']}",
                    'created_at': pet_dict['created_at']
                }
                
                db_animals.append(formatted_pet)
            
            db.close()
        
        # Combine animals from both sources
        all_animals = processed_api_animals + db_animals
        
        # Apply pagination to the combined list
        start_idx = page * size
        end_idx = start_idx + size
        paginated_animals = all_animals[start_idx:end_idx] if start_idx < len(all_animals) else []
        
        return jsonify(paginated_animals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500