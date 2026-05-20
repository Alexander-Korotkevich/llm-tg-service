import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from app.core.security import create_access_token, decode_token
from app.core.config import settings

class TestJWTGeneration:
    """Тесты для создания и валидации JWT токенов"""
    
    def test_create_access_token_contains_required_fields(self):
        """Проверка, что токен содержит все обязательные поля: sub, role, iat, exp"""
        user_id = 123
        role = "admin"
        
        token = create_access_token(user_id, role)
        payload = decode_token(token)
        
        assert payload is not None
        assert "sub" in payload
        assert "role" in payload
        assert "iat" in payload
        assert "exp" in payload
        
        assert payload["sub"] == str(user_id)
        assert payload["role"] == role
    
    def test_create_access_token_iat_is_current_time(self):
        """Проверка, что iat (issued at) соответствует текущему времени"""
        user_id = 456
        role = "user"
        
        before = datetime.now(timezone.utc)
        token = create_access_token(user_id, role)
        after = datetime.now(timezone.utc)
        
        payload = decode_token(token)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        
        # Убираем микросекунды для корректного сравнения
        before_floor = before.replace(microsecond=0)
        iat_floor = iat.replace(microsecond=0)
        after_ceil = after.replace(microsecond=0)
        
        assert before_floor <= iat_floor <= after_ceil
    
    def test_create_access_token_exp_is_correct(self):
        """Проверка, что exp (expiration) установлено правильно"""
        user_id = 789
        role = "user"
        
        token = create_access_token(user_id, role)
        payload = decode_token(token)
        
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        expected_exp = iat + timedelta(minutes=settings.access_token_expire_minutes)
        
        # Допускаем небольшую погрешность в 1 секунду
        assert abs((exp - expected_exp).total_seconds()) < 1
    
    def test_decode_token_valid_token_returns_payload(self):
        """Проверка, что валидный токен корректно декодируется"""
        user_id = 999
        role = "moderator"
        
        token = create_access_token(user_id, role)
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["role"] == role
    
    def test_decode_token_invalid_token_returns_none(self):
        """Проверка, что невалидный токен возвращает None"""
        invalid_token = "invalid.token.here"
        
        payload = decode_token(invalid_token)
        
        assert payload is None
    
    def test_decode_token_tampered_token_returns_none(self):
        """Проверка, что поддельный токен не проходит валидацию"""
        user_id = 123
        role = "user"
        
        valid_token = create_access_token(user_id, role)
        # Подделываем токен (меняем последний символ)
        tampered_token = valid_token[:-1] + ("x" if valid_token[-1] != "x" else "y")
        
        payload = decode_token(tampered_token)
        
        assert payload is None
    
    def test_decode_token_missing_sub_returns_none(self):
        """Проверка, что токен без sub не валиден"""
        from jose import jwt
        payload = {"role": "user", "iat": datetime.now(timezone.utc)}
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
        
        result = decode_token(token)
        
        assert result is None
    
    def test_decode_token_missing_role_returns_none(self):
        """Проверка, что токен без role не валиден"""
        from jose import jwt
        payload = {"sub": "123", "iat": datetime.now(timezone.utc)}
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
        
        result = decode_token(token)
        
        assert result is None
    
    @patch('app.core.security.settings.access_token_expire_minutes', -1)
    def test_decode_token_expired_token_returns_none(self):
        """Проверка, что просроченный токен возвращает None"""
        user_id = 123
        role = "user"
        
        # Токен с отрицательным временем жизни (уже просрочен)
        token = create_access_token(user_id, role)
        
        payload = decode_token(token)
        
        assert payload is None
