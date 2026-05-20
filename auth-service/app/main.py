from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import init_db
from app.api.router import router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager для управления жизненным циклом приложения"""
    # Startup
    await init_db()
    yield
    # Shutdown
    # Здесь можно добавить cleanup если необходимо

# Создание приложения FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Auth Service: регистрация, логин и выдача JWT",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене нужно ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(router)

# Системные ручки
@app.get("/health", tags=["system"])
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "healthy", "service": settings.app_name, "env": settings.env}

@app.get("/", tags=["system"])
async def root():
    """Корневой эндпоинт"""
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }
