"""Маршруты пользователя."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import get_current_user, get_session
from dimatech.db.models import User
from dimatech.repositories.account import AccountRepository
from dimatech.repositories.payment import PaymentRepository
from dimatech.schemas.user import AccountRead, PaymentRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/accounts", response_model=list[AccountRead])
async def list_my_accounts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[AccountRead]:
    """Возвращает список счетов текущего пользователя."""
    repository = AccountRepository(session=session)
    accounts = await repository.list_by_user_id(user_id=current_user.id)
    return [AccountRead.model_validate(account) for account in accounts]


@router.get("/me/payments", response_model=list[PaymentRead])
async def list_my_payments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[PaymentRead]:
    """Возвращает список платежей текущего пользователя."""
    repository = PaymentRepository(session=session)
    payments = await repository.list_by_user_id(user_id=current_user.id)
    return [PaymentRead.model_validate(payment) for payment in payments]
