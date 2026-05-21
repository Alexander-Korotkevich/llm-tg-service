import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator
from fakeredis import FakeRedis
from fakeredis.aioredis import FakeRedis as FakeAioredis

# Импортируем настройки для переопределения
from app.core.config import settings


# --------------------------------------------------------------------
# Фикстуры для Redis (fakeredis)
# --------------------------------------------------------------------
@pytest.fixture
def fake_redis_client():
    """
    Создаёт синхронный фейковый Redis клиент (для тестов, где нужен синхронный доступ).
    """
    return FakeRedis()


@pytest.fixture
async def fake_redis_aclient():
    """
    Создаёт асинхронный фейковый Redis клиент (для тестов aiogram).
    """
    return FakeAioredis()


@pytest.fixture
def mock_redis_get_handlers(fake_redis_aclient):
    """
    Патчит функцию get_redis в модуле handlers, чтобы тесты не подключались к реальному Redis.
    Возвращает мок, который возвращает фейковый Redis клиент.
    """
    with patch("app.bot.handlers.get_redis", new_callable=AsyncMock) as mock_get_redis:
        mock_get_redis.return_value = fake_redis_aclient
        yield mock_get_redis


@pytest.fixture
def mock_redis_get_dispatcher(fake_redis_aclient):
    """
    Патчит функцию get_redis в модуле dispatcher (для FSM с Redis).
    """
    with patch("app.bot.dispatcher.get_redis", new_callable=AsyncMock) as mock_get_redis:
        mock_get_redis.return_value = fake_redis_aclient
        yield mock_get_redis


@pytest.fixture
def mock_redis_all(fake_redis_aclient):
    """
    Патчит все места использования get_redis одновременно.
    Используется для тестов, где задействованы несколько модулей.
    """
    with patch("app.bot.handlers.get_redis", new_callable=AsyncMock) as mock_handlers, \
         patch("app.bot.dispatcher.get_redis", new_callable=AsyncMock) as mock_dispatcher, \
         patch("app.infra.redis.get_redis", new_callable=AsyncMock) as mock_infra:
        
        mock_handlers.return_value = fake_redis_aclient
        mock_dispatcher.return_value = fake_redis_aclient
        mock_infra.return_value = fake_redis_aclient
        
        yield {
            "handlers": mock_handlers,
            "dispatcher": mock_dispatcher,
            "infra": mock_infra,
        }


# --------------------------------------------------------------------
# Фикстуры для JWT (мокаем валидацию)
# --------------------------------------------------------------------
@pytest.fixture
def mock_jwt_valid():
    """
    Мокает успешную валидацию JWT токена.
    Возвращает тестовый payload.
    """
    test_payload = {
        "sub": "test_user_123",
        "email": "test@example.com",
        "exp": 9999999999,  # Далекое будущее
        "iat": 1234567890,
    }
    
    with patch("app.bot.handlers.decode_and_validate") as mock_decode:
        mock_decode.return_value = test_payload
        yield mock_decode


@pytest.fixture
def mock_jwt_invalid():
    """
    Мокает невалидный JWT токен (выбрасывает исключение).
    """
    from app.core.jwt import JWTValidationError
    
    with patch("app.bot.handlers.decode_and_validate") as mock_decode:
        mock_decode.side_effect = JWTValidationError("Неверный токен")
        yield mock_decode


@pytest.fixture
def mock_jwt_expired():
    """
    Мокает просроченный JWT токен.
    """
    from app.core.jwt import JWTValidationError
    
    with patch("app.bot.handlers.decode_and_validate") as mock_decode:
        mock_decode.side_effect = JWTValidationError("Срок действия токена истёк")
        yield mock_decode


# --------------------------------------------------------------------
# Фикстуры для Celery (мокаем отправку задач)
# --------------------------------------------------------------------
@pytest.fixture
def mock_celery_task():
    """
    Мокает отправку задачи в Celery.
    """
    mock_task = MagicMock()
    mock_task.id = "test_task_123"
    
    with patch("app.bot.handlers.llm_request") as mock_llm_request:
        mock_llm_request.delay.return_value = mock_task
        yield mock_llm_request


@pytest.fixture
def mock_celery_task_error():
    """
    Мокает ошибку при отправке задачи в Celery.
    """
    with patch("app.bot.handlers.llm_request") as mock_llm_request:
        mock_llm_request.delay.side_effect = Exception("Celery недоступен")
        yield mock_llm_request


