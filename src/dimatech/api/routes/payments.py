"""Маршрут обработки платежного вебхука."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import (
    get_cache_dependency,
    get_session,
    get_settings_dependency,
)
from dimatech.cache.redis import BaseCache
from dimatech.core.config import Settings
from dimatech.schemas.payment import PaymentWebhookRequest, PaymentWebhookResponse
from dimatech.services.payment import PaymentWebhookService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/webhook", response_model=PaymentWebhookResponse)
async def process_payment_webhook(
    payload: PaymentWebhookRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings_dependency),
    cache: BaseCache = Depends(get_cache_dependency),
) -> PaymentWebhookResponse:
    """Обрабатывает вебхук от внешней платежной системы."""
    service = PaymentWebhookService(session=session, settings=settings, cache=cache)
    return await service.process(payload=payload)
