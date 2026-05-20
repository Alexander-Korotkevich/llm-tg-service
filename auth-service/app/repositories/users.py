from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.db.models import User

class UserRepository:
    """Репозиторий для работы с пользователями в базе данных"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[User]: Объект пользователя или None если не найден
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Получить пользователя по email
        
        Args:
            email: Email пользователя
            
        Returns:
            Optional[User]: Объект пользователя или None если не найден
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, email: str, password_hash: str, role: str = "user") -> User:
        """
        Создать нового пользователя
        
        Args:
            email: Email пользователя
            password_hash: Хеш пароля
            role: Роль пользователя (по умолчанию "user")
            
        Returns:
            User: Созданный объект пользователя
        """
        user = User(
            email=email,
            password_hash=password_hash,
            role=role
        )
        self.db.add(user)
        await self.db.flush()  # Не коммитим, только получаем ID
        await self.db.refresh(user)
        return user
