from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Настройка контекста для bcrypt хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        str: Хеш пароля
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хешу
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хеш пароля из БД
        
    Returns:
        bool: True если пароль совпадает, False в противном случае
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int, role: str) -> str:
    """
    Создает JWT токен доступа
    
    Args:
        user_id: ID пользователя (будет в поле sub)
        role: Роль пользователя
        
    Returns:
        str: JWT токен
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "sub": str(user_id),  # subject - идентификатор пользователя
        "role": role,          # роль пользователя
        "iat": datetime.now(timezone.utc),  # issued at - время выдачи
        "exp": expire,         # expiration - время жизни
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_alg
    )
    
    return token

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Декодирует и валидирует JWT токен
    
    Args:
        token: JWT токен
        
    Returns:
        Optional[Dict[str, Any]]: Декодированный payload токена,
                                  None если токен невалидный
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg]
        )
        
        # Проверяем наличие обязательных полей
        if "sub" not in payload or "role" not in payload:
            return None
        
        # Проверяем время жизни (jwt.decode уже проверяет exp,
        # но дополнительно проверяем наличие)
        exp = payload.get("exp")
        if exp:
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            if exp_datetime < datetime.now(timezone.utc):
                return None
        
        return payload
        
    except JWTError:
        # Ошибка верификации подписи или неверный формат
        return None
