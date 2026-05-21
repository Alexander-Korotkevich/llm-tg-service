from celery import Celery
from app.core.config import settings


# Создаём экземпляр Celery приложения
celery_app = Celery(
    "bot_service",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.llm_tasks"],  # Явно указываем модуль с задачами
)


# Настройки Celery
celery_app.conf.update(
    # Сериализация
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Кодировка
    task_default_queue="celery",
    task_default_exchange="celery",
    task_default_routing_key="celery",
    
    # Таймауты и повторы
    task_time_limit=60,  # Максимальное время выполнения задачи (секунд)
    task_soft_time_limit=50,  # Мягкий таймаут (выбрасывает исключение)
    
    # Количество попыток при ошибке
    task_acks_late=True,  # Подтверждение задачи после выполнения
    task_reject_on_worker_lost=True,
    
    # Повторы при ошибках
    task_retry_policy={
        "max_retries": 3,
        "interval_start": 5,  # Начальная задержка (секунд)
        "interval_step": 10,   # Увеличение задержки при каждой попытке
        "interval_max": 60,    # Максимальная задержка
    },
    
    # Отслеживание результатов
    result_expires=3600,  # Результаты хранятся 1 час
    
    # Отслеживание задач
    task_track_started=True,
    task_send_sent_event=True,
    
    # Безопасность
    broker_connection_retry_on_startup=True,
)


# Автоматическое обнаружение задач из модуля app.tasks
celery_app.autodiscover_tasks(["app.tasks"])


# Декоратор для привязки задачи к приложению (для удобства)
def register_task(name=None, **options):
    """
    Вспомогательный декоратор для регистрации задач.
    Используется если нужно добавить дополнительные настройки к задаче.
    
    Пример:
        @register_task(name="my_task", time_limit=30)
        def my_task():
            pass
    """
    def decorator(func):
        task_name = name or f"app.tasks.{func.__name__}"
        return celery_app.task(func, name=task_name, **options)
    return decorator


# Функция для получения статуса задачи
def get_task_status(task_id: str) -> dict:
    """
    Получает статус выполнения задачи по ID.
    
    Аргументы:
        task_id: Идентификатор задачи
        
    Возвращает:
        dict: Статус и результат задачи
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.result
        elif result.failed():
            response["error"] = str(result.info)
    
    return response


# Функция для проверки здоровья Celery
def check_celery_health() -> bool:
    """
    Проверяет доступность Celery (проверяет соединение с брокером).
    
    Возвращает:
        bool: True если Celery доступен, иначе False
    """
    try:
        # Пытаемся отправить тестовое соединение
        inspect = celery_app.control.inspect()
        # Если получаем ответ, значит Celery доступен
        stats = inspect.stats()
        return stats is not None
    except Exception:
        return False
