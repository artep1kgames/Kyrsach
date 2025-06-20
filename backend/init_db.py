#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""
import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import engine
from app.models.models import Category, Event, User, UserRole, EventStatus, EventType
from app.utils.password import get_password_hash
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

async def init_database():
    """Инициализация базы данных"""
    print("Инициализация базы данных...")
    
    try:
        # Создаем таблицы
        async with engine.begin() as conn:
            from app.models.models import Base
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Таблицы созданы")
        
        # Создаем сессию
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        async with async_session() as session:
            # Проверяем, есть ли уже данные
            categories_count = await session.execute(select(Category))
            categories_count = len(categories_count.scalars().all())
            
            if categories_count == 0:
                print("Добавляем категории...")
                categories_data = [
                    ("CONFERENCE", "Конференция"),
                    ("SEMINAR", "Семинар"),
                    ("WORKSHOP", "Мастер-класс"),
                    ("EXHIBITION", "Выставка"),
                    ("CONCERT", "Концерт"),
                    ("FESTIVAL", "Фестиваль"),
                    ("SPORTS", "Спортивное мероприятие"),
                    ("OTHER", "Другое")
                ]
                
                for code, name in categories_data:
                    category = Category(name=code, description=name)
                    session.add(category)
                
                await session.commit()
                print("✓ Категории добавлены")
            else:
                print(f"✓ Категории уже существуют ({categories_count} шт.)")
            
            # Проверяем пользователей
            users_count = await session.execute(select(User))
            users_count = len(users_count.scalars().all())
            
            if users_count == 0:
                print("Добавляем тестовых пользователей...")
                
                # Добавляем организатора
                organizer = User(
                    email="organizer@test.com",
                    username="test_organizer",
                    full_name="Test Organizer",
                    hashed_password=get_password_hash("password123"),
                    role=UserRole.ORGANIZER
                )
                session.add(organizer)
                
                # Добавляем админа
                admin = User(
                    email="admin@test.com",
                    username="test_admin",
                    full_name="Test Admin",
                    hashed_password=get_password_hash("password123"),
                    role=UserRole.ADMIN
                )
                session.add(admin)
                
                await session.commit()
                print("✓ Тестовые пользователи добавлены")
            else:
                print(f"✓ Пользователи уже существуют ({users_count} шт.)")
            
            # Проверяем события
            events_count = await session.execute(select(Event))
            events_count = len(events_count.scalars().all())
            
            if events_count == 0:
                print("Добавляем тестовое событие...")
                
                # Получаем организатора
                organizer_result = await session.execute(
                    select(User).where(User.email == "organizer@test.com")
                )
                organizer = organizer_result.scalar_one()
                
                if organizer:
                    # Получаем категорию
                    category_result = await session.execute(
                        select(Category).where(Category.name == "CONFERENCE")
                    )
                    category = category_result.scalar_one()
                    
                    event = Event(
                        title="Тестовая конференция",
                        short_description="Тестовая конференция для отладки",
                        full_description="Это тестовая конференция, созданная для отладки системы.",
                        location="Тестовая локация",
                        start_date=datetime.now() + timedelta(days=7),
                        end_date=datetime.now() + timedelta(days=7, hours=2),
                        max_participants=50,
                        current_participants=0,
                        event_type=EventType.FREE,
                        status=EventStatus.APPROVED,
                        organizer_id=organizer.id
                    )
                    
                    if category:
                        event.categories = [category]
                    
                    session.add(event)
                    await session.commit()
                    print("✓ Тестовое событие добавлено")
                else:
                    print("⚠ Организатор не найден, пропускаем создание события")
            else:
                print(f"✓ События уже существуют ({events_count} шт.)")
        
        print("✓ Инициализация базы данных завершена успешно!")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка при инициализации: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(init_database()) 