"""Общие вспомогательные функции для тестов."""

from decimal import Decimal
from http import HTTPStatus
from typing import Any, cast

from httpx import AsyncClient

from dimatech.services.payment import WebhookSignaturePayload, build_webhook_signature


async def authenticate(*, client: AsyncClient, email: str, password: str) -> str:
	"""Выполняет логин и возвращает bearer token."""
	response = await client.post(
		'/api/v1/auth/login',
		json={'email': email, 'password': password},
	)
	assert response.status_code == HTTPStatus.OK
	return cast(str, response.json()['access_token'])


def auth_headers(*, token: str) -> dict[str, str]:
	"""Формирует заголовки авторизации."""
	return {'Authorization': f'Bearer {token}'}


def build_webhook_body(
	*,
	transaction_id: str,
	user_id: int,
	account_id: int,
	amount: int | str | Decimal,
	secret_key: str,
) -> dict[str, Any]:
	"""Формирует валидное тело платежного вебхука."""
	payload: WebhookSignaturePayload = {
		'transaction_id': transaction_id,
		'user_id': user_id,
		'account_id': account_id,
		'amount': amount,
	}
	signature = build_webhook_signature(payload=payload, secret_key=secret_key)
	return {**payload, 'signature': signature}
