import redis.asyncio as redis
from typing import Optional
from app.core.config import settings


class RedisClientManager:
    """
    Менеджер Redis клиента с ленивой инициализацией.
    Обеспечивает единый экземпляр клиента на всё приложение.
    """
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """
        Возвращает экземпляр Redis клиента.
        При первом вызове создаёт новый клиент.
        Последующие вызовы возвращают тот же экземпляр.
        
        Возвращает:
            redis.Redis: Асинхронный Redis клиент
            
        Пример:
            redis_client = await get_redis()
            await redis_client.set("key", "value")
        """
        if self._client is None:
            # Создаём новый клиент при первом обращении
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,  # Автоматически декодировать ответы в строки
            )
        
        return self._client
    
    async def close(self) -> None:
        """
        Закрывает соединение с Redis.
        Должен вызываться при завершении работы приложения.
        """
        if self._client is not None:
            await self._client.close()
            self._client = None


# Глобальный экземпляр менеджера
_redis_manager = RedisClientManager()


# Упрощённая функция для получения клиента
async def get_redis() -> redis.Redis:
    """
    Функция для получения Redis клиента.
    Рекомендуемый способ доступа к Redis в приложении.
    
    Возвращает:
        redis.Redis: Асинхронный Redis клиент
        
    Пример:
        # В любом месте приложения
        redis_client = await get_redis()
        await redis_client.set("user:123:jwt", "token_value", ex=3600)
    """
    return await _redis_manager.get_client()


# Функция для закрытия соединения (вызывать при выключении)
async def close_redis() -> None:
    """
    Закрывает соединение с Redis.
    Вызывать при остановке приложения (например, в lifespan).
    """
    await _redis_manager.close()


# Вспомогательная функция для проверки соединения
async def check_redis_health() -> bool:
    """
    Проверяет доступность Redis.
    
    Возвращает:
        bool: True если Redis доступен, иначе False
    """
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception:
        return False
