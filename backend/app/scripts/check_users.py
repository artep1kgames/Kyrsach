import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.models import User, UserRole
from app.database import DATABASE_URL

async def check_users():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Получаем всех пользователей
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Найдено пользователей: {len(users)}")
        print("\nСписок пользователей:")
        print("-" * 50)
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Username: {user.username}")
            print(f"Full Name: {user.full_name}")
            print(f"Role: {user.role.value if user.role else 'None'}")
            print("-" * 30)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_users()) 