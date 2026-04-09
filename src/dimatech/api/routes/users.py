"""Маршруты пользователя."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import (
    get_cache_dependency,
    get_current_user,
    get_session,
    get_settings_dependency,
)
from dimatech.cache.keys import user_accounts_key, user_payments_key
from dimatech.cache.redis import BaseCache
from dimatech.core.config import Settings
from dimatech.db.models import User
from dimatech.repositories.account import AccountRepository
from dimatech.repositories.payment import PaymentRepository
from dimatech.schemas.user import AccountRead, PaymentRead

router = APIRouter(prefix="/users", tags=["users"])
ACCOUNTS_ADAPTER = TypeAdapter(list[AccountRead])
PAYMENTS_ADAPTER = TypeAdapter(list[PaymentRead])


@router.get("/me/accounts", response_model=list[AccountRead])
async def list_my_accounts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: BaseCache = Depends(get_cache_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> list[AccountRead]:
    """Возвращает список счетов текущего пользователя."""
    cache_key = user_accounts_key(user_id=current_user.id)
    cached_accounts = await cache.get(cache_key)
    if cached_accounts is not None:
        return ACCOUNTS_ADAPTER.validate_json(cached_accounts)

    repository = AccountRepository(session=session)
    accounts = await repository.list_by_user_id(user_id=current_user.id)
    payload = [AccountRead.model_validate(account) for account in accounts]
    await cache.set(
        cache_key,
        ACCOUNTS_ADAPTER.dump_json(payload).decode(),
        ttl_seconds=settings.cache_ttl_seconds,
    )
    return payload


@router.get("/me/payments", response_model=list[PaymentRead])
async def list_my_payments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: BaseCache = Depends(get_cache_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> list[PaymentRead]:
    """Возвращает список платежей текущего пользователя."""
    cache_key = user_payments_key(user_id=current_user.id)
    cached_payments = await cache.get(cache_key)
    if cached_payments is not None:
        return PAYMENTS_ADAPTER.validate_json(cached_payments)

    repository = PaymentRepository(session=session)
    payments = await repository.list_by_user_id(user_id=current_user.id)
    payload = [PaymentRead.model_validate(payment) for payment in payments]
    await cache.set(
        cache_key,
        PAYMENTS_ADAPTER.dump_json(payload).decode(),
        ttl_seconds=settings.cache_ttl_seconds,
    )
    return payload
