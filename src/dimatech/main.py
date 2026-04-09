"""Фабрика приложения FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from starlette.types import Lifespan

from dimatech.api.docs import OPENAPI_TAGS
from dimatech.api.router import api_router
from dimatech.core.config import Settings, get_settings
from dimatech.db.session import DatabaseManager
from dimatech.schemas.common import HealthcheckResponse


def build_lifespan(settings: Settings) -> Lifespan[FastAPI]:
	"""Создает lifespan с замкнутыми настройками приложения."""

	@asynccontextmanager
	async def lifespan(app: FastAPI) -> AsyncIterator[None]:
		"""Подготавливает инфраструктурные зависимости приложения."""
		database = DatabaseManager()
		database.initialize(database_url=settings.database_url, echo=settings.debug)
		app.state.settings = settings
		app.state.database = database
		yield
		await database.dispose()

	return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
	"""Создает и конфигурирует экземпляр приложения."""
	app_settings = settings or get_settings()
	app = FastAPI(
		title=app_settings.app_name,
		description=(
			'REST API для управления пользователями, '
			'счетами и платежными вебхуками.'
		),
		version='0.1.0',
		debug=app_settings.debug,
		lifespan=build_lifespan(settings=app_settings),
		openapi_tags=OPENAPI_TAGS,
	)

	@app.get(
		'/health',
		tags=['health'],
		summary='Проверка доступности сервиса',
		description='Служебная ручка для smoke-проверок и healthcheck контейнера.',
		response_model=HealthcheckResponse,
		response_description='Сервис доступен и готов принимать запросы.',
		status_code=status.HTTP_200_OK,
	)
	async def healthcheck() -> HealthcheckResponse:
		"""Простой healthcheck для оркестрации и smoke-проверок."""
		return HealthcheckResponse(status='ok')

	app.include_router(api_router, prefix=app_settings.api_prefix)
	return app
