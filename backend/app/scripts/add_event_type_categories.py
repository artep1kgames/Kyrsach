import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.models import Category
import asyncio

DATABASE_URL = "sqlite+aiosqlite:///app/events.db"

CATEGORIES = [
    ("CONFERENCE", "Конференция"),
    ("SEMINAR", "Семинар"),
    ("WORKSHOP", "Мастер-класс"),
    ("EXHIBITION", "Выставка"),
    ("CONCERT", "Концерт"),
    ("FESTIVAL", "Фестиваль"),
    ("SPORTS", "Спортивное мероприятие"),
    ("OTHER", "Другое")
]

async def main():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        for code, name in CATEGORIES:
            exists = await session.execute(
                Category.__table__.select().where(Category.name == code)
            )
            if not exists.first():
                category = Category(name=code, description=name)
                session.add(category)
        await session.commit()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main()) 