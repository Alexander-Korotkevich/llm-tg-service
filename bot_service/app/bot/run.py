# Точка входа для запуска aiogram бота отдельным процессом

import asyncio
import logging
from app.bot.dispatcher import get_bot, get_dispatcher, close_bot, close_dispatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Запуск Telegram бота."""
    logger.info("Запуск aiogram бота...")
    
    try:
        bot = await get_bot()
        dispatcher = await get_dispatcher()
        
        logger.info("Бот успешно инициализирован, начинаю polling...")
        
        # Запускаем polling
        await dispatcher.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            skip_updates=True  # Пропускаем старые обновления
        )
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        # Корректное завершение
        await close_dispatcher()
        await close_bot()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
