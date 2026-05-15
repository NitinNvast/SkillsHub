#!/bin/bash
set -e

echo "→ Running Alembic migrations…"
uv run alembic upgrade head

echo "→ Seeding users + skills catalog…"
uv run python -m app.seed.seed_demo

echo "→ Seeding demo employee profiles (requires VOYAGE_API_KEY)…"
uv run python -m app.seed.seed_employees || echo "⚠  Demo employee seeding skipped — run manually: docker compose exec backend uv run python -m app.seed.seed_employees"

echo "→ Starting API server…"
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
