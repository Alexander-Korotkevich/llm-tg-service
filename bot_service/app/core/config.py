from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Настройки Bot Service.
    Для docker-compose значения по умолчанию - имена сервисов (redis, rabbitmq).
    """
    
    # --- Общие настройки ---
    APP_NAME: str = Field(default="bot-service", description="Название приложения")
    ENV: str = Field(default="local", description="Окружение: local, dev, prod")
    
    # --- Telegram бот ---
    TELEGRAM_BOT_TOKEN: str = Field(
        ...,  # обязательный параметр, нет значения по умолчанию
        description="Токен Telegram бота (получается у @BotFather)"
    )
    
    # --- JWT аутентификация ---
    JWT_SECRET: str = Field(
        default="change_me_super_secret",
        description="Секретный ключ для валидации JWT (HS256)"
    )
    JWT_ALG: str = Field(
        default="HS256",
        description="Алгоритм подписи JWT"
    )
    
    # --- OpenRouter (LLM) ---
    OPENROUTER_API_KEY: str = Field(
        ...,  # обязательный параметр
        description="API ключ OpenRouter"
    )
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai",
        description="Базовый URL OpenRouter API"
    )
    OPENROUTER_MODEL: str = Field(
        default="stepfun/step-3.5-flash:free",
        description="Модель LLM для использования"
    )
    OPENROUTER_SITE_URL: str = Field(
        default="https://example.com",
        description="URL сайта для OpenRouter"
    )
    OPENROUTER_APP_NAME: str = Field(
        default="bot-service",
        description="Название приложения для OpenRouter"
    )
    
    # --- Redis (для Celery брокера и кэширования) ---
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",  # имя сервиса 'redis' в docker-compose
        description="URL подключения к Redis"
    )
    
    # --- RabbitMQ (для Celery брокера) ---
    RABBITMQ_URL: str = Field(
        default="amqp://guest:guest@rabbitmq:5672//",  # имя сервиса 'rabbitmq' в docker-compose
        description="URL подключения к RabbitMQ"
    )
    
    # --- Опционально: Auth Service (если потребуется) ---
    AUTH_SERVICE_URL: Optional[str] = Field(
        default=None,
        description="URL Auth Service (если потребуется синхронизация)"
    )
    
    class Config:
        """Настройки Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Создаём глобальный экземпляр настроек
settings = Settings()


# Вспомогательная функция для вывода конфигурации (без секретов)
def get_public_settings() -> dict:
    """
    Возвращает настройки для отладки (без чувствительных данных).
    """
    return {
        "APP_NAME": settings.APP_NAME,
        "ENV": settings.ENV,
        "JWT_ALG": settings.JWT_ALG,
        "OPENROUTER_BASE_URL": settings.OPENROUTER_BASE_URL,
        "OPENROUTER_MODEL": settings.OPENROUTER_MODEL,
        "REDIS_URL": settings.REDIS_URL,
        "RABBITMQ_URL": settings.RABBITMQ_URL,
        "AUTH_SERVICE_URL": settings.AUTH_SERVICE_URL,
    }
