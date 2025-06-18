#!/usr/bin/env python3
import asyncio
import sys
import os

# Добавляем путь к модулям приложения
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import engine
from app.models.models import Event, Category
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

async def check_events_categories():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Получаем все мероприятия
        events = session.query(Event).all()
        print(f"Найдено мероприятий: {len(events)}")
        
        for event in events:
            print(f"\nМероприятие: {event.title}")
            print(f"  ID: {event.id}")
            print(f"  Статус: {event.status}")
            print(f"  Тип: {event.event_type}")
            print(f"  Категории: {len(event.categories) if event.categories else 0}")
            
            if event.categories:
                for cat in event.categories:
                    print(f"    - {cat.name} (ID: {cat.id}, Описание: {cat.description})")
            else:
                print("    - Категории не назначены")
                
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(check_events_categories()) 