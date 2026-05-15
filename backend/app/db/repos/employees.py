"""Employee repository — upsert from extraction pipeline output."""
from __future__ import annotations

import logging
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Certification,
    Employee,
    EmployeeSkill,
    Project,
    Skill,
    SkillCategory,
    SkillSource,
)
from app.schemas.extraction import StructuredProfile

log = logging.getLogger(__name__)


async def load_skill_catalog(session: AsyncSession) -> dict[str, Skill]:
    """Return a lowercased-name → Skill map for fast lookup."""
    result = await session.execute(select(Skill))
    skills = result.scalars().all()
    catalog: dict[str, Skill] = {}
    for s in skills:
        catalog[s.name.lower()] = s
        for alias in (s.aliases or []):
            catalog[alias.lower()] = s
    return catalog


async def find_or_create_skill(
    session: AsyncSession,
    name: str,
    catalog: dict[str, Skill],
) -> Skill:
    """Find skill by name/alias, or create a new catalog entry."""
    key = name.lower().strip()
    if key in catalog:
        return catalog[key]

    # Not in catalog — infer a sensible category from common patterns
    category = _infer_category(name)
    skill = Skill(name=name, category=category, aliases=[])
    session.add(skill)
    await session.flush()
    catalog[key] = skill
    log.info("New skill added to catalog: %s (%s)", name, category)
    return skill


def _infer_category(name: str) -> str:
    n = name.lower()
    if any(kw in n for kw in ["aws", "gcp", "azure", "k8s", "docker", "postgres", "mongo", "redis", "kafka"]):
        return SkillCategory.PLATFORM.value
    if any(kw in n for kw in ["react", "vue", "angular", "next", "nest", "django", "flask", "spring", "rails", "express", "fastapi"]):
        return SkillCategory.FRAMEWORK.value
    if any(kw in n for kw in ["python", "javascript", "typescript", "java", "go", "rust", "ruby", "kotlin", "swift", "c++", "c#", "sql", "bash"]):
        return SkillCategory.LANGUAGE.value
    if any(kw in n for kw in ["payment", "machine learning", "devops", "realtime", "websocket", "nlp", "fintech", "healthcare"]):
        return SkillCategory.DOMAIN.value
    return SkillCategory.TOOL.value


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        if len(s) == 4:
            return date(int(s), 1, 1)
        parts = s.split("-")
        return date(int(parts[0]), int(parts[1]), 1)
    except (ValueError, IndexError):
        return None


async def upsert_from_extraction(
    session: AsyncSession,
    employee_id: uuid.UUID,
    profile: StructuredProfile,
    inferred_skills: list[dict] | None = None,
) -> None:
    """
    Persist the LLM-extracted profile onto the employee row.

    - Updates basic employee fields
    - Upserts employee_skills (source=extracted or inferred)
    - Replaces projects and certifications for this employee
    """
    # ─── Load employee & catalog ─────────────────────────────────
    emp_res = await session.execute(select(Employee).where(Employee.id == employee_id))
    employee = emp_res.scalar_one_or_none()
    if employee is None:
        raise ValueError(f"Employee {employee_id} not found")

    catalog = await load_skill_catalog(session)

    # ─── Update employee fields ──────────────────────────────────
    employee.name = profile.name or employee.name
    if profile.email and not profile.email.endswith("@upload.local"):
        employee.email = profile.email
    employee.location = profile.location or employee.location
    employee.title = profile.title or employee.title
    employee.summary = profile.summary or employee.summary
    if profile.total_years_exp is not None:
        from decimal import Decimal
        employee.total_years_exp = Decimal(str(round(profile.total_years_exp, 1)))

    # ─── Upsert skills ───────────────────────────────────────────
    # Delete old extracted/inferred rows (keep manual edits)
    existing_res = await session.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.source.in_([SkillSource.EXTRACTED.value, SkillSource.INFERRED.value]),
        )
    )
    for row in existing_res.scalars().all():
        await session.delete(row)
    await session.flush()

    seen_skill_ids: set[uuid.UUID] = set()
    all_skills = list(profile.skills)

    # Merge inferred skills from Step 8 inference pipeline
    if inferred_skills:
        for inf in inferred_skills:
            all_skills.append(
                type("_Inf", (), {
                    "name": inf["name"],
                    "proficiency": inf.get("proficiency", "intermediate"),
                    "years": inf.get("years"),
                    "evidence": inf.get("reasoning"),
                    "confidence": inf.get("confidence", 0.75),
                    "_source": SkillSource.INFERRED.value,
                })()
            )

    for s in all_skills:
        if not s.name:
            continue
        skill_obj = await find_or_create_skill(session, s.name, catalog)
        if skill_obj.id in seen_skill_ids:
            continue
        seen_skill_ids.add(skill_obj.id)

        source = getattr(s, "_source", SkillSource.EXTRACTED.value)

        from decimal import Decimal
        session.add(
            EmployeeSkill(
                employee_id=employee_id,
                skill_id=skill_obj.id,
                proficiency=s.proficiency if s.proficiency in ("novice", "intermediate", "expert") else "intermediate",
                years=Decimal(str(round(s.years, 1))) if s.years is not None else None,
                source=source,
                confidence=Decimal(str(round(float(s.confidence), 2))) if s.confidence is not None else None,
                evidence=getattr(s, "evidence", None),
            )
        )

    # ─── Replace projects ────────────────────────────────────────
    proj_res = await session.execute(
        select(Project).where(Project.employee_id == employee_id)
    )
    for p in proj_res.scalars().all():
        await session.delete(p)

    for p in profile.projects:
        session.add(
            Project(
                employee_id=employee_id,
                name=p.name,
                role=p.role,
                description=p.description,
                start_date=_parse_date(p.start_date),
                end_date=_parse_date(p.end_date),
                technologies=p.technologies or [],
            )
        )

    # ─── Replace certifications ──────────────────────────────────
    cert_res = await session.execute(
        select(Certification).where(Certification.employee_id == employee_id)
    )
    for c in cert_res.scalars().all():
        await session.delete(c)

    for c in profile.certifications:
        session.add(
            Certification(
                employee_id=employee_id,
                name=c.name,
                issuer=c.issuer,
                year=c.year,
            )
        )

    await session.commit()
    log.info(
        "Upserted employee %s: %d skills, %d projects, %d certs",
        employee_id,
        len(all_skills),
        len(profile.projects),
        len(profile.certifications),
    )
