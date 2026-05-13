"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from cursor_metrics import __version__


class Settings(BaseSettings):
    """Central configuration consumed by all application layers."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_EXPIRE_MINUTES: int = 1440
    APP_VERSION: str = __version__
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton, usable as a FastAPI dependency."""
    return Settings()
