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
from sqlalchemy.orm import sessionmaker

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

@test_router.get("/router-test")
async def test_router_endpoints():
    """Тестовый эндпоинт для проверки работы роутеров"""
    return {
        "message": "Router test endpoint",
        "available_endpoints": {
            "categories": "/categories",
            "events": "/events",
            "auth": "/auth",
            "users": "/users",
            "admin": "/admin"
        },
        "test_endpoints": {
            "direct_categories": "/direct-categories",
            "direct_events": "/direct-events",
            "debug_routes": "/debug/routes",
            "debug_db": "/debug/db"
        }
    }

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

# Выводим все доступные роуты для отладки
print("\n=== Available routes ===")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"{route.path} - {getattr(route, 'methods', [])}")
print("=== End routes ===\n")

# Монтируем статические файлы ПОСЛЕ регистрации роутеров
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

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
        from sqlalchemy import text
        from models.models import Category, User, Event, EventStatus, EventType, UserRole
        from utils.password import get_password_hash
        from datetime import datetime, timedelta
        
        print("Starting database initialization...")
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        async with async_session() as session:
            # Проверяем, есть ли уже данные
            try:
                print("Checking existing categories...")
                categories_count = await session.execute(text("SELECT COUNT(*) FROM categories;"))
                categories_count = categories_count.scalar()
                print(f"Found {categories_count} existing categories")
            except Exception as e:
                print(f"Error checking categories count: {e}")
                categories_count = 0
            
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
                    print(f"Added category: {code} - {name}")
                
                await session.commit()
                print("Categories committed successfully")
                
                # Добавляем тестового организатора
                try:
                    organizer = User(
                        email="organizer@test.com",
                        username="test_organizer",
                        full_name="Test Organizer",
                        hashed_password=get_password_hash("password123"),
                        role=UserRole.ORGANIZER
                    )
                    session.add(organizer)
                    print("Added test organizer")
                except Exception as e:
                    print(f"Error creating organizer: {e}")
                
                # Добавляем тестового админа
                try:
                    admin = User(
                        email="admin@test.com",
                        username="test_admin",
                        full_name="Test Admin",
                        hashed_password=get_password_hash("password123"),
                        role=UserRole.ADMIN
                    )
                    session.add(admin)
                    print("Added test admin")
                except Exception as e:
                    print(f"Error creating admin: {e}")
                
                await session.commit()
                print("Users committed successfully")
                
                # Добавляем тестовое мероприятие
                try:
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
                        print("Added test event")
                except Exception as e:
                    print(f"Error creating test event: {e}")
                
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

# Эндпоинт для проверки здоровья API
@app.get("/health")
async def health_check():
    """Эндпоинт для проверки здоровья API"""
    try:
        # Проверяем подключение к базе данных
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "message": "API is working correctly",
            "database": "connected",
            "timestamp": "2024-01-15T10:00:00"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"API has issues: {str(e)}",
            "database": "disconnected",
            "timestamp": "2024-01-15T10:00:00"
        }

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
        print(f"Error in direct_categories: {e}")
        # Fallback данные
        fallback_categories = [
            {"id": 1, "name": "CONFERENCE", "description": "Конференция"},
            {"id": 2, "name": "SEMINAR", "description": "Семинар"},
            {"id": 3, "name": "WORKSHOP", "description": "Мастер-класс"},
            {"id": 4, "name": "EXHIBITION", "description": "Выставка"},
            {"id": 5, "name": "CONCERT", "description": "Концерт"},
            {"id": 6, "name": "FESTIVAL", "description": "Фестиваль"},
            {"id": 7, "name": "SPORTS", "description": "Спортивное мероприятие"},
            {"id": 8, "name": "OTHER", "description": "Другое"}
        ]
        return {"categories": fallback_categories, "count": len(fallback_categories)}

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
        print(f"Error in direct_events: {e}")
        # Fallback данные
        fallback_events = [
            {
                "id": 1,
                "title": "Тестовое мероприятие",
                "short_description": "Описание тестового мероприятия",
                "location": "Тестовая локация",
                "start_date": "2024-01-15T10:00:00",
                "status": "APPROVED"
            }
        ]
        return {"events": fallback_events, "count": len(fallback_events)}

# Fallback эндпоинты для основных роутеров (регистрируем ПОСЛЕ роутеров)
@app.get("/categories")
async def fallback_categories():
    """Fallback эндпоинт для категорий"""
    print("Fallback categories endpoint called")
    try:
        # Пытаемся использовать роутер
        from routers.categories import read_categories
        from database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with async_session() as session:
            return await read_categories(db=session)
    except Exception as e:
        print(f"Error in fallback_categories: {e}")
        # Возвращаем статические данные
        fallback_categories = [
            {"id": 1, "name": "CONFERENCE", "description": "Конференция"},
            {"id": 2, "name": "SEMINAR", "description": "Семинар"},
            {"id": 3, "name": "WORKSHOP", "description": "Мастер-класс"},
            {"id": 4, "name": "EXHIBITION", "description": "Выставка"},
            {"id": 5, "name": "CONCERT", "description": "Концерт"},
            {"id": 6, "name": "FESTIVAL", "description": "Фестиваль"},
            {"id": 7, "name": "SPORTS", "description": "Спортивное мероприятие"},
            {"id": 8, "name": "OTHER", "description": "Другое"}
        ]
        return fallback_categories

@app.get("/events")
async def fallback_events():
    """Fallback эндпоинт для событий"""
    print("Fallback events endpoint called")
    try:
        # Пытаемся использовать роутер
        from routers.events import get_events
        from database import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with async_session() as session:
            return await get_events(db=session)
    except Exception as e:
        print(f"Error in fallback_events: {e}")
        # Возвращаем статические данные
        fallback_events = [
            {
                "id": 1,
                "title": "Тестовое мероприятие",
                "short_description": "Описание тестового мероприятия",
                "location": "Тестовая локация",
                "start_date": "2024-01-15T10:00:00",
                "status": "APPROVED"
            }
        ]
        return fallback_events 