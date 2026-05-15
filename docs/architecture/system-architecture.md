# System Architecture

> **Audience:** New engineers, judges, architecture reviewers.
> **Goal:** Convey the full system in one diagram + a short tour of every component.

---

## 1. Context (C4 Level 1)

```mermaid
C4Context
    title SkillsHub — System Context

    Person(hr, "HR Partner", "Searches the talent pool, reviews extractions, approves profiles.")
    Person(emp, "Employee", "Uploads a resume and views the extracted profile.")

    System(skillshub, "SkillsHub", "AI-powered skills intelligence platform")

    System_Ext(anthropic, "Anthropic API", "Claude Sonnet 4.6 + Haiku 4.5")
    System_Ext(voyage, "Voyage AI", "Text embeddings (voyage-3-large)")

    Rel(hr, skillshub, "Searches, reviews, approves")
    Rel(emp, skillshub, "Uploads resume, views profile")
    Rel(skillshub, anthropic, "Extracts, infers, parses, re-ranks", "HTTPS / tool_use")
    Rel(skillshub, voyage, "Embeds profiles and queries", "HTTPS")
```

---

## 2. Container View (C4 Level 2)

```mermaid
flowchart TB
    subgraph Browser["Browser"]
        UI["Next.js 15 SPA<br/>(App Router)"]
    end

    subgraph DockerHost["Docker Compose Host"]
        FE["skillshub-frontend<br/>Node 22 / pnpm<br/>:3000"]
        BE["skillshub-backend<br/>Python 3.12 / FastAPI<br/>:8000"]
        DB[("skillshub-postgres<br/>pgvector/pgvector:pg16<br/>:5432")]
        VOL[("Volume:<br/>uploads/")]
    end

    subgraph External["External Services"]
        ANTH["Anthropic API"]
        VOY["Voyage AI"]
    end

    UI -->|HTTPS<br/>JSON + JWT| FE
    FE -.->|SSR / static| UI
    UI -->|fetch + JWT<br/>Bearer| BE
    BE -->|asyncpg<br/>SQLAlchemy 2| DB
    BE -->|HTTPS<br/>tool_use| ANTH
    BE -->|HTTPS| VOY
    BE -->|read/write| VOL

    classDef ext fill:#fef3c7,stroke:#d97706
    classDef svc fill:#dbeafe,stroke:#2563eb
    classDef data fill:#dcfce7,stroke:#16a34a
    class ANTH,VOY ext
    class UI,FE,BE svc
    class DB,VOL data
```

### Containers

| Container | Image / Build | Port | Role |
|---|---|---|---|
| `skillshub-postgres` | `pgvector/pgvector:pg16` | 5432 (host) | Primary OLTP store + vector index |
| `skillshub-backend`  | `./backend/Dockerfile` (python:3.12-slim + uv) | 8001 → 8000 | REST API, AI orchestration |
| `skillshub-frontend` | `./frontend/Dockerfile` (node:22-alpine + pnpm) | 3000 | Next.js dev server (SSR + RSC) |

The `uploads/` directory is bind-mounted into the backend so resume PDFs persist across container rebuilds during dev.

---

## 3. Logical Architecture (Code-Level)

```mermaid
flowchart LR
    subgraph FE["Frontend (Next.js 15)"]
        FE_PAGES["App Router Pages<br/>(auth) / (hr) / (employee)"]
        FE_HOOKS["React Query Hooks<br/>lib/api/hooks.ts"]
        FE_AUTH["AuthContext + ThemeContext"]
        FE_CLIENT["fetch wrapper<br/>lib/api/client.ts"]
    end

    subgraph BE["Backend (FastAPI)"]
        BE_API["api/<br/>(thin HTTP layer)"]
        BE_DEPS["core/deps.py<br/>(JWT + role gates)"]
        BE_SVC["services/<br/>(orchestration)"]
        BE_AI["ai/pipelines/<br/>(extraction · inference · search)"]
        BE_REPO["db/repos/<br/>(data access)"]
        BE_MODELS["db/models/<br/>(SQLAlchemy ORM)"]
    end

    DB[("PostgreSQL 16<br/>+ pgvector HNSW")]
    EXT[["Anthropic + Voyage AI"]]

    FE_PAGES --> FE_HOOKS --> FE_CLIENT
    FE_AUTH --> FE_CLIENT
    FE_CLIENT -->|Bearer JWT| BE_API
    BE_API --> BE_DEPS
    BE_API --> BE_SVC
    BE_SVC --> BE_AI
    BE_SVC --> BE_REPO
    BE_AI --> BE_REPO
    BE_AI --> EXT
    BE_REPO --> BE_MODELS --> DB
```

