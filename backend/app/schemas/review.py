"""Review queue request/response schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.employee import EmployeeDetail
from app.schemas.skill import EmployeeSkillOut


class ReviewQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    upload_id: UUID
    employee_id: UUID | None
    candidate_name: str
    source: str
    status: str
    created_at: datetime
    skill_count: int = 0
    inferred_count: int = 0


class ReviewQueueDetail(BaseModel):
    upload_id: UUID
    employee_id: UUID | None
    source: str
    status: str
    created_at: datetime
    raw_text_preview: str | None = None
    current_profile: EmployeeDetail | None = None
    extracted_payload: dict | None = None
    inferred_skills: list[EmployeeSkillOut] = []
    error: str | None = None


class ProfileEditRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    title: str | None = None
    location: str | None = None
    summary: str | None = None
    total_years_exp: float | None = None
    availability: str | None = None


class ApproveResponse(BaseModel):
    upload_id: UUID
    employee_id: UUID
    status: str
    message: str


class RejectRequest(BaseModel):
    reason: str | None = None


class RejectResponse(BaseModel):
    upload_id: UUID
    status: str
    message: str
