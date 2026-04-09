"""Сервисы пользовательских и административных операций."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.cache.redis import BaseCache
from dimatech.core.security import hash_password
from dimatech.db.models import User
from dimatech.repositories.user import UserRepository
from dimatech.schemas.user import UserCreateRequest, UserUpdateRequest
from dimatech.services.cache import CacheInvalidationService


class UserService:
    """Сервис операций над пользователями."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        user_repository: UserRepository,
        cache: BaseCache,
    ) -> None:
        """Сохраняет зависимости сервиса."""
        self._session = session
        self._user_repository = user_repository
        self._cache_invalidation = CacheInvalidationService(cache=cache)

    async def create_user(self, *, payload: UserCreateRequest) -> User:
        """Создает пользователя и фиксирует изменения."""
        existing_user = await self._user_repository.get_by_email(email=payload.email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует.",
            )

        user = await self._user_repository.create(
            email=str(payload.email),
            full_name=payload.full_name,
            password_hash=hash_password(password=payload.password),
        )
        await self._session.commit()
        await self._session.refresh(user)
        await self._cache_invalidation.invalidate_admin_users()
        return user

    async def update_user(self, *, user_id: int, payload: UserUpdateRequest) -> User:
        """Частично обновляет пользователя."""
        user = await self._user_repository.get_by_id(user_id=user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден.",
            )

        if payload.email is not None and payload.email != user.email:
            same_email_user = await self._user_repository.get_by_email(email=str(payload.email))
            if same_email_user is not None and same_email_user.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Пользователь с таким email уже существует.",
                )
            user.email = str(payload.email)

        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.password is not None:
            user.password_hash = hash_password(password=payload.password)
        if payload.is_active is not None:
            user.is_active = payload.is_active

        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Не удалось обновить пользователя из-за конфликта данных.",
            ) from error

        await self._session.refresh(user)
        await self._cache_invalidation.invalidate_user_related(user_id=user.id)
        return user

    async def delete_user(self, *, user_id: int) -> None:
        """Удаляет пользователя по идентификатору."""
        user = await self._user_repository.get_by_id(user_id=user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден.",
            )

        await self._user_repository.delete(user=user)
        await self._session.commit()
        await self._cache_invalidation.invalidate_user_related(user_id=user_id)
