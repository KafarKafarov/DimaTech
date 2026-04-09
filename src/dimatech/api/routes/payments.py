"""Маршрут обработки платежного вебхука."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from dimatech.api.dependencies import get_session, get_settings_dependency
from dimatech.api.docs import VALIDATION_ERROR_RESPONSE, build_error_response
from dimatech.core.config import Settings
from dimatech.schemas.payment import PaymentWebhookRequest, PaymentWebhookResponse
from dimatech.services.payment import PaymentWebhookService

router = APIRouter(prefix='/payments', tags=['payments'])


@router.post(
	'/webhook',
	response_model=PaymentWebhookResponse,
	status_code=status.HTTP_200_OK,
	summary='Обработка платежного вебхука',
	description=(
		'Проверяет подпись вебхука, создает счет при отсутствии, '
		'фиксирует платеж и начисляет сумму на баланс.'
	),
	response_description='Результат обработки платежной транзакции.',
	responses={
		status.HTTP_400_BAD_REQUEST: build_error_response(
			description='Подпись вебхука не прошла проверку.',
			detail='Некорректная подпись вебхука.',
		),
		status.HTTP_404_NOT_FOUND: build_error_response(
			description='Пользователь, указанный в вебхуке, не найден.',
			detail='Пользователь не найден.',
		),
		status.HTTP_409_CONFLICT: build_error_response(
			description='Конфликт данных счета или транзакции.',
			detail='Счет с таким идентификатором принадлежит другому пользователю.',
		),
		422: VALIDATION_ERROR_RESPONSE,
	},
)
async def process_payment_webhook(
	payload: PaymentWebhookRequest,
	session: AsyncSession = Depends(get_session),
	settings: Settings = Depends(get_settings_dependency),
) -> PaymentWebhookResponse:
	"""Обрабатывает вебхук от внешней платежной системы."""
	service = PaymentWebhookService(session=session, settings=settings)
	return await service.process(payload=payload)
