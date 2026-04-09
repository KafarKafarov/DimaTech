"""Сервис обработки платежного вебхука."""

from decimal import Decimal
from hashlib import sha256
from secrets import compare_digest
from typing import TypedDict

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.cache.memory import BaseCache
from dimatech.core.config import Settings
from dimatech.db.models import Account
from dimatech.repositories.account import AccountRepository
from dimatech.repositories.payment import PaymentRepository
from dimatech.repositories.user import UserRepository
from dimatech.schemas.payment import PaymentWebhookRequest, PaymentWebhookResponse
from dimatech.services.cache import CacheInvalidationService


class WebhookSignaturePayload(TypedDict):
	"""Структура данных для вычисления подписи вне Pydantic-модели."""

	transaction_id: str
	user_id: int
	account_id: int
	amount: int | str | Decimal


def format_amount_for_signature(*, amount: Decimal) -> str:
	"""Нормализует сумму для формирования подписи без экспоненциальной записи."""
	normalized = format(amount.normalize(), 'f')
	if '.' not in normalized:
		return normalized
	return normalized.rstrip('0').rstrip('.')


def build_webhook_signature(
	*,
	payload: PaymentWebhookRequest | WebhookSignaturePayload,
	secret_key: str,
) -> str:
	"""Строит SHA256-подпись по правилам платежной системы."""
	if isinstance(payload, PaymentWebhookRequest):
		account_id = payload.account_id
		amount = payload.amount
		transaction_id = payload.transaction_id
		user_id = payload.user_id
	else:
		account_id = payload['account_id']
		amount = Decimal(str(payload['amount']))
		transaction_id = payload['transaction_id']
		user_id = payload['user_id']

	message = (
		f'{account_id}'
		f'{format_amount_for_signature(amount=amount)}'
		f'{transaction_id}'
		f'{user_id}'
		f'{secret_key}'
	)
	return sha256(message.encode('utf-8')).hexdigest()


class PaymentWebhookService:
	"""Обрабатывает входящие уведомления о пополнении счета."""

	def __init__(
		self,
		*,
		session: AsyncSession,
		settings: Settings,
		cache: BaseCache,
	) -> None:
		"""Сохраняет зависимости сервиса."""
		self._session = session
		self._settings = settings
		self._account_repository = AccountRepository(session=session)
		self._payment_repository = PaymentRepository(session=session)
		self._user_repository = UserRepository(session=session)
		self._cache_invalidation = CacheInvalidationService(cache=cache)

	async def process(
		self, *, payload: PaymentWebhookRequest
	) -> PaymentWebhookResponse:
		"""Проверяет подпись, обеспечивает идемпотентность и начисляет средства."""
		expected_signature = build_webhook_signature(
			payload=payload,
			secret_key=self._settings.payment_signature_secret,
		)
		if not compare_digest(payload.signature, expected_signature):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail='Некорректная подпись вебхука.',
			)

		existing_payment = await self._payment_repository.get_by_transaction_id(
			transaction_id=payload.transaction_id
		)
		if existing_payment is not None:
			return PaymentWebhookResponse(
				status='already_processed',
				account_id=existing_payment.account_id,
				transaction_id=existing_payment.transaction_id,
			)

		user = await self._user_repository.get_by_id(user_id=payload.user_id)
		if user is None:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail='Пользователь не найден.',
			)

		account = await self._ensure_account(payload=payload)
		try:
			await self._account_repository.add_amount(
				account=account, amount=payload.amount
			)
			await self._payment_repository.create(
				transaction_id=payload.transaction_id,
				user_id=payload.user_id,
				account_id=account.id,
				amount=payload.amount,
			)
			await self._session.commit()
		except IntegrityError:
			await self._session.rollback()
			duplicated_payment = await self._payment_repository.get_by_transaction_id(
				transaction_id=payload.transaction_id
			)
			if duplicated_payment is not None:
				return PaymentWebhookResponse(
					status='already_processed',
					account_id=duplicated_payment.account_id,
					transaction_id=duplicated_payment.transaction_id,
				)
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail='Не удалось обработать платеж из-за конфликта данных.',
			) from None

		await self._cache_invalidation.invalidate_user_related(user_id=payload.user_id)
		return PaymentWebhookResponse(
			status='processed',
			account_id=account.id,
			transaction_id=payload.transaction_id,
		)

	async def _ensure_account(self, *, payload: PaymentWebhookRequest) -> Account:
		"""Возвращает существующий счет пользователя или создает новый."""
		account = await self._account_repository.get_by_id(
			account_id=payload.account_id
		)
		if account is not None and account.user_id != payload.user_id:
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail='Счет с таким идентификатором принадлежит другому пользователю.',
			)
		if account is not None:
			return account

		return await self._account_repository.create(
			user_id=payload.user_id,
			account_id=payload.account_id,
		)
