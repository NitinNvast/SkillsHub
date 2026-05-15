"""Review queue endpoints — HR-only."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import CurrentUser, SessionDep, require_hr
from app.schemas.review import (
    ApproveResponse,
    ProfileEditRequest,
    RejectRequest,
    RejectResponse,
    ReviewQueueDetail,
    ReviewQueueItem,
)
from app.services import review as svc

router = APIRouter(dependencies=[Depends(require_hr)])


@router.get("", response_model=list[ReviewQueueItem])
async def list_queue(session: SessionDep) -> list[ReviewQueueItem]:
    """All pending review items, newest first."""
    return await svc.list_pending(session)


@router.get("/{upload_id}", response_model=ReviewQueueDetail)
async def get_review_item(upload_id: UUID, session: SessionDep) -> ReviewQueueDetail:
    """Full diff view: extracted payload + current employee profile side by side."""
    detail = await svc.get_review_detail(session, upload_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    return detail


@router.patch("/{upload_id}", response_model=ReviewQueueDetail)
async def edit_review_item(
    upload_id: UUID,
    patch: ProfileEditRequest,
    session: SessionDep,
    user: CurrentUser,
) -> ReviewQueueDetail:
    """Edit employee fields before approving — manual corrections to AI extraction."""
    detail = await svc.edit_profile(session, upload_id, patch, reviewer_id=user.id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Upload or employee not found")
    return detail


@router.post("/{upload_id}/approve", response_model=ApproveResponse)
async def approve_upload(
    upload_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> ApproveResponse:
    """Approve extracted profile → mark approved + re-index embedding."""
    result = await svc.approve(session, upload_id, reviewer_id=user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    return result


@router.post("/{upload_id}/reject", response_model=RejectResponse)
async def reject_upload(
    upload_id: UUID,
    payload: RejectRequest,
    session: SessionDep,
    user: CurrentUser,
) -> RejectResponse:
    """Reject and remove from queue."""
    result = await svc.reject(session, upload_id, reviewer_id=user.id, reason=payload.reason)
    if result is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    return result
