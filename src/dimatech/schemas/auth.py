"""Схемы аутентификации."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from dimatech.db.models import UserRole


class AuthUserRead(BaseModel):
	"""Краткое представление пользователя в ответе аутентификации."""

	model_config = ConfigDict(
		from_attributes=True,
		json_schema_extra={
			'example': {
				'id': 1,
				'email': 'user@example.com',
				'full_name': 'Тестовый пользователь',
				'role': 'user',
			},
		},
	)

	id: int
	email: EmailStr
	full_name: str
	role: UserRole


class LoginRequest(BaseModel):
	"""Тело запроса на аутентификацию."""

	model_config = ConfigDict(
		json_schema_extra={
			'example': {
				'email': 'user@example.com',
				'password': 'user12345',
			},
		}
	)

	email: EmailStr = Field(description='Email пользователя.')
	password: str = Field(
		min_length=8,
		max_length=128,
		description='Пароль пользователя.',
	)


class TokenResponse(BaseModel):
	"""Ответ с access token."""

	model_config = ConfigDict(
		json_schema_extra={
			'example': {
				'access_token': 'jwt-token',
				'token_type': 'bearer',
				'expires_in': 3600,
				'user': {
					'id': 1,
					'email': 'user@example.com',
					'full_name': 'Тестовый пользователь',
					'role': 'user',
				},
			},
		}
	)

	access_token: str
	token_type: str = 'bearer'
	expires_in: int
	user: AuthUserRead
