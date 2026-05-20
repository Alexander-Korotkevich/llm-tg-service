import pytest
from httpx import AsyncClient

class TestAuthAPI:
    """Интеграционные тесты API аутентификации"""
    
    async def test_register_success(self, client: AsyncClient):
        """Тест успешной регистрации пользователя"""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepass123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "role" in data
        assert "created_at" in data
        assert "password" not in data
        assert "password_hash" not in data
    
    async def test_register_duplicate_email_returns_409(self, client: AsyncClient, test_user_data):
        """Тест повторной регистрации с тем же email - ожидаем 409"""
        # Первая регистрация
        response1 = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Вторая регистрация с тем же email
        response2 = await client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()
    
    async def test_register_invalid_email_returns_422(self, client: AsyncClient):
        """Тест регистрации с невалидным email"""
        user_data = {
            "email": "invalid-email",
            "password": "password123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    async def test_register_weak_password_returns_422(self, client: AsyncClient):
        """Тест регистрации со слабым паролем (< 6 символов)"""
        user_data = {
            "email": "user@example.com",
            "password": "123"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    async def test_login_success(self, client: AsyncClient, test_user_data):
        """Тест успешного входа с получением токена"""
        # Сначала регистрируем пользователя
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Пытаемся войти
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,  # form-data для OAuth2PasswordRequestForm
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    async def test_login_wrong_password_returns_401(self, client: AsyncClient, test_user_data):
        """Тест входа с неверным паролем - ожидаем 401"""
        # Сначала регистрируем пользователя
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Пытаемся войти с неверным паролем
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    async def test_login_nonexistent_user_returns_401(self, client: AsyncClient):
        """Тест входа с несуществующим пользователем - ожидаем 401"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
    
    async def test_me_with_valid_token_returns_user(self, client: AsyncClient, test_user_data):
        """Тест получения информации о пользователе с валидным токеном"""
        # Регистрируем и логинимся
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token = login_response.json()["access_token"]
        
        # Запрашиваем /me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "role" in data
        assert "created_at" in data
    
    async def test_me_without_token_returns_401(self, client: AsyncClient):
        """Тест доступа к /me без токена - ожидаем 401"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "missing" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()
    
    async def test_me_with_invalid_token_returns_401(self, client: AsyncClient):
        """Тест доступа к /me с неверным токеном - ожидаем 401"""
        invalid_token = "invalid.token.here"
        
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        assert response.status_code == 401
    
    async def test_me_with_expired_token_returns_401(self, client: AsyncClient, test_user_data):
        """Тест доступа к /me с просроченным токеном - ожидаем 401"""
        from unittest.mock import patch
        from app.core.config import settings
        
        # Регистрируем пользователя
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Патчим время жизни токена на отрицательное и логинимся
        with patch.object(settings, 'access_token_expire_minutes', -1):
            login_response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user_data["email"],
                    "password": test_user_data["password"]
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # Может вернуть 200, но токен будет просрочен
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                
                # Пытаемся использовать просроченный токен
                response = await client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                # Должен вернуть 401
                assert response.status_code == 401
    
    async def test_full_auth_flow(self, client: AsyncClient):
        """Полный сценарий аутентификации: регистрация -> логин -> получение профиля"""
        user_email = "flow@example.com"
        user_password = "flowpassword123"
        
        # 1. Регистрация
        register_response = await client.post("/api/v1/auth/register", json={
            "email": user_email,
            "password": user_password
        })
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == user_email
        
        # 2. Логин
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": user_email,
                "password": user_password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        token = token_data["access_token"]
        
        # 3. Получение профиля
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        profile = me_response.json()
        assert profile["email"] == user_email
        assert profile["id"] == user_data["id"]
        assert profile["role"] == "user"
