# SkillsHub Documentation

> **AI-Powered Skills Intelligence Platform** — Production-grade technical documentation.

This directory contains the complete technical documentation for SkillsHub: architecture, AI pipelines, API reference, operational runbooks, and onboarding guides.

---

## How to Read These Docs

| If you are... | Start here |
|---|---|
| **A judge / new visitor** | [Overview](./overview.md) → [System Architecture](./architecture/system-architecture.md) → [AI Pipelines](./ai/overview.md) |
| **A new engineer onboarding** | [Developer Onboarding](./guides/developer-onboarding.md) → [Local Setup](./guides/local-setup.md) → [Backend Architecture](./architecture/backend.md) |
| **Backend developer** | [Backend Architecture](./architecture/backend.md) → [Database Schema](./architecture/database.md) → [API Reference](./api/reference.md) |
| **Frontend developer** | [Frontend Architecture](./architecture/frontend.md) → [API Reference](./api/reference.md) |
| **AI/ML engineer** | [AI Overview](./ai/overview.md) → [Ingestion](./ai/resume-ingestion.md) → [Search](./ai/semantic-search.md) → [Prompts](./ai/prompt-strategy.md) |
| **DevOps / SRE** | [Deployment](./architecture/deployment.md) → [Observability](./operations/observability.md) → [Performance](./operations/performance.md) |
| **Security reviewer** | [Auth & Security](./operations/auth-and-security.md) → [Error Handling](./operations/error-handling.md) |

---

## Table of Contents

### 1. Foundations

- [Project Overview](./overview.md) — Problem statement, solution, key differentiators, stack summary.

### 2. Architecture

- [System Architecture](./architecture/system-architecture.md) — High-level C4-style view, components, data flow, technology choices.
- [Backend Architecture](./architecture/backend.md) — FastAPI layering (api → services → repos → models), async patterns, dependency injection.
- [Frontend Architecture](./architecture/frontend.md) — Next.js App Router, route groups, React Query, theme system.
- [Database Schema](./architecture/database.md) — Entity relationship diagram, table-by-table reference, indexes, migrations.
- [Service Communication](./architecture/service-communication.md) — How services talk to each other (HTTP, JWT, internal contracts).
- [Deployment Architecture](./architecture/deployment.md) — Docker Compose topology, environment configuration, container layout.

### 3. AI / LLM Workflows

- [AI Overview](./ai/overview.md) — Dual-model strategy (Sonnet 4.6 + Haiku 4.5), prompt caching, tool_use philosophy.
- [Resume Ingestion Pipeline](./ai/resume-ingestion.md) — PDF → text → Claude extraction → structured profile.
- [Skill Inference Engine](./ai/skill-inference.md) — Two-stage inference (deterministic rules + Haiku contextual).
- [Semantic Search Pipeline](./ai/semantic-search.md) — Query parsing → embeddings → pgvector → LLM re-rank.
- [Match Scoring Workflow](./ai/match-scoring.md) — How a 0–100 score and human-readable reasoning are produced.
- [Embedding & Vector Search](./ai/embedding-flow.md) — Voyage AI, 1024-dim vectors, HNSW index, profile rendering.
- [Prompt Strategy](./ai/prompt-strategy.md) — System prompts, tool schemas, caching, retry policy.

### 4. API Reference

- [API Reference](./api/reference.md) — Every endpoint with method, path, auth role, request/response examples.

### 5. Operations

- [Authentication & Authorization](./operations/auth-and-security.md) — JWT design, role gates, password hashing.
- [Error Handling Strategy](./operations/error-handling.md) — Exception taxonomy, retry policy, user-facing errors.
- [Logging & Observability](./operations/observability.md) — structlog setup, metrics surface, what to log and where.
- [Performance Optimization](./operations/performance.md) — Caching, indexing, batching, latency budgets.
- [Scalability Considerations](./operations/scalability.md) — Horizontal scale paths, async queues, vector DB growth.

### 6. Guides

- [Local Setup](./guides/local-setup.md) — Docker + bare-metal setup steps with troubleshooting.
- [Developer Onboarding](./guides/developer-onboarding.md) — First-week checklist, code conventions, PR workflow.
- [Production Deployment](./guides/production-deployment.md) — Hardening checklist, env separation, secrets management.

### 7. Lifecycle & Roadmap

- [Data Lifecycle](./data-lifecycle.md) — From resume upload to publishable profile to searchable embedding.
- [Roadmap](./roadmap.md) — Short, medium, and long-term scalability and product roadmap.

---

## Documentation Conventions

- **Diagrams** are written in [Mermaid](https://mermaid.js.org/) and render natively on GitHub.
- **Code references** use `file:line` format (e.g. `backend/app/ai/pipelines/extraction.py:42`).
- **Endpoints** are listed as `METHOD /path` with auth scope in brackets.
- **Models, env vars, and table names** are in `code formatting`.
- **Sequence diagrams** depict request → response paths; **flowcharts** depict pipelines.

---

## Project at a Glance

```
SkillsHub
├── Smart Ingestion: resume → structured profile (HR-reviewed)
├── Semantic Search: NL query → ranked candidates with reasoning
└── Skill Gap Analysis: org-wide coverage map
```

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind 4, React Query 5 |
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic 2, Alembic |
| Database | PostgreSQL 16 + pgvector (HNSW, cosine) |
| AI | Claude Sonnet 4.6 + Haiku 4.5 (Anthropic), Voyage AI `voyage-3-large` |
| Infrastructure | Docker Compose, uv (Python), pnpm (Node) |

---

_See also: [root README](../README.md), [PRESENTATION.md](../PRESENTATION.md), [DEMO_SCRIPT.md](../DEMO_SCRIPT.md)._
