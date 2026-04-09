"""Интеграционные тесты платежного вебхука."""

from http import HTTPStatus

from httpx import AsyncClient

from tests.utils import auth_headers, authenticate, build_webhook_body


async def test_hook_bad_sig(client: AsyncClient) -> None:
	"""Неверная подпись должна приводить к 400."""
	response = await client.post(
		'/api/v1/payments/webhook',
		json={
			'transaction_id': 'tx-invalid-signature',
			'user_id': 1,
			'account_id': 1,
			'amount': 50,
			'signature': '0' * 64,
		},
	)

	assert response.status_code == HTTPStatus.BAD_REQUEST
	assert response.json()['detail'] == 'Некорректная подпись вебхука.'


async def test_hook_unknown_user(client: AsyncClient) -> None:
	"""Вебхук для неизвестного пользователя должен возвращать 404."""
	response = await client.post(
		'/api/v1/payments/webhook',
		json=build_webhook_body(
			transaction_id='tx-unknown-user',
			user_id=99,
			account_id=5,
			amount=100,
			secret_key='test-payment-secret',
		),
	)

	assert response.status_code == HTTPStatus.NOT_FOUND
	assert response.json()['detail'] == 'Пользователь не найден.'


async def test_hook_create_account(client: AsyncClient) -> None:
	"""Вебхук должен создавать отсутствующий счет и фиксировать платеж."""
	response = await client.post(
		'/api/v1/payments/webhook',
		json=build_webhook_body(
			transaction_id='tx-create-account',
			user_id=1,
			account_id=10,
			amount=100,
			secret_key='test-payment-secret',
		),
	)

	assert response.status_code == HTTPStatus.OK
	assert response.json()['status'] == 'processed'

	user_token = await authenticate(
		client=client,
		email='user@example.com',
		password='user12345',
	)
	headers = auth_headers(token=user_token)
	accounts_response = await client.get(
		'/api/v1/users/me/accounts',
		headers=headers,
	)
	payments_response = await client.get(
		'/api/v1/users/me/payments',
		headers=headers,
	)

	assert accounts_response.status_code == HTTPStatus.OK
	assert any(
		account['id'] == 10 and account['balance'] == '100.00'
		for account in accounts_response.json()
	)
	assert payments_response.status_code == HTTPStatus.OK
	assert payments_response.json()[0]['transaction_id'] == 'tx-create-account'


async def test_hook_idempotent(client: AsyncClient) -> None:
	"""Повторная транзакция не должна начислять средства дважды."""
	payload = build_webhook_body(
		transaction_id='tx-idempotent',
		user_id=1,
		account_id=1,
		amount=50,
		secret_key='test-payment-secret',
	)

	first_response = await client.post('/api/v1/payments/webhook', json=payload)
	second_response = await client.post('/api/v1/payments/webhook', json=payload)

	assert first_response.status_code == HTTPStatus.OK
	assert first_response.json()['status'] == 'processed'
	assert second_response.status_code == HTTPStatus.OK
	assert second_response.json()['status'] == 'already_processed'

	user_token = await authenticate(
		client=client,
		email='user@example.com',
		password='user12345',
	)
	headers = auth_headers(token=user_token)
	accounts_response = await client.get(
		'/api/v1/users/me/accounts',
		headers=headers,
	)
	payments_response = await client.get(
		'/api/v1/users/me/payments',
		headers=headers,
	)

	assert any(
		account['id'] == 1 and account['balance'] == '1050.00'
		for account in accounts_response.json()
	)
	assert len(payments_response.json()) == 1


async def test_hook_account_conflict(client: AsyncClient) -> None:
	"""Счет другого пользователя не должен быть доступен в чужом вебхуке."""
	response = await client.post(
		'/api/v1/payments/webhook',
		json=build_webhook_body(
			transaction_id='tx-account-conflict',
			user_id=2,
			account_id=1,
			amount=10,
			secret_key='test-payment-secret',
		),
	)

	assert response.status_code == HTTPStatus.CONFLICT
	assert (
		response.json()['detail']
		== 'Счет с таким идентификатором принадлежит другому пользователю.'
	)


async def test_hook_bad_amount(client: AsyncClient) -> None:
	"""Отрицательная сумма должна отсеиваться валидацией схемы."""
	response = await client.post(
		'/api/v1/payments/webhook',
		json={
			'transaction_id': 'tx-negative',
			'user_id': 1,
			'account_id': 1,
			'amount': -1,
			'signature': '0' * 64,
		},
	)

	assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
