# SkillsHub

**An AI-Powered Skills Intelligence Platform.**
Upload a resume → auto-extract skills, projects, and proficiencies. Ask in natural language → get ranked candidates with plain-English reasoning.

Built for the SkillsHub hackathon. The two centerpieces are:

1. **Smart profile ingestion** — PDF/text resume → structured profile (Claude Sonnet, tool_use) → inferred related skills (deterministic rules + Claude Haiku) → HR review queue.
2. **Semantic natural-language search** — query parsing (Haiku) → pgvector HNSW hybrid retrieval → LLM re-rank with match scores and per-candidate reasoning (Sonnet).

Stretch goal implemented: **Skill Gap Analysis** — live talent pool coverage map on the HR dashboard.

---

## Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 (App Router) + TypeScript + Tailwind 4 |
| Backend | FastAPI + SQLAlchemy 2 (async) + Alembic + Pydantic v2 |
| Database | PostgreSQL 16 + pgvector (HNSW index, cosine similarity) |
| LLM | Claude Sonnet 4.6 (extraction, re-rank) + Claude Haiku 4.5 (inference, query parsing) |
| Embeddings | Voyage AI `voyage-3-large` (1024 dim) |
| Container | Docker Compose |

---

## Quick Start

**Prerequisites:** Docker, Docker Compose, an Anthropic API key, a Voyage AI API key.

```bash
git clone <repo>
cd skillshub

# 1. Copy and fill in your API keys
cp .env.example .env
# Required: ANTHROPIC_API_KEY, VOYAGE_API_KEY
# Required: JWT_SECRET  (generate: python -c "import secrets; print(secrets.token_urlsafe(48))")

# 2. Build and start everything
docker compose up --build
```

On first startup the backend automatically:
- Runs Alembic migrations (creates all tables + pgvector HNSW index)
- Seeds demo users and the canonical skills catalog
- Seeds 12 realistic demo employee profiles with Voyage AI embeddings

Open:
- **Frontend** → http://localhost:3000
- **API docs** → http://localhost:8000/docs

---

## Local Development (Without Docker)

### Prerequisites

