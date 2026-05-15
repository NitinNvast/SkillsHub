"""Search pipeline — full implementation (provider-agnostic).

embed_employee():        index a profile into pgvector (called post-ingestion).
run_semantic_search():   end-to-end NL search with LLM re-rank + reasoning.

Full search flow:
  1. task='parsing' → NL query parsed into ParsedQuery (filters + semantic_text)
  2. Embedding provider embeds semantic_text
  3. pgvector pre-filtered KNN retrieval (top-20)
  4. Load full profiles for all 20 candidates
  5. task='rerank' → all candidates scored + reasoned in a single LLM call
  6. Return top-K (default 8)

All LLM and embedding calls flow through `app.ai.providers.ai_manager`.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Employee, EmployeeSkill

log = logging.getLogger(__name__)


# ─── Embed a single employee ──────────────────────────────────────────────────


async def embed_employee(session: AsyncSession, employee_id: UUID) -> None:
    """Build profile summary, embed via the configured embedding provider,
    upsert into employee_embeddings."""
    from app.ai.providers import ai_manager
    from app.db.repos.embeddings import render_profile_summary, upsert_employee_embedding

    result = await session.execute(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.skills).joinedload(EmployeeSkill.skill),
            selectinload(Employee.projects),
            selectinload(Employee.certifications),
        )
    )
    employee = result.scalar_one_or_none()
    if employee is None:
        log.warning("embed_employee: employee %s not found", employee_id)
        return

    summary_text = render_profile_summary(employee)
    if not summary_text.strip():
        log.warning("embed_employee: empty summary for %s, skipping", employee_id)
        return

    vector = await ai_manager.embed_single(summary_text, input_type="document")
    await upsert_employee_embedding(session, employee_id, vector, summary_text)
    log.info("Embedding stored for employee %s", employee_id)


# ─── Step 1: Parse NL query ───────────────────────────────────────────────────


_PARSE_FALLBACK: dict = {
    "semantic_text": "",  # filled at call site
    "required_skills": [],
    "min_years_per_skill": {},
    "availability": [],
}


async def _parse_query(query: str) -> dict:
    from app.ai.prompts.parse_query import (
        PARSE_QUERY_SYSTEM,
        PARSE_QUERY_TOOL,
        build_parse_message,
    )
    from app.ai.providers import ChatRequest, ai_manager
    from app.ai.providers.base import ProviderError

    request = ChatRequest(
        system=PARSE_QUERY_SYSTEM,
        messages=[{"role": "user", "content": build_parse_message(query)}],
        tools=[PARSE_QUERY_TOOL],
        tool_choice="any",
        max_tokens=512,
    )
    try:
        resp = await ai_manager.chat(request, task="parsing")
    except ProviderError as exc:
        log.warning("Query parsing failed (%s) — using raw query as semantic text", exc)
        return {**_PARSE_FALLBACK, "semantic_text": query}

    call = resp.first_tool_call()
    if call is None:
        log.warning("Query parsing returned no tool call — using raw query as semantic text")
        return {**_PARSE_FALLBACK, "semantic_text": query}

    raw = call.arguments if isinstance(call.arguments, dict) else {}
    return {
        "semantic_text": raw.get("semantic_text", query),
        "required_skills": raw.get("required_skills", []),
        "min_years_per_skill": raw.get("min_years_per_skill", {}),
        "location": raw.get("location"),
        "availability": raw.get("availability", []),
        "seniority_hint": raw.get("seniority_hint"),
    }


# ─── Step 5: Re-rank + reason ─────────────────────────────────────────────────


async def _rerank_candidates(
    query: str,
    candidates: list[dict],
    limit: int,
) -> list[dict]:
    """Single LLM call for all candidates — scores + plain-English reasoning.
    Routed via task='rerank' — defaults to the highest-quality configured model."""
    if not candidates:
        return []

    from app.ai.prompts.rerank_reason import (
        RERANK_SYSTEM,
        RERANK_TOOL,
        build_rerank_message,
    )
    from app.ai.providers import ChatRequest, ai_manager

    user_msg = build_rerank_message(query, candidates)
    request = ChatRequest(
        system=RERANK_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
        tools=[RERANK_TOOL],
        tool_choice="any",
        max_tokens=4096,
    )
    from app.ai.providers.base import ProviderError

    try:
        resp = await ai_manager.chat(request, task="rerank")
    except ProviderError as exc:
        log.warning("Re-rank failed (%s) — falling back to similarity order", exc)
        return [
            {
                **c,
                "match_score": int(c.get("similarity", 0.5) * 100),
                "reasoning": "Matched based on semantic similarity.",
                "strengths": [],
                "gaps": [],
            }
            for c in candidates[:limit]
        ]

    call = resp.first_tool_call()
    if call is None:
        log.warning("Re-rank returned no tool call — falling back to similarity order")
        return [
            {
                **c,
                "match_score": int(c.get("similarity", 0.5) * 100),
                "reasoning": "Matched based on semantic similarity.",
                "strengths": [],
                "gaps": [],
            }
            for c in candidates[:limit]
        ]

    raw = call.arguments if isinstance(call.arguments, dict) else {}
    ranked_raw = raw.get("ranked", [])

    # Build id → result map, merge with candidate metadata
    id_to_candidate = {c["employee_id"]: c for c in candidates}
    results = []
    for r in ranked_raw[:limit]:
        eid = r.get("employee_id", "")
        base = id_to_candidate.get(eid, {})
        results.append(
            {
                **base,
                "match_score": max(0, min(100, int(r.get("match_score", 50)))),
                "reasoning": r.get("reasoning", ""),
                "strengths": r.get("strengths", []),
                "gaps": r.get("gaps", []),
            }
        )

    return results


# ─── Full search pipeline ─────────────────────────────────────────────────────


async def run_semantic_search(
    session: AsyncSession,
    query: str,
    limit: int = 8,
) -> dict:
    """
    End-to-end semantic search.

    Returns:
        {
          "parsed_query": ParsedQuery dict,
          "results": list of ranked+reasoned candidate dicts,
          "total_candidates_retrieved": int
        }
    """
    from app.ai.providers import ai_manager
    from app.db.repos.embeddings import (
        load_employee_for_rerank,
        render_profile_summary,
        vector_search,
    )
    from app.schemas.skill import EmployeeSkillOut

    # ── 1. Parse NL query ──────────────────────────────────────
    parsed = await _parse_query(query)
    log.info(
        "Parsed query: semantic='%s', skills=%s, loc=%s",
        parsed["semantic_text"][:60],
        parsed["required_skills"],
        parsed.get("location"),
    )

    # ── 2. Embed the semantic text ─────────────────────────────
    query_vector = await ai_manager.embed_single(parsed["semantic_text"], input_type="query")

    # ── 3. pgvector pre-filtered retrieval ────────────────────
    from app.core.config import settings

    retrieval_rows = await vector_search(
        session,
        query_vector,
        top_k=settings.search_top_k_retrieval,
        filter_availability=parsed["availability"] or None,
        filter_location=parsed.get("location"),
        filter_skill_years=parsed["min_years_per_skill"] or None,
    )
    log.info("Vector search returned %d candidates", len(retrieval_rows))

    if not retrieval_rows:
        return {
            "parsed_query": parsed,
            "results": [],
            "total_candidates_retrieved": 0,
        }

    # ── 4. Load full profiles + build summary texts ────────────
    candidates_for_rerank = []
    for row in retrieval_rows:
        emp = await load_employee_for_rerank(session, UUID(row["employee_id"]))
        if emp is None:
            continue
        summary = render_profile_summary(emp)
        top_skills = sorted(
            emp.skills,
            key=lambda s: (
                {"expert": 0, "intermediate": 1, "novice": 2}.get(s.proficiency, 1),
                -(float(s.years) if s.years else 0),
            ),
        )[:6]

        candidates_for_rerank.append(
            {
                **row,
                "summary_text": summary,
                "top_skills_raw": top_skills,
            }
        )

    # ── 5. Sonnet re-rank (single call, all candidates) ────────
    ranked = await _rerank_candidates(query, candidates_for_rerank, limit=limit)

    # ── 6. Build final response shape ─────────────────────────
    results = []
    for r in ranked:
        skills_out = []
        for s in r.get("top_skills_raw", []):
            try:
                skills_out.append(EmployeeSkillOut.from_orm_row(s))
            except Exception:
                pass

        results.append(
            {
                "employee_id": r["employee_id"],
                "name": r.get("name", ""),
                "title": r.get("title"),
                "location": r.get("location"),
                "availability": r.get("availability", "unknown"),
                "total_years_exp": r.get("total_years_exp"),
                "match_score": r.get("match_score", 0),
                "reasoning": r.get("reasoning", ""),
                "strengths": r.get("strengths", []),
                "gaps": r.get("gaps", []),
                "top_skills": skills_out,
                "similarity": r.get("similarity", 0.0),
            }
        )

    return {
        "parsed_query": parsed,
        "results": results,
        "total_candidates_retrieved": len(retrieval_rows),
    }
