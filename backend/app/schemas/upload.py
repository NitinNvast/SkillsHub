"""Upload request / response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class TextUploadRequest(BaseModel):
    text: str = Field(min_length=50, description="Raw resume text (LinkedIn copy-paste, etc.)")
    name: str | None = Field(None, description="Candidate name hint (optional)")


class UploadResponse(BaseModel):
    upload_id: UUID
    employee_id: UUID | None = None
    status: str
    message: str


class UploadStatusResponse(BaseModel):
    upload_id: UUID
    status: str
    extracted_payload: dict | None = None
    error: str | None = None
