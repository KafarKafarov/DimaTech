.PHONY: lint format test migrate down clear

lint:
	python3 -m ruff check src tests main.py migrations
	python3 -m mypy src tests

format:
	python3 -m ruff format src tests main.py migrations

test:
	python3 -m pytest

migrate:
	python3 -m alembic upgrade head

down:
	docker compose down

clear:
	docker compose down -v
