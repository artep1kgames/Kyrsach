#!/usr/bin/env python3
"""
Скрипт для проверки мероприятий в базе данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from models.models import Event, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

def check_events():
    """Проверяет мероприятия в базе данных"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Получаем все мероприятия
        query = select(Event)
        result = session.execute(query)
        events = result.scalars().all()
        
        print(f"Найдено мероприятий: {len(events)}")
        print("\nСписок мероприятий:")
        print("-" * 80)
        
        for event in events:
            print(f"ID: {event.id}")
            print(f"Название: {event.title}")
            print(f"Статус: {event.status}")
            print(f"Организатор ID: {event.organizer_id}")
            print(f"Дата создания: {event.created_at}")
            print("-" * 80)
        
        # Проверяем конкретное мероприятие с ID 2
        print(f"\nПроверка мероприятия с ID 2:")
        event_2 = session.get(Event, 2)
        if event_2:
            print(f"Мероприятие найдено: {event_2.title}")
            print(f"Статус: {event_2.status}")
        else:
            print("Мероприятие с ID 2 не найдено")
        
        # Проверяем пользователей
        print(f"\nПроверка пользователей:")
        users_query = select(User)
        users_result = session.execute(users_query)
        users = users_result.scalars().all()
        
        print(f"Найдено пользователей: {len(users)}")
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Роль: {user.role}")
            
    except Exception as e:
        print(f"Ошибка при проверке: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_events() 