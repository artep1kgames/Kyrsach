from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
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
from sqlalchemy import text

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

# Тестовый роутер для проверки
test_router = APIRouter(prefix="/test-api", tags=["test"])

@test_router.get("/hello")
async def hello():
    return {"message": "Hello from test router!"}

@test_router.get("/categories")
async def test_categories():
    return {"message": "Categories endpoint test", "categories": ["test1", "test2"]}

@test_router.get("/events")
async def test_events():
    return {"message": "Events endpoint test", "events": ["event1", "event2"]}

# Регистрируем роутеры ПЕРЕД монтированием статических файлов
print("Registering routers...")
app.include_router(test_router)
print("✓ Test router registered")
app.include_router(auth.router)
print("✓ Auth router registered")
app.include_router(events.router)
print("✓ Events router registered")
app.include_router(users.router)
print("✓ Users router registered")
app.include_router(calendar.router)
print("✓ Calendar router registered")
app.include_router(admin.router)
print("✓ Admin router registered")
app.include_router(categories.router)
print("✓ Categories router registered")
app.include_router(event_creation.router)
print("✓ Event creation router registered")
print("All routers registered successfully!")

# Монтируем статические файлы ПОСЛЕ регистрации роутеров
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Монтируем изображения фронтенда для обратной совместимости
FRONTEND_IMAGES_DIR = BASE_DIR.parent / "frontend" / "images"
app.mount("/frontend/images", StaticFiles(directory=str(FRONTEND_IMAGES_DIR)), name="frontend_images")

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
        print("Starting application...")
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        print("Database tables created successfully")
        
        # Инициализируем базу данных тестовыми данными
        try:
            await initialize_database()
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
            print("Application will continue without test data")
            
    except Exception as e:
        print(f"Error during startup: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения при ошибках
        print("Application will continue despite startup errors")

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
            categories_count = await session.execute(text("SELECT COUNT(*) FROM categories;"))
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

# Тестовый эндпоинт для проверки работы сервера
@app.get("/test")
async def test_endpoint():
    return {"message": "Server is working", "status": "ok"}

# Эндпоинт для проверки работы роутеров
@app.get("/test/routers")
async def test_routers():
    return {
        "message": "Testing router endpoints",
        "endpoints": {
            "categories": "/categories",
            "events": "/events",
            "test_api": "/test-api/hello"
        }
    }

# Эндпоинт для просмотра всех зарегистрированных роутов
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "name": getattr(route, 'name', 'Unknown'),
                "methods": getattr(route, 'methods', [])
            })
    return {"routes": routes}

# Отладочный эндпоинт для проверки базы данных
@app.get("/debug/db")
async def debug_database():
    try:
        async with engine.begin() as conn:
            # Проверяем таблицы
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = result.fetchall()
            
            # Проверяем количество записей в основных таблицах
            events_count = await conn.execute(text("SELECT COUNT(*) FROM events;"))
            events_count = events_count.scalar()
            
            categories_count = await conn.execute(text("SELECT COUNT(*) FROM categories;"))
            categories_count = categories_count.scalar()
            
            users_count = await conn.execute(text("SELECT COUNT(*) FROM users;"))
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

# Прямые эндпоинты для тестирования (без роутеров)
@app.get("/direct-categories")
async def direct_categories():
    try:
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import select
        from models.models import Category
        
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        async with async_session() as session:
            query = select(Category)
            result = await session.execute(query)
            categories = result.scalars().all()
            
            categories_list = []
            for category in categories:
                categories_list.append({
                    "id": category.id,
                    "name": category.name,
                    "description": category.description
                })
            
            return {"categories": categories_list, "count": len(categories_list)}
    except Exception as e:
        return {"error": str(e), "categories": []}

@app.get("/direct-events")
async def direct_events():
    try:
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import select
        from models.models import Event
        
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        async with async_session() as session:
            query = select(Event)
            result = await session.execute(query)
            events = result.scalars().all()
            
            events_list = []
            for event in events:
                events_list.append({
                    "id": event.id,
                    "title": event.title,
                    "short_description": event.short_description,
                    "location": event.location,
                    "start_date": event.start_date.isoformat() if event.start_date else None,
                    "status": event.status.value if event.status else None
                })
            
            return {"events": events_list, "count": len(events_list)}
    except Exception as e:
        return {"error": str(e), "events": []} 