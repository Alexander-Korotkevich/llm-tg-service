from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class BaseHTTPException(HTTPException):
    """
    Базовое исключение для HTTP ошибок в Auth Service
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

# 4xx Client Errors

class UserAlreadyExistsError(BaseHTTPException):
    """Пользователь с таким email/username уже существует"""
    def __init__(self, detail: str = "User already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

class InvalidCredentialsError(BaseHTTPException):
    """Неверные учетные данные (email/пароль не совпадают)"""
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class InvalidTokenError(BaseHTTPException):
    """Неверный или поврежденный токен"""
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class TokenExpiredError(BaseHTTPException):
    """Срок действия токена истек"""
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class UserNotFoundError(BaseHTTPException):
    """Пользователь не найден в базе данных"""
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class PermissionDeniedError(BaseHTTPException):
    """Недостаточно прав для выполнения операции"""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

# Дополнительные полезные исключения

class DatabaseError(BaseHTTPException):
    """Ошибка при работе с базой данных"""
    def __init__(self, detail: str = "Database error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class MissingTokenError(BaseHTTPException):
    """Отсутствует токен авторизации"""
    def __init__(self, detail: str = "Missing authorization token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )
