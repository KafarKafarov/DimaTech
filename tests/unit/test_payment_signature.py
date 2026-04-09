"""Unit-тесты подписи платежного вебхука."""

from decimal import Decimal

from dimatech.services.payment import (
	build_webhook_signature,
	format_amount_for_signature,
)


def test_amount_int() -> None:
	"""Целая сумма должна сериализоваться без дробной части."""
	assert format_amount_for_signature(amount=Decimal('100.00')) == '100'


def test_amount_fraction() -> None:
	"""Дробная сумма должна сохранять значимые знаки после точки."""
	assert format_amount_for_signature(amount=Decimal('100.50')) == '100.5'


def test_sig_task_example() -> None:
	"""Подпись должна совпадать с примером из тестового задания."""
	signature = build_webhook_signature(
		payload={
			'transaction_id': '5eae174f-7cd0-472c-bd36-35660f00132b',
			'user_id': 1,
			'account_id': 1,
			'amount': 100,
		},
		secret_key='gfdmhghif38yrf9ew0jkf32',
	)

	assert (
		signature
		== '7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8'
	)


def test_sig_normalized_amount() -> None:
	"""Одинаковые суммы в разных форматах должны давать одну подпись."""
	signature_a = build_webhook_signature(
		payload={
			'transaction_id': 'tx-1',
			'user_id': 1,
			'account_id': 1,
			'amount': Decimal('10.00'),
		},
		secret_key='secret',
	)
	signature_b = build_webhook_signature(
		payload={
			'transaction_id': 'tx-1',
			'user_id': 1,
			'account_id': 1,
			'amount': '10',
		},
		secret_key='secret',
	)

	assert signature_a == signature_b
