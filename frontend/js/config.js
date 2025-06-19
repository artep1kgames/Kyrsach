const API_CONFIG = {
    BASE_URL: '',
    ENDPOINTS: {
        AUTH: {
            LOGIN: '/auth/token',
            REGISTER: '/auth/register',
            PROFILE: '/users/me',
            LOGOUT: '/auth/logout'
        },
        EVENTS: {
            BASE: '/events',
            DETAIL: '/events/{id}',
            MODERATION: '/events/moderation',
            MODERATE: '/events/moderate',
            CREATE: '/events',
            UPDATE: '/events/update',
            DELETE: '/events/delete',
            JOIN: '/events/join',
            LEAVE: '/events/leave',
            PARTICIPATE: '/events/{id}/participate',
            CANCEL_PARTICIPATION: '/events/{id}/participate'
        },
        USERS: {
            BASE: '/users',
            PROFILE: '/users/me',
            UPDATE: '/users/update'
        }
    },
    HEADERS: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    METHODS: {
        EVENTS: {
            LIST: 'GET',
            DETAIL: 'GET',
            CREATE: 'POST',
            UPDATE: 'PUT',
            DELETE: 'DELETE',
            REGISTER: 'POST'
        }
    }
};

// Функция для получения полного URL эндпоинта
function getApiUrl(endpoint, params = {}) {
    console.log('getApiUrl вызвана с параметрами:', { endpoint, params });
    
    // Убедимся, что endpoint начинается с '/'
    if (!endpoint.startsWith('/')) {
        endpoint = '/' + endpoint;
    }
    
    let url = API_CONFIG.BASE_URL + endpoint;
    console.log('Базовый URL:', url);
    
    // Создаем множество для отслеживания использованных параметров
    const usedParams = new Set();
    
    // Заменяем параметры в URL
    Object.keys(params).forEach(key => {
        const oldUrl = url;
        url = url.replace(`{${key}}`, params[key]);
        if (oldUrl !== url) {
            console.log(`Заменен параметр {${key}} на ${params[key]}`);
            usedParams.add(key);
        }
    });
    
    // Добавляем параметры запроса, если они есть (только те, которые не были использованы в URL)
    const queryParams = Object.entries(params)
        .filter(([key]) => !usedParams.has(key))
        .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
        .join('&');
    
    if (queryParams) {
        url += (url.includes('?') ? '&' : '?') + queryParams;
        console.log('Добавлены параметры запроса:', queryParams);
    }
    
    console.log('Итоговый API URL:', url);
    return url;
}

// Экспортируем конфигурацию и вспомогательные функции
window.API_CONFIG = API_CONFIG;
window.getApiUrl = getApiUrl; 