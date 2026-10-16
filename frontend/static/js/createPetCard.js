/**
 * PetFinder (docXaOs) - Modern Pet Card Generator
 */

function createPetCard(pet) {
    const card = document.createElement('div');
    card.className = 'pet-card';
    card.setAttribute('data-id', pet.id || '');

    // Normalize Pet Name
    const petName = pet.name || pet.petName || (typeof pet.breed === 'object' ? pet.breed?.name : pet.breed) || 'Безымянный питомец';

    // Normalize Status & Category
    let statusLabel = 'Найден';
    let statusPillClass = 'pill-found';

    if (pet.type === 'lost' || pet.category === 'lost') {
        statusLabel = 'Потерян';
        statusPillClass = 'pill-lost';
    } else if (pet.type === 'find-home' || pet.category === 'find-home' || pet.category === 'Ищут дом') {
        statusLabel = 'Ищет дом';
        statusPillClass = 'pill-home';
    }

    // Category name
    let categoryName = 'Питомец';
    const rawCat = (pet.category || pet.type || pet.characters?.petCategory || '').toString().toLowerCase();
    if (rawCat.includes('dog') || rawCat.includes('собак')) categoryName = 'Собака';
    else if (rawCat.includes('cat') || rawCat.includes('кош') || rawCat.includes('кот')) categoryName = 'Кошка';
    else if (rawCat.includes('bird') || rawCat.includes('птиц')) categoryName = 'Птица';
    else if (rawCat.includes('rodent') || rawCat.includes('грызун')) categoryName = 'Грызун';
    else if (pet.category) categoryName = pet.category;

    // Breed
    let breedName = 'Порода не указана';
    if (pet.breed) {
        breedName = typeof pet.breed === 'object' ? (pet.breed.name || 'Смешанная') : pet.breed;
    }

    // Gender
    let genderLabel = 'Пол: ?';
    if (pet.gender !== undefined) {
        if (typeof pet.gender === 'boolean') {
            genderLabel = pet.gender ? '♂ Самец' : '♀ Самка';
        } else if (typeof pet.gender === 'string') {
            genderLabel = pet.gender.toLowerCase().includes('мал') || pet.gender === 'MALE' ? '♂ Самец' : '♀ Самка';
        }
    }

    // Location
    const locationName = pet.city || pet.location || pet.district || pet.dicMunicipality?.name || 'Локация не указана';

    // Photo URL
    let photoUrl = '/static/images/noPhotoAnimals.png';
    if (pet.photos && Array.isArray(pet.photos) && pet.photos.length > 0 && pet.photos[0]) {
        photoUrl = pet.photos[0].startsWith('http') ? pet.photos[0] : `/uploads/${pet.photos[0]}`;
    } else if (pet.photo_url) {
        photoUrl = pet.photo_url;
    }

    // Similarity Score
    let similarityBadgeHtml = '';
    if (pet.similarity_score !== undefined) {
        const scorePct = Math.round(pet.similarity_score * 100);
        const scoreClass = scorePct >= 75 ? 'similarity-score-high' : 'similarity-score-med';
        similarityBadgeHtml = `
            <div class="similarity-badge">
                <span class="${scoreClass}">⚡ ${scorePct}%</span> совпадение
            </div>
        `;
    }

    // Card Template
    card.innerHTML = `
        <div class="pet-media">
            <img src="${photoUrl}" class="pet-img" alt="${petName}" loading="lazy" onerror="this.src='/static/images/noPhotoAnimals.png';" />
            <div class="badge-group">
                <span class="pill-badge ${statusPillClass}">${statusLabel}</span>
                <span class="pill-badge" style="background: rgba(15, 23, 42, 0.7); color: #fff;">${categoryName}</span>
            </div>
            ${similarityBadgeHtml}
        </div>
        
        <div class="pet-body">
            <div class="pet-header">
                <h3 class="pet-title">${petName}</h3>
                <div class="pet-location">
                    <span>📍</span>
                    <span>${locationName}</span>
                </div>
            </div>

            <div class="tag-chips">
                <span class="tag-chip">${genderLabel}</span>
                <span class="tag-chip">${breedName}</span>
                ${pet.color ? `<span class="tag-chip">🎨 ${pet.color}</span>` : ''}
                ${pet.age && pet.age !== 'Не указан' ? `<span class="tag-chip">⏳ ${pet.age}</span>` : ''}
            </div>

            <p class="pet-desc">${pet.description || pet.additional_info || pet.special_marks || 'Особые приметы не указаны. Нажмите «Подробнее» для просмотра всех характеристик.'}</p>

            <div class="card-actions">
                <button type="button" class="btn btn-secondary btn-details" style="flex: 1; padding: 7px 12px; font-size: 0.82rem;">
                    👁️ Детали
                </button>
                <button type="button" class="btn btn-primary btn-similar" style="flex: 1.2; padding: 7px 12px; font-size: 0.82rem;" title="Поиск совпадений через AI">
                    🔍 Похожие
                </button>
                ${pet.user_id && currentUserId && pet.user_id === currentUserId ? `
                    <button type="button" class="btn btn-danger btn-delete" style="padding: 7px 10px; font-size: 0.82rem;" title="Удалить карточку">
                        🗑️
                    </button>
                ` : ''}
                ${pet.match_id ? `
                    <button type="button" class="btn btn-secondary btn-archive" style="padding: 7px 10px; font-size: 0.82rem;" title="Архивировать совпадение">
                        📦
                    </button>
                ` : ''}
            </div>
        </div>
    `;

    // Event Listeners
    const btnDetails = card.querySelector('.btn-details');
    if (btnDetails) {
        btnDetails.addEventListener('click', (e) => {
            e.stopPropagation();
            if (typeof window.openPetDetailsModal === 'function') {
                window.openPetDetailsModal(pet);
            }
        });
    }

    const btnSimilar = card.querySelector('.btn-similar');
    if (btnSimilar) {
        btnSimilar.addEventListener('click', (e) => {
            e.stopPropagation();
            if (typeof window.openSimilarMatcherModal === 'function') {
                window.openSimilarMatcherModal(pet.id, pet);
            }
        });
    }

    const btnDelete = card.querySelector('.btn-delete');
    if (btnDelete) {
        btnDelete.addEventListener('click', (e) => {
            e.stopPropagation();
            if (typeof window.deletePet === 'function') {
                window.deletePet(pet.id);
            }
        });
    }

    const btnArchive = card.querySelector('.btn-archive');
    if (btnArchive) {
        btnArchive.addEventListener('click', (e) => {
            e.stopPropagation();
            if (typeof window.archiveMatch === 'function') {
                window.archiveMatch(pet.match_id);
            }
        });
    }

    // Clicking anywhere on card opens details
    card.addEventListener('click', () => {
        if (typeof window.openPetDetailsModal === 'function') {
            window.openPetDetailsModal(pet);
        }
    });

    return card;
}
