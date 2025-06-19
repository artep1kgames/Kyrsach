from passlib.context import CryptContext
import hashlib
import os

# Настройка хеширования паролей с более простой конфигурацией
try:
pwd_context = CryptContext(
    schemes=["bcrypt"],
        deprecated="auto"
)
    USE_BCRYPT = True
except Exception as e:
    print(f"Warning: bcrypt not available, using fallback hashing: {e}")
    USE_BCRYPT = False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хешу
    """
    try:
        if USE_BCRYPT:
        return pwd_context.verify(plain_password, hashed_password)
        else:
            # Fallback: простое хеширование (не для продакшена)
            return hashed_password == simple_hash(plain_password)
    except Exception as e:
        print(f"Ошибка при проверке пароля: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Создает хеш пароля
    """
    try:
        if USE_BCRYPT:
        return pwd_context.hash(password)
        else:
            # Fallback: простое хеширование (не для продакшена)
            return simple_hash(password)
    except Exception as e:
        print(f"Ошибка при хешировании пароля: {e}")
        # Используем fallback
        return simple_hash(password)

def simple_hash(password: str) -> str:
    """
    Простое хеширование пароля (только для отладки)
    """
    salt = "eventsalt"  # Фиксированная соль для отладки
    return hashlib.sha256((password + salt).encode()).hexdigest() 