.PHONY: install run sync test lint format migrate docker-build docker-up docker-down

install:
	pip install -e ".[dev]"

run:
	uvicorn tickethub.main:app --reload

sync:
	python -m tickethub.sync

test:
	pytest -v

lint:
	ruff check .

format:
	ruff format .

migrate:
	alembic upgrade head

docker-build:
	docker compose build

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down