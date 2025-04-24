let currentPage = 0;
let currentTab = 'lost';
let currentUserId = null;
const pageSize = 8;
let searchQuery = '';
let activeFilters = {
    category: '',
    gender: '',
    size: '',
    fur: ''
};

window.addEventListener('load', async function() {
    try {
        const response = await fetch('/api/check-auth');
        const data = await response.json();
        
        if (data.authenticated) {
            document.getElementById('authSection').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            currentUserId = data.user_id;
            loadPets();
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
});

async function deletePet(petId) {
    if (!confirm('Вы уверены, что хотите удалить этого питомца?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/pets/${petId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Питомец успешно удален');
            loadPets();
        } else {
            alert(data.error || 'Ошибка при удалении питомца');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при удалении питомца');
    }
}

function showAddPetForm() {
    document.getElementById('formOverlay').classList.remove('hidden');
    document.getElementById('addPetForm').classList.remove('hidden');
    document.getElementById('petsGrid').classList.add('hidden');
    document.querySelector('.pagination').classList.add('hidden');
}

function hideAddPetForm() {
    document.getElementById('formOverlay').classList.add('hidden');
    document.getElementById('addPetForm').classList.add('hidden');
    document.getElementById('petsGrid').classList.remove('hidden');
    document.querySelector('.pagination').classList.remove('hidden');
    document.getElementById('petForm').reset();
}

document.getElementById('formOverlay').addEventListener('click', function(e) {
    if (e.target === this) {
        hideAddPetForm();
    }
});

document.getElementById('petForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    
    try {
        const response = await fetch('/api/pets', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Питомец успешно добавлен');
            hideAddPetForm();
            loadPets();
        } else {
            alert(data.error || 'Ошибка при добавлении питомца');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при добавлении питомца');
    }
});

function showForm(formId) {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.add('hidden');
    document.getElementById(formId).classList.remove('hidden');
    
    const tabs = document.querySelectorAll('#authSection .tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
}

function switchTab(tab) {
    currentTab = tab;
    currentPage = 0;
    const tabs = document.querySelectorAll('#mainApp .tab');
    tabs.forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    loadPets();
}

function previousPage() {
    if (currentPage > 0) {
        currentPage--;
        loadPets();
    }
}

function nextPage() {
    currentPage++;
    loadPets();
}

// Search and Filter Functions
function toggleFilters() {
    const filtersContainer = document.getElementById('filtersContainer');
    filtersContainer.classList.toggle('hidden');
}

function performSearch() {
    searchQuery = document.getElementById('searchInput').value.trim();
    currentPage = 0;
    loadPets();
}

function applyFilters() {
    activeFilters = {
        category: document.getElementById('filterCategory').value,
        gender: document.getElementById('filterGender').value,
        size: document.getElementById('filterSize').value,
        fur: document.getElementById('filterFur').value
    };
    currentPage = 0;
    loadPets();
}

function resetFilters() {
    document.getElementById('filterCategory').value = '';
    document.getElementById('filterGender').value = '';
    document.getElementById('filterSize').value = '';
    document.getElementById('filterFur').value = '';
    document.getElementById('searchInput').value = '';
    
    searchQuery = '';
    activeFilters = {
        category: '',
        gender: '',
        size: '',
        fur: ''
    };
    
    currentPage = 0;
    loadPets();
}

async function loadPets() {
    try {
        let endpoint = '/api/pets';
        let animalType = 'all';
        
        if (currentTab === 'lost') {
            animalType = 'lost';
        } else if (currentTab === 'found') {
            animalType = 'found';
        } else if (currentTab === 'matches') {
            endpoint = '/api/matches';
        }
        
        let data;
        if (endpoint === '/api/matches') {
            const response = await fetch(`${endpoint}?page=${currentPage}&size=${pageSize}`);
            if (!response.ok) {
                throw new Error('Failed to load matches');
            }
            data = await response.json();
        } else {

            let url = `${endpoint}?type=${animalType}&page=${currentPage}&size=${pageSize}`;
            
            if (searchQuery) {
                url += `&search=${encodeURIComponent(searchQuery)}`;
            }
            
            if (activeFilters.category) {
                url += `&category=${encodeURIComponent(activeFilters.category)}`;
            }
            if (activeFilters.gender) {
                url += `&gender=${encodeURIComponent(activeFilters.gender)}`;
            }
            if (activeFilters.size) {
                url += `&size_filter=${encodeURIComponent(activeFilters.size)}`;
            }
            if (activeFilters.fur) {
                url += `&fur=${encodeURIComponent(activeFilters.fur)}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to load pets');
            }
            data = await response.json();
        }

        const petsGrid = document.getElementById('petsGrid');
        petsGrid.innerHTML = '';

        if (!data || data.length === 0) {
            petsGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 20px;">Животные не найдены</div>';
        } else {
            data.forEach(pet => {
                const card = createPetCard(pet);
                petsGrid.appendChild(card);
            });
        }

        document.getElementById('prevButton').disabled = currentPage === 0;
        document.getElementById('nextButton').disabled = data.length < pageSize;
        document.getElementById('pageInfo').textContent = `Страница ${currentPage + 1}`;
    } catch (error) {
        console.error('Error loading pets:', error);
        const petsGrid = document.getElementById('petsGrid');
        petsGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 20px; color: red;">Произошла ошибка при загрузке данных о животных</div>';
    }
}

function showNotificationPrefs() {
    document.getElementById('notificationPrefsForm').classList.remove('hidden');
    document.getElementById('petsGrid').classList.add('hidden');
    document.querySelector('.pagination').classList.add('hidden');
    
    loadNotificationPreferences();
}

function hideNotificationPrefs() {
    document.getElementById('notificationPrefsForm').classList.add('hidden');
    document.getElementById('petsGrid').classList.remove('hidden');
    document.querySelector('.pagination').classList.remove('hidden');
}

async function loadNotificationPreferences() {
    try {
        const response = await fetch('/api/notification-preferences');
        const prefs = await response.json();
        
        document.getElementById('telegramEnabled').checked = prefs.telegram_enabled || false;
        document.getElementById('notificationFrequency').value = prefs.frequency || '1';
        document.getElementById('minSimilarity').value = (prefs.min_similarity || 70) * 100;
        document.getElementById('similarityValue').textContent = `${document.getElementById('minSimilarity').value}%`;
    } catch (error) {
        console.error('Error loading preferences:', error);
    }
}

document.getElementById('minSimilarity').addEventListener('input', function(e) {
    document.getElementById('similarityValue').textContent = `${e.target.value}%`;
});

document.getElementById('notificationForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const prefs = {
        telegram_enabled: document.getElementById('telegramEnabled').checked,
        frequency: parseInt(document.getElementById('notificationFrequency').value),
        min_similarity: parseInt(document.getElementById('minSimilarity').value) / 100
    };
    
    try {
        const response = await fetch('/api/notification-preferences', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(prefs)
        });
        
        if (response.ok) {
            alert('Настройки уведомлений сохранены');
            hideNotificationPrefs();
        } else {
            const data = await response.json();
            alert(data.error || 'Ошибка при сохранении настроек');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при сохранении настроек');
    }
});

async function archiveMatch(matchId) {
    try {
        const response = await fetch(`/api/matches/${matchId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_archived: true })
        });
        
        if (response.ok) {
            loadPets();
        } else {
            const data = await response.json();
            alert(data.error || 'Ошибка при архивации совпадения');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при архивации совпадения');
    }
}
async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        
        if (response.ok) {
            currentUserId = null;
            
            document.getElementById('authSection').classList.remove('hidden');
            document.getElementById('mainApp').classList.add('hidden');
            
            document.getElementById('loginForm').reset();
            document.getElementById('registerForm').reset();
        } else {
            const data = await response.json();
            alert(data.error || 'Ошибка при выходе из системы');
        }
    } catch (error) {
        console.error('Error during logout:', error);
        alert('Произошла ошибка при выходе из системы');
    }
}

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('authSection').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            
            const authResponse = await fetch('/api/check-auth');
            const authData = await authResponse.json();
            currentUserId = authData.user_id;
            
            loadPets();
        } else {
            alert(data.error || 'Ошибка при входе в систему');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при входе в систему');
    }
});

document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Регистрация успешна! Теперь вы можете войти в систему.');
            showForm('loginForm');
            document.getElementById('loginEmail').value = email;
        } else {
            alert(data.error || 'Ошибка при регистрации');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при регистрации');
    }
});

document.getElementById('searchInput').addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
});