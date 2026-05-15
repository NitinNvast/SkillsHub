"""Employee read/write business logic."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Employee, EmployeeSkill
from app.schemas.employee import EmployeeDetail, EmployeeListItem, EmployeeUpdate
from app.schemas.skill import EmployeeSkillOut


async def list_employees(session: AsyncSession, q: str | None = None) -> list[EmployeeListItem]:
    stmt = (
        select(Employee)
        .options(selectinload(Employee.skills).joinedload(EmployeeSkill.skill))
        .order_by(Employee.name)
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Employee.name.ilike(like))
            | (Employee.title.ilike(like))
            | (Employee.location.ilike(like))
        )
    result = await session.execute(stmt)
    employees = result.scalars().unique().all()
    items: list[EmployeeListItem] = []
    for e in employees:
        # Top 5 skills by years desc (a small heuristic for the directory card)
        top = sorted(e.skills, key=lambda s: (s.years or 0), reverse=True)[:5]
        items.append(
            EmployeeListItem(
                id=e.id,
                name=e.name,
                email=e.email,
                title=e.title,
                location=e.location,
                total_years_exp=e.total_years_exp,
                availability=e.availability,
                top_skills=[s.skill.name for s in top],
            )
        )
    return items


async def get_employee(session: AsyncSession, employee_id: UUID) -> EmployeeDetail | None:
    stmt = (
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.skills).joinedload(EmployeeSkill.skill),
            selectinload(Employee.projects),
            selectinload(Employee.certifications),
        )
    )
    result = await session.execute(stmt)
    e = result.scalar_one_or_none()
    if e is None:
        return None
    return EmployeeDetail(
        id=e.id,
        name=e.name,
        email=e.email,
        title=e.title,
        location=e.location,
        summary=e.summary,
        total_years_exp=e.total_years_exp,
        current_project=e.current_project,
        last_project_end_date=e.last_project_end_date,
        availability=e.availability,
        created_at=e.created_at,
        updated_at=e.updated_at,
        skills=[EmployeeSkillOut.from_orm_row(s) for s in e.skills],
        projects=[
            {
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "description": p.description,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "technologies": p.technologies or [],
            }
            for p in e.projects
        ],
        certifications=[
            {"id": c.id, "name": c.name, "issuer": c.issuer, "year": c.year}
            for c in e.certifications
        ],
    )


async def update_employee(
    session: AsyncSession, employee_id: UUID, patch: EmployeeUpdate
) -> EmployeeDetail | None:
    result = await session.execute(select(Employee).where(Employee.id == employee_id))
    e = result.scalar_one_or_none()
    if e is None:
        return None
    data = patch.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(e, field, value)
    await session.commit()
    return await get_employee(session, employee_id)