- Python 3.11+ with [`uv`](https://docs.astral.sh/uv/) installed
- PostgreSQL 16 with the [pgvector extension](https://github.com/pgvector/pgvector)
- Node.js 18+ and [pnpm](https://pnpm.io/)
- API keys: `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`

### Backend

```bash
cd backend

# 1. Install dependencies
uv sync

# 2. Create backend/.env — copy from root .env.example, then change DATABASE_URL:
#    If Postgres is running via Docker Compose (port 5433 on host):
#      DATABASE_URL=postgresql+asyncpg://skillshub:skillshub_dev_pw@localhost:5433/skillshub
#    If using a local Postgres install (default port 5432):
#      DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/skillshub

# 3. Enable pgvector in your Postgres database
#    psql -U postgres -d skillshub -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 4. Run migrations
uv run alembic upgrade head

# 5. Seed demo users and skills catalog
uv run python -m app.seed.seed_demo

# 6. Seed 12 demo employee profiles (requires VOYAGE_API_KEY)
uv run python -m app.seed.seed_employees

# 7. Start the dev server (API on http://localhost:8000)
uv run uvicorn app.main:app --reload
```

Interactive API docs are available at **http://localhost:8000/docs** once the server is running.

### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Start the dev server (on http://localhost:3000)
pnpm dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` if the frontend is not picking up the backend URL automatically.

### Useful backend commands

```bash
uv run alembic downgrade -1                         # Rollback one migration
uv run alembic revision --autogenerate -m "msg"     # Generate a new migration
uv run pytest tests                                 # Run tests
uv run ruff check .                                 # Lint
uv run ruff format .                                # Format
```

---

## Demo Logins

| Role | Email | Password |
|---|---|---|
| HR | `hr@demo.com` | `demo1234` |
| Employee | `emp@demo.com` | `demo1234` |

---

## Demo Path

1. **Sign in as employee** (`emp@demo.com`) → **Upload Resume** → drop a PDF and watch Claude extract skills, projects, and certifications in ~20 seconds.
2. **Sign in as HR** (`hr@demo.com`) → **Review Queue** → see the extracted profile with AI-inferred skills (✨ badge). Click **Approve & Publish**.
3. **HR → Search** → try these queries:
   - *"Who can lead a React project with WebSocket experience?"*
   - *"Find a backend dev in Pune with 3+ years of Java and any payment gateway integration."*
   - *"Senior frontend engineers who haven't been on a new project recently."*
   - *"Full-stack developers with cloud (AWS or GCP) and microservices experience."*
4. **Click any result** → see the full profile, inferred skills with evidence, and project history.
5. **Dashboard** → see the **Skill Gap Analysis** panel showing talent pool coverage.

---

## Project Layout

```
skillshub/
├── backend/
│   ├── app/
│   │   ├── api/              HTTP routers (thin layer)
│   │   ├── services/         Business orchestration
│   │   ├── ai/
│   │   │   ├── pipelines/    extraction.py, inference.py, search.py
│   │   │   ├── prompts/      Claude tool schemas + system prompts
│   │   │   ├── client.py     Anthropic async client (singleton)
│   │   │   └── embeddings.py Voyage AI embedding client
│   │   ├── db/
│   │   │   ├── models/       SQLAlchemy ORM models
│   │   │   └── repos/        DB access layer (embeddings, employees)
│   │   ├── schemas/          Pydantic v2 DTOs
│   │   ├── core/             Config, JWT, deps
│   │   └── seed/             Demo data (seed_demo.py + seed_employees.py)
│   └── alembic/              Migrations
├── frontend/
│   ├── app/
│   │   ├── (auth)/           Login page
│   │   ├── (hr)/             Dashboard, Search, Review Queue, Directory
│   │   └── (employee)/       Upload, My Profile
│   ├── components/           SkillChip, ResultCard, ScoreRing
│   └── lib/                  API client, auth context, React Query hooks
├── scripts/                  DB init SQL
├── uploads/                  Resume PDFs (volume-mounted)
├── PRESENTATION.md           7-slide deck outline
├── DEMO_SCRIPT.md            2–3 minute demo walkthrough
└── docker-compose.yml
```

---

## AI Pipeline Detail

### Extraction (Hard Problem #1)
```
PDF → pypdf text extraction
    → Claude Sonnet tool_use (EXTRACT_PROFILE_TOOL)
         system: cached large prompt (saves ~80% input tokens on repeated calls)
         output: StructuredProfile JSON {name, skills[], projects[], certifications[]}
         each skill: {name, proficiency, years, evidence, confidence}
    → Deterministic inference (40+ rules: Next.js→React, Spring Boot→Java, …)
    → Claude Haiku inference (contextual: Stripe+Node → "Payment Integration")
    → Upsert employees + skills + projects
    → Voyage AI embed → pgvector upsert
    → Status: pending_review
```

### Search (Hard Problem #2)
```
NL query → Claude Haiku parse_query tool
            {semantic_text, required_skills, min_years_per_skill, location}
         → Voyage AI embed(semantic_text, input_type="query")
         → pgvector HNSW KNN + SQL pre-filters (availability, location, min years)
            top-20 candidates retrieved
         → Load full profiles + render_profile_summary()
         → Claude Sonnet rank_candidates tool (single call, all 20)
            each result: {match_score, reasoning, strengths[], gaps[]}
         → Return top-8 ranked results
```

---

## Manual Seed (if auto-seed skipped)

```bash
# If seed_employees failed on startup (check container logs):
docker compose exec backend uv run python -m app.seed.seed_employees
```

---

## License

MIT (hackathon project).
# SkillsHub
