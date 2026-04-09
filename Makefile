.PHONY: lint format test migrate down clear

lint:
	.venv/bin/ruff check src tests main.py migrations
	.venv/bin/mypy src tests

format:
	.venv/bin/ruff format src tests main.py migrations

test:
	.venv/bin/pytest

migrate:
	.venv/bin/alembic upgrade head

down:
	docker compose down

clear:
	docker compose down -v
