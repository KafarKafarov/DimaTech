"""Интеграция с Redis для прикладного кеширования."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from redis.asyncio import Redis


class BaseCache:
    """Базовый интерфейс кеша."""

    async def get(self, key: str) -> str | None:
        """Возвращает значение по ключу."""
        raise NotImplementedError

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        """Сохраняет значение в кеше."""
        raise NotImplementedError

    async def delete(self, *keys: str) -> None:
        """Удаляет один или несколько ключей."""
        raise NotImplementedError

    async def close(self) -> None:
        """Закрывает ресурсы кеша."""
        return None


class NullCache(BaseCache):
    """Заглушка кеша для окружений без Redis."""

    async def get(self, key: str) -> str | None:
        """Возвращает отсутствие значения."""
        return None

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        """Игнорирует запись в кеш."""
        return None

    async def delete(self, *keys: str) -> None:
        """Игнорирует удаление ключей."""
        return None


class RedisCache(BaseCache):
    """Асинхронная обертка над Redis."""

    def __init__(self, client: Redis) -> None:
        """Сохраняет инициализированный Redis-клиент."""
        self._client = client

    async def get(self, key: str) -> str | None:
        """Возвращает строковое значение из Redis."""
        return await self._client.get(name=key)

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        """Сохраняет значение с TTL."""
        await self._client.set(name=key, value=value, ex=ttl_seconds)

    async def delete(self, *keys: str) -> None:
        """Удаляет ключи, если они были переданы."""
        if not keys:
            return
        await self._client.delete(*keys)

    async def close(self) -> None:
        """Закрывает Redis-соединение."""
        await self._client.aclose()


@asynccontextmanager
async def build_cache(redis_url: str | None) -> AsyncIterator[BaseCache]:
    """Создает экземпляр кеша в зависимости от конфигурации."""
    if not redis_url:
        yield NullCache()
        return

    client = Redis.from_url(url=redis_url, decode_responses=True)
    cache = RedisCache(client=client)

    try:
        yield cache
    finally:
        await cache.close()
