"""Интеграционные тесты пользовательских ручек."""

from http import HTTPStatus

from httpx import AsyncClient

from tests.utils import auth_headers, authenticate


async def test_accounts_ok(client: AsyncClient) -> None:
	"""Пользователь должен видеть свои счета."""
	token = await authenticate(
		client=client,
		email='user@example.com',
		password='user12345',
	)

	response = await client.get(
		'/api/v1/users/me/accounts',
		headers=auth_headers(token=token),
	)

	assert response.status_code == HTTPStatus.OK
	assert response.json() == [
		{
			'id': 1,
			'user_id': 1,
			'balance': '1000.00',
		},
	]


async def test_payments_empty(client: AsyncClient) -> None:
	"""На старте у пользователя не должно быть платежей."""
	token = await authenticate(
		client=client,
		email='user@example.com',
		password='user12345',
	)

	response = await client.get(
		'/api/v1/users/me/payments',
		headers=auth_headers(token=token),
	)

	assert response.status_code == HTTPStatus.OK
	assert response.json() == []


async def test_accounts_no_token(client: AsyncClient) -> None:
	"""Список счетов должен быть защищен авторизацией."""
	response = await client.get('/api/v1/users/me/accounts')

	assert response.status_code == HTTPStatus.UNAUTHORIZED
	assert response.json()['detail'] == 'Отсутствует токен доступа.'
