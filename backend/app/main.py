from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
from routers import auth, events, users, calendar, admin, event_creation
from routes import categories
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
        "http://localhost:5500"
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

# Монтируем фронтенд (отдача index.html и других файлов)
FRONTEND_DIR = BASE_DIR.parent / "frontend"
app.mount("", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# Регистрируем роутеры
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(users.router)
app.include_router(calendar.router)
app.include_router(admin.router)
app.include_router(categories.router)
app.include_router(event_creation.router)

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
    except Exception as e:
        print(f"Error during startup: {e}")
        raise

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

# Обработчик для favicon
@app.get("/favicon.ico")
async def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    return {"message": "Favicon not found"} 