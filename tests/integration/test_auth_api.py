"""Интеграционные тесты ручек аутентификации."""

from http import HTTPStatus

from httpx import AsyncClient

from tests.utils import auth_headers, authenticate


async def test_login_ok(client: AsyncClient) -> None:
	"""Пользователь должен получать access token по корректным данным."""
	token = await authenticate(
		client=client,
		email='user@example.com',
		password='user12345',
	)

	response = await client.get('/api/v1/auth/me', headers=auth_headers(token=token))

	assert response.status_code == HTTPStatus.OK
	assert response.json() == {
		'id': 1,
		'email': 'user@example.com',
		'full_name': 'Тестовый пользователь',
		'role': 'user',
	}


async def test_login_bad_pass(client: AsyncClient) -> None:
	"""Неверный пароль должен приводить к 401."""
	response = await client.post(
		'/api/v1/auth/login',
		json={'email': 'user@example.com', 'password': 'wrong-pass'},
	)

	assert response.status_code == HTTPStatus.UNAUTHORIZED
	assert response.json()['detail'] == 'Неверный email или пароль.'


async def test_me_no_token(client: AsyncClient) -> None:
	"""Ручка профиля должна требовать токен."""
	response = await client.get('/api/v1/auth/me')

	assert response.status_code == HTTPStatus.UNAUTHORIZED
	assert response.json()['detail'] == 'Отсутствует токен доступа.'


async def test_me_bad_token(client: AsyncClient) -> None:
	"""Некорректный токен должен приводить к 401."""
	response = await client.get(
		'/api/v1/auth/me',
		headers=auth_headers(token='broken-token'),
	)

	assert response.status_code == HTTPStatus.UNAUTHORIZED
	assert response.json()['detail'] == 'Некорректный токен доступа.'
