"""Маршруты аутентификации."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import get_current_user, get_session, get_settings_dependency
from dimatech.core.config import Settings
from dimatech.db.models import User
from dimatech.repositories.user import UserRepository
from dimatech.schemas.auth import LoginRequest, TokenResponse
from dimatech.schemas.user import UserRead
from dimatech.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Авторизует пользователя по email и паролю."""
    service = AuthService(settings=settings, user_repository=UserRepository(session=session))
    return await service.login(email=str(payload.email), password=payload.password)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Возвращает данные текущего пользователя."""
    return UserRead.model_validate(current_user)
