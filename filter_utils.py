def filter_matches_api_animal(animal, search_query, filter_category, filter_gender, filter_size, filter_fur, filter_color, filter_district, filter_special_marks):
    """Helper function to check if an API animal matches the filter criteria"""
    # Check search query
    if search_query:
        search_fields = [
            animal.get('breed', ''),
            animal.get('location', ''),
            animal.get('district', ''),
            animal.get('municipality', ''),
            animal.get('description', ''),
            animal.get('special_marks', ''),
            animal.get('color', '')
        ]
        search_text = ' '.join([str(field) for field in search_fields]).lower()
        if search_query.lower() not in search_text:
            return False
    
    # Check category filter
    if filter_category and animal.get('type') != filter_category:
        return False
    
    # Check gender filter
    if filter_gender and animal.get('gender') != filter_gender:
        return False
    
    # Check size filter
    if filter_size and filter_size.lower() not in str(animal.get('size', '')).lower():
        return False
    
    # Check fur filter
    if filter_fur and filter_fur.lower() not in str(animal.get('fur', '')).lower():
        return False
    
    # Check color filter
    if filter_color and filter_color.lower() not in str(animal.get('color', '')).lower():
        return False
    
    # Check district filter
    if filter_district and filter_district.lower() not in str(animal.get('district', '')).lower():
        return False
    
    # Check special marks filter
    if filter_special_marks and filter_special_marks.lower() not in str(animal.get('special_marks', '')).lower():
        return False
    
    return True