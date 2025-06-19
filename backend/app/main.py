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

# Прямые эндпоинты для тестирования (БЕЗ роутеров) - ДОЛЖНЫ БЫТЬ ПЕРЕД монтированием статики
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
        import traceback
        traceback.print_exc()
        return {"error": str(e), "categories": []}

@app.get("/direct-events")
async def direct_events():
    try:
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import select
        from models.models import Event, User, Category
        from sqlalchemy.orm import selectinload, joinedload
        
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        async with async_session() as session:
            # Загружаем события с организатором и категориями
            query = select(Event).options(
                joinedload(Event.organizer),
                selectinload(Event.categories)
            )
            result = await session.execute(query)
            events = result.unique().scalars().all()
            
            events_list = []
            for event in events:
                # Получаем участников для каждого мероприятия
                participants_query = select(models.event_participants).where(
                    models.event_participants.c.event_id == event.id
                )
                participants_result = await session.execute(participants_query)
                participants = participants_result.fetchall()
                
                event_dict = {
                    "id": event.id,
                    "title": event.title,
                    "short_description": event.short_description,
                    "full_description": event.full_description,
                    "location": event.location,
                    "start_date": event.start_date.isoformat() if event.start_date else None,
                    "end_date": event.end_date.isoformat() if event.end_date else None,
                    "max_participants": event.max_participants,
                    "current_participants": event.current_participants,
                    "status": event.status.value if event.status else None,
                    "event_type": event.event_type.value if event.event_type else None,
                    "ticket_price": event.ticket_price,
                    "image_url": event.image_url,
                    "organizer_id": event.organizer_id,
                    "organizer": {
                        "id": event.organizer.id,
                        "username": event.organizer.username,
                        "email": event.organizer.email,
                        "full_name": event.organizer.full_name
                    } if event.organizer else None,
                    "categories": [
                        {
                            "id": cat.id,
                            "name": cat.name,
                            "description": cat.description
                        } for cat in event.categories
                    ] if event.categories else [],
                    "participants": [
                        {
                            "user_id": p.user_id,
                            "event_id": p.event_id,
                            "ticket_purchased": p.ticket_purchased
                        } for p in participants
                    ] if participants else []
                }
                events_list.append(event_dict)
            
            return {"events": events_list, "count": len(events_list)}
    except Exception as e:
        print(f"Error in direct_events: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "events": []}

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
        
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        
        async with async_session() as session:
            # Проверяем, есть ли уже данные
            try:
                categories_count = await session.execute(text("SELECT COUNT(*) FROM categories;"))
                categories_count = categories_count.scalar()
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

# Отладочный эндпоинт для проверки прямых эндпоинтов
@app.get("/debug/direct-endpoints")
async def debug_direct_endpoints():
    return {
        "message": "Direct endpoints test",
        "endpoints": {
            "direct_categories": "/direct-categories",
            "direct_events": "/direct-events",
            "test_categories": "/test-api/categories",
            "test_events": "/test-api/events"
        },
        "note": "These endpoints should work before static file mounting"
    }

# Обработчик для favicon
@app.get("/favicon.ico")
async def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    return {"message": "Favicon not found"} 