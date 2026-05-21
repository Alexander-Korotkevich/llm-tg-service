import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from app.core.jwt import decode_and_validate, JWTValidationError


class TestJWTValidation:
    
    def test_expired_token_raises_error(self):
        """Тест: просроченный токен должен вызывать ошибку."""
        test_secret = "test_secret_key_for_jwt_validation"
        
        now = datetime.now()
        expired_time = int((now - timedelta(minutes=10)).timestamp())
        
        payload = {
            "sub": "test_user",
            "exp": expired_time,
            "iat": int((now - timedelta(minutes=20)).timestamp()),
        }
        
        token = jwt.encode(payload, test_secret, algorithm="HS256")
        
        original_secret = settings.JWT_SECRET
        settings.JWT_SECRET = test_secret
        
        try:
            with pytest.raises(JWTValidationError) as exc_info:
                decode_and_validate(token)
            
            error_message = str(exc_info.value).lower()
            assert "истёк" in error_message or "expired" in error_message
        finally:
            settings.JWT_SECRET = original_secret
    
    def test_valid_token_passes(self):
        """Тест: валидный токен проходит проверку."""
        now = datetime.now()
        valid_time = int((now + timedelta(hours=1)).timestamp())
        issued_time = int(now.timestamp())
        
        payload = {
            "sub": "test_user",
            "exp": valid_time,
            "iat": issued_time,
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
        
        result = decode_and_validate(token)
        assert result["sub"] == "test_user"
    
    def test_invalid_token_raises_error(self):
        """Тест: неверный токен вызывает ошибку."""
        with pytest.raises(JWTValidationError):
            decode_and_validate("invalid.token.here")
    
    def test_empty_token_raises_error(self):
        """Тест: пустой токен вызывает ошибку."""
        with pytest.raises(JWTValidationError):
            decode_and_validate("")
    
    def test_none_token_raises_error(self):
        """Тест: None вызывает ошибку."""
        with pytest.raises(JWTValidationError):
            decode_and_validate(None)
