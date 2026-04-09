"""Схемы платежей и вебхука."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentWebhookRequest(BaseModel):
	"""Тело входящего вебхука от платежной системы."""

	model_config = ConfigDict(
		json_schema_extra={
			'example': {
				'transaction_id': '5eae174f-7cd0-472c-bd36-35660f00132b',
				'user_id': 1,
				'account_id': 1,
				'amount': 100,
				'signature': (
					'7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8'
				),
			},
		}
	)

	transaction_id: str = Field(
		min_length=1,
		max_length=64,
		description='Уникальный идентификатор транзакции во внешней системе.',
	)
	user_id: int = Field(
		gt=0,
		description='Идентификатор пользователя.',
	)
	account_id: int = Field(
		gt=0,
		description='Идентификатор счета пользователя.',
	)
	amount: Decimal = Field(
		gt=0,
		max_digits=12,
		decimal_places=2,
		description='Сумма пополнения.',
	)
	signature: str = Field(
		min_length=64,
		max_length=64,
		description='SHA256-подпись входящего вебхука.',
	)


class PaymentWebhookResponse(BaseModel):
	"""Ответ обработчика вебхука."""

	model_config = ConfigDict(
		from_attributes=True,
		json_schema_extra={
			'example': {
				'status': 'processed',
				'account_id': 1,
				'transaction_id': '5eae174f-7cd0-472c-bd36-35660f00132b',
			},
		},
	)

	status: str
	account_id: int
	transaction_id: str
