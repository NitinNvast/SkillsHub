"""Skills catalog endpoints — read the canonical taxonomy + gap analysis."""

from fastapi import APIRouter
from sqlalchemy import case, func, select

from app.core.deps import CurrentUser, SessionDep
from app.db.models import Employee, EmployeeSkill, Skill
from app.schemas.skill import SkillCatalogOut, SkillGapItem

router = APIRouter()


@router.get("/catalog", response_model=list[SkillCatalogOut])
async def list_catalog(session: SessionDep, _user: CurrentUser) -> list[SkillCatalogOut]:
    """All canonical skills — used by frontend for autocomplete & filters."""
    result = await session.execute(select(Skill).order_by(Skill.category, Skill.name))
    return [SkillCatalogOut.model_validate(s) for s in result.scalars().all()]


@router.get("/gaps", response_model=list[SkillGapItem])
async def skill_gaps(session: SessionDep, _user: CurrentUser) -> list[SkillGapItem]:
    """
    Talent pool skill gap analysis.

    Returns skills present in the catalog ordered by how few employees have them.
    Skills with zero coverage in the active workforce show up first — these are gaps.
    Only counts extracted + manual skills (not inferred) for accuracy.
    Excludes skills only held by zero employees in the catalog.
    """
    total_employees_result = await session.execute(select(func.count()).select_from(Employee))
    total_employees: int = total_employees_result.scalar_one() or 1

    # Per-skill employee count (all levels) and expert count
    # LEFT JOIN so skills with zero employees still appear
    count_stmt = (
        select(
            Skill.name,
            Skill.category,
            func.count(EmployeeSkill.id).label("employee_count"),
            func.sum(case((EmployeeSkill.proficiency == "expert", 1), else_=0)).label(
                "expert_count"
            ),
        )
        .outerjoin(
            EmployeeSkill,
            (EmployeeSkill.skill_id == Skill.id)
            & (EmployeeSkill.source.in_(["extracted", "manual"])),
        )
        .group_by(Skill.id, Skill.name, Skill.category)
        .order_by(func.count(EmployeeSkill.id).asc(), Skill.name)
        .limit(30)
    )
    rows = await session.execute(count_stmt)

    items: list[SkillGapItem] = []
    for row in rows:
        count = row.employee_count or 0
        expert = row.expert_count or 0
        coverage = count / total_employees

        if coverage == 0:
            severity = "critical"
        elif coverage < 0.25:
            severity = "warning"
        else:
            severity = "healthy"

        items.append(
            SkillGapItem(
                name=row.name,
                category=row.category,
                employee_count=count,
                expert_count=int(expert),
                gap_severity=severity,
            )
        )

    return items
