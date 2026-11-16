.PHONY: up down dev test test-unit test-integration eval lint format seed

up:
	docker compose up -d

down:
	docker compose down

seed:
	python3.11 data/scripts/generate_seed.py
	python3.11 backend/migrations/run_migrations.py
	python3.11 data/scripts/load_seed.py

dev:
	python3.11 -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001 --reload

test:
	python3.11 -m pytest backend/tests/unit
	python3.11 -m pytest backend/tests/integration

test-unit:
	python3.11 -m pytest backend/tests/unit

test-integration:
	python3.11 -m pytest backend/tests/integration

eval:
	python3.11 evals/run_risk_eval.py

lint:
	python3.11 -m ruff check backend

format:
	python3.11 -m ruff format backend
