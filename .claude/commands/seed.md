Re-seed the SkillsHub demo database.

Run in order:

1. Seed demo users (hr@demo.com / emp@demo.com, password: demo123) and the skills catalog (~40 canonical skills):
```
docker compose exec backend uv run python -m app.seed.seed_demo
```

2. Seed 12 realistic employee profiles with Voyage AI embeddings (requires VOYAGE_API_KEY in .env):
```
docker compose exec backend uv run python -m app.seed.seed_employees
```

Step 2 calls the Voyage API and takes ~30 seconds. Skip it if VOYAGE_API_KEY is not set.

If running locally (not in Docker), run from the `backend/` directory replacing `docker compose exec backend` with nothing.
