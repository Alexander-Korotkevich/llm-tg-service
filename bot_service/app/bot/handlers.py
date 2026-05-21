import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.infra.redis import get_redis
from app.core.jwt import decode_and_validate, JWTValidationError
from app.tasks.llm_tasks import llm_request

logger = logging.getLogger(__name__)

# Создаём роутер для регистрации хендлеров
router = Router()


# Определяем состояния FSM (если потребуется для многошаговых действий)
class AuthStates(StatesGroup):
    """Состояния для процесса авторизации."""
    waiting_for_token = State()  # Ожидание ввода JWT токена


# --------------------------------------------------------------------
# Обработчик команды /start
# --------------------------------------------------------------------
@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Приветственное сообщение и инструкция по авторизации.
    """
    welcome_text = (
        "👋 <b>Добро пожаловать в Bot Service!</b>\n\n"
        "Я бот с интеграцией искусственного интеллекта.\n"
        "Для использования моих возможностей необходимо авторизоваться.\n\n"
        "🔑 <b>Как авторизоваться:</b>\n"
        "1. Перейдите в Auth Service и получите JWT токен\n"
        "2. Отправьте мне токен командой:\n"
        "   <code>/token ваш_jwt_токен</code>\n\n"
        "✅ После успешной авторизации вы сможете задавать мне любые вопросы.\n"
        "❌ Если токен неверный или истёк - я попрошу вас авторизоваться заново.\n\n"
        "📌 <i>Пример:</i>\n"
        "<code>/token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...</code>"
    )
    await message.answer(welcome_text)


# --------------------------------------------------------------------
# Обработчик команды /token - сохранение JWT токена
# --------------------------------------------------------------------
@router.message(Command("token"))
async def cmd_save_token(message: Message):
    """
    Сохраняет JWT токен пользователя в Redis.
    Ожидает токен как аргумент команды.
    """
    # Извлекаем аргументы команды
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer(
            "❌ <b>Ошибка:</b> Вы не передали JWT токен.\n\n"
            "Правильный формат:\n"
            "<code>/token ваш_jwt_токен</code>\n\n"
            "Получить токен можно в Auth Service."
        )
        return
    
    jwt_token = parts[1].strip()
    telegram_id = str(message.from_user.id)
    
    # Сначала проверяем валидность токена
    try:
        payload = decode_and_validate(jwt_token)
        user_id_from_token = payload.get("sub")
        
        logger.info(f"Пользователь {telegram_id} пытается сохранить токен для user_id={user_id_from_token}")
        
    except JWTValidationError as e:
        await message.answer(
            f"❌ <b>Неверный токен!</b>\n\n"
            f"Ошибка: {e.message}\n\n"
            f"Пожалуйста, получите новый токен в Auth Service и повторите попытку.\n"
            f"Команда: <code>/token новый_токен</code>"
        )
        return
    
    # Сохраняем токен в Redis
    try:
        redis_client = await get_redis()
        key = f"telegram:{telegram_id}:jwt"
        
        # Сохраняем токен с TTL (например, на 7 дней)
        await redis_client.set(key, jwt_token, ex=604800)  # 7 дней
        
        # Также сохраняем user_id из токена для быстрого доступа
        user_id_key = f"telegram:{telegram_id}:user_id"
        await redis_client.set(user_id_key, payload.get("sub"), ex=604800)
        
        await message.answer(
            "✅ <b>Авторизация успешна!</b>\n\n"
            f"Ваш JWT токен сохранён.\n"
            f"Идентификатор пользователя: <code>{payload.get('sub')}</code>\n\n"
            "Теперь вы можете задавать мне любые вопросы.\n"
            "Просто напишите сообщение, и я отвечу с помощью искусственного интеллекта.\n\n"
            "⏳ <i>Обработка запроса может занять несколько секунд.</i>"
        )
        
        logger.info(f"JWT токен сохранён для Telegram user {telegram_id}")
        
    except Exception as e:
        logger.error(f"Ошибка сохранения токена в Redis: {e}")
        await message.answer(
            "❌ <b>Техническая ошибка</b>\n\n"
            "Не удалось сохранить токен. Пожалуйста, попробуйте позже."
        )


# --------------------------------------------------------------------
# Обработчик команды /login - альтернативный способ авторизации
# --------------------------------------------------------------------
@router.message(Command("login"))
async def cmd_login(message: Message, state: FSMContext):
    """
    Запускает процесс авторизации с ожиданием ввода токена.
    """
    await state.set_state(AuthStates.waiting_for_token)
    await message.answer(
        "🔐 <b>Авторизация через Auth Service</b>\n\n"
        "Пожалуйста, отправьте мне ваш JWT токен одним сообщением.\n\n"
        "Токен можно получить в Auth Service.\n"
        "Для отмены операции отправьте /cancel"
    )


@router.message(AuthStates.waiting_for_token)
async def process_token_input(message: Message, state: FSMContext):
    """
    Обрабатывает ввод JWT токена в состоянии ожидания.
    """
    jwt_token = message.text.strip()
    telegram_id = str(message.from_user.id)
    
    # Проверяем валидность токена
    try:
        payload = decode_and_validate(jwt_token)
        
    except JWTValidationError as e:
        await message.answer(
            f"❌ <b>Неверный токен!</b>\n\n"
            f"Ошибка: {e.message}\n\n"
            f"Попробуйте снова командой /login или получите новый токен в Auth Service."
        )
        await state.clear()
        return
    
    # Сохраняем токен
    try:
        redis_client = await get_redis()
        key = f"telegram:{telegram_id}:jwt"
        await redis_client.set(key, jwt_token, ex=604800)
        
        user_id_key = f"telegram:{telegram_id}:user_id"
        await redis_client.set(user_id_key, payload.get("sub"), ex=604800)
        
        await message.answer(
            "✅ <b>Авторизация успешна!</b>\n\n"
            f"Идентификатор пользователя: <code>{payload.get('sub')}</code>\n\n"
            "Теперь вы можете задавать вопросы."
        )
        
        logger.info(f"JWT токен сохранён через /login для Telegram user {telegram_id}")
        
    except Exception as e:
        logger.error(f"Ошибка сохранения токена: {e}")
        await message.answer("❌ Техническая ошибка при сохранении токена.")
    
    finally:
        await state.clear()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Отменяет текущую операцию (например, ожидание ввода токена).
    """
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("✅ Операция отменена.")
    else:
        await message.answer("Нет активных операций для отмены.")


