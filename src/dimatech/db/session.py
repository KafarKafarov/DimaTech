"""Инициализация асинхронной SQLAlchemy-сессии."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
	AsyncEngine,
	AsyncSession,
	async_sessionmaker,
	create_async_engine,
)


class DatabaseManager:
	"""Управляет жизненным циклом подключения к базе данных."""

	def __init__(self) -> None:
		"""Создает неинициализированный менеджер БД."""
		self._engine: AsyncEngine | None = None
		self._session_factory: async_sessionmaker[AsyncSession] | None = None

	def initialize(
			self,
			*,
			database_url: str,
			echo: bool,
	) -> None:
		"""Создает engine и фабрику сессий."""
		self._engine = create_async_engine(
			url=database_url,
			echo=echo,
		)
		self._session_factory = async_sessionmaker(
			bind=self._engine,
			autoflush=False,
			expire_on_commit=False,
		)

	async def dispose(self) -> None:
		"""Освобождает ресурсы engine."""
		if self._engine is None:
			return
		await self._engine.dispose()

	async def session(self) -> AsyncIterator[AsyncSession]:
		"""Возвращает асинхронную сессию БД."""
		if self._session_factory is None:
			message = 'Менеджер базы данных не инициализирован.'
			raise RuntimeError(message)

		async with self._session_factory() as session:
			yield session
