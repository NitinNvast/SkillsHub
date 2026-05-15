"""Review & approval service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Employee, EmployeeSkill, ResumeUpload, UploadStatus
from app.schemas.employee import CertificationOut, EmployeeDetail, ProjectOut
from app.schemas.review import (
    ApproveResponse,
    ProfileEditRequest,
    RejectResponse,
    ReviewQueueDetail,
    ReviewQueueItem,
)
from app.schemas.skill import EmployeeSkillOut
from app.services.employees import get_employee

log = logging.getLogger(__name__)


async def list_pending(session: AsyncSession) -> list[ReviewQueueItem]:
    """Return all uploads with status pending_review, newest first."""
    result = await session.execute(
        select(ResumeUpload)
        .where(ResumeUpload.status == UploadStatus.PENDING_REVIEW.value)
        .order_by(ResumeUpload.created_at.desc())
    )
    uploads = result.scalars().all()

    items = []
    for u in uploads:
        # Get candidate name from employee row
        name = "Unknown"
        skill_count = 0
        inferred_count = 0

        if u.employee_id:
            emp_res = await session.execute(
                select(Employee)
                .where(Employee.id == u.employee_id)
                .options(selectinload(Employee.skills))
            )
            emp = emp_res.scalar_one_or_none()
            if emp:
                name = emp.name
                skill_count = len(emp.skills)
                inferred_count = sum(1 for s in emp.skills if s.source == "inferred")

        items.append(
            ReviewQueueItem(
                upload_id=u.id,
                employee_id=u.employee_id,
                candidate_name=name,
                source=u.source,
                status=u.status,
                created_at=u.created_at,
                skill_count=skill_count,
                inferred_count=inferred_count,
            )
        )
    return items


async def get_review_detail(session: AsyncSession, upload_id: UUID) -> ReviewQueueDetail | None:
    result = await session.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id))
    upload = result.scalar_one_or_none()
    if upload is None:
        return None

    current_profile: EmployeeDetail | None = None
    inferred_skills: list[EmployeeSkillOut] = []

    if upload.employee_id:
        current_profile = await get_employee(session, upload.employee_id)
        if current_profile:
            inferred_skills = [s for s in current_profile.skills if s.source == "inferred"]

    return ReviewQueueDetail(
        upload_id=upload.id,
        employee_id=upload.employee_id,
        source=upload.source,
        status=upload.status,
        created_at=upload.created_at,
        raw_text_preview=(upload.raw_text or "")[:500] if upload.raw_text else None,
        current_profile=current_profile,
        extracted_payload=upload.extracted_payload,
        inferred_skills=inferred_skills,
        error=upload.error,
    )


async def edit_profile(
    session: AsyncSession,
    upload_id: UUID,
    patch: ProfileEditRequest,
    reviewer_id: UUID,
) -> ReviewQueueDetail | None:
    """Apply manual edits to the employee record before approval."""
    result = await session.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id))
    upload = result.scalar_one_or_none()
    if upload is None or upload.employee_id is None:
        return None

    emp_result = await session.execute(select(Employee).where(Employee.id == upload.employee_id))
    emp = emp_result.scalar_one_or_none()
    if emp is None:
        return None

    data = patch.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field == "total_years_exp" and value is not None:
            setattr(emp, field, Decimal(str(round(value, 1))))
        else:
            setattr(emp, field, value)

    await session.commit()
    return await get_review_detail(session, upload_id)


async def approve(
    session: AsyncSession,
    upload_id: UUID,
    reviewer_id: UUID,
) -> ApproveResponse | None:
    """
    Approve an extracted profile:
      1. Mark upload as approved
      2. Re-embed employee (captures any manual edits)
    """
    result = await session.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id))
    upload = result.scalar_one_or_none()
    if upload is None:
        return None

    upload.status = UploadStatus.APPROVED.value
    upload.reviewed_at = datetime.now(timezone.utc)
    upload.reviewed_by = reviewer_id
    await session.commit()

    # Re-embed with any edits applied
    if upload.employee_id:
        try:
            from app.ai.pipelines.search import embed_employee

            await embed_employee(session, upload.employee_id)
        except Exception as exc:
            log.warning("Re-embed failed for %s: %s", upload.employee_id, exc)

    return ApproveResponse(
        upload_id=upload.id,
        employee_id=upload.employee_id,
        status=upload.status,
        message="Profile approved and indexed for search.",
    )


async def reject(
    session: AsyncSession,
    upload_id: UUID,
    reviewer_id: UUID,
    reason: str | None = None,
) -> RejectResponse | None:
    result = await session.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id))
    upload = result.scalar_one_or_none()
    if upload is None:
        return None

    upload.status = UploadStatus.REJECTED.value
    upload.reviewed_at = datetime.now(timezone.utc)
    upload.reviewed_by = reviewer_id
    if reason:
        upload.notes = reason

    # Delete the placeholder employee row if it was auto-created
    if upload.employee_id:
        emp_res = await session.execute(select(Employee).where(Employee.id == upload.employee_id))
        emp = emp_res.scalar_one_or_none()
        if emp and emp.name == "Pending Review":
            await session.delete(emp)

    await session.commit()

    return RejectResponse(
        upload_id=upload.id,
        status=upload.status,
        message="Upload rejected and removed from queue.",
    )
