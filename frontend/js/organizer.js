// Проверка роли пользователя при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    const user = getUser();
    if (!user || user.role !== 'organizer') {
        window.location.href = './index.html';
        return;
    }

    // Инициализация модального окна
    const createEventModal = new bootstrap.Modal(document.getElementById('createEventModal'));
    
    // Обработчик кнопки создания мероприятия
    document.getElementById('createEventBtn').addEventListener('click', () => {
        createEventModal.show();
    });

    // Обработчик переключения платного/бесплатного мероприятия
    document.getElementById('isPaidEvent').addEventListener('change', function() {
        const ticketPriceGroup = document.getElementById('ticketPriceGroup');
        ticketPriceGroup.style.display = this.checked ? 'block' : 'none';
        if (!this.checked) {
            document.getElementById('ticketPrice').value = '';
        }
    });

    // Обработчик сохранения мероприятия
    document.getElementById('saveEventBtn').addEventListener('click', async function() {
        const form = document.getElementById('createEventForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        try {
            showLoading();
            const formData = new FormData();
            formData.append('title', document.getElementById('eventTitle').value);
            formData.append('description', document.getElementById('eventDescription').value);
            formData.append('full_description', document.getElementById('eventFullDescription').value);
            formData.append('date', document.getElementById('eventDate').value);
            formData.append('location', document.getElementById('eventLocation').value);
            formData.append('max_participants', document.getElementById('maxParticipants').value);
            
            const isPaidEvent = document.getElementById('isPaidEvent').checked;
            formData.append('is_paid', isPaidEvent);
            if (isPaidEvent) {
                formData.append('ticket_price', document.getElementById('ticketPrice').value);
            }

            const imageFile = document.getElementById('eventImage').files[0];
            if (imageFile) {
                formData.append('image', imageFile);
            }

            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.EVENTS.CREATE), {
                method: 'POST',
                headers: getAuthHeaders(),
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка при создании мероприятия');
            }

            const event = await response.json();
            showSuccess('Мероприятие успешно создано');
            createEventModal.hide();
            form.reset();
            loadEvents(); // Перезагружаем список мероприятий
        } catch (error) {
            console.error('Ошибка при создании мероприятия:', error);
            showError(error.message);
        } finally {
            hideLoading();
        }
    });

    // Загружаем список мероприятий
    await loadEvents();
});

// Функция загрузки мероприятий организатора
async function loadEvents() {
    try {
        showLoading();
        const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.EVENTS.LIST), {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Не удалось загрузить мероприятия');
        }

        const events = await response.json();
        displayEvents(events);
    } catch (error) {
        console.error('Ошибка при загрузке мероприятий:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// Функция отображения списка мероприятий
function displayEvents(events) {
    const eventsList = document.getElementById('eventsList');
    if (!eventsList) return;

    if (events.length === 0) {
        eventsList.innerHTML = '<div class="col-12"><p>У вас пока нет созданных мероприятий</p></div>';
        return;
    }

    eventsList.innerHTML = events.map(event => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100">
                ${event.image_url ? `<img src="${event.image_url}" class="card-img-top" alt="${event.title}">` : ''}
                <div class="card-body">
                    <h5 class="card-title">${event.title}</h5>
                    <p class="card-text">${event.description}</p>
                    <p class="card-text">
                        <small class="text-muted">
                            Дата: ${new Date(event.date).toLocaleString()}<br>
                            Место: ${event.location}<br>
                            Участников: ${event.current_participants}/${event.max_participants}
                        </small>
                    </p>
                    <div class="d-flex justify-content-between">
                        <button class="btn btn-primary" onclick="editEvent(${event.id})">Редактировать</button>
                        <button class="btn btn-danger" onclick="deleteEvent(${event.id})">Удалить</button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Функция редактирования мероприятия
async function editEvent(eventId) {
    // TODO: Реализовать редактирование мероприятия
    console.log('Редактирование мероприятия:', eventId);
}

// Функция удаления мероприятия
async function deleteEvent(eventId) {
    if (!confirm('Вы уверены, что хотите удалить это мероприятие?')) {
        return;
    }

    try {
        showLoading();
        const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.EVENTS.DELETE, { id: eventId }), {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Не удалось удалить мероприятие');
        }

        showSuccess('Мероприятие успешно удалено');
        loadEvents(); // Перезагружаем список мероприятий
    } catch (error) {
        console.error('Ошибка при удалении мероприятия:', error);
        showError(error.message);
    } finally {
        hideLoading();
    }
} 