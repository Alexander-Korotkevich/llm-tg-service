from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.users import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
    InvalidTokenError,
    TokenExpiredError
)
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserPublic

class AuthUseCase:
    """Бизнес-логика аутентификации и управления пользователями"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def register(self, register_data: RegisterRequest) -> UserPublic:
        """
        Регистрация нового пользователя
        
        Args:
            register_data: Данные для регистрации (email, password)
            
        Returns:
            UserPublic: Публичные данные зарегистрированного пользователя
            
        Raises:
            UserAlreadyExistsError: Если пользователь с таким email уже существует
        """
        # Проверяем, существует ли пользователь с таким email
        existing_user = await self.user_repo.get_by_email(register_data.email)
        if existing_user:
            raise UserAlreadyExistsError(f"User with email {register_data.email} already exists")
        
        # Хешируем пароль
        password_hash = hash_password(register_data.password)
        
        # Создаем пользователя (роль по умолчанию "user")
        user = await self.user_repo.create(
            email=register_data.email,
            password_hash=password_hash,
            role="user"
        )
        
        # Возвращаем публичные данные
        return UserPublic(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at
        )
    
    async def login(self, email: str, password: str) -> str:
        """
        Аутентификация пользователя и выдача JWT токена
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            str: JWT токен доступа
            
        Raises:
            InvalidCredentialsError: Если пользователь не найден или пароль неверный
        """
        # Ищем пользователя по email
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        # Проверяем пароль
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        
        # Создаем JWT токен
        access_token = create_access_token(user_id=user.id, role=user.role)
        
        return access_token
    
    async def get_current_user(self, token: str) -> UserPublic:
        """
        Получение текущего пользователя по JWT токену
        
        Args:
            token: JWT токен
            
        Returns:
            UserPublic: Публичные данные текущего пользователя
            
        Raises:
            InvalidTokenError: Если токен невалидный
            TokenExpiredError: Если срок действия токена истек
            UserNotFoundError: Если пользователь не найден в БД
        """
        # Декодируем токен
        payload = decode_token(token)
        if not payload:
            raise InvalidTokenError("Invalid or malformed token")
        
        # Проверяем, что токен не истек (decode_token уже проверяет exp,
        # но для явной обработки добавим дополнительную проверку)
        from datetime import datetime, timezone
        exp = payload.get("exp")
        if exp:
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            if exp_datetime < datetime.now(timezone.utc):
                raise TokenExpiredError("Token has expired")
        
        # Извлекаем user_id из поля sub
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenError("Token missing user identifier")
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            raise InvalidTokenError("Invalid user identifier in token")
        
        # Ищем пользователя в БД
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        
        # Возвращаем публичные данные
        return UserPublic(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at
        )
    
    async def me(self, token: str) -> UserPublic:
        """
        Получение информации о текущем пользователе (алиас для get_current_user)
        
        Args:
            token: JWT токен
            
        Returns:
            UserPublic: Публичные данные текущего пользователя
        """
        return await self.get_current_user(token)
