.PHONY: up down dev test eval lint format seed

up:
	docker compose up -d

down:
	docker compose down

seed:
	python3.11 data/scripts/generate_seed.py
	python3.11 data/scripts/load_seed.py

dev:
	python3.11 -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001 --reload

test:
	python3.11 -m pytest backend/tests

eval:
	python3.11 evals/run_risk_eval.py

lint:
	python3.11 -m ruff check backend

format:
	python3.11 -m ruff format backend
