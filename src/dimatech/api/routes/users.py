"""Маршруты пользователя."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import get_current_user, get_session
from dimatech.db.models import Account, Payment, User
from dimatech.repositories.account import AccountRepository
from dimatech.repositories.payment import PaymentRepository
from dimatech.schemas.user import AccountRead, PaymentRead

router = APIRouter(prefix='/users', tags=['users'])


def build_accounts_payload(*, accounts: list[Account]) -> list[AccountRead]:
	"""Преобразует список ORM-счетов в ответ API."""
	payload: list[AccountRead] = []
	for account in accounts:
		payload.append(AccountRead.model_validate(account))
	return payload


def build_payments_payload(*, payments: list[Payment]) -> list[PaymentRead]:
	"""Преобразует список ORM-платежей в ответ API."""
	payload: list[PaymentRead] = []
	for payment in payments:
		payload.append(PaymentRead.model_validate(payment))
	return payload


@router.get('/me/accounts', response_model=list[AccountRead])
async def list_my_accounts(
	current_user: User = Depends(get_current_user),
	session: AsyncSession = Depends(get_session),
) -> list[AccountRead]:
	"""Возвращает список счетов текущего пользователя."""
	repository = AccountRepository(session=session)
	accounts = await repository.list_by_user_id(user_id=current_user.id)
	return build_accounts_payload(accounts=accounts)


@router.get('/me/payments', response_model=list[PaymentRead])
async def list_my_payments(
	current_user: User = Depends(get_current_user),
	session: AsyncSession = Depends(get_session),
) -> list[PaymentRead]:
	"""Возвращает список платежей текущего пользователя."""
	repository = PaymentRepository(session=session)
	payments = await repository.list_by_user_id(user_id=current_user.id)
	return build_payments_payload(payments=payments)
