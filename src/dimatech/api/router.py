"""Композиция маршрутов приложения."""

from fastapi import APIRouter

from dimatech.api.routes.admin import router as admin_router
from dimatech.api.routes.auth import router as auth_router
from dimatech.api.routes.payments import router as payments_router
from dimatech.api.routes.users import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(payments_router)
