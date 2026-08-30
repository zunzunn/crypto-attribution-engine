# Simple developer convenience targets. All *v1* commands assume the
# virtualenv at v1/backend/.venv.

.PHONY: backend-install test test-unit test-api dev dev-reload migrate-db seed-demo reset-demo compose-up compose-down

backend-install:
	python3 -m venv v1/backend/.venv
	v1/backend/.venv/bin/pip install --upgrade pip
	v1/backend/.venv/bin/pip install --no-cache-dir -r v1/backend/requirements.txt -r v1/backend/requirements-dev.txt

test:
	cd v1/backend && .venv/bin/pytest

test-unit:
	cd v1/backend && .venv/bin/pytest tests/unit

test-api:
	cd v1/backend && .venv/bin/pytest tests/api

dev:
	cd v1/backend && .venv/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000

dev-reload:
	cd v1/backend && .venv/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload

# Create/apply Alembic migrations (requires DATABASE_URL in v1/backend/.env).
migrate-db:
	cd v1/backend && .venv/bin/alembic -c alembic.ini upgrade head

# Seed the DEVELOPMENT database with deterministic SYNTHETIC demo data
# (SEED -> INTER -> VASP_A + a clearly-marked demo entity). Idempotent - safe
# to re-run; never point at a production database.
seed-demo:
	cd v1/backend && .venv/bin/python -m app.dev.seed_demo

# Remove only the demo-owned rows from the development database.
reset-demo:
	cd v1/backend && .venv/bin/python -m app.dev.seed_demo --reset

# Docker Compose PostgreSQL (optional; Homebrew Postgres also works).
compose-up:
	docker compose up -d postgres

compose-down:
	docker compose down