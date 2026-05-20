from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Application settings
    app_name: str = Field(default="auth-service", alias="APP_NAME")
    env: str = Field(default="local", alias="ENV")
    
    # JWT settings
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database settings
    sqlite_path: str = Field(default="./auth.db", alias="SQLITE_PATH")
    
    @property
    def database_url(self) -> str:
        """Формирует URL для подключения к БД"""
        return f"sqlite+aiosqlite:///{self.sqlite_path}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

# Создание единого объекта настроек
settings = Settings()
