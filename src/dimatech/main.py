"""Фабрика приложения FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from starlette.types import Lifespan

from dimatech.api.router import api_router
from dimatech.cache.redis import BaseCache, build_cache
from dimatech.core.config import Settings, get_settings
from dimatech.db.session import DatabaseManager


def build_lifespan(settings: Settings) -> Lifespan[FastAPI]:
    """Создает lifespan с замкнутыми настройками приложения."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Подготавливает инфраструктурные зависимости приложения."""
        database = DatabaseManager()
        database.initialize(database_url=settings.database_url, echo=settings.debug)

        async with build_cache(redis_url=settings.redis_url) as cache:
            app.state.settings = settings
            app.state.database = database
            app.state.cache = cache
            yield
            await database.dispose()

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """Создает и конфигурирует экземпляр приложения."""
    app_settings = settings or get_settings()
    app = FastAPI(
        title=app_settings.app_name,
        debug=app_settings.debug,
        lifespan=build_lifespan(settings=app_settings),
    )

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        """Простой healthcheck для оркестрации и smoke-проверок."""
        return {"status": "ok"}

    app.include_router(api_router, prefix=app_settings.api_prefix)
    return app


def get_cache_from_app(app: FastAPI) -> BaseCache:
    """Возвращает инстанс кеша, сохраненный в состоянии приложения."""
    return cast(BaseCache, app.state.cache)
