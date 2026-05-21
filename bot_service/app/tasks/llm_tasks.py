import httpx
import logging
from typing import Optional, Dict, Any
from celery import Task
from app.infra.celery_app import celery_app
from app.core.config import settings
from app.infra.redis import get_redis
from app.services.openrouter_client import chat_completion_sync
from app.services.openrouter_client import OpenRouterNetworkError, OpenRouterAPIError, OpenRouterError

# Настройка логирования
logger = logging.getLogger(__name__)


class LLMRequestTask(Task):
    """Базовый класс для задачи запроса к LLM с обработкой ошибок и повторов."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Логирование ошибок при выполнении задачи."""
        logger.error(f"Задача {task_id} провалилась: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=LLMRequestTask,
    name="llm_request",
    max_retries=3,
    default_retry_delay=60,
)
def llm_request(
    self,
    tg_chat_id: int,
    prompt: str,
    user_jwt: str,
    send_directly: bool = True
) -> Dict[str, Any]:
    """
    Асинхронная задача для отправки запроса к LLM через OpenRouter.
    """
    
    logger.info(f"Задача llm_request: обрабатываю запрос от chat_id={tg_chat_id}")
    
    try:
        # 1. Вызываем OpenRouter API через клиент
        llm_response = chat_completion_sync(prompt=prompt, temperature=0.7, max_tokens=1000)
        
        # 2. Формируем результат
        result = {
            "success": True,
            "response": llm_response,
            "error": None,
            "tg_chat_id": tg_chat_id,
        }
        
        # 3. Отправляем результат пользователю
        if send_directly:
            send_telegram_message(tg_chat_id, llm_response)
            logger.info(f"Ответ отправлен напрямую в чат {tg_chat_id}")
        else:
            save_result_to_redis(tg_chat_id, llm_response)
            logger.info(f"Результат сохранён в Redis для чата {tg_chat_id}")
        
        return result
        
    except OpenRouterNetworkError as e:
        # Проблемы с сетью - повторяем задачу
        logger.warning(f"Сетевая ошибка OpenRouter для чата {tg_chat_id}: {e}")
        raise self.retry(exc=e, countdown=60)
        
    except OpenRouterAPIError as e:
        # Ошибка API - не повторяем, сообщаем пользователю
        error_msg = f"Ошибка OpenRouter API: {e.message}"
        logger.error(error_msg)
        
        error_result = {
            "success": False,
            "response": None,
            "error": error_msg,
            "tg_chat_id": tg_chat_id,
        }
        
        if send_directly:
            send_telegram_message(tg_chat_id, f"❌ {error_msg}")
        else:
            save_result_to_redis(tg_chat_id, f"Ошибка: {error_msg}", is_error=True)
        
        return error_result
        
    except OpenRouterError as e:
        # Другие ошибки OpenRouter
        error_msg = f"Ошибка при запросе к LLM: {str(e)}"
        logger.error(error_msg)
        
        error_result = {
            "success": False,
            "response": None,
            "error": error_msg,
            "tg_chat_id": tg_chat_id,
        }
        
        if send_directly:
            send_telegram_message(tg_chat_id, f"❌ {error_msg}")
        else:
            save_result_to_redis(tg_chat_id, f"Ошибка: {error_msg}", is_error=True)
        
        return error_result
        
    except Exception as e:
        # Непредвиденная ошибка
        error_msg = f"Непредвиденная ошибка: {str(e)}"
        logger.error(error_msg)
        
        error_result = {
            "success": False,
            "response": None,
            "error": error_msg,
            "tg_chat_id": tg_chat_id,
        }
        
        if send_directly:
            send_telegram_message(tg_chat_id, f"❌ Извините, произошла ошибка. Попробуйте позже.")
        else:
            save_result_to_redis(tg_chat_id, f"Ошибка: {error_msg}", is_error=True)
        
        return error_result


def send_telegram_message(chat_id: int, text: str) -> None:
    """
    Отправляет сообщение в Telegram через Bot API.
    """
    # URL для отправки сообщения
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Сообщение отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение в чат {chat_id}: {e}")
        raise


def save_result_to_redis(chat_id: int, response_text: str, is_error: bool = False) -> None:
    """
    Сохраняет результат запроса в Redis для последующей отправки ботом.
    """
    import asyncio
    
    async def _save():
        redis_client = await get_redis()
        key = f"telegram:response:{chat_id}"
        
        await redis_client.set(key, response_text, ex=300)
        
        if is_error:
            error_key = f"telegram:response:{chat_id}:error"
            await redis_client.set(error_key, "true", ex=300)
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_save())
        else:
            loop.run_until_complete(_save())
    except RuntimeError:
        asyncio.run(_save())


@celery_app.task(name="check_llm_health")
def check_llm_health() -> Dict[str, Any]:
    """Задача для проверки доступности OpenRouter API."""
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{settings.OPENROUTER_BASE_URL}/auth/key",
                headers=headers,
            )
            
            if response.status_code == 200:
                return {"status": "healthy", "message": "OpenRouter API доступен"}
            else:
                return {"status": "unhealthy", "message": f"Ошибка: {response.status_code}"}
                
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
