# Manual Test Instructions for Category Validation Fix

## Overview
These instructions will help you manually test the fix for the category validation issue in the pet finder application. The issue was that the server was expecting lowercase 'dog' or 'cat' values for the category field, but the HTML form was sending uppercase 'DOG' or 'CAT' values.

## Prerequisites
1. The pet finder application is running
2. You have access to the application through a web browser
3. You have a user account or can register a new one

## Test Steps

### Test Case 1: Adding a pet with category "dog"
1. Log in to the application
2. Click the "Добавить питомца" (Add Pet) button
3. Fill out the form with the following values:
   - Тип объявления (Announcement Type): "Потерянный питомец" (Lost Pet)
   - Категория (Category): "Собака" (Dog)
   - Порода (Breed): Any value
   - Fill in other required fields
   - Upload a photo
4. Click the "Добавить" (Add) button
5. **Expected Result**: The pet should be added successfully without any validation errors

### Test Case 2: Adding a pet with category "cat"
1. Log in to the application
2. Click the "Добавить питомца" (Add Pet) button
3. Fill out the form with the following values:
   - Тип объявления (Announcement Type): "Потерянный питомец" (Lost Pet)
   - Категория (Category): "Кошка" (Cat)
   - Порода (Breed): Any value
   - Fill in other required fields
   - Upload a photo
4. Click the "Добавить" (Add) button
5. **Expected Result**: The pet should be added successfully without any validation errors

### Test Case 3: Filtering pets by category
1. Log in to the application
2. Click the "Фильтры" (Filters) button
3. Select "Собака" (Dog) from the category dropdown
4. Click "Применить фильтры" (Apply Filters)
5. **Expected Result**: Only dogs should be displayed in the results

6. Reset filters
7. Select "Кошка" (Cat) from the category dropdown
8. Click "Применить фильтры" (Apply Filters)
9. **Expected Result**: Only cats should be displayed in the results

## Verification
If all test cases pass, the fix for the category validation issue has been successfully implemented. The application should now:
1. Accept lowercase 'dog' and 'cat' values from the form
2. Properly validate these values on the server
3. Display the correct category information in the UI
4. Filter pets correctly by category

## Troubleshooting
If any test fails, check the following:
1. Verify that the changes to pet-finder.html were applied correctly
2. Verify that the changes to createPetCard.js were applied correctly
3. Check the browser console for any JavaScript errors
4. Check the server logs for any backend errors