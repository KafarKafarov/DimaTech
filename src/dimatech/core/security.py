"""Утилиты безопасности: хеширование паролей и работа с JWT."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from dimatech.core.config import Settings

password_hasher = PasswordHash.recommended()


class TokenPayloadError(ValueError):
	"""Ошибка разбора или валидации токена доступа."""


def hash_password(password: str) -> str:
	"""Возвращает хеш пароля."""
	return password_hasher.hash(password=password)


def verify_password(password: str, password_hash: str) -> bool:
	"""Проверяет пароль относительно сохраненного хеша."""
	return password_hasher.verify(password=password, hash=password_hash)


def create_access_token(*, user_id: int, role: str, settings: Settings) -> str:
	"""Создает JWT-токен доступа."""
	expires_at = datetime.now(tz=UTC) + timedelta(
		minutes=settings.access_token_expire_minutes
	)
	payload = {
		'sub': str(user_id),
		'role': role,
		'exp': expires_at,
	}
	return jwt.encode(
		payload=payload,
		key=settings.jwt_secret_key,
		algorithm=settings.jwt_algorithm,
	)


def decode_access_token(*, token: str, settings: Settings) -> dict[str, str]:
	"""Декодирует JWT и возвращает полезную нагрузку."""
	try:
		payload = jwt.decode(
			jwt=token,
			key=settings.jwt_secret_key,
			algorithms=[settings.jwt_algorithm],
		)
	except jwt.PyJWTError as error:
		raise TokenPayloadError('Некорректный токен доступа.') from error

	subject = payload.get('sub')
	role = payload.get('role')
	if not isinstance(subject, str) or not subject.isdigit():
		raise TokenPayloadError(
			'Токен не содержит корректный идентификатор пользователя.'
		)
	if not isinstance(role, str):
		raise TokenPayloadError('Токен не содержит корректную роль пользователя.')

	return {'sub': subject, 'role': role}
