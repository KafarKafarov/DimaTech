PYTHON := .venv/bin/python
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest
ALEMBIC := .venv/bin/alembic

.PHONY: lint format test migrate

lint:
	$(RUFF) check src tests main.py migrations
	$(MYPY) src tests

format:
	$(RUFF) format src tests main.py migrations

test:
	$(PYTEST)

migrate:
	$(ALEMBIC) upgrade head
