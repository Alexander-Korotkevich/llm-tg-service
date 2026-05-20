from fastapi import APIRouter
from app.api.routes_auth import router as auth_router

# Создание основного роутера API
api_router = APIRouter(prefix="/api/v1")

# Подключение роутера аутентификации
api_router.include_router(auth_router)

# Здесь в будущем можно подключить другие роутеры:
# api_router.include_router(users_router)
# api_router.include_router(admin_router)

# Экспорт роутера для использования в main.py
router = api_router
