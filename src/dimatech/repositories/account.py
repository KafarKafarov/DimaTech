"""Репозиторий счетов."""

from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.db.models import Account


class AccountRepository:
	"""Инкапсулирует операции над сущностью счета."""

	def __init__(self, *, session: AsyncSession) -> None:
		"""Сохраняет ссылку на сессию."""
		self._session = session

	async def list_by_user_id(self, *, user_id: int) -> list[Account]:
		"""Возвращает все счета пользователя."""
		query: Select[tuple[Account]] = select(Account).where(
			Account.user_id == user_id
		)
		query = query.order_by(Account.id)
		result = await self._session.execute(query)
		return list(result.scalars().all())

	async def get_by_id(self, *, account_id: int) -> Account | None:
		"""Ищет счет по идентификатору."""
		query: Select[tuple[Account]] = select(Account).where(Account.id == account_id)
		result = await self._session.execute(query)
		return result.scalar_one_or_none()

	async def get_by_id_and_user_id(
		self, *, account_id: int, user_id: int
	) -> Account | None:
		"""Ищет счет по идентификатору и владельцу."""
		query: Select[tuple[Account]] = select(Account).where(
			Account.id == account_id,
			Account.user_id == user_id,
		)
		result = await self._session.execute(query)
		return result.scalar_one_or_none()

	async def create(self, *, user_id: int, account_id: int | None = None) -> Account:
		"""Создает новый счет для пользователя."""
		account = Account(user_id=user_id)
		if account_id is not None:
			account.id = account_id
		self._session.add(account)
		await self._session.flush()
		return account

	async def add_amount(self, *, account: Account, amount: Decimal) -> Account:
		"""Начисляет сумму на баланс счета."""
		account.balance += amount
		await self._session.flush()
		return account
