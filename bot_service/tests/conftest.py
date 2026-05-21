import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


# Правильный асинхронный фейковый Redis
class FakeAioredisClient:
    """Асинхронный фейковый Redis клиент."""
    def __init__(self):
        self._data = {}
    
    async def get(self, key):
        return self._data.get(key)
    
    async def set(self, key, value, ex=None):
        self._data[key] = value
        return True
    
    async def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)
        return len(keys)
    
    async def ping(self):
        return True
    
    def __await__(self):
        """Чтобы объект можно было использовать с await."""
        async def wrapper():
            return self
        return wrapper().__await__()


@pytest.fixture
async def fake_redis_aclient():
    return FakeAioredisClient()


@pytest.fixture
def mock_redis_get_handlers(fake_redis_aclient):
    with patch("app.bot.handlers.get_redis", new_callable=AsyncMock) as mock_get_redis:
        mock_get_redis.return_value = fake_redis_aclient
        yield mock_get_redis


@pytest.fixture
def mock_jwt_valid():
    test_payload = {
        "sub": "test_user_123",
        "exp": int((datetime.now() + timedelta(days=1)).timestamp())
    }
    with patch("app.bot.handlers.decode_and_validate") as mock_decode:
        mock_decode.return_value = test_payload
        yield mock_decode


@pytest.fixture
def mock_jwt_invalid():
    from app.core.jwt import JWTValidationError
    with patch("app.bot.handlers.decode_and_validate") as mock_decode:
        mock_decode.side_effect = JWTValidationError("Неверный токен")
        yield mock_decode


@pytest.fixture
def mock_jwt_expired():
    from app.core.jwt import JWTValidationError
    with patch("app.bot.handlers.decode_and_validate") as mock_decode:
        mock_decode.side_effect = JWTValidationError("Срок действия токена истёк")
        yield mock_decode


@pytest.fixture
def mock_celery_task():
    mock_task = MagicMock()
    mock_task.id = "test_task_123"
    with patch("app.bot.handlers.llm_request") as mock_llm:
        mock_llm.delay.return_value = mock_task
        yield mock_llm


@pytest.fixture
def mock_telegram_message():
    """Правильно настроенный мок сообщения Telegram."""
    message = AsyncMock()
    
    user = MagicMock()
    user.id = 123456789
    user.username = "test_user"
    user.first_name = "Test"
    user.last_name = "User"
    user.is_bot = False
    message.from_user = user
    
    chat = MagicMock()
    chat.id = 123456789
    chat.type = "private"
    chat.username = "test_user"
    message.chat = chat
    
    message.text = "Тестовое сообщение"
    message.message_id = 1
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    
    return message


@pytest.fixture
def no_auth_mocks(fake_redis_aclient):
    with patch("app.bot.handlers.get_redis", new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = fake_redis_aclient
        yield mock_redis


@pytest.fixture
async def full_handler_mocks(fake_redis_aclient, mock_jwt_valid):
    with patch("app.bot.handlers.get_redis", new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = fake_redis_aclient
        await fake_redis_aclient.set("telegram:123456789:jwt", "valid_token", ex=300)
        yield {
            "redis": mock_redis,
            "fake_redis": fake_redis_aclient,
            "jwt": mock_jwt_valid,
        }


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
