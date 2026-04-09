"""Создание схемы приложения и тестовых данных."""

from decimal import Decimal

import sqlalchemy as sa
from alembic import op

from dimatech.core.security import hash_password
from dimatech.db.models import UserRole

revision = '20260409_0001'
down_revision = None
branch_labels = None
depends_on = None


def _set_postgresql_sequence_value(table_name: str, column_name: str) -> None:
	"""Синхронизирует sequence с текущим максимальным значением PK."""
	statement = sa.text(
		'SELECT setval('
		'pg_get_serial_sequence(:table_name, :column_name), '
		'COALESCE((SELECT MAX(id) FROM ' + table_name + '), 1), '
		'true'
		')'
	)
	op.execute(statement.bindparams(table_name=table_name, column_name=column_name))


def upgrade() -> None:
	"""Создает таблицы и начальные тестовые данные."""
	op.create_table(
		'users',
		sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
		sa.Column('email', sa.String(length=255), nullable=False),
		sa.Column('full_name', sa.String(length=255), nullable=False),
		sa.Column('password_hash', sa.String(length=255), nullable=False),
		sa.Column(
			'role',
			sa.Enum(UserRole, native_enum=False, length=16),
			nullable=False,
		),
		sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
		sa.Column(
			'created_at',
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
		sa.Column(
			'updated_at',
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('email'),
	)
	op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

	op.create_table(
		'accounts',
		sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
		sa.Column('user_id', sa.Integer(), nullable=False),
		sa.Column('balance', sa.Numeric(12, 2), nullable=False, server_default='0.00'),
		sa.Column(
			'created_at',
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
		sa.Column(
			'updated_at',
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
		sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
		sa.PrimaryKeyConstraint('id'),
	)
	op.create_index(op.f('ix_accounts_user_id'), 'accounts', ['user_id'], unique=False)

	op.create_table(
		'payments',
		sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
		sa.Column('transaction_id', sa.String(length=64), nullable=False),
		sa.Column('user_id', sa.Integer(), nullable=False),
		sa.Column('account_id', sa.Integer(), nullable=False),
		sa.Column('amount', sa.Numeric(12, 2), nullable=False),
		sa.Column(
			'created_at',
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
		sa.Column(
			'updated_at',
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
		sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
		sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('transaction_id'),
	)
	op.create_index(
		op.f('ix_payments_account_id'), 'payments', ['account_id'], unique=False
	)
	op.create_index(
		op.f('ix_payments_transaction_id'),
		'payments',
		['transaction_id'],
		unique=False,
	)
	op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)

	users_table = sa.table(
		'users',
		sa.column('id', sa.Integer()),
		sa.column('email', sa.String()),
		sa.column('full_name', sa.String()),
		sa.column('password_hash', sa.String()),
		sa.column('role', sa.String()),
		sa.column('is_active', sa.Boolean()),
	)
	accounts_table = sa.table(
		'accounts',
		sa.column('id', sa.Integer()),
		sa.column('user_id', sa.Integer()),
		sa.column('balance', sa.Numeric(12, 2)),
	)

	op.bulk_insert(
		users_table,
		[
			{
				'id': 1,
				'email': 'user@example.com',
				'full_name': 'Тестовый пользователь',
				'password_hash': hash_password(password='user12345'),
				'role': UserRole.USER.value,
				'is_active': True,
			},
			{
				'id': 2,
				'email': 'admin@example.com',
				'full_name': 'Тестовый администратор',
				'password_hash': hash_password(password='admin12345'),
				'role': UserRole.ADMIN.value,
				'is_active': True,
			},
		],
	)

	op.bulk_insert(
		accounts_table,
		[
			{
				'id': 1,
				'user_id': 1,
				'balance': Decimal('1000.00'),
			},
		],
	)

	bind = op.get_bind()
	if bind.dialect.name == 'postgresql':
		_set_postgresql_sequence_value(table_name='users', column_name='id')
		_set_postgresql_sequence_value(table_name='accounts', column_name='id')
		_set_postgresql_sequence_value(table_name='payments', column_name='id')


def downgrade() -> None:
	"""Удаляет таблицы приложения."""
	op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
	op.drop_index(op.f('ix_payments_transaction_id'), table_name='payments')
	op.drop_index(op.f('ix_payments_account_id'), table_name='payments')
	op.drop_table('payments')
	op.drop_index(op.f('ix_accounts_user_id'), table_name='accounts')
	op.drop_table('accounts')
	op.drop_index(op.f('ix_users_email'), table_name='users')
	op.drop_table('users')
