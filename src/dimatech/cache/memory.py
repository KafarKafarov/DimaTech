"""In-memory LRU-кеш приложения."""

from collections import OrderedDict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from time import monotonic


@dataclass(slots=True)
class CacheEntry:
	"""Элемент кеша со сроком жизни."""

	value: str
	expires_at: float


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
		"""Освобождает ресурсы кеша."""
		return None


class NullCache(BaseCache):
	"""Пустая реализация кеша."""

	async def get(self, key: str) -> str | None:
		"""Всегда возвращает отсутствие значения."""
		return None

	async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
		"""Игнорирует запись."""
		return None

	async def delete(self, *keys: str) -> None:
		"""Игнорирует удаление."""
		return None


class LruMemoryCache(BaseCache):
	"""Простой LRU-кеш в памяти процесса."""

	def __init__(self, *, max_size: int) -> None:
		"""Создает кеш ограниченного размера."""
		self._max_size = max_size
		self._storage: OrderedDict[str, CacheEntry] = OrderedDict()

	async def get(self, key: str) -> str | None:
		"""Возвращает значение, если оно есть и не просрочено."""
		entry = self._storage.get(key)
		if entry is None:
			return None

		if entry.expires_at <= monotonic():
			self._storage.pop(key, None)
			return None

		self._storage.move_to_end(key)
		return entry.value

	async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
		"""Сохраняет значение и поддерживает LRU-порядок."""
		if ttl_seconds <= 0:
			self._storage.pop(key, None)
			return

		expires_at = monotonic() + ttl_seconds
		if key in self._storage:
			self._storage.pop(key, None)

		self._storage[key] = CacheEntry(value=value, expires_at=expires_at)
		self._storage.move_to_end(key)
		await self._evict()

	async def delete(self, *keys: str) -> None:
		"""Удаляет ключи из кеша."""
		for key in keys:
			self._storage.pop(key, None)

	async def close(self) -> None:
		"""Очищает кеш."""
		self._storage.clear()

	async def _evict(self) -> None:
		"""Удаляет просроченные и лишние элементы."""
		now = monotonic()
		expired_keys: list[str] = []
		for key, entry in self._storage.items():
			if entry.expires_at > now:
				continue
			expired_keys.append(key)

		for key in expired_keys:
			self._storage.pop(key, None)

		while len(self._storage) > self._max_size:
			self._storage.popitem(last=False)


@asynccontextmanager
async def build_cache(*, max_size: int) -> AsyncIterator[BaseCache]:
	"""Создает кеш в памяти или его пустую реализацию."""
	if max_size <= 0:
		yield NullCache()
		return

	cache = LruMemoryCache(max_size=max_size)
	try:
		yield cache
	finally:
		await cache.close()
