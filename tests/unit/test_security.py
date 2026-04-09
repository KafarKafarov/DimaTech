"""Unit-тесты вспомогательных функций безопасности."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from dimatech.core.config import Settings
from dimatech.core.security import (
	TokenPayloadError,
	create_access_token,
	decode_access_token,
	hash_password,
	verify_password,
)


def test_hash_ok() -> None:
	"""Хеш пароля должен успешно проходить обратную проверку."""
	password_hash = hash_password('secret-pass-123')

	assert verify_password('secret-pass-123', password_hash)
	assert not verify_password('wrong-pass', password_hash)


def test_token_roundtrip(test_settings: Settings) -> None:
	"""Созданный токен должен успешно декодироваться."""
	token = create_access_token(user_id=15, role='admin', settings=test_settings)

	payload = decode_access_token(token=token, settings=test_settings)

	assert payload == {'sub': '15', 'role': 'admin'}


def test_bad_token(test_settings: Settings) -> None:
	"""Некорректный токен должен отклоняться."""
	with pytest.raises(TokenPayloadError, match=r'Некорректный токен доступа\.'):
		decode_access_token(token='broken-token', settings=test_settings)


def test_token_without_role(test_settings: Settings) -> None:
	"""Токен без корректной роли должен отклоняться."""
	token = jwt.encode(
		payload={
			'sub': '1',
			'exp': datetime.now(tz=UTC) + timedelta(minutes=5),
		},
		key=test_settings.jwt_secret_key,
		algorithm=test_settings.jwt_algorithm,
	)

	with pytest.raises(
		TokenPayloadError,
		match=r'Токен не содержит корректную роль пользователя\.',
	):
		decode_access_token(token=token, settings=test_settings)
