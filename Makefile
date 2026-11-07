.PHONY: up down test lint format run seed reconcile evaluate test-integration

up:
	docker compose up -d

down:
	docker compose down

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

run:
	uv run uvicorn ragsync.api:app --reload

seed:
	uv run python -m ragsync.sync

reconcile:
	uv run python -m ragsync.sync nightly

evaluate:
	uv run python -m ragsync.evaluate

test-integration:
	TEST_DATABASE_URL=postgresql://postgres:dev@localhost:5432/ragsync_test uv run pytest tests/test_integration_sync.py -v
