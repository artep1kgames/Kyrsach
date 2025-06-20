#!/usr/bin/env python3
"""
Скрипт для диагностики проблем с API
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent / "app"))

from app.database import engine
from app.models.models import Base, Event, Category, User, UserRole, EventStatus, EventType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from datetime import datetime, timedelta

async def check_database():
    """Проверяем состояние базы данных"""
    print("=== Проверка базы данных ===")
    
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Проверяем таблицы
        result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = result.fetchall()
        print(f"Таблицы в базе данных: {[t[0] for t in tables]}")
        
        # Проверяем пользователей
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Пользователей в базе: {len(users)}")
        for user in users:
            print(f"  - {user.username} ({user.email}) - {user.role.value}")
        
        # Проверяем категории
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        print(f"Категорий в базе: {len(categories)}")
        for cat in categories:
            print(f"  - {cat.name}: {cat.description}")
        
        # Проверяем события
        result = await session.execute(select(Event))
        events = result.scalars().all()
        print(f"Событий в базе: {len(events)}")
        for event in events:
            print(f"  - {event.id}: {event.title} (статус: {event.status.value})")

async def create_test_data():
    """Создаем тестовые данные если их нет"""
    print("\n=== Создание тестовых данных ===")
    
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Проверяем есть ли пользователи
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("Создаем тестового пользователя...")
            test_user = User(
                email="test@example.com",
                username="testuser",
                full_name="Test User",
                role=UserRole.ORGANIZER,
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2"  # password: test123
            )
            session.add(test_user)
            await session.commit()
            print("Тестовый пользователь создан")
        else:
            print("Пользователи уже существуют")
        
        # Проверяем есть ли категории
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        
        if not categories:
            print("Создаем тестовые категории...")
            test_categories = [
                Category(name="CONFERENCE", description="Конференция"),
                Category(name="SEMINAR", description="Семинар"),
                Category(name="WORKSHOP", description="Мастер-класс"),
                Category(name="EXHIBITION", description="Выставка"),
                Category(name="CONCERT", description="Концерт"),
                Category(name="FESTIVAL", description="Фестиваль"),
                Category(name="SPORTS", description="Спортивное мероприятие"),
                Category(name="OTHER", description="Другое")
            ]
            for cat in test_categories:
                session.add(cat)
            await session.commit()
            print("Тестовые категории созданы")
        else:
            print("Категории уже существуют")
        
        # Проверяем есть ли события
        result = await session.execute(select(Event))
        events = result.scalars().all()
        
        if not events:
            print("Создаем тестовое событие...")
            # Получаем пользователя и категорию
            user_result = await session.execute(select(User).where(User.email == "test@example.com"))
            user = user_result.scalar_one()
            
            cat_result = await session.execute(select(Category).where(Category.name == "CONFERENCE"))
            category = cat_result.scalar_one()
            
            test_event = Event(
                title="Тестовая конференция",
                short_description="Краткое описание тестовой конференции",
                full_description="Полное описание тестовой конференции с подробностями",
                location="Москва, ул. Тестовая, 1",
                start_date=datetime.now() + timedelta(days=7),
                end_date=datetime.now() + timedelta(days=7, hours=3),
                max_participants=100,
                current_participants=0,
                event_type=EventType.FREE,
                status=EventStatus.APPROVED,
                organizer_id=user.id
            )
            test_event.categories = [category]
            session.add(test_event)
            await session.commit()
            print("Тестовое событие создано")
        else:
            print("События уже существуют")

async def test_api_endpoints():
    """Тестируем API эндпоинты"""
    print("\n=== Тестирование API эндпоинтов ===")
    
    import httpx
    
    base_url = "https://kyrsach-0x7m.onrender.com"
    
    async with httpx.AsyncClient() as client:
        # Тест категорий
        try:
            response = await client.get(f"{base_url}/api/categories")
            print(f"GET /api/categories: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Категорий получено: {len(data)}")
            else:
                print(f"  Ошибка: {response.text}")
        except Exception as e:
            print(f"  Ошибка запроса: {e}")
        
        # Тест событий
        try:
            response = await client.get(f"{base_url}/api/events")
            print(f"GET /api/events: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Событий получено: {len(data)}")
            else:
                print(f"  Ошибка: {response.text}")
        except Exception as e:
            print(f"  Ошибка запроса: {e}")
        
        # Тест прямых эндпоинтов
        try:
            response = await client.get(f"{base_url}/api/direct-categories")
            print(f"GET /api/direct-categories: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Прямых категорий получено: {len(data.get('categories', []))}")
            else:
                print(f"  Ошибка: {response.text}")
        except Exception as e:
            print(f"  Ошибка запроса: {e}")
        
        try:
            response = await client.get(f"{base_url}/api/direct-events")
            print(f"GET /api/direct-events: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Прямых событий получено: {len(data.get('events', []))}")
            else:
                print(f"  Ошибка: {response.text}")
        except Exception as e:
            print(f"  Ошибка запроса: {e}")

async def main():
    """Основная функция"""
    print("Запуск диагностики API...")
    
    # Проверяем базу данных
    await check_database()
    
    # Создаем тестовые данные
    await create_test_data()
    
    # Проверяем снова после создания данных
    await check_database()
    
    # Тестируем API
    await test_api_endpoints()
    
    print("\nДиагностика завершена!")

if __name__ == "__main__":
    asyncio.run(main()) 