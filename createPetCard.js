function createPetCard(pet) {
    const card = document.createElement('div');
    card.className = 'pet-card';
    
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

    const category = pet.category || 'Неизвестно';
    const type = pet.type || 'Не указан';
    const breed = pet.breed || 'Не указана';
    const gender = pet.gender || 'Не указан';
    const color = pet.color || 'Не указан';
    const district = pet.district || pet.municipality || 'Не указан';
    const location = pet.location || 'Не указано';
    const date = pet.date || 'Не указана';
    const age = pet.age !== undefined ? pet.age : 'Не указан';
    const description = pet.description || 'Описание отсутствует';
    const contactInfo = pet.contact_info || (pet.phone ? `Телефон: ${pet.phone}` : 'Контактная информация отсутствует');
    
    const size = pet.size || (pet.characters?.petSize || 'Не указан');
    const fur = pet.fur || (pet.characters?.hair || 'Не указана');
    const tail = pet.tail || (pet.characters?.tail || 'Не указан');
    const ears = pet.ears || (pet.characters?.ears || 'Не указаны');
    const weight = pet.weight || (pet.characters?.weight || 'Не указан');
    const specialMarks = pet.special_marks || (pet.characters?.specialSigns || 'Нет');
    const additionalInfo = pet.additional_info || pet.additionalInfo || '';

    const shelter = pet.shelter || 'Не указано';
    const aviary = pet.aviary || 'Не указан';

    cardContent += `
        <h3>${type} - ${breed}</h3>
        <div class="pet-details">
            <p><strong>Категория:</strong> ${category}</p>
    `;

    if (gender !== 'Не указан') {
        cardContent += `<p><strong>Пол:</strong> ${gender}</p>`;
    }
    
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
    
    if (location !== 'Не указано') {
        cardContent += `<p><strong>Место:</strong> ${location}</p>`;
    }
    
    if (date !== 'Не указана') {
        cardContent += `<p><strong>Дата:</strong> ${date}</p>`;
    }

    if (pet.coordinates) {
        const lat = pet.coordinates.lat;
        const lng = pet.coordinates.lng;
        if (lat && lng) {
            cardContent += `
                <p><strong>Координаты:</strong> ${lat}, ${lng}</p>
                <p><a href="https://maps.google.com/?q=${lat},${lng}" target="_blank">Открыть на карте</a></p>
            `;
        }
    }

    cardContent += `<p><strong>Контакты:</strong> ${contactInfo}</p>`;

    if (description && description !== 'Описание отсутствует') {
        cardContent += `<p><strong>Описание:</strong> ${description}</p>`;
    }

    if (additionalInfo) {
        cardContent += `<p><strong>Дополнительная информация:</strong> ${additionalInfo}</p>`;
    }

    cardContent += `</div>`;

    if (category === 'Ищут дом' || shelter !== 'Не указано') {
        cardContent += `
            <div class="pet-details">
                <p><strong>Приют:</strong> ${shelter}</p>
                <p><strong>Вольер:</strong> ${aviary}</p>
            </div>
        `;
    }

    if (pet.similarity_score !== undefined) {
        const score = Math.round(pet.similarity_score * 100);
        cardContent += `
            <div class="pet-details">
                <p><strong>Сходство:</strong> ${score}%</p>
            </div>
        `;
    }

    if (pet.match_status) {
        cardContent += `
            <div class="pet-details">
                <p><strong>Статус:</strong> ${pet.match_status}</p>
            </div>
        `;
    }

    if (pet.user_id === currentUserId) {
        cardContent += `
            <button onclick="deletePet(${pet.id})" style="background-color: #ff4444; margin-top: 10px;">
                Удалить
            </button>
        `;
    }

    if (pet.match_id) {
        cardContent += `
            <button onclick="archiveMatch(${pet.match_id})" style="background-color: #666; margin-top: 10px;">
                Архивировать
            </button>
        `;
    }

    card.innerHTML = cardContent;
    return card;
}