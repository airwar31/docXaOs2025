/**
 * PetFinder (docXaOs) - Modern Single-Page Application Controller
 */

// Global Application State
let currentPage = 0;
let currentTab = 'lost';
let currentUserId = null;
let currentUserEmail = null;
const pageSize = 8;
let searchQuery = '';
let activeFilters = {
    category: '',
    gender: '',
    size: '',
    fur: '',
    city: '',
    district: ''
};

// ===================================================================
// Initialization & Theme
// ===================================================================

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    checkAuth();
    setupEventListeners();
});

function initTheme() {
    const savedTheme = localStorage.getItem('petfinder_theme') || 'light';
    setTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(nextTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('petfinder_theme', theme);
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

function setupEventListeners() {
    // Search on enter key
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }

    // Forms
    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.addEventListener('submit', handleLogin);

    const registerForm = document.getElementById('registerForm');
    if (registerForm) registerForm.addEventListener('submit', handleRegister);

    const petForm = document.getElementById('petForm');
    if (petForm) petForm.addEventListener('submit', handleAddPet);

    const telegramSettingsForm = document.getElementById('telegramSettingsForm');
    if (telegramSettingsForm) telegramSettingsForm.addEventListener('submit', handleSaveTelegramSettings);
}

// ===================================================================
// Toast Notifications
// ===================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️'
    };

    toast.innerHTML = `
        <span style="font-size: 1.1rem;">${icons[type] || 'ℹ️'}</span>
        <span style="flex: 1;">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3800);
}

// ===================================================================
// Authentication Flow
// ===================================================================

async function checkAuth() {
    try {
        const res = await fetch('/api/check-auth');
        const data = await res.json();

        if (data.authenticated) {
            currentUserId = data.user_id;
            currentUserEmail = data.email || 'Пользователь';
            onUserAuthenticated();
        } else {
            onUserUnauthenticated();
        }
    } catch (err) {
        console.warn('Auth check error:', err);
        onUserUnauthenticated();
    }
}

function onUserAuthenticated() {
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');

    const profileNav = document.getElementById('userProfileNav');
    if (profileNav) {
        profileNav.classList.remove('hidden');
        document.getElementById('userEmailBadge').textContent = currentUserEmail;
    }

    loadPets();
}

function onUserUnauthenticated() {
    document.getElementById('authSection').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');

    const profileNav = document.getElementById('userProfileNav');
    if (profileNav) profileNav.classList.add('hidden');
}

function switchAuthTab(mode) {
    const tabLogin = document.getElementById('tabAuthLogin');
    const tabRegister = document.getElementById('tabAuthRegister');
    const formLogin = document.getElementById('loginForm');
    const formRegister = document.getElementById('registerForm');

    if (mode === 'login') {
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
        formLogin.classList.remove('hidden');
        formRegister.classList.add('hidden');
    } else {
        tabLogin.classList.remove('active');
        tabRegister.classList.add('active');
        formLogin.classList.add('hidden');
        formRegister.classList.remove('hidden');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (res.ok) {
            currentUserId = data.user?.id;
            currentUserEmail = data.user?.email || email;
            showToast('Успешный вход в систему!', 'success');
            onUserAuthenticated();
        } else {
            showToast(data.error || 'Ошибка входа в систему', 'error');
        }
    } catch (err) {
        showToast('Сервер временно недоступен', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (res.ok) {
            showToast('Аккаунт создан! Пожалуйста, выполните вход.', 'success');
            switchAuthTab('login');
            document.getElementById('loginEmail').value = email;
            document.getElementById('loginPassword').value = '';
        } else {
            showToast(data.error || 'Ошибка регистрации', 'error');
        }
    } catch (err) {
        showToast('Произошла ошибка при регистрации', 'error');
    }
}

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        currentUserId = null;
        currentUserEmail = null;
        showToast('Вы вышли из системы', 'info');
        onUserUnauthenticated();
    } catch (err) {
        console.error('Logout error:', err);
    }
}

// ===================================================================
// Pet Grid & Tab Switching
// ===================================================================

function switchCategoryTab(tab) {
    currentTab = tab;
    currentPage = 0;

    const tabs = document.querySelectorAll('.nav-tabs .nav-tab');
    tabs.forEach(t => {
        if (t.getAttribute('data-tab') === tab) {
            t.classList.add('active');
        } else {
            t.classList.remove('active');
        }
    });

    loadPets();
}

async function loadPets() {
    const grid = document.getElementById('petsGrid');
    if (!grid) return;

    // Show Skeleton / Loading State
    grid.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon" style="animation: spin 1s infinite linear;">🔄</div>
            <div class="empty-title">Загрузка карточек...</div>
            <p class="empty-subtitle">Синхронизация данных с реестром ХМАО и базой поиска</p>
        </div>
    `;

    try {
        let url = '';

        if (currentTab === 'matches') {
            url = `/api/matches?page=${currentPage}&size=${pageSize}`;
        } else {
            const animalType = currentTab === 'my_pets' ? 'all' : currentTab;
            url = `/api/pets?type=${animalType}&page=${currentPage}&size=${pageSize}`;

            if (currentTab === 'my_pets' && currentUserId) {
                url += `&user_id=${currentUserId}`;
            }

            if (searchQuery) {
                url += `&search=${encodeURIComponent(searchQuery)}`;
            }

            // Append active filters
            if (activeFilters.category) url += `&category=${encodeURIComponent(activeFilters.category)}`;
            if (activeFilters.gender) url += `&gender=${encodeURIComponent(activeFilters.gender)}`;
            if (activeFilters.size) url += `&size_filter=${encodeURIComponent(activeFilters.size)}`;
            if (activeFilters.fur) url += `&fur=${encodeURIComponent(activeFilters.fur)}`;
            if (activeFilters.city) url += `&city=${encodeURIComponent(activeFilters.city)}`;
            if (activeFilters.district) url += `&district=${encodeURIComponent(activeFilters.district)}`;
        }

        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch pets');

        const data = await res.json();
        renderPetsGrid(data);

        // Update Pagination Controls
        const prevBtn = document.getElementById('prevButton');
        const nextBtn = document.getElementById('nextButton');
        const pageInfo = document.getElementById('pageInfo');

        if (prevBtn) prevBtn.disabled = currentPage === 0;
        if (nextBtn) nextBtn.disabled = !data || data.length < pageSize;
        if (pageInfo) pageInfo.textContent = `Страница ${currentPage + 1}`;

    } catch (err) {
        console.error('Error loading pets:', err);
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <div class="empty-title">Не удалось загрузить данные</div>
                <p class="empty-subtitle">Проверьте подключение к серверу или попробуйте обновить страницу.</p>
                <button type="button" class="btn btn-primary" style="margin-top: 14px;" onclick="loadPets()">Повторить</button>
            </div>
        `;
    }
}

function renderPetsGrid(pets) {
    const grid = document.getElementById('petsGrid');
    grid.innerHTML = '';

    if (!pets || pets.length === 0) {
        let msg = 'В данной категории пока нет объявлений';
        if (currentTab === 'matches') msg = 'Автоматических совпадений пока не найдено. Наш ИИ проверяет реестр каждые 15 минут.';
        else if (currentTab === 'my_pets') msg = 'У вас пока нет размещенных объявлений. Нажмите «Подать объявление», чтобы добавить питомца!';

        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🐾</div>
                <div class="empty-title">Питомцы не найдены</div>
                <p class="empty-subtitle">${msg}</p>
            </div>
        `;
        return;
    }

    pets.forEach(pet => {
        const card = createPetCard(pet);
        grid.appendChild(card);
    });
}

