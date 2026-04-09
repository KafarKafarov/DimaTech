"""Схемы платежей и вебхука."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentWebhookRequest(BaseModel):
	"""Тело входящего вебхука от платежной системы."""

	transaction_id: str = Field(min_length=1, max_length=64)
	user_id: int = Field(gt=0)
	account_id: int = Field(gt=0)
	amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
	signature: str = Field(min_length=64, max_length=64)


class PaymentWebhookResponse(BaseModel):
	"""Ответ обработчика вебхука."""

	model_config = ConfigDict(from_attributes=True)

	status: str
	account_id: int
	transaction_id: str
