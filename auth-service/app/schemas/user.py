from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserPublic(BaseModel):
    """Публичное представление пользователя без конфиденциальной информации"""
    id: int = Field(..., description="ID пользователя", example=1)
    email: EmailStr = Field(..., description="Email пользователя", example="user@example.com")
    role: str = Field(..., description="Роль пользователя", example="user")
    created_at: datetime = Field(..., description="Дата и время регистрации")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "role": "user",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
        from_attributes = True  # Позволяет создавать схему из ORM модели

class UserWithToken(BaseModel):
    """Публичное представление пользователя вместе с токеном"""
    user: UserPublic
    access_token: str
    token_type: str = "bearer"
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "role": "user",
                    "created_at": "2024-01-01T12:00:00Z"
                },
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer"
            }
        }
