"""Embedding repository — build profile summaries, upsert vectors, run vector search.

The profile summary is what we embed. Its design determines search quality:
  - Dense skill listing (name + proficiency + years) → strong keyword recall
  - Project descriptions → semantic match for "has built X" style queries
  - Title/role/location → structured filter fallback
  - Inferred skills included → "who knows React" finds Next.js devs too
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Employee, EmployeeEmbedding, EmployeeSkill, Project
from app.core.config import settings

log = logging.getLogger(__name__)


# ─── Profile summary renderer ────────────────────────────────────────────────


def render_profile_summary(employee: Employee) -> str:
    """
    Build the text string we embed for an employee.

    Quality of this function directly determines search quality.
    It must be dense, structured, and cover all signals HR might query for.
    """
    lines: list[str] = []

    # Header — role + seniority signal
    title_part = employee.title or "Software Engineer"
    years_part = f"{employee.total_years_exp} years experience" if employee.total_years_exp else ""
    header = title_part
    if years_part:
        header += f" | {years_part}"
    lines.append(header)

    # Location + availability
    meta_parts = []
    if employee.location:
        meta_parts.append(f"Location: {employee.location}")
    avail = employee.availability
    if avail == "available":
        meta_parts.append("Status: Available for new project")
    elif avail == "partial":
        meta_parts.append("Status: Partially available")
    elif avail == "allocated":
        if employee.last_project_end_date:
            meta_parts.append(
                f"Status: Currently allocated (until {employee.last_project_end_date})"
            )
        else:
            meta_parts.append("Status: Currently allocated")
    if meta_parts:
        lines.append(" | ".join(meta_parts))

    # Summary paragraph
    if employee.summary:
        lines.append(f"\nSUMMARY: {employee.summary}")

    # Skills — separated by source for clarity
    extracted_skills = [s for s in employee.skills if s.source == "extracted"]
    inferred_skills = [s for s in employee.skills if s.source == "inferred"]
    manual_skills = [s for s in employee.skills if s.source == "manual"]

    all_primary = extracted_skills + manual_skills
    if all_primary:
        sorted_skills = sorted(
            all_primary,
            key=lambda s: (
                {"expert": 0, "intermediate": 1, "novice": 2}.get(s.proficiency, 1),
                -(float(s.years) if s.years else 0),
            ),
        )
        skill_parts = []
        for s in sorted_skills:
            part = f"{s.skill.name} ({s.proficiency}"
            if s.years:
                part += f", {s.years}y"
            part += ")"
            skill_parts.append(part)
        lines.append(f"\nSKILLS: {', '.join(skill_parts)}")

    if inferred_skills:
        inf_parts = [f"{s.skill.name} ({s.proficiency})" for s in inferred_skills]
        lines.append(f"ALSO KNOWS (inferred): {', '.join(inf_parts)}")

    # Projects — rich narrative for semantic matching
    if employee.projects:
        lines.append("\nPROJECTS:")
        for p in employee.projects:
            date_range = ""
            if p.start_date or p.end_date:
                s = str(p.start_date.year) if p.start_date else "?"
                e = str(p.end_date.year) if p.end_date else "present"
                date_range = f" ({s}–{e})"
            role_part = f" | {p.role}" if p.role else ""
            tech_part = f" | Tech: {', '.join(p.technologies)}" if p.technologies else ""
            lines.append(f"  [{p.name}{date_range}{role_part}]{tech_part}")
            if p.description:
                lines.append(f"  {p.description}")

    # Certifications
    if employee.certifications:
        cert_parts = []
        for c in employee.certifications:
            part = c.name
            if c.issuer:
                part += f" by {c.issuer}"
            if c.year:
                part += f" ({c.year})"
            cert_parts.append(part)
        lines.append(f"\nCERTIFICATIONS: {', '.join(cert_parts)}")

    return "\n".join(lines)


# ─── Upsert embedding ─────────────────────────────────────────────────────────


async def upsert_employee_embedding(
    session: AsyncSession,
    employee_id: UUID,
    vector: list[float],
    summary_text: str,
) -> None:
    result = await session.execute(
        select(EmployeeEmbedding).where(EmployeeEmbedding.employee_id == employee_id)
    )
    emb = result.scalar_one_or_none()
    if emb is None:
        emb = EmployeeEmbedding(
            employee_id=employee_id,
            vector=vector,
            summary_text=summary_text,
        )
        session.add(emb)
    else:
        emb.vector = vector
        emb.summary_text = summary_text
    await session.commit()


# ─── Vector search ────────────────────────────────────────────────────────────


async def vector_search(
    session: AsyncSession,
    query_vector: list[float],
    *,
    top_k: int | None = None,
    filter_availability: list[str] | None = None,
    filter_location: str | None = None,
    filter_skill_years: dict[str, float] | None = None,
) -> list[dict]:
    """
    Hybrid pgvector search:
      1. Apply structured pre-filters (availability, location, min skill years)
      2. Order by cosine distance to query vector (HNSW index used automatically)
      3. Return top_k candidates with similarity score

    Pre-filters narrow the candidate set so the LLM re-ranker only sees
    genuinely relevant profiles, improving both quality and cost.
    """
    limit = top_k or settings.search_top_k_retrieval

    # Build the base query with vector similarity
    base_sql = """
        SELECT
            e.id                                          AS employee_id,
            1 - (emb.vector <=> CAST(:query_vec AS vector))      AS similarity,
            e.name, e.title, e.location, e.availability,
            e.total_years_exp, e.summary
        FROM employees e
        JOIN employee_embeddings emb ON emb.employee_id = e.id
        WHERE 1=1
    """
    params: dict = {"query_vec": str(query_vector)}

    # ── Availability filter ──────────────────────────────────────
    if filter_availability:
        placeholders = ", ".join(f":avail_{i}" for i in range(len(filter_availability)))
        base_sql += f" AND e.availability IN ({placeholders})"
        for i, v in enumerate(filter_availability):
            params[f"avail_{i}"] = v

    # ── Location filter (case-insensitive partial match) ─────────
    if filter_location:
        base_sql += " AND e.location ILIKE :location"
        params["location"] = f"%{filter_location}%"

    # ── Minimum years for specific skills ────────────────────────
    if filter_skill_years:
        for i, (skill_name, min_years) in enumerate(filter_skill_years.items()):
            alias = f"es_{i}"
            base_sql += f"""
                AND EXISTS (
                    SELECT 1
                    FROM employee_skills {alias}
                    JOIN skills_catalog sc_{i} ON sc_{i}.id = {alias}.skill_id
                    WHERE {alias}.employee_id = e.id
                      AND LOWER(sc_{i}.name) = :skill_name_{i}
                      AND {alias}.years >= :min_years_{i}
                )
            """
            params[f"skill_name_{i}"] = skill_name.lower()
            params[f"min_years_{i}"] = min_years

    base_sql += " ORDER BY emb.vector <=> CAST(:query_vec AS vector) LIMIT :limit"
    params["limit"] = limit

    rows = await session.execute(text(base_sql), params)
    results = []
    for row in rows:
        results.append(
            {
                "employee_id": str(row.employee_id),
                "similarity": float(row.similarity),
                "name": row.name,
                "title": row.title,
                "location": row.location,
                "availability": row.availability,
                "total_years_exp": float(row.total_years_exp) if row.total_years_exp else None,
                "summary": row.summary,
            }
        )
    return results


async def load_employee_for_rerank(session: AsyncSession, employee_id: UUID) -> Employee | None:
    """Load full employee with eager-loaded skills, projects, certs for re-ranking."""
    result = await session.execute(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.skills).joinedload(EmployeeSkill.skill),
            selectinload(Employee.projects),
            selectinload(Employee.certifications),
        )
    )
    return result.scalar_one_or_none()
