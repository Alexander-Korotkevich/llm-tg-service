from pydantic import BaseModel, EmailStr, Field

# Request schemas

class RegisterRequest(BaseModel):
    """Схема для регистрации нового пользователя"""
    email: EmailStr = Field(..., description="Email пользователя", example="user@example.com")
    password: str = Field(
        ..., 
        min_length=6, 
        max_length=100,
        description="Пароль (минимум 6 символов)",
        example="securepassword123"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }

# Response schemas

class TokenResponse(BaseModel):
    """Схема ответа с JWT токеном"""
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field(default="bearer", description="Тип токена")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer"
            }
        }

class UserResponse(BaseModel):
    """Схема ответа с информацией о пользователе (без пароля)"""
    id: int
    email: EmailStr
    role: str
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "role": "user",
                "created_at": "2024-01-01T12:00:00"
            }
        }

class ErrorResponse(BaseModel):
    """Схема ответа с ошибкой"""
    detail: str = Field(..., description="Сообщение об ошибке")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials"
            }
        }
