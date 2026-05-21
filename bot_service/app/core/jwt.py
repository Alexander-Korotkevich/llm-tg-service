from jose import jwt, JWTError, ExpiredSignatureError
from typing import Dict, Any
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
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": False,  # Отключаем проверку iat для упрощения
                "verify_aud": False,
            }
        )
        
        # Дополнительная проверка: наличие обязательных полей
        if "sub" not in payload:
            raise JWTValidationError("В токене отсутствует идентификатор пользователя (sub)")
        
        return payload
        
    except ExpiredSignatureError:
        # Эта ошибка должна обрабатываться первой!
        raise JWTValidationError("Срок действия токена истёк")
    except JWTError as e:
        error_message = str(e).lower()
        if "signature" in error_message:
            raise JWTValidationError("Неверная подпись токена")
        elif "expired" in error_message:
            raise JWTValidationError("Срок действия токена истёк")
        else:
            raise JWTValidationError(f"Ошибка валидации JWT: {str(e)}")
    except Exception as e:
        raise JWTValidationError(f"Непредвиденная ошибка при проверке токена: {str(e)}")


# Вспомогательная функция для получения ID пользователя из токена
def get_user_id_from_token(token: str) -> str:
    """
    Извлекает user_id (sub) из валидного JWT токена.
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
    """
    return decode_and_validate(token)