function previousPage() {
    if (currentPage > 0) {
        currentPage--;
        loadPets();
        window.scrollTo({ top: 300, behavior: 'smooth' });
    }
}

function nextPage() {
    currentPage++;
    loadPets();
    window.scrollTo({ top: 300, behavior: 'smooth' });
}

// ===================================================================
// Search & Extended Filter Logic
// ===================================================================

function toggleFiltersDrawer() {
    const drawer = document.getElementById('filtersDrawer');
    if (drawer) {
        drawer.classList.toggle('hidden');
    }
}

function performSearch() {
    searchQuery = (document.getElementById('searchInput')?.value || '').trim();
    currentPage = 0;
    loadPets();
}

function applyFilters() {
    activeFilters = {
        category: document.getElementById('filterCategory')?.value || '',
        gender: document.getElementById('filterGender')?.value || '',
        size: document.getElementById('filterSize')?.value || '',
        fur: document.getElementById('filterFur')?.value || '',
        city: document.getElementById('filterCity')?.value.trim() || '',
        district: document.getElementById('filterDistrict')?.value.trim() || ''
    };

    // Update active filter badge counter
    const activeCount = Object.values(activeFilters).filter(v => v !== '').length;
    const badge = document.getElementById('activeFilterBadge');
    if (badge) {
        if (activeCount > 0) {
            badge.textContent = activeCount;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }

    currentPage = 0;
    loadPets();
}

function resetFilters() {
    ['filterCategory', 'filterGender', 'filterSize', 'filterFur'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    ['filterCity', 'filterDistrict', 'searchInput'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    searchQuery = '';
    activeFilters = {
        category: '',
        gender: '',
        size: '',
        fur: '',
        city: '',
        district: ''
    };

    const badge = document.getElementById('activeFilterBadge');
    if (badge) badge.classList.add('hidden');

    currentPage = 0;
    loadPets();
    showToast('Фильтры сброшены', 'info');
}

// ===================================================================
// Modals Management
// ===================================================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

function handleBackdropClick(event, modalId) {
    if (event.target.id === modalId) {
        closeModal(modalId);
    }
}

// 1. Details Modal
window.openPetDetailsModal = function(pet) {
    const modal = document.getElementById('petDetailsModal');
    if (!modal) return;

    const petName = pet.name || pet.petName || (typeof pet.breed === 'object' ? pet.breed?.name : pet.breed) || 'Безымянный питомец';
    document.getElementById('modalPetName').textContent = petName;

    // Photo
    let photoUrl = '/static/images/noPhotoAnimals.png';
    if (pet.photos && pet.photos.length > 0 && pet.photos[0]) {
        photoUrl = pet.photos[0].startsWith('http') ? pet.photos[0] : `/uploads/${pet.photos[0]}`;
    } else if (pet.photo_url) {
        photoUrl = pet.photo_url;
    }
    document.getElementById('modalPetPhoto').src = photoUrl;

    // Traits Grid
    const traitGrid = document.getElementById('modalTraitGrid');
    traitGrid.innerHTML = `
        <div class="tag-chip"><strong>Порода:</strong> ${typeof pet.breed === 'object' ? pet.breed?.name : (pet.breed || 'Не указана')}</div>
        <div class="tag-chip"><strong>Пол:</strong> ${pet.gender ? (pet.gender === true || pet.gender === 'MALE' ? 'Мальчик' : 'Девочка') : 'Не указан'}</div>
        <div class="tag-chip"><strong>Категория:</strong> ${pet.category || pet.type || 'Не указана'}</div>
        <div class="tag-chip"><strong>Окрас:</strong> ${pet.color || pet.characters?.color || 'Не указан'}</div>
        <div class="tag-chip"><strong>Размер:</strong> ${pet.size || 'Средний'}</div>
        <div class="tag-chip"><strong>Шерсть:</strong> ${pet.fur || 'Обычная'}</div>
        <div class="tag-chip"><strong>Город:</strong> ${pet.city || pet.location || 'Не указан'}</div>
        <div class="tag-chip"><strong>Чип:</strong> ${pet.chip_number || pet.chip || 'Отсутствует'}</div>
    `;

    // Description
    document.getElementById('modalPetDesc').textContent = pet.description || pet.additional_info || pet.special_marks || 'Особые приметы отсутствуют.';

    // Contact
    const contactText = pet.phone ? `Телефон: ${pet.phone} ${pet.user_email ? `| Email: ${pet.user_email}` : ''}` :
                       (pet.user_email ? `Email: ${pet.user_email}` : 'Связь через службу отлова / реестр ХМАО');
    document.getElementById('modalPetContact').textContent = contactText;

    // Map link
    const mapLink = document.getElementById('modalMapLink');
    if (pet.coordinates || (pet.dicMunicipality?.coordinate)) {
        const lat = pet.coordinates?.lat || pet.dicMunicipality?.coordinate?.coordY;
        const lng = pet.coordinates?.lng || pet.dicMunicipality?.coordinate?.coordX;
        if (lat && lng) {
            mapLink.href = `https://maps.google.com/?q=${lat},${lng}`;
            mapLink.classList.remove('hidden');
        } else {
            mapLink.classList.add('hidden');
        }
    } else {
        mapLink.classList.add('hidden');
    }

    // Similar trigger button
    const similarBtn = document.getElementById('modalFindSimilarBtn');
    if (similarBtn) {
        similarBtn.onclick = () => {
            closeModal('petDetailsModal');
            openSimilarMatcherModal(pet.id, pet);
        };
    }

    openModal('petDetailsModal');
};

// 2. Similar Matcher Modal
window.openSimilarMatcherModal = async function(petId, petInfo) {
    openModal('similarPetsModal');
    const container = document.getElementById('similarResultsContainer');
    if (!container) return;

    container.innerHTML = `
        <div style="text-align: center; padding: 40px 20px;">
            <div style="font-size: 2.5rem; animation: spin 1s infinite linear; margin-bottom: 12px;">🧠</div>
            <h4 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 6px;">Сканирование дескрипторов SIFT & параметров...</h4>
            <p style="font-size: 0.88rem; color: var(--text-muted);">ИИ сопоставляет визуальные ориентиры и текстовые атрибуты по базе</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/similar/${petId}`);
        const matches = await res.json();

        if (!matches || matches.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <div class="empty-title">Прямых совпадений не обнаружено</div>
                    <p class="empty-subtitle">Мы продолжаем отслеживать поступления новых животных в фоновом режиме через планировщик.</p>
                </div>
            `;
            return;
        }

        let html = '<div style="display: flex; flex-direction: column; gap: 14px;">';

        matches.forEach(m => {
            const scorePct = Math.round((m.similarity_score || 0.7) * 100);
            let photo = '/static/images/noPhotoAnimals.png';
            if (m.photos && m.photos.length > 0) {
                photo = m.photos[0].startsWith('http') ? m.photos[0] : `/uploads/${m.photos[0]}`;
            } else if (m.photo_url) photo = m.photo_url;

            html += `
                <div style="display: flex; gap: 16px; background: var(--bg-surface-elevated); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 16px; align-items: center;">
                    <img src="${photo}" style="width: 90px; height: 90px; border-radius: var(--radius-md); object-fit: cover;" onerror="this.src='/static/images/noPhotoAnimals.png';" />
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <h4 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary);">${m.name || m.breed || 'Питомец'}</h4>
                            <span class="brand-badge" style="background: var(--success-light); color: var(--success); font-size: 0.82rem;">⚡ ${scorePct}% сходство</span>
                        </div>
                        <div style="font-size: 0.84rem; color: var(--text-secondary); margin-bottom: 8px;">
                            <span>Порода: <strong>${m.breed || 'Не указана'}</strong></span> • 
                            <span>Город: <strong>${m.city || m.location || 'ХМАО'}</strong></span> • 
                            <span>Пол: <strong>${m.gender || 'Не указан'}</strong></span>
                        </div>
                        <div style="height: 6px; width: 100%; background: var(--bg-muted); border-radius: 3px; overflow: hidden;">
                            <div style="height: 100%; width: ${scorePct}%; background: linear-gradient(90deg, #6366f1, #10b981);"></div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

    } catch (err) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <div class="empty-title">Ошибка при поиске</div>
                <p class="empty-subtitle">Не удалось выполнить сопоставление. Попробуйте позже.</p>
            </div>
        `;
    }
};

// 3. Add Pet Flow
function openAddPetModal() {
    if (!currentUserId) {
        showToast('Пожалуйста, войдите в систему для подачи объявления', 'info');
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return;
    }
    openModal('addPetModal');
}

function handlePhotoSelect(event) {
    const previewGrid = document.getElementById('photosPreviewGrid');
    if (!previewGrid) return;
    previewGrid.innerHTML = '';

    const files = event.target.files;
    if (files) {
        Array.from(files).forEach(file => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = document.createElement('img');
                img.className = 'preview-thumb';
                img.src = e.target.result;
                previewGrid.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
    }
}

async function handleAddPet(e) {
    e.preventDefault();
    const btn = document.getElementById('submitPetBtn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Публикация анкеты...';
    }

    const formData = new FormData(e.target);

    try {
        const res = await fetch('/api/pets', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (res.ok) {
            showToast('Объявление успешно опубликовано!', 'success');
            closeModal('addPetModal');
            e.target.reset();
            document.getElementById('photosPreviewGrid').innerHTML = '';
            loadPets();
        } else {
            showToast(data.error || 'Ошибка при сохранении объявления', 'error');
        }
    } catch (err) {
        showToast('Сервер недоступен, повторите попытку позже', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Опубликовать объявление';
        }
    }
}

// 4. Telegram Connect Modal
function openTelegramModal() {
    openModal('telegramModal');
    loadTelegramPreferences();
}

async function loadTelegramPreferences() {
    try {
        const res = await fetch('/api/notification-preferences');
        if (!res.ok) return;
        const data = await res.json();

        const tgSwitch = document.getElementById('tgEnabledSwitch');
        if (tgSwitch) tgSwitch.checked = data.telegram_enabled || false;

        const tgRange = document.getElementById('tgSimilarityRange');
        if (tgRange) {
            const pct = Math.round((data.min_similarity || 0.7) * 100);
            tgRange.value = pct;
            document.getElementById('tgSimilarityVal').textContent = pct + '%';
        }
    } catch (err) {
        console.warn('Could not load preferences:', err);
    }
}

async function handleSaveTelegramSettings(e) {
    e.preventDefault();

    const payload = {
        telegram_enabled: document.getElementById('tgEnabledSwitch')?.checked || false,
        min_similarity: parseInt(document.getElementById('tgSimilarityRange')?.value || 70) / 100
    };

    try {
        const res = await fetch('/api/notification-preferences', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast('Настройки уведомлений Telegram сохранены!', 'success');
            closeModal('telegramModal');
        } else {
            showToast('Не удалось сохранить настройки', 'error');
        }
    } catch (err) {
        showToast('Ошибка при связи с сервером', 'error');
    }
}

// 5. Actions: Delete & Archive
window.deletePet = async function(petId) {
    if (!confirm('Вы уверены, что хотите удалить эту анкету?')) return;

    try {
        const res = await fetch(`/api/pets/${petId}`, { method: 'DELETE' });
        const data = await res.json();

        if (res.ok) {
            showToast('Анкета успешно удалена', 'success');
            loadPets();
        } else {
            showToast(data.error || 'Ошибка удаления', 'error');
        }
    } catch (err) {
        showToast('Ошибка при удалении питомца', 'error');
    }
};

window.archiveMatch = async function(matchId) {
    try {
        const res = await fetch(`/api/matches/${matchId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_archived: true })
        });

        if (res.ok) {
            showToast('Совпадение отправлено в архив', 'info');
            loadPets();
        }
    } catch (err) {
        showToast('Ошибка при архивации', 'error');
    }
};