# --------------------------------------------------------------------
# Фикстуры для OpenRouter клиента
# --------------------------------------------------------------------
@pytest.fixture
def mock_openrouter_success():
    """
    Мокает успешный ответ от OpenRouter.
    """
    with patch("app.services.openrouter_client.chat_completion_sync") as mock_chat:
        mock_chat.return_value = "Это тестовый ответ от LLM"
        yield mock_chat


@pytest.fixture
def mock_openrouter_error():
    """
    Мокает ошибку OpenRouter.
    """
    from app.services.openrouter_client import OpenRouterAPIError
    
    with patch("app.services.openrouter_client.chat_completion_sync") as mock_chat:
        mock_chat.side_effect = OpenRouterAPIError(
            status_code=500,
            message="OpenRouter временно недоступен"
        )
        yield mock_chat


@pytest.fixture
def mock_openrouter_timeout():
    """
    Мокает таймаут OpenRouter.
    """
    from app.services.openrouter_client import OpenRouterNetworkError
    
    with patch("app.services.openrouter_client.chat_completion_sync") as mock_chat:
        mock_chat.side_effect = OpenRouterNetworkError("Таймаут соединения")
        yield mock_chat


# --------------------------------------------------------------------
# Фикстуры для Telegram бота (aiogram)
# --------------------------------------------------------------------
@pytest.fixture
def mock_bot():
    """
    Создаёт мок для Telegram бота.
    """
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_message():
    """
    Создаёт мок для сообщения Telegram.
    """
    message = AsyncMock()
    message.from_user.id = 123456789
    message.from_user.username = "test_user"
    message.chat.id = 123456789
    message.text = "/token test_token"
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_message_without_token():
    """
    Создаёт мок для сообщения без токена (простой текст).
    """
    message = AsyncMock()
    message.from_user.id = 123456789
    message.chat.id = 123456789
    message.text = "Привет, как дела?"
    message.answer = AsyncMock()
    return message


# --------------------------------------------------------------------
# Фикстуры для тестовых данных
# --------------------------------------------------------------------
@pytest.fixture
def test_jwt_token():
    """
    Тестовый JWT токен (невалидный, только для тестов).
    """
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjk5OTk5OTk5OTl9.test_signature"


@pytest.fixture
def test_telegram_id():
    """
    Тестовый Telegram ID.
    """
    return "123456789"


@pytest.fixture
def test_redis_key(test_telegram_id):
    """
    Тестовый ключ Redis для JWT токена.
    """
    return f"telegram:{test_telegram_id}:jwt"


# --------------------------------------------------------------------
# Фикстуры для настроек тестового окружения
# --------------------------------------------------------------------
@pytest.fixture(autouse=True)
def test_settings():
    """
    Переопределяет настройки для тестового окружения.
    Autouse - применяется ко всем тестам автоматически.
    """
    # Сохраняем оригинальные значения
    original_env = settings.ENV
    
    # Устанавливаем тестовое окружение
    settings.ENV = "test"
    
    yield settings
    
    # Восстанавливаем оригинальные значения
    settings.ENV = original_env


# --------------------------------------------------------------------
# Фикстура для event loop (pytest-asyncio)
# --------------------------------------------------------------------
@pytest.fixture
def event_loop() -> Generator:
    """
    Создаёт event loop для асинхронных тестов.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# --------------------------------------------------------------------
# Комплексная фикстура для полного тестирования хендлера сообщений
# --------------------------------------------------------------------
@pytest.fixture
def full_handler_mocks(fake_redis_aclient, mock_jwt_valid, mock_celery_task):
    """
    Комплексная фикстура, мокающая все зависимости для тестирования.
    Возвращает словарь со всеми моками.
    """
    with patch("app.bot.handlers.get_redis", new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = fake_redis_aclient
        
        # Устанавливаем тестовый токен в фейковый Redis
        async def setup_redis():
            await fake_redis_aclient.set("telegram:123456789:jwt", "valid_test_token", ex=604800)
        
        # Запускаем настройку
        asyncio.create_task(setup_redis())
        
        yield {
            "redis": mock_redis,
            "fake_redis": fake_redis_aclient,
            "jwt": mock_jwt_valid,
            "celery": mock_celery_task,
        }


# --------------------------------------------------------------------
# Фикстура для тестирования без авторизации
# --------------------------------------------------------------------
@pytest.fixture
def no_auth_mocks(fake_redis_aclient, mock_celery_task):
    """
    Фикстура для тестирования сценариев без авторизации.
    """
    with patch("app.bot.handlers.get_redis", new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = fake_redis_aclient
        # Не сохраняем токен в Redis - имитируем отсутствие авторизации
        
        yield {
            "redis": mock_redis,
            "fake_redis": fake_redis_aclient,
            "celery": mock_celery_task,
        }
