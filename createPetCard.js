function createPetCard(pet) {
    const card = document.createElement('div');
    card.className = 'pet-card';
    
    const petName = pet.name || pet.petName || (typeof pet.breed === 'object' ? pet.breed?.name : pet.breed) || 'Неизвестное животное';
    
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
    
    let cardContent = '';
    
    if (pet.photos && pet.photos.length > 0) {
        if (typeof pet.photos[0] === 'string' && pet.photos[0].startsWith('http')) {
            cardContent += `<img src="${pet.photos[0]}" class="pet-image" alt="Фото животного" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22><rect width=%22200%22 height=%22200%22 fill=%22%23ddd%22/><text x=%22100%22 y=%22100%22 font-family=%22Arial%22 font-size=%2220%22 fill=%22%23666%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22>Фото отсутствует</text></svg>';">`;
        } else {
            const photoUrl = `/api/uploads/${pet.photos[0]}`;
            cardContent += `<img src="${photoUrl}" class="pet-image" alt="Фото животного" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22><rect width=%22200%22 height=%22200%22 fill=%22%23ddd%22/><text x=%22100%22 y=%22100%22 font-family=%22Arial%22 font-size=%2220%22 fill=%22%23666%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22>Фото отсутствует</text></svg>';">`;
        }
    } else if (pet.photo_url) {
        cardContent += `<img src="${pet.photo_url}" class="pet-image" alt="Фото животного" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22><rect width=%22200%22 height=%22200%22 fill=%22%23ddd%22/><text x=%22100%22 y=%22100%22 font-family=%22Arial%22 font-size=%2220%22 fill=%22%23666%22 text-anchor=%22middle%22 dominant-baseline=%22middle%22>Фото отсутствует</text></svg>';">`;
    } else {
        cardContent += `<div class="pet-image" style="display: flex; align-items: center; justify-content: center; background-color: #ddd;"><span>Фото отсутствует</span></div>`;
    }

    cardContent += `
        <h3>${petName}</h3>
        <div class="pet-summary">
            <p><strong>Пол:</strong> ${gender}</p>
            <p><strong>Город:</strong> ${location}</p>
        </div>
    `;

    cardContent += `<div class="pet-details hidden-details">`;

    const category = pet.api_type ? {
        'lost': 'Пропавшие',
        'found': 'Найденные',
        'find-home': 'Ищут дом'
    }[pet.api_type] || 'Неизвестно' : (pet.category || 'Неизвестно');
    
    let type = 'Не указан';
    if (pet.characters && pet.characters.petCategory) {
        type = {
            'DOG': 'Собака',
            'CAT': 'Кошка',
            'OTHER': 'Другое'
        }[pet.characters.petCategory] || pet.characters.petCategory;
    } else if (pet.type) {
        type = pet.type;
    }
    
    let breed = 'Не указана';
    if (pet.breed) {
        if (typeof pet.breed === 'object') {
            breed = pet.breed.name || 'Не указана';
        } else {
            breed = pet.breed;
        }
    }
    
    const color = pet.characters?.color || pet.color || 'Не указан';
    
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
    
    const date = pet.placementDate || pet.foundDate || pet.date || 'Не указана';
    
    const age = pet.age !== undefined ? pet.age : 'Не указан';
    
    let description = pet.description || '';
    if (!description) {
        const descParts = [];
        if (type !== 'Не указан') descParts.push(`Тип: ${type}`);
        if (breed !== 'Не указана') descParts.push(`Порода: ${breed}`);
        if (color !== 'Не указан') descParts.push(`Окрас: ${color}`);
        if (pet.additionalInfo) descParts.push(pet.additionalInfo);
        
        description = descParts.length > 0 ? descParts.join('. ') : 'Описание отсутствует';
    }
    
    const contactInfo = pet.contact_info || 
                       (pet.phone ? `Телефон: ${pet.phone}` : 
                       (pet.email ? `Email: ${pet.email}` : 
                       (pet.characters?.specialSigns ? `${pet.characters.specialSigns}` : 
                       (pet.additionalInfo ? `${pet.additionalInfo}` : 'Контактная информация отсутствует'))));
    
    const size = pet.size || (pet.characters?.petSize || 'Не указан');
    const fur = pet.fur || (pet.characters?.hair || 'Не указана');
    const tail = pet.tail || (pet.characters?.tail || 'Не указан');
    const ears = pet.ears || (pet.characters?.ears || 'Не указаны');
    const weight = pet.weight || (pet.characters?.weight || 'Не указан');
    
    const specialMarks = pet.special_marks || (pet.characters?.specialSigns || 'Нет');
    
    const additionalInfo = pet.additional_info || pet.additionalInfo || '';

    const shelter = pet.shelter || 'Не указано';
    const aviary = pet.aviary || 'Не указан';

    cardContent += `<p><strong>Категория:</strong> ${category}</p>`;
    cardContent += `<p><strong>Тип:</strong> ${type}</p>`;
    cardContent += `<p><strong>Порода:</strong> ${breed}</p>`;
    
    if (age !== 'Не указан') {
        cardContent += `<p><strong>Возраст:</strong> ${age}</p>`;
    }
    
    if (color !== 'Не указан') {
        cardContent += `<p><strong>Окрас:</strong> ${color}</p>`;
    }
    
    if (size !== 'Не указан') {
        cardContent += `<p><strong>Размер:</strong> ${size}</p>`;
    }
    
    if (fur !== 'Не указана') {
        cardContent += `<p><strong>Шерсть:</strong> ${fur}</p>`;
    }
    
    if (tail !== 'Не указан') {
        cardContent += `<p><strong>Хвост:</strong> ${tail}</p>`;
    }
    
    if (ears !== 'Не указаны') {
        cardContent += `<p><strong>Уши:</strong> ${ears}</p>`;
    }
    
    if (weight !== 'Не указан') {
        cardContent += `<p><strong>Вес:</strong> ${weight}</p>`;
    }
    
    if (specialMarks !== 'Нет') {
        cardContent += `<p><strong>Особые приметы:</strong> ${specialMarks}</p>`;
    }

    if (district !== 'Не указан') {
        cardContent += `<p><strong>Район:</strong> ${district}</p>`;
    }
    
    if (date !== 'Не указана') {
        cardContent += `<p><strong>Дата пропажи:</strong> ${date}</p>`;
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

    cardContent += `<p><strong>Контакты для связи:</strong> ${contactInfo}</p>`;

    if (description && description !== 'Описание отсутствует') {
        cardContent += `<p><strong>Описание:</strong> ${description}</p>`;
    }

    if (additionalInfo) {
        cardContent += `<p><strong>Дополнительная информация:</strong> ${additionalInfo}</p>`;
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