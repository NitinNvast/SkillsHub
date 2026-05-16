# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkillsHub is an AI-powered skills intelligence platform. It solves two problems:
1. **Resume ingestion** — PDF/text → structured employee profile via LLM extraction → HR review queue → published profile
2. **Semantic search** — Natural-language HR queries → pgvector similarity + SQL filters + LLM re-ranking → ranked candidates with match scores and reasoning

**Stack:** FastAPI + SQLAlchemy 2 (async) + PostgreSQL 16 + pgvector | Next.js 15 (App Router) + TypeScript + React Query | Groq `llama-3.3-70b-versatile` / `llama-3.1-8b-instant` + Voyage AI embeddings | Docker Compose

---

## Commands

### Full stack (recommended)
```bash
docker compose up --build      # Start postgres + backend + frontend
```
First run auto-runs migrations, seeds demo users and 12 employee profiles.

**Demo credentials:** `hr@demo.com` / `emp@demo.com` (password: `demo1234`)

### Backend (local, inside container or with uv installed)
```bash
uv run uvicorn app.main:app --reload   # Dev server on :8000
uv run alembic upgrade head            # Apply migrations
uv run alembic downgrade -1            # Rollback one
uv run python -m app.seed.seed_demo    # Re-seed users + skills catalog
uv run python -m app.seed.seed_employees  # Re-seed 12 employee profiles (needs VOYAGE_API_KEY)
uv run pytest tests                    # Run tests (303 tests)
uv run ruff check .                    # Lint
uv run ruff format .                   # Format
```

### Frontend (local, inside container or with Node 18+ and pnpm)
```bash
pnpm install
pnpm dev          # Dev server on :3000
pnpm build
pnpm lint         # ESLint + next lint
pnpm typecheck    # tsc --noEmit
```

### In running Docker containers
```bash
docker compose exec backend uv run alembic upgrade head
docker compose exec backend uv run python -m app.seed.seed_employees
```

---

## Architecture

### Backend layout
```
backend/app/
├── api/          HTTP thin layer — validates input, calls services, returns responses
├── services/     Business logic (auth, ingestion, review)
├── ai/
│   ├── pipelines/   extraction.py, inference.py, search.py — core AI algorithms
│   ├── prompts/     Tool schemas + system prompts (tool_use definitions)
│   ├── providers/   Groq (chat) + Voyage (embeddings) provider layer
│   └── embeddings.py  Thin shim over ai_manager.embed() — use ai_manager directly in new code
├── db/
│   ├── models/   SQLAlchemy ORM models
│   ├── repos/    Data access layer (employees, embeddings)
│   └── session.py  AsyncSession factory
├── schemas/      Pydantic v2 DTOs (request/response shapes)
├── core/         config.py (Settings from env), security.py (JWT), deps.py (FastAPI Depends)
└── seed/         Demo data generators
```

### AI Pipeline — Resume Ingestion (`app/ai/pipelines/extraction.py`)
1. Load canonical skill names from DB → inject into system prompt as normalization hint
2. **Groq `llama-3.3-70b-versatile` tool_use** (EXTRACT_PROFILE_TOOL) → `StructuredProfile` JSON
   - Proficiency rules enforced in prompt: expert=4+yr/led, intermediate=1.5–4yr, novice=<1.5yr
   - Fallback: if extracted text <200 chars, retry with vision (base64 images from first 3 PDF pages)
3. **Inference pipeline** (`inference.py`) — two-stage skill expansion:
   - Deterministic rules: 40+ hard-coded parent/sibling mappings (e.g. Next.js→React at 0.97, React→JS at 0.95)
   - Groq `llama-3.1-8b-instant` contextual: project context + tech stack → domain/cross-cutting skills
4. Upsert `Employee` + `EmployeeSkill` + `Project` + `Certification` via `db/repos/employees.py`
5. Compute Voyage embedding → upsert `EmployeeEmbedding`
6. Mark `ResumeUpload.status = "pending_review"` → HR review queue

### AI Pipeline — Search (`app/ai/pipelines/search.py`)
1. **Groq `llama-3.3-70b-versatile`** parses NL query → `ParsedQuery` (semantic_text, required_skills, min_years_per_skill, location, availability, seniority_hint)
2. Voyage embed `semantic_text` with `input_type="query"`
3. pgvector HNSW KNN (top-20) + SQL pre-filters (availability, location, min years per skill) in one query
4. Load full Employee profiles (skills + projects + certifications)
5. **Groq `llama-3.3-70b-versatile`** re-ranks all 20 candidates in one call → match_score (0–100), reasoning, strengths[], gaps[]
6. Return top-K (default 8) sorted by match_score

### Dual-model strategy
| Task | Model | Reason |
|------|-------|--------|
| Resume extraction, search re-ranking, query parsing | `llama-3.3-70b-versatile` | Accuracy-critical; reliable tool_use |
| Skill inference | `llama-3.1-8b-instant` | Latency + cost; simpler structured tasks |

### Provider layer (`app/ai/providers/`)
- **Chat:** `GroqProvider` (subclasses `OpenAICompatibleProvider`) — only supported chat provider
- **Embeddings:** `VoyageEmbeddingProvider` — only supported embedding provider (Groq has no embeddings endpoint)
- **`AIManager`** (`manager.py`) — resolves task → (provider, model), handles retries + logging
- **`ProviderRegistry`** (`factory.py`) — lazy singleton cache; raises `ProviderUnavailableError` for unknown providers

### Data flow: Staged ingestion
`ResumeUpload` (staging) → extraction runs async → status: `pending_review` → HR approves/rejects → on approve: `Employee` + skills/projects/certs committed + embedding computed

### Auth
- JWT (HS256), 1-day expiry, payload: `{sub: user_id, role: "hr"|"employee"}`
- Frontend stores token in `localStorage` as `skillshub_jwt`, attaches as `Authorization: Bearer`
- Backend FastAPI `Depends(get_current_user)` / `Depends(require_hr)` enforce role gates

### Key env vars (see `.env.example`)
```
GROQ_API_KEY        # https://console.groq.com (free tier available)
VOYAGE_API_KEY      # https://dash.voyageai.com (required for embeddings)
JWT_SECRET          # Generate: python -c "import secrets; print(secrets.token_urlsafe(48))"
DATABASE_URL        # postgres+asyncpg://...
```

---

## Key patterns

**All LLM calls use tool_use** — never free-text generation. This enforces structured output without fragile JSON parsing.

**Async-first** — all DB operations use SQLAlchemy async sessions; all external calls (Groq, Voyage) are awaited. Never mix sync DB calls into async handlers.

**No prompt caching** — Groq does not support `cache_control=ephemeral`. Do not add cache_control blocks to prompts.

**Hybrid search** — vector similarity alone is insufficient; pgvector handles semantic proximity, SQL filters handle hard constraints (availability, location, years), and the LLM handles nuanced reasoning. All three layers are required for correct results.

**Embeddings schema** — `EmployeeEmbedding.vector` is 1024-dim (Voyage `voyage-3-large`). The HNSW index in migration `001` uses cosine distance. If you change the embedding model or dimension, you must drop and recreate the index and re-embed all employees.

**Ruff config** — line length 100, ignores E501. Imports sorted (I), bugbear (B), pyupgrade (UP), naming (N) rules active.
