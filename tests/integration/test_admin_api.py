"""Интеграционные тесты административных ручек."""

from http import HTTPStatus

from httpx import AsyncClient

from tests.utils import auth_headers, authenticate


async def test_admin_list_ok(client: AsyncClient) -> None:
	"""Администратор должен видеть пользователей вместе со счетами."""
	token = await authenticate(
		client=client,
		email='admin@example.com',
		password='admin12345',
	)

	response = await client.get(
		url='/api/v1/admin/users',
		headers=auth_headers(token=token),
	)

	assert response.status_code == HTTPStatus.OK
	assert len(response.json()) == 2
	assert response.json()[0]['accounts'] == [
		{
			'id': 1,
			'user_id': 1,
			'balance': '1000.00',
		},
	]


async def test_admin_forbidden(client: AsyncClient) -> None:
	"""Обычный пользователь не должен попадать в админские ручки."""
	token = await authenticate(
		client=client,
		email='user@example.com',
		password='user12345',
	)

	response = await client.get(
		url='/api/v1/admin/users',
		headers=auth_headers(token=token),
	)

	assert response.status_code == HTTPStatus.FORBIDDEN
	assert response.json()['detail'] == 'Недостаточно прав для выполнения операции.'


async def test_admin_crud_ok(client: AsyncClient) -> None:
	"""Администратор должен уметь создать, обновить и удалить пользователя."""
	token = await authenticate(
		client=client,
		email='admin@example.com',
		password='admin12345',
	)
	headers = auth_headers(token=token)

	create_response = await client.post(
		url='/api/v1/admin/users',
		headers=headers,
		json={
			'email': 'new-user@example.com',
			'full_name': 'Новый пользователь',
			'password': 'new-user-123',
		},
	)
	assert create_response.status_code == HTTPStatus.CREATED
	user_id = create_response.json()['id']

	update_response = await client.patch(
		url=f'/api/v1/admin/users/{user_id}',
		headers=headers,
		json={'full_name': 'Обновленное имя', 'is_active': False},
	)
	assert update_response.status_code == HTTPStatus.OK
	assert update_response.json()['full_name'] == 'Обновленное имя'
	assert update_response.json()['email'] == 'new-user@example.com'

	delete_response = await client.delete(
		url=f'/api/v1/admin/users/{user_id}',
		headers=headers,
	)

	assert delete_response.status_code == HTTPStatus.NO_CONTENT


async def test_admin_create_dup(client: AsyncClient) -> None:
	"""Повторное создание пользователя с тем же email должно отклоняться."""
	token = await authenticate(
		client=client,
		email='admin@example.com',
		password='admin12345',
	)

	response = await client.post(
		url='/api/v1/admin/users',
		headers=auth_headers(token=token),
		json={
			'email': 'user@example.com',
			'full_name': 'Дубликат',
			'password': 'duplicate-123',
		},
	)

	assert response.status_code == HTTPStatus.CONFLICT
	assert response.json()['detail'] == 'Пользователь с таким email уже существует.'


async def test_admin_update_missing(client: AsyncClient) -> None:
	"""Обновление неизвестного пользователя должно возвращать 404."""
	token = await authenticate(
		client=client,
		email='admin@example.com',
		password='admin12345',
	)

	response = await client.patch(
		url='/api/v1/admin/users/999',
		headers=auth_headers(token=token),
		json={'full_name': 'Не найден'},
	)

	assert response.status_code == HTTPStatus.NOT_FOUND
	assert response.json()['detail'] == 'Пользователь не найден.'


async def test_admin_delete_missing(client: AsyncClient) -> None:
	"""Удаление неизвестного пользователя должно возвращать 404."""
	token = await authenticate(
		client=client,
		email='admin@example.com',
		password='admin12345',
	)

	response = await client.delete(
		url='/api/v1/admin/users/999',
		headers=auth_headers(token=token),
	)

	assert response.status_code == HTTPStatus.NOT_FOUND
	assert response.json()['detail'] == 'Пользователь не найден.'
