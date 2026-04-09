"""Конфигурация приложения."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Настройки приложения и внешних интеграций."""

	model_config = SettingsConfigDict(
		env_file='.env',
		env_file_encoding='utf-8',
		frozen=True,
		extra='ignore',
	)

	app_name: str = 'DimaTech API'
	api_prefix: str = '/api/v1'
	debug: bool = False

	database_url: str
	database_url_sync: str

	jwt_secret_key: str
	jwt_algorithm: str
	access_token_expire_minutes: int

	payment_signature_secret: str
	cache_ttl_seconds: int
	cache_max_size: int


@lru_cache
def get_settings() -> Settings:
	"""Возвращает закешированный объект настроек."""
	return Settings()  # type: ignore[call-arg]
