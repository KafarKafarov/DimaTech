"""Маршруты аутентификации."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import (
	get_current_user,
	get_session,
	get_settings_dependency,
)
from dimatech.api.docs import VALIDATION_ERROR_RESPONSE, build_error_response
from dimatech.core.config import Settings
from dimatech.db.models import User
from dimatech.repositories.user import UserRepository
from dimatech.schemas.auth import LoginRequest, TokenResponse
from dimatech.schemas.user import UserRead
from dimatech.services.auth import AuthService

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post(
	path='/login',
	response_model=TokenResponse,
	status_code=status.HTTP_200_OK,
	summary='Аутентификация по email и паролю',
	description='Проверяет учетные данные пользователя и возвращает JWT access token.',
	responses={
		status.HTTP_401_UNAUTHORIZED: build_error_response(
			description='Неверные учетные данные или пользователь деактивирован.',
			detail='Неверный email или пароль.',
		),
		422: VALIDATION_ERROR_RESPONSE,
	},
)
async def login(
	payload: LoginRequest,
	session: AsyncSession = Depends(get_session),
	settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
	"""Авторизует пользователя по email и паролю."""
	service = AuthService(
		settings=settings, user_repository=UserRepository(session=session)
	)
	return await service.login(email=str(payload.email), password=payload.password)


@router.get(
	path='/me',
	response_model=UserRead,
	status_code=status.HTTP_200_OK,
	summary='Получение профиля текущего пользователя',
	description=(
		'Возвращает публичные данные пользователя, '
		'извлеченного из access token.'
	),
	responses={
		status.HTTP_401_UNAUTHORIZED: build_error_response(
			description='Пользователь не аутентифицирован или токен недействителен.',
			detail='Отсутствует токен доступа.',
		),
	},
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
	"""Возвращает данные текущего пользователя."""
	return UserRead.model_validate(current_user)
