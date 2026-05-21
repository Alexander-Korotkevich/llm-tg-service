from jose import jwt, JWTError
from typing import Dict, Any
from datetime import datetime
from app.core.config import settings


class JWTValidationError(Exception):
    """
    Исключение при ошибке валидации JWT токена.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def decode_and_validate(token: str) -> Dict[str, Any]:
    """
    Декодирует и проверяет JWT токен.
    
    Аргументы:
        token: JWT токен в формате строки
        
    Возвращает:
        Dict[str, Any]: Payload токена (данные пользователя)
        
    Исключения:
        JWTValidationError: Если токен невалидный, истёк или имеет неверную подпись
        
    Пример:
        try:
            payload = decode_and_validate(user_jwt)
            user_id = payload.get("sub")
        except JWTValidationError as e:
            # Токен неверный
            print(f"Ошибка: {e}")
    """
    
    # Проверяем, что токен не пустой
    if not token or not isinstance(token, str):
        raise JWTValidationError("Токен отсутствует или имеет неверный формат")
    
    try:
        # Декодируем и проверяем токен
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
            options={
                "verify_signature": True,      # Проверка подписи
                "verify_exp": True,            # Проверка срока действия
                "verify_iat": True,            # Проверка времени выдачи (опционально)
                "verify_aud": False,           # Не проверяем аудиторию (по умолчанию)
            }
        )
        
        # Дополнительная проверка: наличие обязательных полей
        if "sub" not in payload:
            raise JWTValidationError("В токене отсутствует идентификатор пользователя (sub)")
        
        # Проверяем, не истёк ли токен явно
        if "exp" in payload:
            exp_timestamp = payload["exp"]
            if isinstance(exp_timestamp, (int, float)):
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                if exp_datetime < datetime.now():
                    raise JWTValidationError("Срок действия токена истёк")
        
        return payload
        
    except JWTError as e:
        # Обрабатываем специфические ошибки jose
        error_message = str(e)
        
        if "signature" in error_message.lower():
            raise JWTValidationError("Неверная подпись токена")
        elif "expired" in error_message.lower():
            raise JWTValidationError("Срок действия токена истёк")
        elif "invalid" in error_message.lower():
            raise JWTValidationError("Неверный формат токена")
        else:
            raise JWTValidationError(f"Ошибка валидации JWT: {error_message}")
    
    except Exception as e:
        # Ловим любые другие ошибки
        raise JWTValidationError(f"Непредвиденная ошибка при проверке токена: {str(e)}")


# Вспомогательная функция для получения ID пользователя из токена
def get_user_id_from_token(token: str) -> str:
    """
    Извлекает user_id (sub) из валидного JWT токена.
    
    Аргументы:
        token: JWT токен
        
    Возвращает:
        str: Идентификатор пользователя
        
    Исключения:
        JWTValidationError: Если токен невалидный
    """
    payload = decode_and_validate(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise JWTValidationError("В токене отсутствует поле sub с идентификатором пользователя")
    
    return str(user_id)


# Вспомогательная функция для получения всех данных пользователя из токена
def get_user_payload(token: str) -> Dict[str, Any]:
    """
    Возвращает весь payload из валидного JWT токена.
    
    Аргументы:
        token: JWT токен
        
    Возвращает:
        Dict[str, Any]: Полные данные из токена
    """
    return decode_and_validate(token)
