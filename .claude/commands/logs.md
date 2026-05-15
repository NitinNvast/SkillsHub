Show Docker Compose logs for SkillsHub services.

Show the last 50 lines from all services:
```
docker compose logs --tail=50
```

To follow a specific service live:
- Backend only: `docker compose logs -f backend`
- Frontend only: `docker compose logs -f frontend`
- Postgres only: `docker compose logs -f postgres`

If the argument `$ARGUMENTS` is provided, use it as the service name (backend / frontend / postgres).
