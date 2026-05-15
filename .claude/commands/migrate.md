Run Alembic database migrations for the SkillsHub backend.

If Docker is running, use:
```
docker compose exec backend uv run alembic upgrade head
```

If running locally inside the backend directory:
```
cd backend && uv run alembic upgrade head
```

After running, confirm the migration applied by checking:
```
docker compose exec backend uv run alembic current
```

Report the current migration revision and whether it is up to date.