# --------------------------------------------------------------------
# Обработчик текстовых сообщений (основная логика)
# --------------------------------------------------------------------
@router.message(F.text)
async def handle_text_message(message: Message):
    """
    Обрабатывает обычные текстовые сообщения (не команды).
    """
    # Проверяем, что это не команда
    if message.text.startswith('/'):
        return  # Игнорируем команды
    
    telegram_id = str(message.from_user.id)
    user_message = message.text.strip()

    
    if not user_message:
        await message.answer("Пожалуйста, отправьте текст сообщения.")
        return
    
    # Получаем JWT токен из Redis
    try:
        redis_client = await get_redis()
        key = f"telegram:{telegram_id}:jwt"
        jwt_token = await redis_client.get(key)
        
        if not jwt_token:
            # Токен не найден
            await message.answer(
                "🔒 <b>Доступ запрещён</b>\n\n"
                "У вас нет активной сессии.\n"
                "Пожалуйста, авторизуйтесь через Auth Service и отправьте токен командой:\n"
                "<code>/token ваш_jwt_токен</code>\n\n"
                "Или используйте команду /login для пошаговой авторизации.\n\n"
                "Получить токен можно в Auth Service."
            )
            return
        
        # Валидируем токен
        try:
            payload = decode_and_validate(jwt_token)
            user_id = payload.get("sub")
            logger.info(f"Токен валиден для пользователя {user_id} (Telegram: {telegram_id})")
            
        except JWTValidationError as e:
            # Токен невалидный или истёк - удаляем его из Redis
            await redis_client.delete(key)
            await redis_client.delete(f"telegram:{telegram_id}:user_id")
            
            await message.answer(
                f"🔒 <b>Срок действия токена истёк или он неверный</b>\n\n"
                f"Ошибка: {e.message}\n\n"
                "Пожалуйста, получите новый токен в Auth Service и авторизуйтесь заново командой:\n"
                "<code>/token новый_токен</code>"
            )
            return
        
    except Exception as e:
        logger.error(f"Ошибка при работе с Redis или JWT: {e}")
        await message.answer(
            "❌ <b>Техническая ошибка</b>\n\n"
            "Не удалось проверить авторизацию. Пожалуйста, попробуйте позже."
        )
        return
    
    # Отправляем задачу в Celery
    try:
        # Отправляем асинхронную задачу
        task = llm_request.delay(
            tg_chat_id=message.chat.id,
            prompt=user_message,
            user_jwt=jwt_token,
            send_directly=True  # Ответ отправляется прямо из воркера
        )
        
        logger.info(f"Задача {task.id} отправлена в Celery для пользователя {telegram_id}")
        
        # Уведомляем пользователя, что запрос принят в обработку
        await message.answer(
            "🤔 <b>Запрос принят</b>\n\n"
            "Я думаю над ответом... Обычно это занимает несколько секунд.\n"
            "Ответ придёт в этот чат, когда будет готов.\n\n"
            "<i>Вы можете продолжать задавать вопросы, они будут обработаны в очереди.</i>"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при отправке задачи в Celery: {e}")
        await message.answer(
            "❌ <b>Ошибка обработки запроса</b>\n\n"
            "Не удалось отправить запрос в очередь. Пожалуйста, попробуйте позже.\n"
            "Наша команда уже уведомлена о проблеме."
        )


# --------------------------------------------------------------------
# Обработчик команды /reset - сброс токена
# --------------------------------------------------------------------
@router.message(Command("reset"))
async def cmd_reset_token(message: Message):
    """
    Сбрасывает сохранённый JWT токен пользователя.
    """
    telegram_id = str(message.from_user.id)
    
    try:
        redis_client = await get_redis()
        key = f"telegram:{telegram_id}:jwt"
        user_id_key = f"telegram:{telegram_id}:user_id"
        
        # Проверяем, был ли токен
        jwt_token = await redis_client.get(key)
        
        if jwt_token:
            await redis_client.delete(key)
            await redis_client.delete(user_id_key)
            await message.answer(
                "✅ <b>Токен сброшен</b>\n\n"
                "Ваша сессия завершена. Чтобы снова использовать бота, авторизуйтесь заново:\n"
                "<code>/token ваш_jwt_токен</code>"
            )
            logger.info(f"Токен сброшен для Telegram user {telegram_id}")
        else:
            await message.answer(
                "ℹ️ <b>Активная сессия не найдена</b>\n\n"
                "У вас нет сохранённого токена.\n"
                "Используйте команду /token для авторизации."
            )
            
    except Exception as e:
        logger.error(f"Ошибка при сбросе токена: {e}")
        await message.answer("❌ Техническая ошибка при сбросе токена.")


# --------------------------------------------------------------------
# Обработчик команды /help - справка
# --------------------------------------------------------------------
@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Выводит справку по доступным командам.
    """
    help_text = (
        "<b>📚 Доступные команды:</b>\n\n"
        "/start - Приветственное сообщение\n"
        "/help - Эта справка\n\n"
        "<b>🔐 Авторизация:</b>\n"
        "/token &lt;JWT&gt; - Сохранить JWT токен\n"
        "/login - Пошаговая авторизация\n"
        "/reset - Сбросить токен (выйти из системы)\n\n"
        "<b>💬 Общение:</b>\n"
        "Просто отправьте любое текстовое сообщение\n"
        "Бот ответит с помощью искусственного интеллекта\n\n"
        "<b>ℹ️ Информация:</b>\n"
        "/cancel - Отменить текущую операцию\n\n"
        "<i>Токен можно получить в Auth Service</i>"
    )
    await message.answer(help_text)
