"""Зависимости FastAPI для доступа к приложению, БД и текущему пользователю."""

from collections.abc import AsyncIterator
from typing import cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.cache.memory import BaseCache
from dimatech.core.config import Settings
from dimatech.core.security import TokenPayloadError, decode_access_token
from dimatech.db.models import User, UserRole
from dimatech.db.session import DatabaseManager
from dimatech.repositories.user import UserRepository

http_bearer = HTTPBearer(auto_error=False)


def get_settings_dependency(request: Request) -> Settings:
	"""Возвращает настройки приложения из состояния FastAPI."""
	return cast(Settings, request.app.state.settings)


def get_cache_dependency(request: Request) -> BaseCache:
	"""Возвращает кеш-прослойку из состояния приложения."""
	return cast(BaseCache, request.app.state.cache)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
	"""Возвращает асинхронную SQLAlchemy-сессию."""
	database = cast(DatabaseManager, request.app.state.database)
	async for session in database.session():
		yield session


async def get_current_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
	session: AsyncSession = Depends(get_session),
	settings: Settings = Depends(get_settings_dependency),
) -> User:
	"""Возвращает текущего аутентифицированного пользователя."""
	if credentials is None:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Отсутствует токен доступа.',
		)

	try:
		payload = decode_access_token(token=credentials.credentials, settings=settings)
	except TokenPayloadError as error:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=str(error),
		) from error

	repository = UserRepository(session=session)
	user = await repository.get_by_id(user_id=int(payload['sub']))
	if user is None or not user.is_active:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Пользователь не найден или деактивирован.',
		)

	return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
	"""Проверяет, что текущий пользователь обладает ролью администратора."""
	if current_user.role is not UserRole.ADMIN:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail='Недостаточно прав для выполнения операции.',
		)
	return current_user
