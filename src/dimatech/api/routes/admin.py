"""Маршруты администратора."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import get_admin_user, get_session
from dimatech.db.models import User
from dimatech.repositories.user import UserRepository
from dimatech.schemas.user import (
	UserCreateRequest,
	UserRead,
	UserUpdateRequest,
	UserWithAccountsRead,
)
from dimatech.services.user import UserService

router = APIRouter(prefix='/admin', tags=['admin'])


def build_users_payload(*, users: list[User]) -> list[UserWithAccountsRead]:
	"""Преобразует ORM-модели пользователей в ответ API."""
	payload: list[UserWithAccountsRead] = []
	for user in users:
		payload.append(UserWithAccountsRead.model_validate(user))
	return payload


@router.get('/users', response_model=list[UserWithAccountsRead])
async def list_users(
	_: User = Depends(get_admin_user),
	session: AsyncSession = Depends(get_session),
) -> list[UserWithAccountsRead]:
	"""Возвращает список пользователей и их счетов."""
	repository = UserRepository(session=session)
	users = await repository.list_with_accounts()
	return build_users_payload(users=users)


@router.post('/users', response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
	payload: UserCreateRequest,
	_: User = Depends(get_admin_user),
	session: AsyncSession = Depends(get_session),
) -> UserRead:
	"""Создает нового пользователя."""
	service = UserService(
		session=session,
		user_repository=UserRepository(session=session),
	)
	user = await service.create_user(payload=payload)
	return UserRead.model_validate(user)


@router.patch('/users/{user_id}', response_model=UserRead)
async def update_user(
	user_id: int,
	payload: UserUpdateRequest,
	_: User = Depends(get_admin_user),
	session: AsyncSession = Depends(get_session),
) -> UserRead:
	"""Частично обновляет пользователя."""
	service = UserService(
		session=session,
		user_repository=UserRepository(session=session),
	)
	user = await service.update_user(user_id=user_id, payload=payload)
	return UserRead.model_validate(user)


@router.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
	user_id: int,
	_: User = Depends(get_admin_user),
	session: AsyncSession = Depends(get_session),
) -> Response:
	"""Удаляет пользователя."""
	service = UserService(
		session=session,
		user_repository=UserRepository(session=session),
	)
	await service.delete_user(user_id=user_id)
	return Response(status_code=status.HTTP_204_NO_CONTENT)
