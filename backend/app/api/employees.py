"""Employee directory + profile endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import CurrentUser, SessionDep, require_hr
from app.db.models import UserRole
from app.schemas.employee import (
    CreateEmployeeRequest,
    EmployeeDetail,
    EmployeeListItem,
    EmployeeUpdate,
    GitHubSyncRequest,
)
from app.services import employees as svc

router = APIRouter()


@router.get("/me", response_model=EmployeeDetail)
async def get_my_profile(session: SessionDep, user: CurrentUser) -> EmployeeDetail:
    """Return the employee record linked to the authenticated user."""
    from sqlalchemy import select

    from app.db.models import Employee

    result = await session.execute(
        select(Employee)
        .where(Employee.user_id == user.id)
        .order_by(Employee.created_at.desc())
        .limit(1)
    )
    emp = result.scalar_one_or_none()
    if emp is None:
        raise HTTPException(status_code=404, detail="No employee profile found for this account")
    detail = await svc.get_employee(session, emp.id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return detail


@router.post("", response_model=EmployeeDetail, status_code=201, dependencies=[Depends(require_hr)])
async def create_employee(payload: CreateEmployeeRequest, session: SessionDep) -> EmployeeDetail:
    """HR creates a new employee account with login credentials."""
    try:
        return await svc.create_employee_with_account(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[EmployeeListItem])
async def list_employees(
    session: SessionDep,
    _user: CurrentUser,
    q: str | None = None,
) -> list[EmployeeListItem]:
    """Directory — both HR and Employees can browse."""
    return await svc.list_employees(session, q=q)


@router.get("/{employee_id}", response_model=EmployeeDetail)
async def get_employee(
    employee_id: UUID,
    session: SessionDep,
    _user: CurrentUser,
) -> EmployeeDetail:
    detail = await svc.get_employee(session, employee_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return detail


@router.patch("/{employee_id}", response_model=EmployeeDetail)
async def update_employee(
    employee_id: UUID,
    patch: EmployeeUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> EmployeeDetail:
    """HR can edit anyone; an employee can edit only their own profile."""
    if user.role != UserRole.HR.value:
        # Employee path: only allowed on their own profile
        from sqlalchemy import select

        from app.db.models import Employee

        own = await session.execute(select(Employee).where(Employee.user_id == user.id))
        own_e = own.scalar_one_or_none()
        if own_e is None or own_e.id != employee_id:
            raise HTTPException(status_code=403, detail="Cannot edit another employee's profile")

    detail = await svc.update_employee(session, employee_id, patch)
    if detail is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return detail


@router.post("/{employee_id}/github", response_model=EmployeeDetail)
async def sync_github(
    employee_id: UUID,
    payload: GitHubSyncRequest,
    session: SessionDep,
    user: CurrentUser,
) -> EmployeeDetail:
    """Sync GitHub public repo skills for an employee. HR can sync anyone; employee can only sync their own."""
    from app.services.github import sync_github_skills

    if user.role != UserRole.HR.value:
        from sqlalchemy import select

        from app.db.models import Employee

        own = await session.execute(select(Employee).where(Employee.user_id == user.id))
        own_e = own.scalar_one_or_none()
        if own_e is None or own_e.id != employee_id:
            raise HTTPException(status_code=403, detail="Cannot sync another employee's GitHub")

    try:
        await sync_github_skills(session, employee_id, payload.github_username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    detail = await svc.get_employee(session, employee_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return detail


@router.delete("/{employee_id}", status_code=204, dependencies=[Depends(require_hr)])
async def delete_employee(employee_id: UUID, session: SessionDep) -> None:
    from sqlalchemy import select

    from app.db.models import Employee

    result = await session.execute(select(Employee).where(Employee.id == employee_id))
    e = result.scalar_one_or_none()
    if e is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    await session.delete(e)
    await session.commit()
