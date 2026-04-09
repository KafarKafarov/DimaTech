"""ORM-модели предметной области."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dimatech.db.base import Base


class UserRole(StrEnum):
	"""Роль учетной записи в системе."""

	USER = 'user'
	ADMIN = 'admin'


class TimestampMixin:
	"""Общие временные поля для сущностей."""

	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)


class User(TimestampMixin, Base):
	"""Пользователь или администратор приложения."""

	__tablename__ = 'users'

	id: Mapped[int] = mapped_column(
		primary_key=True,
		autoincrement=True,
	)
	email: Mapped[str] = mapped_column(
		String(255),
		unique=True,
		nullable=False,
	)
	full_name: Mapped[str] = mapped_column(
		String(255),
		nullable=False,
	)
	password_hash: Mapped[str] = mapped_column(
		String(255),
		nullable=False,
	)
	role: Mapped[UserRole] = mapped_column(
		Enum(
			UserRole,
			native_enum=False,
			length=16,
		),
		default=UserRole.USER,
		nullable=False,
	)
	is_active: Mapped[bool] = mapped_column(
		default=True,
		nullable=False,
	)

	accounts: Mapped[list['Account']] = relationship(
		back_populates='user',
		cascade='all, delete-orphan',
		passive_deletes=True,
	)
	payments: Mapped[list['Payment']] = relationship(
		back_populates='user',
		cascade='all, delete-orphan',
		passive_deletes=True,
	)


class Account(TimestampMixin, Base):
	"""Счет пользователя с текущим балансом."""

	__tablename__ = 'accounts'

	id: Mapped[int] = mapped_column(
		primary_key=True,
		autoincrement=True,
	)
	user_id: Mapped[int] = mapped_column(
		ForeignKey(
			column='users.id',
			ondelete='CASCADE',
		),
		index=True,
		nullable=False,
	)
	balance: Mapped[Decimal] = mapped_column(
		Numeric(
			precision=12,
			scale=2,
		),
		default=Decimal('0.00'),
		nullable=False,
	)

	user: Mapped[User] = relationship(back_populates='accounts')
	payments: Mapped[list['Payment']] = relationship(
		back_populates='account',
		cascade='all, delete-orphan',
		passive_deletes=True,
	)


class Payment(TimestampMixin, Base):
	"""Платеж пополнения баланса пользователя."""

	__tablename__ = 'payments'

	id: Mapped[int] = mapped_column(
		primary_key=True,
		autoincrement=True,
	)
	transaction_id: Mapped[str] = mapped_column(
		String(64),
		unique=True,
		nullable=False,
	)
	user_id: Mapped[int] = mapped_column(
		ForeignKey(column='users.id', ondelete='CASCADE'),
		index=True,
		nullable=False,
	)
	account_id: Mapped[int] = mapped_column(
		ForeignKey(column='accounts.id', ondelete='CASCADE'),
		index=True,
		nullable=False,
	)
	amount: Mapped[Decimal] = mapped_column(Numeric(
		precision=12,
		scale=2,
	), nullable=False)

	user: Mapped[User] = relationship(back_populates='payments')
	account: Mapped['Account'] = relationship(back_populates='payments')
