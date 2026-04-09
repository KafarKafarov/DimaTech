"""Конфигурация приложения."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения и внешних интеграций."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        validate_assignment=True,
        extra="ignore",
    )

    app_name: str = "DimaTech API"
    api_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/dimatech"
    database_url_sync: str = "postgresql+psycopg://postgres:postgres@localhost:5432/dimatech"
    redis_url: str | None = "redis://localhost:6379/0"

    jwt_secret_key: str = "super-secret-jwt-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    payment_signature_secret: str = "gfdmhghif38yrf9ew0jkf32"
    cache_ttl_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    """Возвращает закешированный объект настроек."""
    return Settings()
