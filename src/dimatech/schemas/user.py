"""Схемы пользователя, счета и платежа."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from dimatech.db.models import UserRole


class UserRead(BaseModel):
	"""Публичные данные пользователя."""

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


class AccountRead(BaseModel):
	"""Данные счета пользователя."""

	model_config = ConfigDict(
		from_attributes=True,
		json_schema_extra={
			'example': {
				'id': 1,
				'user_id': 1,
				'balance': '1000.00',
			},
		},
	)

	id: int
	user_id: int
	balance: Decimal


class PaymentRead(BaseModel):
	"""Данные платежа пользователя."""

	model_config = ConfigDict(
		from_attributes=True,
		json_schema_extra={
			'example': {
				'id': 1,
				'transaction_id': 'tx-100',
				'user_id': 1,
				'account_id': 1,
				'amount': '100.00',
				'created_at': '2026-04-09T12:00:00Z',
			},
		},
	)

	id: int
	transaction_id: str
	user_id: int
	account_id: int
	amount: Decimal
	created_at: datetime


class UserCreateRequest(BaseModel):
	"""Запрос на создание пользователя администратором."""

	model_config = ConfigDict(
		json_schema_extra={
			'example': {
				'email': 'new-user@example.com',
				'full_name': 'Новый пользователь',
				'password': 'new-user-123',
			},
		}
	)

	email: EmailStr = Field(description='Email нового пользователя.')
	full_name: str = Field(
		min_length=1,
		max_length=255,
		description='Полное имя пользователя.',
	)
	password: str = Field(
		min_length=8,
		max_length=128,
		description='Пароль нового пользователя.',
	)


class UserUpdateRequest(BaseModel):
	"""Запрос на частичное обновление пользователя."""

	model_config = ConfigDict(
		json_schema_extra={
			'example': {
				'full_name': 'Обновленное имя',
				'is_active': False,
			},
		}
	)

	email: EmailStr | None = None
	full_name: str | None = Field(default=None, min_length=1, max_length=255)
	password: str | None = Field(default=None, min_length=8, max_length=128)
	is_active: bool | None = None


class UserWithAccountsRead(UserRead):
	"""Пользователь со списком счетов."""

	model_config = ConfigDict(
		from_attributes=True,
		json_schema_extra={
			'example': {
				'id': 1,
				'email': 'user@example.com',
				'full_name': 'Тестовый пользователь',
				'role': 'user',
				'accounts': [
					{
						'id': 1,
						'user_id': 1,
						'balance': '1000.00',
					},
				],
			},
		},
	)

	accounts: list[AccountRead]
