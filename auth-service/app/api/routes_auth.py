from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.usecases.auth import AuthUseCase
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.api.deps import get_auth_uc, get_current_user
from app.core.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post(
    "/register",
    response_model=UserPublic,
    status_code=201,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя с указанными email и паролем"
)
async def register(
    register_data: RegisterRequest,
    auth_uc: AuthUseCase = Depends(get_auth_uc)
):
    """
    Регистрация пользователя
    
    - **email**: Email пользователя (должен быть уникальным)
    - **password**: Пароль (минимум 6 символов)
    """
    try:
        user = await auth_uc.register(register_data)
        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Аутентификация пользователя",
    description="Проверяет email и пароль, возвращает JWT токен"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_uc: AuthUseCase = Depends(get_auth_uc)
):
    """
    Вход пользователя
    
    - **username**: Email пользователя (поле username используется для email)
    - **password**: Пароль пользователя
    """
    try:
        access_token = await auth_uc.login(form_data.username, form_data.password)
        return TokenResponse(access_token=access_token, token_type="bearer")
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get(
    "/me",
    response_model=UserPublic,
    summary="Получение информации о текущем пользователе",
    description="Возвращает публичные данные пользователя по JWT токену"
)
async def get_me(
    current_user: UserPublic = Depends(get_current_user)
):
    """
    Получение информации о текущем пользователе
    
    Требует наличия JWT токена в заголовке Authorization: Bearer <token>
    """
    return current_user