### Strict layering rules (backend)

1. **`api/` is the only HTTP-aware layer.** Routers validate inputs (via Pydantic), call services, return responses. No business logic.
2. **`services/` orchestrates** — composes multiple repos / AI pipelines, owns transactions, returns DTOs.
3. **`ai/pipelines/` owns AI calls** — never invoked directly from `api/`. Pure functions over async session + inputs.
4. **`db/repos/` owns SQL** — every query that touches the DB lives here. Services never assemble SQL inline.
5. **`db/models/` owns the schema** — ORM declarations only. No queries.

Crossing layers (e.g. an API route calling a repo directly) is a smell.

---

## 4. Two Centerpiece Workflows

### 4.1 Resume Ingestion (Smart Profile Extraction)

```mermaid
sequenceDiagram
    autonumber
    actor Emp as Employee
    participant FE as Next.js
    participant API as FastAPI /uploads
    participant SVC as ingestion service
    participant EXT as extraction pipeline
    participant CL as Claude Sonnet
    participant INF as inference pipeline
    participant CH as Claude Haiku
    participant VOY as Voyage AI
    participant DB as PostgreSQL

    Emp->>FE: Drop PDF
    FE->>API: POST /uploads/resume (multipart)
    API->>SVC: ingest_pdf(bytes)
    SVC->>SVC: pypdf extract text
    SVC->>DB: INSERT ResumeUpload(status=processing)
    SVC->>EXT: run_extraction_pipeline(text)
    EXT->>DB: SELECT canonical skills (catalog)
    EXT->>CL: tool_use(EXTRACT_PROFILE_TOOL)<br/>system prompt cached
    CL-->>EXT: StructuredProfile JSON
    EXT->>INF: infer_skills(extracted)
    INF->>INF: deterministic rules (77)
    INF->>CH: tool_use(INFER_SKILLS_TOOL)
    CH-->>INF: contextual inferences
    INF-->>EXT: merged inferred[]
    EXT->>DB: upsert Employee + Skills + Projects + Certs
    EXT->>VOY: embed(profile_summary)
    VOY-->>EXT: 1024-dim vector
    EXT->>DB: upsert EmployeeEmbedding
    EXT->>DB: UPDATE ResumeUpload(status=pending_review)
    API-->>FE: 202 { upload_id, status: pending_review }
    FE-->>Emp: "Profile in review queue"
```

Full detail: [Resume Ingestion Pipeline](../ai/resume-ingestion.md).

### 4.2 Semantic Search (Natural-Language Talent Discovery)

```mermaid
sequenceDiagram
    autonumber
    actor HR as HR
    participant FE as Next.js
    participant API as FastAPI /search
    participant SR as search pipeline
    participant CH as Claude Haiku
    participant VOY as Voyage AI
    participant DB as PostgreSQL<br/>+ pgvector
    participant CL as Claude Sonnet

    HR->>FE: "Lead React dev with WebSocket experience"
    FE->>API: POST /search { query }
    API->>SR: run_search(query)
    SR->>CH: tool_use(PARSE_QUERY_TOOL)
    CH-->>SR: ParsedQuery<br/>{semantic_text, skills[], min_years[], filters}
    SR->>VOY: embed(semantic_text, input_type=query)
    VOY-->>SR: 1024-dim query vector
    SR->>DB: HNSW KNN (top-20) + SQL pre-filters
    DB-->>SR: 20 candidate IDs + similarity
    SR->>DB: load full profiles + render_profile_summary
    SR->>CL: tool_use(RERANK_TOOL) — single call, all 20
    CL-->>SR: ranked[] with score + reasoning + strengths + gaps
    SR-->>API: top-K (default 8) + parsed_query
    API-->>FE: SearchResponse
    FE-->>HR: Ranked cards with score + reasoning
```

