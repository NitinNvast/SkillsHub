"""Resume uploads + extracted payload + review state.

This is the staging area for the review queue. Approved uploads result in
employees + skills + projects being committed.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UploadSource(str, Enum):
    PDF = "pdf"
    TEXT = "text"
    LINKEDIN = "linkedin"


class UploadStatus(str, Enum):
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class ResumeUpload(Base):
    __tablename__ = "resume_uploads"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )

    source: Mapped[str] = mapped_column(String(20), nullable=False)  # UploadSource
    file_path: Mapped[str | None] = mapped_column(String(1024))  # local disk path for PDFs
    raw_text: Mapped[str | None] = mapped_column(Text)  # extracted text
    status: Mapped[str] = mapped_column(String(20), default="processing", nullable=False)

    # The complete LLM extraction output (StructuredProfile JSON).
    # Persisted so we can re-run inference without re-calling extraction.
    extracted_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # Optional reviewer notes / error message
    notes: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
