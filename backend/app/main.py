from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
from routers import auth, events, users, calendar, admin, event_creation, categories
from database import engine, Base
from sqladmin import Admin
from admin import UserAdmin, EventAdmin, CategoryAdmin
from models import models
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI(title="EventHub API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://kyrsach-0x7m.onrender.com",
        "http://kyrsach-0x7m.onrender.com",
        "*"  # Временно разрешаем все источники для отладки
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Получаем абсолютный путь к директории приложения
BASE_DIR = Path(__file__).resolve().parent.parent

# Создаем директории для загрузки файлов
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"

# Создаем необходимые директории
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "events").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "users").mkdir(parents=True, exist_ok=True)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Регистрируем роутеры
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(users.router)
app.include_router(calendar.router)
app.include_router(admin.router)
app.include_router(categories.router)
app.include_router(event_creation.router)

# Монтируем фронтенд (отдача index.html и других файлов)
FRONTEND_DIR = BASE_DIR.parent / "frontend"
app.mount("", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# Настройка админ-панели
admin = Admin(app, engine)
admin.add_view(UserAdmin)
admin.add_view(EventAdmin)
admin.add_view(CategoryAdmin)

@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        
        # Инициализируем базу данных тестовыми данными
        await initialize_database()
    except Exception as e:
        print(f"Error during startup: {e}")
        raise

async def initialize_database():
    """Инициализация базы данных тестовыми данными"""
    try:
        from sqlalchemy.orm import sessionmaker
        from models.models import Category, User, Event, EventStatus, EventType, UserRole
        from utils.password import get_password_hash
        from datetime import datetime, timedelta
        
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        async with async_session() as session:
            # Проверяем, есть ли уже данные
            categories_count = await session.execute("SELECT COUNT(*) FROM categories;")
            categories_count = categories_count.scalar()
            
            if categories_count == 0:
                print("Initializing database with test data...")
                
                # Добавляем категории
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
                
                # Добавляем тестового организатора
                organizer = User(
                    email="organizer@test.com",
                    username="test_organizer",
                    full_name="Test Organizer",
                    hashed_password=get_password_hash("password123"),
                    role=UserRole.ORGANIZER
                )
                session.add(organizer)
                
                # Добавляем тестового админа
                admin = User(
                    email="admin@test.com",
                    username="test_admin",
                    full_name="Test Admin",
                    hashed_password=get_password_hash("password123"),
                    role=UserRole.ADMIN
                )
                session.add(admin)
                
                await session.commit()
                
                # Добавляем тестовое мероприятие
                organizer = await session.execute(
                    User.__table__.select().where(User.email == "organizer@test.com")
                )
                organizer = organizer.scalar_one()
                
                if organizer:
                    event = Event(
                        title="Test Event",
                        short_description="Test event description",
                        full_description="Full test event description",
                        location="Test Location",
                        start_date=datetime.now() + timedelta(days=7),
                        end_date=datetime.now() + timedelta(days=7, hours=2),
                        max_participants=50,
                        current_participants=0,
                        event_type=EventType.FREE,
                        status=EventStatus.APPROVED,
                        organizer_id=organizer.id
                    )
                    session.add(event)
                    await session.commit()
                    print("Database initialized with test data")
            else:
                print(f"Database already contains {categories_count} categories")
                
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()

# Корректное завершение работы
@app.on_event("shutdown")
async def shutdown():
    try:
        await engine.dispose()
    except Exception as e:
        print(f"Error during shutdown: {e}")

# Обработчик для корневого пути
@app.get("/")
async def read_root():
    return {"message": "Welcome to EventHub API"}

# Отладочный эндпоинт для проверки базы данных
@app.get("/debug/db")
async def debug_database():
    try:
        async with engine.begin() as conn:
            # Проверяем таблицы
            result = await conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = result.fetchall()
            
            # Проверяем количество записей в основных таблицах
            events_count = await conn.execute("SELECT COUNT(*) FROM events;")
            events_count = events_count.scalar()
            
            categories_count = await conn.execute("SELECT COUNT(*) FROM categories;")
            categories_count = categories_count.scalar()
            
            users_count = await conn.execute("SELECT COUNT(*) FROM users;")
            users_count = users_count.scalar()
            
            return {
                "tables": [table[0] for table in tables],
                "events_count": events_count,
                "categories_count": categories_count,
                "users_count": users_count,
                "database_url": str(engine.url)
            }
    except Exception as e:
        return {"error": str(e)}

# Обработчик для favicon
@app.get("/favicon.ico")
async def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    return {"message": "Favicon not found"} 