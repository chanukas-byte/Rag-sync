.PHONY: up down test lint format run seed

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
