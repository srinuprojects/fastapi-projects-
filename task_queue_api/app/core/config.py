from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Task Queue API"
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
