"""Общие схемы ответов API."""

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
	"""Стандартная схема ошибки FastAPI."""

	model_config = ConfigDict(
		json_schema_extra={
			'example': {
				'detail': 'Недостаточно прав для выполнения операции.',
			},
		}
	)

	detail: str


class HealthcheckResponse(BaseModel):
	"""Ответ healthcheck-ручки."""

	model_config = ConfigDict(
		json_schema_extra={
			'example': {
				'status': 'ok',
			},
		}
	)

	status: str
