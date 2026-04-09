"""Сквозные e2e-сценарии пользовательских потоков."""

from http import HTTPStatus

from httpx import AsyncClient

from tests.utils import auth_headers, authenticate, build_webhook_body


async def test_flow_topup(client: AsyncClient) -> None:
	"""Полный поток пополнения счета через админа, вебхук и пользовательский кабинет."""
	admin_token = await authenticate(
		client=client,
		email='admin@example.com',
		password='admin12345',
	)
	admin_headers = auth_headers(token=admin_token)

	create_response = await client.post(
		url='/api/v1/admin/users',
		headers=admin_headers,
		json={
			'email': 'flow-user@example.com',
			'full_name': 'Пользователь потока',
			'password': 'flow-user-123',
		},
	)
	assert create_response.status_code == HTTPStatus.CREATED
	user_id = create_response.json()['id']

	user_token = await authenticate(
		client=client,
		email='flow-user@example.com',
		password='flow-user-123',
	)
	user_headers = auth_headers(token=user_token)

	accounts_before = await client.get(
		url='/api/v1/users/me/accounts',
		headers=user_headers,
	)
	payments_before = await client.get(
		url='/api/v1/users/me/payments',
		headers=user_headers,
	)
	assert accounts_before.status_code == HTTPStatus.OK
	assert accounts_before.json() == []
	assert payments_before.status_code == HTTPStatus.OK
	assert payments_before.json() == []

	webhook_response = await client.post(
		url='/api/v1/payments/webhook',
		json=build_webhook_body(
			transaction_id='tx-flow-topup',
			user_id=user_id,
			account_id=77,
			amount='250.50',
			secret_key='test-payment-secret',
		),
	)
	assert webhook_response.status_code == HTTPStatus.OK
	assert webhook_response.json() == {
		'status': 'processed',
		'account_id': 77,
		'transaction_id': 'tx-flow-topup',
	}

	accounts_after = await client.get(
		url='/api/v1/users/me/accounts',
		headers=user_headers,
	)
	payments_after = await client.get(
		url='/api/v1/users/me/payments',
		headers=user_headers,
	)
	admin_list = await client.get(
		url='/api/v1/admin/users',
		headers=admin_headers,
	)

	assert accounts_after.status_code == HTTPStatus.OK
	assert accounts_after.json() == [
		{
			'id': 77,
			'user_id': user_id,
			'balance': '250.50',
		},
	]
	assert payments_after.status_code == HTTPStatus.OK
	assert len(payments_after.json()) == 1
	assert payments_after.json()[0]['transaction_id'] == 'tx-flow-topup'
	assert admin_list.status_code == HTTPStatus.OK
	assert any(
		user['email'] == 'flow-user@example.com'
		and user['accounts'] == [
			{
				'id': 77,
				'user_id': user_id,
				'balance': '250.50',
			},
		]
		for user in admin_list.json()
	)
