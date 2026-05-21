import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """
    Базовое исключение для ошибок OpenRouter.
    """
    pass


class OpenRouterNetworkError(OpenRouterError):
    """
    Ошибка сети при подключении к OpenRouter.
    """
    pass


class OpenRouterAPIError(OpenRouterError):
    """
    Ошибка API OpenRouter (статус ответа не 200).
    """
    def __init__(self, status_code: int, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"OpenRouter API ошибка {status_code}: {message}")


class OpenRouterClient:
    """
    Клиент для взаимодействия с OpenRouter API.
    Поддерживает синхронные и асинхронные запросы.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Инициализация клиента OpenRouter.
        
        Аргументы:
            base_url: Базовый URL API (по умолчанию из настроек)
            api_key: API ключ (по умолчанию из настроек)
            timeout: Таймаут запроса в секундах
        """
        self.base_url = base_url or settings.OPENROUTER_BASE_URL
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.timeout = timeout
        self.model = settings.OPENROUTER_MODEL
        
        # Заголовки, общие для всех запросов
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-Title": settings.OPENROUTER_APP_NAME,
        }
    
    def _build_payload(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Формирует payload для запроса к /chat/completions.
        
        Аргументы:
            prompt: Запрос пользователя
            system_prompt: Системный промпт (опционально)
            temperature: Креативность (0-1)
            max_tokens: Максимальная длина ответа
            **kwargs: Дополнительные параметры
            
        Возвращает:
            Dict[str, Any]: Сформированный payload
        """
        messages = []
        
        # Добавляем системный промпт, если указан
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Добавляем запрос пользователя
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Формируем полный payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Добавляем дополнительные параметры, если они есть
        payload.update(kwargs)
        
        return payload
    
    def _parse_response(self, response_data: Dict[str, Any]) -> str:
        """
        Извлекает текст ответа из ответа OpenRouter.
        
        Аргументы:
            response_data: JSON ответа от OpenRouter
            
        Возвращает:
            str: Текст ответа LLM
            
        Исключения:
            OpenRouterError: Если ответ имеет неожиданный формат
        """
        try:
            # Проверяем наличие поля choices
            if "choices" not in response_data:
                raise OpenRouterError("В ответе отсутствует поле 'choices'")
            
            choices = response_data["choices"]
            if not choices or len(choices) == 0:
                raise OpenRouterError("Поле 'choices' пустое")
            
            # Извлекаем сообщение из первого выбора
            first_choice = choices[0]
            if "message" not in first_choice:
                raise OpenRouterError("В ответе отсутствует поле 'message'")
            
            message = first_choice["message"]
            if "content" not in message:
                raise OpenRouterError("В сообщении отсутствует поле 'content'")
            
            content = message["content"]
            if not content or not isinstance(content, str):
                raise OpenRouterError("Содержимое ответа пустое или имеет неверный тип")
            
            return content.strip()
            
        except KeyError as e:
            logger.error(f"Ошибка парсинга ответа OpenRouter: отсутствует ключ {e}")
            raise OpenRouterError(f"Неожиданный формат ответа от OpenRouter: отсутствует {e}")
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа OpenRouter: {e}")
            raise OpenRouterError(f"Ошибка обработки ответа: {str(e)}")
    
    def chat_completion_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Синхронный запрос к OpenRouter API (для использования в Celery).
        
        Аргументы:
            prompt: Запрос пользователя
            system_prompt: Системный промпт (опционально)
            temperature: Креативность (0-1)
            max_tokens: Максимальная длина ответа
            
        Возвращает:
            str: Текст ответа LLM
            
        Исключения:
            OpenRouterNetworkError: При проблемах с сетью
            OpenRouterAPIError: При ошибке API (статус не 200)
            OpenRouterError: При других ошибках
        """
        
        # Формируем payload
        payload = self._build_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        url = f"{self.base_url}/chat/completions"
        
        logger.info(f"Отправка запроса к OpenRouter. Модель: {self.model}, температура: {temperature}")
        
        try:
            # Выполняем синхронный запрос
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                )
                
                # Проверяем статус ответа
                if response.status_code != 200:
                    # Пытаемся извлечь сообщение об ошибке из ответа
                    error_message = f"HTTP {response.status_code}"
                    error_details = None
                    
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_message = error_data["error"].get("message", error_message)
                            error_details = error_data["error"]
                    except:
                        # Если не удалось распарсить JSON, используем текст ответа
                        error_message = response.text[:200] if response.text else error_message
                    
                    logger.error(f"OpenRouter вернул ошибку: {error_message}")
                    raise OpenRouterAPIError(
                        status_code=response.status_code,
                        message=error_message,
                        details=error_details
                    )
                
                # Парсим успешный ответ
                response_data = response.json()
                result = self._parse_response(response_data)
                
                logger.info(f"Успешный ответ от OpenRouter. Длина ответа: {len(result)} символов")
                return result
                
        except httpx.TimeoutException as e:
            logger.error(f"Таймаут при запросе к OpenRouter: {e}")
            raise OpenRouterNetworkError(f"Таймаут соединения с OpenRouter ({self.timeout} сек)")
            
        except httpx.ConnectError as e:
            logger.error(f"Ошибка подключения к OpenRouter: {e}")
            raise OpenRouterNetworkError(f"Не удалось подключиться к OpenRouter: {str(e)}")
            
        except httpx.RequestError as e:
            logger.error(f"Ошибка при запросе к OpenRouter: {e}")
            raise OpenRouterNetworkError(f"Ошибка сети при запросе к OpenRouter: {str(e)}")
            
        except OpenRouterError:
            # Пробрасываем дальше уже обработанные ошибки
            raise
            
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при запросе к OpenRouter: {e}")
            raise OpenRouterError(f"Непредвиденная ошибка: {str(e)}")
    
    async def chat_completion_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Асинхронный запрос к OpenRouter API (для использования в FastAPI).
        
        Аргументы:
            prompt: Запрос пользователя
            system_prompt: Системный промпт (опционально)
            temperature: Креативность (0-1)
            max_tokens: Максимальная длина ответа
            
        Возвращает:
            str: Текст ответа LLM
            
        Исключения:
            OpenRouterNetworkError: При проблемах с сетью
            OpenRouterAPIError: При ошибке API (статус не 200)
            OpenRouterError: При других ошибках
        """
        
        # Формируем payload
        payload = self._build_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        url = f"{self.base_url}/chat/completions"
        
        logger.info(f"Асинхронный запрос к OpenRouter. Модель: {self.model}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                )
                
                # Проверяем статус ответа
                if response.status_code != 200:
                    error_message = f"HTTP {response.status_code}"
                    error_details = None
                    
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_message = error_data["error"].get("message", error_message)
                            error_details = error_data["error"]
                    except:
                        error_message = response.text[:200] if response.text else error_message
                    
                    logger.error(f"OpenRouter вернул ошибку: {error_message}")
                    raise OpenRouterAPIError(
                        status_code=response.status_code,
                        message=error_message,
                        details=error_details
                    )
                
                # Парсим успешный ответ
                response_data = response.json()
                result = self._parse_response(response_data)
                
                logger.info(f"Успешный асинхронный ответ от OpenRouter")
                return result
                
        except httpx.TimeoutException as e:
            logger.error(f"Таймаут при асинхронном запросе: {e}")
            raise OpenRouterNetworkError(f"Таймаут соединения с OpenRouter ({self.timeout} сек)")
            
        except httpx.ConnectError as e:
            logger.error(f"Ошибка подключения при асинхронном запросе: {e}")
            raise OpenRouterNetworkError(f"Не удалось подключиться к OpenRouter: {str(e)}")
            
        except httpx.RequestError as e:
            logger.error(f"Ошибка при асинхронном запросе: {e}")
            raise OpenRouterNetworkError(f"Ошибка сети: {str(e)}")
            
        except OpenRouterError:
            raise
            
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при асинхронном запросе: {e}")
            raise OpenRouterError(f"Непредвиденная ошибка: {str(e)}")


# Создаём глобальный экземпляр клиента (для удобства)
_default_client = None


def get_openrouter_client() -> OpenRouterClient:
    """
    Возвращает глобальный экземпляр клиента OpenRouter.
    
    Возвращает:
        OpenRouterClient: Экземпляр клиента
    """
    global _default_client
    if _default_client is None:
        _default_client = OpenRouterClient()
    return _default_client


# Упрощённые функции для вызова
def chat_completion_sync(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> str:
    """
    Упрощённая синхронная функция для запроса к OpenRouter.
    
    Аргументы:
        prompt: Запрос пользователя
        system_prompt: Системный промпт (опционально)
        temperature: Креативность (0-1)
        max_tokens: Максимальная длина ответа
        
    Возвращает:
        str: Текст ответа LLM
    """
    client = get_openrouter_client()
    return client.chat_completion_sync(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def chat_completion_async(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> str:
    """
    Упрощённая асинхронная функция для запроса к OpenRouter.
    
    Аргументы:
        prompt: Запрос пользователя
        system_prompt: Системный промпт (опционально)
        temperature: Креативность (0-1)
        max_tokens: Максимальная длина ответа
        
    Возвращает:
        str: Текст ответа LLM
    """
    client = get_openrouter_client()
    return await client.chat_completion_async(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
