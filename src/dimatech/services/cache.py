"""Сервис инвалидации прикладного кеша."""

from __future__ import annotations

from dimatech.cache.keys import admin_users_key, user_accounts_key, user_payments_key
from dimatech.cache.redis import BaseCache


class CacheInvalidationService:
    """Удаляет устаревшие значения из Redis-кеша."""

    def __init__(self, *, cache: BaseCache) -> None:
        """Сохраняет кеш-зависимость."""
        self._cache = cache

    async def invalidate_admin_users(self) -> None:
        """Сбрасывает закешированный список пользователей."""
        await self._cache.delete(admin_users_key())

    async def invalidate_user_related(self, *, user_id: int) -> None:
        """Сбрасывает кеш, связанный с конкретным пользователем."""
        await self._cache.delete(
            user_accounts_key(user_id=user_id),
            user_payments_key(user_id=user_id),
            admin_users_key(),
        )
