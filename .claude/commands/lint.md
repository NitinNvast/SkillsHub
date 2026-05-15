Run all linters and type checkers for the SkillsHub project.

**Backend** (ruff, from repo root or inside Docker):
```
docker compose exec backend uv run ruff check backend/
docker compose exec backend uv run ruff format --check backend/
```

Or locally from `backend/`:
```
uv run ruff check .
uv run ruff format --check .
```

**Frontend** (ESLint + TypeScript, from `frontend/`):
```
pnpm lint
pnpm typecheck
```

Report all errors found. If asked to fix them, run `uv run ruff format .` for formatting issues and `uv run ruff check --fix .` for auto-fixable lint issues. Do not auto-fix TypeScript errors — report them for manual resolution.
