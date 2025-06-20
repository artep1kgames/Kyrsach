#!/usr/bin/env python3
"""
Скрипт для добавления тестовых данных в базу данных
"""
import asyncio
import sys
from pathlib import Path

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent / "app"))

from app.database import engine
from app.models.models import Base, Event, Category, User, UserRole, EventStatus, EventType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime, timedelta
from app.utils.password import get_password_hash

async def add_test_data():
    """Добавляем тестовые данные в базу"""
    print("Добавление тестовых данных...")
    
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Проверяем есть ли пользователи
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("Создаем тестовых пользователей...")
            
            # Создаем админа
            admin_user = User(
                email="admin@example.com",
                username="admin",
                full_name="Администратор",
                role=UserRole.ADMIN,
                hashed_password=get_password_hash("admin123")
            )
            session.add(admin_user)
            
            # Создаем организатора
            organizer_user = User(
                email="organizer@example.com",
                username="organizer",
                full_name="Организатор",
                role=UserRole.ORGANIZER,
                hashed_password=get_password_hash("organizer123")
            )
            session.add(organizer_user)
            
            # Создаем обычного пользователя
            visitor_user = User(
                email="visitor@example.com",
                username="visitor",
                full_name="Посетитель",
                role=UserRole.VISITOR,
                hashed_password=get_password_hash("visitor123")
            )
            session.add(visitor_user)
            
            await session.commit()
            print("Тестовые пользователи созданы")
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
            print("Создаем тестовые события...")
            
            # Получаем пользователя-организатора и категории
            organizer_result = await session.execute(select(User).where(User.email == "organizer@example.com"))
            organizer = organizer_result.scalar_one()
            
            conf_cat_result = await session.execute(select(Category).where(Category.name == "CONFERENCE"))
            conf_category = conf_cat_result.scalar_one()
            
            workshop_cat_result = await session.execute(select(Category).where(Category.name == "WORKSHOP"))
            workshop_category = workshop_cat_result.scalar_one()
            
            # Создаем тестовые события
            test_events = [
                Event(
                    title="Технологическая конференция 2024",
                    short_description="Ежегодная конференция по новейшим технологиям",
                    full_description="Подробное описание конференции с программой и спикерами",
                    location="Москва, ул. Тверская, 1",
                    start_date=datetime.now() + timedelta(days=7),
                    end_date=datetime.now() + timedelta(days=7, hours=8),
                    max_participants=200,
                    current_participants=0,
                    event_type=EventType.PAID,
                    ticket_price=1500.0,
                    status=EventStatus.APPROVED,
                    organizer_id=organizer.id
                ),
                Event(
                    title="Мастер-класс по программированию",
                    short_description="Практический мастер-класс для начинающих разработчиков",
                    full_description="Изучите основы программирования на Python",
                    location="Санкт-Петербург, Невский проспект, 50",
                    start_date=datetime.now() + timedelta(days=14),
                    end_date=datetime.now() + timedelta(days=14, hours=4),
                    max_participants=30,
                    current_participants=0,
                    event_type=EventType.FREE,
                    status=EventStatus.APPROVED,
                    organizer_id=organizer.id
                ),
                Event(
                    title="Выставка современного искусства",
                    short_description="Выставка работ современных художников",
                    full_description="Уникальная возможность познакомиться с современным искусством",
                    location="Екатеринбург, ул. Ленина, 10",
                    start_date=datetime.now() + timedelta(days=21),
                    end_date=datetime.now() + timedelta(days=28),
                    max_participants=500,
                    current_participants=0,
                    event_type=EventType.PAID,
                    ticket_price=500.0,
                    status=EventStatus.APPROVED,
                    organizer_id=organizer.id
                )
            ]
            
            for event in test_events:
                session.add(event)
            
            await session.commit()
            
            # Добавляем категории к событиям
            events_result = await session.execute(select(Event))
            events_list = events_result.scalars().all()
            
            if len(events_list) >= 3:
                events_list[0].categories = [conf_category]
                events_list[1].categories = [workshop_category]
                events_list[2].categories = [conf_category]
            
            await session.commit()
            print("Тестовые события созданы")
        else:
            print("События уже существуют")
    
    print("Тестовые данные добавлены успешно!")

async def main():
    """Основная функция"""
    try:
        await add_test_data()
        print("\nСкрипт выполнен успешно!")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 