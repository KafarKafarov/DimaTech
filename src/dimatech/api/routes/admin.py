"""Маршруты администратора."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import (
    get_admin_user,
    get_cache_dependency,
    get_session,
    get_settings_dependency,
)
from dimatech.cache.keys import admin_users_key
from dimatech.cache.redis import BaseCache
from dimatech.core.config import Settings
from dimatech.db.models import User
from dimatech.repositories.user import UserRepository
from dimatech.schemas.user import (
    UserCreateRequest,
    UserRead,
    UserUpdateRequest,
    UserWithAccountsRead,
)
from dimatech.services.user import UserService

router = APIRouter(prefix="/admin", tags=["admin"])
USER_WITH_ACCOUNTS_ADAPTER = TypeAdapter(list[UserWithAccountsRead])


@router.get("/users", response_model=list[UserWithAccountsRead])
async def list_users(
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
    cache: BaseCache = Depends(get_cache_dependency),
    settings: Settings = Depends(get_settings_dependency),
) -> list[UserWithAccountsRead]:
    """Возвращает список пользователей и их счетов."""
    cached_users = await cache.get(admin_users_key())
    if cached_users is not None:
        return USER_WITH_ACCOUNTS_ADAPTER.validate_json(cached_users)

    repository = UserRepository(session=session)
    users = await repository.list_with_accounts()
    payload = [UserWithAccountsRead.model_validate(user) for user in users]
    await cache.set(
        admin_users_key(),
        USER_WITH_ACCOUNTS_ADAPTER.dump_json(payload).decode(),
        ttl_seconds=settings.cache_ttl_seconds,
    )
    return payload


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
    cache: BaseCache = Depends(get_cache_dependency),
) -> UserRead:
    """Создает нового пользователя."""
    service = UserService(
        session=session,
        user_repository=UserRepository(session=session),
        cache=cache,
    )
    user = await service.create_user(payload=payload)
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
    cache: BaseCache = Depends(get_cache_dependency),
) -> UserRead:
    """Частично обновляет пользователя."""
    service = UserService(
        session=session,
        user_repository=UserRepository(session=session),
        cache=cache,
    )
    user = await service.update_user(user_id=user_id, payload=payload)
    return UserRead.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
    cache: BaseCache = Depends(get_cache_dependency),
) -> Response:
    """Удаляет пользователя."""
    service = UserService(
        session=session,
        user_repository=UserRepository(session=session),
        cache=cache,
    )
    await service.delete_user(user_id=user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