Full detail: [Semantic Search Pipeline](../ai/semantic-search.md).

---

## 5. Cross-Cutting Concerns

### Authentication
- JWT (HS256), issued by `/auth/login`, 24h expiry, carries `{ sub: user_id, role }`.
- Frontend stores in `localStorage['skillshub_jwt']`, attaches as `Authorization: Bearer`.
- Backend: `Depends(get_current_user)` decodes; `require_hr` / `require_employee` enforce roles.

### Authorization
- Two roles: `hr` and `employee`.
- HR: full read/write across the platform (search, review, employee directory edits).
- Employee: read self, write self, upload self.
- Self-mutation enforced inside the endpoint (employees can `PATCH /employees/{their_own_id}` but not others).

### Configuration
- 12-factor — all config via env. `pydantic-settings` parses `.env` once at startup.
- Sane defaults baked in (e.g. embedding model, JWT algorithm) so the only mandatory vars are secrets and API keys.

### Persistence
- All schema changes via Alembic migrations. The initial migration `001_initial_schema.py` creates extensions (`vector`, `uuid-ossp`, `pg_trgm`) plus all tables and indexes — including the HNSW vector index.
- All writes happen inside an `AsyncSession` (transaction per request) provided by `core/deps.py:get_session`.

### Observability
- `structlog` is wired in. Logs are JSON-friendly. Per-request log context is added at the FastAPI middleware layer.
- See [Observability](../operations/observability.md).

### Error Handling
- All `tool_use` LLM calls retry on transient failure (`tenacity` exponential backoff, 2 attempts).
- Poor PDF text → vision fallback (base64 first 3 pages → Sonnet vision).
- Extraction failure surfaces in the review queue with `status='failed'` and an `error` field, never silently lost.

---

## 6. Technology Choice Rationale

| Decision | Why |
|---|---|
| **FastAPI** over Django / Flask | Async-first, type-driven, auto Swagger, minimal boilerplate. |
| **SQLAlchemy 2 async** | Mature ORM, `asyncpg` driver, eager-load via `selectinload` avoids N+1. |
| **PostgreSQL + pgvector** | One database for OLTP + vector retrieval. No additional infra. ACID on profile writes is non-negotiable. |
| **HNSW index** | Approximate nearest neighbor, `O(log n)` retrieval. Cosine distance for normalized embeddings. |
| **Claude tool_use** | Guarantees structured output (typed JSON), eliminates fragile prompt → JSON parsing. |
| **Dual model** | Sonnet for hard reasoning (extraction, re-rank). Haiku for fast structured tasks (parse, infer). Cost + latency win. |
| **Prompt caching (`cache_control: ephemeral`)** | Extraction system prompt is large + static + reused → caching cuts input cost ~80% and TTFB ~30%. |
| **Voyage `voyage-3-large`** | Best-in-class for technical / code-adjacent text retrieval. |
| **Next.js 15 App Router** | Server + client component split, type-safe routing, fast iteration. |
| **React Query** | Cache + invalidation handled correctly; the only server-state library that scales to dozens of views. |
| **Docker Compose** | One `docker compose up` runs the entire stack for demo and local dev. |

See [Decision Rationale](./backend.md#design-decisions-tldr) for backend-specific decisions.

---

## 7. Boundary Definitions

| Boundary | What crosses | Contract |
|---|---|---|
| Browser ↔ Frontend | Static assets, RSC payloads | Next.js |
| Frontend ↔ Backend | JSON over HTTPS, JWT in `Authorization` header | Pydantic schemas |
| Backend ↔ Database | Async SQL via SQLAlchemy ORM | Alembic-managed schema |
| Backend ↔ Anthropic | `tool_use` API over HTTPS | Tool input/output schemas in `app/ai/prompts/` |
| Backend ↔ Voyage AI | Embedding requests | 1024-dim float vector |
| Backend ↔ Filesystem | Resume PDF blobs | `uploads/{employee_id}/{uuid}.pdf` |

Every external boundary is async and retryable.

---

_Next: [Backend Architecture](./backend.md) · [Frontend Architecture](./frontend.md)_
