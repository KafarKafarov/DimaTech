"""Репозиторий платежей."""

from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.db.models import Payment


class PaymentRepository:
	"""Инкапсулирует операции над платежами."""

	def __init__(
			self,
			*,
			session: AsyncSession,
	) -> None:
		"""Сохраняет ссылку на сессию."""
		self._session = session

	async def list_by_user_id(
			self,
			*,
			user_id: int,
	) -> list[Payment]:
		"""Возвращает платежи пользователя в обратном хронологическом порядке."""
		query: Select[tuple[Payment]] = (
			select(Payment)
			.where(Payment.user_id == user_id)
			.order_by(Payment.created_at.desc(), Payment.id.desc())
		)
		result = await self._session.execute(query)
		return list(result.scalars().all())

	async def get_by_transaction_id(
			self,
			*,
			transaction_id: str,
	) -> Payment | None:
		"""Ищет платеж по внешнему идентификатору транзакции."""
		query: Select[tuple[Payment]] = select(Payment)
		query = query.where(Payment.transaction_id == transaction_id)
		result = await self._session.execute(query)
		return result.scalar_one_or_none()

	async def create(
		self,
		*,
		transaction_id: str,
		user_id: int,
		account_id: int,
		amount: Decimal,
	) -> Payment:
		"""Создает запись о платеже."""
		payment = Payment(
			transaction_id=transaction_id,
			user_id=user_id,
			account_id=account_id,
			amount=amount,
		)
		self._session.add(payment)
		await self._session.flush()
		return payment
