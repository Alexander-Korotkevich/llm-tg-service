from fastapi import FastAPI
from contextlib import asynccontextmanager

from importlib.metadata import version, PackageNotFoundError


def get_package_version(package_name: str) -> str:
    """Получить версию пакета, вернуть 'unknown' если не найдено."""
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "unknown"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер жизненного цикла для событий запуска/остановки.
    Без тяжёлой логики - бот запускается отдельно.
    """
    # Запуск
    print("FastAPI часть Bot Service запускается...")
    yield
    # Остановка
    print("FastAPI часть Bot Service останавливается...")


# Создаём FastAPI приложение
app = FastAPI(
    title="Bot Service API",
    description="Служебные эндпоинты для мониторинга бота и проверок здоровья",
    version=get_package_version("bot-service"),
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """
    Эндпоинт проверки здоровья для оркестрации контейнеров.
    """
    return {
        "status": "healthy",
        "service": "bot-service-api",
        "version": get_package_version("bot-service"),
    }


@app.get("/readiness")
async def readiness_check():
    """
    Проверка готовности - показывает, что сервис готов принимать запросы.
    """
    # В реальном сценарии здесь проверялись бы зависимости
    # Но по требованию - нет прямой работы с Redis/LLM
    return {"status": "ready"}


@app.get("/")
async def root():
    """
    Корневой эндпоинт с базовой информацией о сервисе.
    """
    return {
        "service": "Bot Service",
        "description": "Telegram бот с JWT аутентификацией и интеграцией с LLM",
        "docs": "/docs",
        "health": "/health",
    }
