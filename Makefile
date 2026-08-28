# Simple developer convenience targets. All *backend* commands assume the
# virtualenv at backend/.venv.

.PHONY: backend-install test test-unit test-api dev dev-reload migrate-db compose-up compose-down

backend-install:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install --upgrade pip
	backend/.venv/bin/pip install --no-cache-dir -r backend/requirements.txt -r backend/requirements-dev.txt

test:
	cd backend && .venv/bin/pytest

test-unit:
	cd backend && .venv/bin/pytest tests/unit

test-api:
	cd backend && .venv/bin/pytest tests/api

dev:
	cd backend && .venv/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000

dev-reload:
	cd backend && .venv/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload

# Create/apply Alembic migrations (requires DATABASE_URL in backend/.env).
migrate-db:
	cd backend && .venv/bin/alembic -c alembic.ini upgrade head

# Docker Compose PostgreSQL (optional; Homebrew Postgres also works).
compose-up:
	docker compose up -d postgres

compose-down:
	docker compose down