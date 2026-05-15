"""Employee directory + profile endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import CurrentUser, SessionDep, require_hr
from app.db.models import UserRole
from app.schemas.employee import EmployeeDetail, EmployeeListItem, EmployeeUpdate
from app.services import employees as svc

router = APIRouter()


@router.get("/me", response_model=EmployeeDetail)
async def get_my_profile(session: SessionDep, user: CurrentUser) -> EmployeeDetail:
    """Return the employee record linked to the authenticated user."""
    from sqlalchemy import select
    from app.db.models import Employee

    result = await session.execute(select(Employee).where(Employee.user_id == user.id))
    emp = result.scalar_one_or_none()
    if emp is None:
        raise HTTPException(status_code=404, detail="No employee profile found for this account")
    detail = await svc.get_employee(session, emp.id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return detail


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
