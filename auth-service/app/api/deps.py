from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.users import UserRepository
from app.usecases.auth import AuthUseCase
from app.core.security import decode_token
from app.core.exceptions import InvalidTokenError, TokenExpiredError, UserNotFoundError
from app.schemas.user import UserPublic

# Настройка безопасности для Bearer токенов
security = HTTPBearer(auto_error=False)

# Dependency для получения репозитория пользователей
async def get_users_repo(
    db: AsyncSession = Depends(get_db)
) -> UserRepository:
    """Получение репозитория пользователей"""
    return UserRepository(db)

# Dependency для получения UseCase аутентификации
async def get_auth_uc(
    db: AsyncSession = Depends(get_db)
) -> AuthUseCase:
    """Получение UseCase аутентификации"""
    return AuthUseCase(db)

# Dependency для получения текущего user_id из токена
async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> int:
    """
    Получение ID текущего пользователя из JWT токена
    
    Returns:
        int: ID пользователя
        
    Raises:
        InvalidTokenError: Если токен отсутствует, невалидный или поврежден
        TokenExpiredError: Если срок действия токена истек
    """
    if not credentials:
        raise InvalidTokenError("Missing or invalid authorization token")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise InvalidTokenError("Invalid or malformed token")
    
    # Проверяем срок действия
    from datetime import datetime, timezone
    exp = payload.get("exp")
    if exp:
        exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
        if exp_datetime < datetime.now(timezone.utc):
            raise TokenExpiredError("Token has expired")
    
    # Извлекаем user_id
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise InvalidTokenError("Token missing user identifier")
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise InvalidTokenError("Invalid user identifier in token")
    
    return user_id

# Dependency для получения текущего пользователя (объект UserPublic)
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_uc: AuthUseCase = Depends(get_auth_uc)
) -> UserPublic:
    """
    Получение текущего пользователя (объект UserPublic) из JWT токена
    
    Returns:
        UserPublic: Публичные данные текущего пользователя
        
    Raises:
        InvalidTokenError: Если токен отсутствует, невалидный или поврежден
        TokenExpiredError: Если срок действия токена истек
        UserNotFoundError: Если пользователь не найден
    """
    if not credentials:
        raise InvalidTokenError("Missing or invalid authorization token")
    
    token = credentials.credentials
    
    # Используем AuthUseCase для получения пользователя
    try:
        user = await auth_uc.get_current_user(token)
        return user
    except (InvalidTokenError, TokenExpiredError, UserNotFoundError):
        raise
    except Exception as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")

# Альтернативная зависимость для опционального получения текущего пользователя
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_uc: AuthUseCase = Depends(get_auth_uc)
) -> Optional[UserPublic]:
    """
    Получение текущего пользователя (опционально, не вызывает ошибку при отсутствии токена)
    
    Returns:
        Optional[UserPublic]: Публичные данные пользователя или None
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    try:
        user = await auth_uc.get_current_user(token)
        return user
    except (InvalidTokenError, TokenExpiredError, UserNotFoundError):
        return None
