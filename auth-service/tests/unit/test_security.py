from app.core.security import hash_password, verify_password

class TestPasswordHashing:
    """Тесты для хеширования паролей"""
    
    def test_hash_password_returns_different_string(self):
        """Проверка, что хеш не равен исходному паролю"""
        password = "my_secure_password123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_returns_different_hash_for_same_password(self):
        """Проверка, что один и тот же пароль дает разные хеши (из-за соли)"""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
    
    def test_verify_password_correct_password_returns_true(self):
        """Проверка, что правильный пароль проходит верификацию"""
        password = "correct_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect_password_returns_false(self):
        """Проверка, что неправильный пароль не проходит верификацию"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty_string(self):
        """Проверка с пустым паролем"""
        password = ""
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is True
        assert verify_password("not_empty", hashed) is False
    
    def test_verify_password_long_password(self):
        """Проверка с длинным паролем (в рамках лимита bcrypt)"""
        # bcrypt обычно обрабатывает только первые 72 байта
        # Используем пароль длиной 70 символов, чтобы быть в пределах лимита
        password = "a" * 70
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        # Немного измененный пароль в пределах первых 72 символов
        assert verify_password(password[:-1] + "b", hashed) is False

    def test_verify_password_very_long_password(self):
        """Проверка с очень длинным паролем (bcrypt обрезает до 72 байт)"""
        # Создаем два разных пароля, которые обрезаются до одинаковых 72 байт
        long_password = "a" * 100
        slightly_different = "a" * 71 + "b" + "a" * 28
        
        hashed_long = hash_password(long_password)
        hashed_diff = hash_password(slightly_different)
        
        # Оба хеша должны быть разными, т.к. пароли разные даже после обрезки
        # Проверяем, что оригинальный пароль верифицируется
        assert verify_password(long_password, hashed_long) is True
        
        # Измененный пароль (обрезанный до 72 символов) может оказаться таким же
        # как и оригинальный из-за особенностей bcrypt, поэтому просто проверяем,
        # что пароль не верифицируется с чужим хешем
        assert verify_password(long_password, hashed_diff) is False
