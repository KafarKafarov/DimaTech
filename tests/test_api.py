"""Интеграционные тесты API."""

from __future__ import annotations

from http import HTTPStatus
from typing import cast

import pytest
from httpx import AsyncClient

from dimatech.services.payment import WebhookSignaturePayload, build_webhook_signature


async def authenticate(*, client: AsyncClient, email: str, password: str) -> str:
    """Логинит пользователя и возвращает bearer token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == HTTPStatus.OK
    return cast(str, response.json()["access_token"])


def auth_headers(*, token: str) -> dict[str, str]:
    """Строит HTTP-заголовки с bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_user_can_login_and_read_own_profile(client: AsyncClient) -> None:
    """Пользователь может авторизоваться и получить данные о себе."""
    token = await authenticate(
        client=client,
        email="user@example.com",
        password="user12345",
    )

    response = await client.get("/api/v1/auth/me", headers=auth_headers(token=token))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "email": "user@example.com",
        "full_name": "Тестовый пользователь",
        "role": "user",
    }


@pytest.mark.asyncio
async def test_login_rejects_invalid_password(client: AsyncClient) -> None:
    """Логин должен отклонять неверный пароль."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-pass"},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["detail"] == "Неверный email или пароль."


@pytest.mark.asyncio
async def test_user_cannot_access_admin_routes(client: AsyncClient) -> None:
    """Обычный пользователь не должен иметь доступ к админским методам."""
    token = await authenticate(
        client=client,
        email="user@example.com",
        password="user12345",
    )

    response = await client.get("/api/v1/admin/users", headers=auth_headers(token=token))

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Недостаточно прав для выполнения операции."


@pytest.mark.asyncio
async def test_admin_can_create_update_and_delete_user(client: AsyncClient) -> None:
    """Администратор может выполнить полный CRUD над пользователем."""
    token = await authenticate(
        client=client,
        email="admin@example.com",
        password="admin12345",
    )
    headers = auth_headers(token=token)

    create_response = await client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "email": "new-user@example.com",
            "full_name": "Новый пользователь",
            "password": "new-user-123",
        },
    )
    assert create_response.status_code == HTTPStatus.CREATED
    user_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/admin/users/{user_id}",
        headers=headers,
        json={"full_name": "Обновленное имя", "is_active": False},
    )
    assert update_response.status_code == HTTPStatus.OK
    assert update_response.json()["full_name"] == "Обновленное имя"

    delete_response = await client.delete(
        f"/api/v1/admin/users/{user_id}",
        headers=headers,
    )
    assert delete_response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature(client: AsyncClient) -> None:
    """Вебхук с неправильной подписью должен отклоняться."""
    response = await client.post(
        "/api/v1/payments/webhook",
        json={
            "transaction_id": "tx-invalid-signature",
            "user_id": 1,
            "account_id": 1,
            "amount": 50,
            "signature": "0" * 64,
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["detail"] == "Некорректная подпись вебхука."


@pytest.mark.asyncio
async def test_webhook_creates_account_updates_payments_and_invalidates_cache(
    client: AsyncClient,
) -> None:
    """Вебхук создает счет, начисляет средства и сбрасывает кеш админского списка."""
    admin_token = await authenticate(
        client=client,
        email="admin@example.com",
        password="admin12345",
    )
    admin_headers = auth_headers(token=admin_token)

    first_admin_list = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert first_admin_list.status_code == HTTPStatus.OK
    assert len(first_admin_list.json()[0]["accounts"]) == 1

    payload: WebhookSignaturePayload = {
        "transaction_id": "tx-create-account",
        "user_id": 1,
        "account_id": 10,
        "amount": 100,
    }
    signature = build_webhook_signature(payload=payload, secret_key="test-payment-secret")
    webhook_response = await client.post(
        "/api/v1/payments/webhook",
        json={**payload, "signature": signature},
    )

    assert webhook_response.status_code == HTTPStatus.OK
    assert webhook_response.json()["status"] == "processed"

    second_admin_list = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert second_admin_list.status_code == HTTPStatus.OK
    user_accounts = second_admin_list.json()[0]["accounts"]
    assert {account["id"] for account in user_accounts} == {1, 10}

    user_token = await authenticate(
        client=client,
        email="user@example.com",
        password="user12345",
    )
    user_headers = auth_headers(token=user_token)
    payments_response = await client.get("/api/v1/users/me/payments", headers=user_headers)
    accounts_response = await client.get("/api/v1/users/me/accounts", headers=user_headers)

    assert payments_response.status_code == HTTPStatus.OK
    assert len(payments_response.json()) == 1
    assert payments_response.json()[0]["transaction_id"] == "tx-create-account"
    assert accounts_response.status_code == HTTPStatus.OK
    assert any(
        account["id"] == 10 and account["balance"] == "100.00"
        for account in accounts_response.json()
    )


@pytest.mark.asyncio
async def test_webhook_is_idempotent_by_transaction_id(client: AsyncClient) -> None:
    """Повторная обработка той же транзакции не должна менять баланс повторно."""
    payload: WebhookSignaturePayload = {
        "transaction_id": "tx-idempotent",
        "user_id": 1,
        "account_id": 1,
        "amount": 50,
    }
    signature = build_webhook_signature(payload=payload, secret_key="test-payment-secret")

    first_response = await client.post(
        "/api/v1/payments/webhook",
        json={**payload, "signature": signature},
    )
    second_response = await client.post(
        "/api/v1/payments/webhook",
        json={**payload, "signature": signature},
    )

    assert first_response.status_code == HTTPStatus.OK
    assert first_response.json()["status"] == "processed"
    assert second_response.status_code == HTTPStatus.OK
    assert second_response.json()["status"] == "already_processed"

    user_token = await authenticate(
        client=client,
        email="user@example.com",
        password="user12345",
    )
    user_headers = auth_headers(token=user_token)
    accounts_response = await client.get("/api/v1/users/me/accounts", headers=user_headers)
    payments_response = await client.get("/api/v1/users/me/payments", headers=user_headers)

    assert accounts_response.status_code == HTTPStatus.OK
    assert any(
        account["id"] == 1 and account["balance"] == "1050.00"
        for account in accounts_response.json()
    )
    assert payments_response.status_code == HTTPStatus.OK
    assert len(payments_response.json()) == 1
