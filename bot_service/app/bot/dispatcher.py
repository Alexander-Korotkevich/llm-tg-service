import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from app.core.config import settings
from app.infra.redis import get_redis
from app.bot.handlers import router  # Импортируем один общий роутер

logger = logging.getLogger(__name__)


# Глобальные переменные для бота и диспетчера
_bot: Bot = None
_dispatcher: Dispatcher = None


async def create_bot() -> Bot:
    """
    Создаёт и настраивает экземпляр Telegram бота.
    
    Возвращает:
        Bot: Настроенный экземпляр бота
    """
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        )
    )
    logger.info("Telegram бот создан")
    return bot


async def create_dispatcher() -> Dispatcher:
    """
    Создаёт и настраивает диспетчер aiogram.
    Регистрирует все роутеры и хендлеры.
    
    Возвращает:
        Dispatcher: Настроенный экземпляр диспетчера
    """
    # Выбираем хранилище для FSM (Finite State Machine)
    # В продакшене используем Redis, в разработке - Memory
    if settings.ENV == "prod":
        # Используем Redis для хранения состояний в продакшене
        redis_client = await get_redis()
        storage = RedisStorage(redis=redis_client)
        logger.info("Используется RedisStorage для FSM")
    else:
        # В разработке используем память
        storage = MemoryStorage()
        logger.info("Используется MemoryStorage для FSM")
    
    # Создаём диспетчер
    dp = Dispatcher(storage=storage)
    
    # Регистрируем роутер с хендлерами
    dp.include_router(router)
    
    logger.info("Все роутеры зарегистрированы в диспетчере")
    return dp


async def get_bot() -> Bot:
    """
    Возвращает глобальный экземпляр бота.
    Если бот ещё не создан, создаёт его.
    
    Возвращает:
        Bot: Экземпляр бота
    """
    global _bot
    if _bot is None:
        _bot = await create_bot()
    return _bot


async def get_dispatcher() -> Dispatcher:
    """
    Возвращает глобальный экземпляр диспетчера.
    Если диспетчер ещё не создан, создаёт его.
    
    Возвращает:
        Dispatcher: Экземпляр диспетчера
    """
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = await create_dispatcher()
    return _dispatcher


async def close_bot():
    """
    Закрывает соединение с Telegram API и освобождает ресурсы.
    Вызывается при остановке приложения.
    """
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None
        logger.info("Соединение с Telegram ботом закрыто")


async def close_dispatcher():
    """
    Закрывает диспетчер и освобождает ресурсы (хранилище состояний).
    Вызывается при остановке приложения.
    """
    global _dispatcher
    if _dispatcher is not None:
        await _dispatcher.storage.close()
        _dispatcher = None
        logger.info("Диспетчер закрыт")


# Функция для получения экземпляра бота внутри хендлеров (альтернативный способ)
def get_bot_instance() -> Bot:
    """
    Возвращает глобальный экземпляр бота для синхронного использования.
    Требует, чтобы бот уже был создан.
    
    Возвращает:
        Bot: Экземпляр бота
    """
    if _bot is None:
        raise RuntimeError("Бот не был инициализирован. Вызовите get_bot() сначала.")
    return _bot
