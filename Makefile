PYTHON ?= python3

.PHONY: lint format test migrate down clear

lint:
	$(PYTHON) -m ruff check src tests main.py migrations
	$(PYTHON) -m mypy src tests

format:
	$(PYTHON) -m ruff format src tests main.py migrations

test:
	$(PYTHON) -m pytest

migrate:
	$(PYTHON) -m alembic upgrade head

down:
	docker compose down

clear:
	docker compose down -v
