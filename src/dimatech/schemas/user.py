"""Схемы пользователя, счета и платежа."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from dimatech.db.models import UserRole


class UserRead(BaseModel):
	"""Публичные данные пользователя."""

	model_config = ConfigDict(from_attributes=True)

	id: int
	email: EmailStr
	full_name: str
	role: UserRole


class AccountRead(BaseModel):
	"""Данные счета пользователя."""

	model_config = ConfigDict(from_attributes=True)

	id: int
	user_id: int
	balance: Decimal


class PaymentRead(BaseModel):
	"""Данные платежа пользователя."""

	model_config = ConfigDict(from_attributes=True)

	id: int
	transaction_id: str
	user_id: int
	account_id: int
	amount: Decimal
	created_at: datetime


class UserCreateRequest(BaseModel):
	"""Запрос на создание пользователя администратором."""

	email: EmailStr
	full_name: str = Field(min_length=1, max_length=255)
	password: str = Field(min_length=8, max_length=128)


class UserUpdateRequest(BaseModel):
	"""Запрос на частичное обновление пользователя."""

	email: EmailStr | None = None
	full_name: str | None = Field(default=None, min_length=1, max_length=255)
	password: str | None = Field(default=None, min_length=8, max_length=128)
	is_active: bool | None = None


class UserWithAccountsRead(UserRead):
	"""Пользователь со списком счетов."""

	accounts: list[AccountRead]
