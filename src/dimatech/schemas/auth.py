"""Схемы аутентификации."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from dimatech.db.models import UserRole


class AuthUserRead(BaseModel):
    """Краткое представление пользователя в ответе аутентификации."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole


class LoginRequest(BaseModel):
    """Тело запроса на аутентификацию."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Ответ с access token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserRead
