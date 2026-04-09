"""Сервис аутентификации."""

from __future__ import annotations

from fastapi import HTTPException, status

from dimatech.core.config import Settings
from dimatech.core.security import create_access_token, verify_password
from dimatech.repositories.user import UserRepository
from dimatech.schemas.auth import AuthUserRead, TokenResponse


class AuthService:
    """Отвечает за аутентификацию пользователей."""

    def __init__(self, *, settings: Settings, user_repository: UserRepository) -> None:
        """Сохраняет зависимости сервиса."""
        self._settings = settings
        self._user_repository = user_repository

    async def login(self, *, email: str, password: str) -> TokenResponse:
        """Проверяет учетные данные и возвращает токен доступа."""
        user = await self._user_repository.get_by_email(email=email)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль.",
            )

        password_is_valid = verify_password(
            password=password,
            password_hash=user.password_hash,
        )
        if not password_is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль.",
            )

        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
            settings=self._settings,
        )

        return TokenResponse(
            access_token=token,
            expires_in=self._settings.access_token_expire_minutes * 60,
            user=AuthUserRead.model_validate(user),
        )
