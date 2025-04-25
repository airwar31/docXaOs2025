function createPetCard(pet) {
    const card = document.createElement('div');
    card.className = 'pet-card';
    
    const petName = pet.name || pet.petName || (typeof pet.breed === 'object' ? pet.breed?.name : pet.breed) || 'Неизвестное животное';
    
    // Define all variables before using them in the template
    // Always set status to "Найденный" as per requirements
    let status = 'Найденный';
    
    // Get animal category (dog/cat/etc) and translate it
    let category = 'Не указан';
    if (pet.category) {
        // Ensure category is translated
        if (pet.category.toLowerCase() === 'dog') {
            category = 'Собака';
        } else if (pet.category.toLowerCase() === 'cat') {
            category = 'Кошка';
        } else {
            category = pet.category;
        }
    } else if (pet.characters && pet.characters.petCategory) {
        category = {
            'DOG': 'Собака',
            'CAT': 'Кошка',
            'OTHER': 'Другое'
        }[pet.characters.petCategory] || pet.characters.petCategory;
    } else if (pet.type) {
        if (pet.type.toLowerCase() === 'dog' || pet.type.toLowerCase() === 'собака') {
            category = 'Собака';
        } else if (pet.type.toLowerCase() === 'cat' || pet.type.toLowerCase() === 'кошка') {
            category = 'Кошка';
        } else {
            category = pet.type;
        }
    }
    
    let breed = 'Не указана';
    if (pet.breed) {
        if (typeof pet.breed === 'object') {
            breed = pet.breed.name || 'Не указана';
        } else {
            breed = pet.breed;
        }
    }
    
    let gender = 'Не указан';
    if (pet.characters && pet.characters.gender !== undefined) {
        gender = pet.characters.gender ? 'Мальчик' : 'Девочка';
    } else if (pet.gender !== undefined) {
        if (typeof pet.gender === 'boolean') {
            gender = pet.gender ? 'Мальчик' : 'Девочка';
        } else {
            gender = pet.gender;
        }
    }
    
    const location = pet.location || 
                    (pet.dicMunicipality?.name) || 
                    pet.district || 
                    pet.municipality || 
                    'Не указано';
    
    let district = 'Не указан';
    if (pet.dicMunicipality) {
        if (pet.dicMunicipality.showOkrug && pet.dicMunicipality.showOkrug.name) {
            district = pet.dicMunicipality.showOkrug.name;
        } else {
            district = pet.dicMunicipality.name || 'Не указан';
        }
    } else if (pet.district) {
        district = pet.district;
    }
    
    let city = pet.city || 'Не указан';
    const color = pet.characters?.color || pet.color || 'Не указан';
    const date = pet.placementDate || pet.foundDate || pet.date || 'Не указана';
    const age = pet.age !== undefined ? pet.age : 'Не указан';
    const size = pet.size || (pet.characters?.petSize || 'Не указан');
    const fur = pet.fur || (pet.characters?.hair || 'Не указана');
    const tail = pet.tail || (pet.characters?.tail || 'Не указан');
    const ears = pet.ears || (pet.characters?.ears || 'Не указаны');
    const weight = pet.weight || (pet.characters?.weight || 'Не указан');
    const specialMarks = pet.special_marks || (pet.characters?.specialSigns || 'Нет');
    const additionalInfo = pet.additional_info || pet.additionalInfo || '';
    const shelter = pet.shelter || 'Не указано';
    const aviary = pet.aviary || 'Не указан';
    
    let description = pet.description || '';
    if (!description) {
        const descParts = [];
        if (category !== 'Не указан') descParts.push(`Категория: ${category}`);
        if (breed !== 'Не указана') descParts.push(`Порода: ${breed}`);
        if (color !== 'Не указан') descParts.push(`Окрас: ${color}`);
        if (pet.additionalInfo) descParts.push(pet.additionalInfo);
        
        description = descParts.length > 0 ? descParts.join('. ') : 'Описание отсутствует';
    }
    
    const contactInfo = pet.contact_info || 
                       (pet.phone ? `Телефон: ${pet.phone}${pet.user_email ? `, Email: ${pet.user_email}` : ''}` : 
                       (pet.user_email ? `Email: ${pet.user_email}` : 
                       (pet.email ? `Email: ${pet.email}` : 
                       (pet.characters?.specialSigns ? `${pet.characters.specialSigns}` : 
                       (pet.additionalInfo ? `${pet.additionalInfo}` : 'Контактная информация отсутствует')))));
    
    let cardContent = '';
    
    // Check if pet has photos and they are valid
    if (pet.photos && Array.isArray(pet.photos) && pet.photos.length > 0 && pet.photos[0]) {
        if (typeof pet.photos[0] === 'string' && pet.photos[0].startsWith('http')) {
            cardContent += `<img src="${pet.photos[0]}" class="pet-image" alt="Фото животного" onerror="this.src='/static/images/noPhotoAnimals.png';">`;
        } else {
            const photoUrl = `/uploads/${pet.photos[0]}`;
            cardContent += `<img src="${photoUrl}" class="pet-image" alt="Фото животного" onerror="this.src='/static/images/noPhotoAnimals.png';">`;
        }
    } else if (pet.photo_url && typeof pet.photo_url === 'string') {
        cardContent += `<img src="${pet.photo_url}" class="pet-image" alt="Фото животного" onerror="this.src='/static/images/noPhotoAnimals.png';">`;
    } else {
        // No valid photos found, display default image
        cardContent += `<img src="/static/images/noPhotoAnimals.png" class="pet-image" alt="Фото животного">`;
    }

    cardContent += `
        <h3>${petName}</h3>
        <div class="pet-summary">
            <p><strong>Пол:</strong> ${gender}</p>
            <p><strong>Город:</strong> ${city}</p>
            <p><strong>Статус:</strong> ${status}</p>
            <p><strong>Категория:</strong> ${category}</p>
            <p><strong>Порода:</strong> ${breed}</p>
            <p><strong>Возраст:</strong> ${age}</p>
            <p><strong>Окрас:</strong> ${color}</p>
            <p><strong>Размер:</strong> ${size}</p>
            <p><strong>Шерсть:</strong> ${fur}</p>
            <p><strong>Хвост:</strong> ${tail}</p>
            <p><strong>Уши:</strong> ${ears}</p>
            <p><strong>Особые приметы:</strong> ${specialMarks}</p>
            <p><strong>Район:</strong> ${district}</p>
            <p><strong>Дата пропажи:</strong> ${pet.lost_date || date}</p>
            <p><strong>Контакты для связи:</strong> ${contactInfo}</p>
            <p><strong>Дополнительная информация:</strong> ${additionalInfo || 'Нет дополнительной информации'}</p>
        </div>
    `;

    cardContent += `<div class="pet-details hidden-details">`;

    // Only show weight in the details section since it's not in the main summary
    if (weight !== 'Не указан') {
        cardContent += `<p><strong>Вес:</strong> ${weight}</p>`;
    }

    if (location !== 'Не указано') {
        cardContent += `<p><strong>Место пропажи/находки:</strong> ${location}</p>`;
    }

    let coordinates = pet.coordinates;
    if (!coordinates && pet.dicMunicipality && pet.dicMunicipality.coordinate) {
        coordinates = {
            lat: pet.dicMunicipality.coordinate.coordY,
            lng: pet.dicMunicipality.coordinate.coordX
        };
    }
    
    if (coordinates) {
        const lat = coordinates.lat;
        const lng = coordinates.lng;
        if (lat && lng) {
            cardContent += `
                <p><strong>Координаты:</strong> ${lat}, ${lng}</p>
                <p><a href="https://maps.google.com/?q=${lat},${lng}" target="_blank">Открыть на карте</a></p>
            `;
        }
    }

    cardContent += `</div>`;

    if (category === 'Ищут дом' || shelter !== 'Не указано') {
        cardContent += `
            <div class="pet-shelter hidden-details">
                <p><strong>Приют:</strong> ${shelter}</p>
                <p><strong>Вольер:</strong> ${aviary}</p>
            </div>
        `;
    }

    if (pet.similarity_score !== undefined) {
        const score = Math.round(pet.similarity_score * 100);
        cardContent += `
            <div class="pet-similarity">
                <p><strong>Сходство:</strong> ${score}%</p>
            </div>
        `;
    }

    if (pet.match_status) {
        cardContent += `
            <div class="pet-match-status">
                <p><strong>Статус:</strong> ${pet.match_status}</p>
            </div>
        `;
    }

    if (pet.user_id === currentUserId) {
        cardContent += `
            <button onclick="event.stopPropagation(); deletePet(${pet.id})" style="background-color: #ff4444; margin-top: 10px;">
                Удалить
            </button>
        `;
    }

    if (pet.match_id) {
        cardContent += `
            <button onclick="event.stopPropagation(); archiveMatch(${pet.match_id})" style="background-color: #666; margin-top: 10px;">
                Архивировать
            </button>
        `;
    }

    card.innerHTML = cardContent;
    
    card.addEventListener('click', function() {
        const detailsElements = this.querySelectorAll('.pet-details, .pet-shelter');
        detailsElements.forEach(element => {
            element.classList.toggle('hidden-details');
        });
    });
    
    return card;
}










