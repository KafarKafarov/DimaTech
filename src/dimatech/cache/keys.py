"""Ключи прикладного кеша для API."""


def user_accounts_key(*, user_id: int) -> str:
	"""Возвращает ключ списка счетов пользователя."""
	return f'user:{user_id}:accounts'


def user_payments_key(*, user_id: int) -> str:
	"""Возвращает ключ списка платежей пользователя."""
	return f'user:{user_id}:payments'


def admin_users_key() -> str:
	"""Возвращает ключ списка пользователей для администратора."""
	return 'admin:users'
