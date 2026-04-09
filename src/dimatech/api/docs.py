"""Константы и вспомогательные функции OpenAPI-документации."""

from dimatech.schemas.common import ErrorResponse

OpenApiResponse = dict[str, object]

OPENAPI_TAGS: list[dict[str, str]] = [
	{
		'name': 'auth',
		'description': 'Аутентификация пользователя и получение данных текущей сессии.',
	},
	{
		'name': 'users',
		'description': 'Операции, доступные обычному пользователю: счета и платежи.',
	},
	{
		'name': 'admin',
		'description': 'Административное управление пользователями и просмотр счетов.',
	},
	{
		'name': 'payments',
		'description': 'Прием и обработка вебхуков платежной системы.',
	},
	{
		'name': 'health',
		'description': 'Служебные проверки доступности приложения.',
	},
]

VALIDATION_ERROR_RESPONSE: OpenApiResponse = {
	'description': 'Ошибка валидации входных данных.',
}


def build_error_response(*, description: str, detail: str) -> OpenApiResponse:
	"""Строит OpenAPI-описание стандартной ошибки API."""
	return {
		'model': ErrorResponse,
		'description': description,
		'content': {
			'application/json': {
				'example': {
					'detail': detail,
				},
			},
		},
	}
