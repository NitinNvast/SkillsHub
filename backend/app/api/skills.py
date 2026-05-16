"""Skills catalog endpoints — read the canonical taxonomy + gap analysis."""

from fastapi import APIRouter
from sqlalchemy import case, func, select

from app.core.deps import CurrentUser, SessionDep
from app.db.models import Employee, EmployeeSkill, Skill
from app.schemas.skill import SkillCatalogOut, SkillGapItem, SkillGapResponse

router = APIRouter()


@router.get("/catalog", response_model=list[SkillCatalogOut])
async def list_catalog(session: SessionDep, _user: CurrentUser) -> list[SkillCatalogOut]:
    """All canonical skills — used by frontend for autocomplete & filters."""
    result = await session.execute(select(Skill).order_by(Skill.category, Skill.name))
    return [SkillCatalogOut.model_validate(s) for s in result.scalars().all()]


@router.get("/gaps", response_model=SkillGapResponse)
async def skill_gaps(session: SessionDep, _user: CurrentUser) -> SkillGapResponse:
    """
    Talent pool skill gap analysis.

    Returns all skills in the catalog ordered by coverage (lowest first).
    Only counts extracted + manual skills (not inferred) for accuracy.
    """
    total_employees_result = await session.execute(select(func.count()).select_from(Employee))
    total_employees: int = total_employees_result.scalar_one() or 1

    count_stmt = (
        select(
            Skill.name,
            Skill.category,
            func.count(EmployeeSkill.id).label("employee_count"),
            func.sum(case((EmployeeSkill.proficiency == "expert", 1), else_=0)).label("expert_count"),
            func.sum(case((EmployeeSkill.proficiency == "intermediate", 1), else_=0)).label("intermediate_count"),
        )
        .outerjoin(
            EmployeeSkill,
            (EmployeeSkill.skill_id == Skill.id)
            & (EmployeeSkill.source.in_(["extracted", "manual", "github"])),
        )
        .group_by(Skill.id, Skill.name, Skill.category)
        .order_by(func.count(EmployeeSkill.id).asc(), Skill.name)
    )
    rows = await session.execute(count_stmt)

    items: list[SkillGapItem] = []
    for row in rows:
        count = int(row.employee_count or 0)
        expert = int(row.expert_count or 0)
        intermediate = int(row.intermediate_count or 0)
        coverage_pct = round((count / total_employees) * 100, 1)

        if coverage_pct == 0:
            severity = "critical"
        elif coverage_pct < 25:
            severity = "warning"
        else:
            severity = "healthy"

        items.append(
            SkillGapItem(
                name=row.name,
                category=row.category,
                employee_count=count,
                expert_count=expert,
                intermediate_count=intermediate,
                gap_severity=severity,
                coverage_pct=coverage_pct,
            )
        )

    return SkillGapResponse(total_employees=total_employees, items=items)
