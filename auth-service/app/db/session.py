from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.db.base import Base

# Создание асинхронного engine
engine = create_async_engine(
    settings.database_url,
    echo=True,  # В продакшене лучше установить False
    future=True,
)

# Создание фабрики асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncSession:
    """
    Dependency для получения сессии базы данных.
    Используется в эндпоинтах FastAPI.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # коммитим транзакцию после успешного выполнения
            await session.commit()
        except Exception:
            # При ошибке откатываем
            await session.rollback()
            raise
        finally:
            # Всегда закрываем сессию
            await session.close()

async def init_db():
    """Инициализация базы данных: создание всех таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db():
    """Удаление всех таблиц (для тестов)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
