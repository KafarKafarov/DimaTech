"""Репозиторий пользователей."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dimatech.db.models import User, UserRole


class UserRepository:
    """Инкапсулирует операции над пользователями."""

    def __init__(self, *, session: AsyncSession) -> None:
        """Сохраняет ссылку на сессию."""
        self._session = session

    async def get_by_id(self, *, user_id: int) -> User | None:
        """Возвращает пользователя по идентификатору."""
        query: Select[tuple[User]] = select(User).where(User.id == user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, *, email: str) -> User | None:
        """Возвращает пользователя по email."""
        query: Select[tuple[User]] = select(User).where(User.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_with_accounts(self) -> list[User]:
        """Возвращает список пользователей со счетами."""
        query: Select[tuple[User]] = (
            select(User).options(selectinload(User.accounts)).order_by(User.id)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        email: str,
        full_name: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Создает пользователя."""
        user = User(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            role=role,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def delete(self, *, user: User) -> None:
        """Удаляет пользователя."""
        await self._session.delete(user)
