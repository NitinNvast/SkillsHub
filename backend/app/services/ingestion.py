"""Resume ingestion orchestration.

Flow (per upload):
  1. Save file to disk (PDF) or accept raw text
  2. Extract text from PDF via pypdf
  3. Create ResumeUpload row (status=processing)
  4. Call extraction pipeline → StructuredProfile JSON
  5. Upsert Employee + Skills + Projects + Certifications
  6. Update upload status → pending_review
  7. Trigger embedding (non-blocking, best-effort)

Steps 4–6 are the AI-heavy part — extraction.py / inference.py are built in Steps 7–8.
This file wires the orchestration so uploads are testable end-to-end immediately.
"""
from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Employee, ResumeUpload, UploadSource, UploadStatus
from app.schemas.upload import UploadResponse

log = logging.getLogger(__name__)

UPLOAD_DIR = Path(settings.upload_dir)


# ─── PDF parsing ──────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, bool]:
    """
    Returns (text, is_good_quality).

    'Good quality' means pypdf extracted >200 characters — typical of
    text-based PDFs. Scanned/image PDFs return short or empty strings;
    in that case callers should fall back to Claude vision.
    """
    import io
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.strip())

    full_text = "\n\n---PAGE BREAK---\n\n".join(p for p in pages if p)
    is_good = len(full_text.strip()) >= 200
    return full_text.strip(), is_good


def sanitize_text(text: str) -> str:
    """Remove excessive whitespace while preserving paragraph structure."""
    import re
    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs on a single line
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# ─── Save file ────────────────────────────────────────────────────────────────

def save_pdf(pdf_bytes: bytes, employee_id: uuid.UUID) -> str:
    dest_dir = UPLOAD_DIR / str(employee_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.pdf"
    path = dest_dir / filename
    path.write_bytes(pdf_bytes)
    return str(path)


# ─── Upsert helpers ───────────────────────────────────────────────────────────

async def get_or_create_employee(
    session: AsyncSession,
    name: str,
    email: str | None,
    user_id: uuid.UUID | None = None,
) -> Employee:
    """
    Find existing employee by email (or user_id), or create a new shell row.
    The shell gets filled in by the approval step (Step 12).
    """
    if email:
        result = await session.execute(select(Employee).where(Employee.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    if user_id:
        result = await session.execute(select(Employee).where(Employee.user_id == user_id))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Generate a placeholder email to satisfy the unique constraint
    placeholder_email = email or f"pending-{uuid.uuid4().hex[:8]}@upload.local"
    employee = Employee(name=name, email=placeholder_email, user_id=user_id)
    session.add(employee)
    await session.flush()  # assigns id without committing
    return employee


# ─── Main orchestration ───────────────────────────────────────────────────────

async def ingest_pdf(
    session: AsyncSession,
    pdf_bytes: bytes,
    original_filename: str,
    uploader_user_id: uuid.UUID | None = None,
) -> UploadResponse:
    """
    Entry point for PDF uploads.
    Returns immediately with upload_id and status=processing.
    AI extraction runs synchronously (visible loading UI in frontend).
    """
    # 1. Parse text
    raw_text, is_good = extract_text_from_pdf(pdf_bytes)
    raw_text = sanitize_text(raw_text)

    # Create a temporary employee shell so we have an ID for file storage
    temp_employee = Employee(
        name="Pending Review",
        email=f"pending-{uuid.uuid4().hex[:8]}@upload.local",
        user_id=uploader_user_id,
    )
    session.add(temp_employee)
    await session.flush()

    # 2. Save file
    file_path = save_pdf(pdf_bytes, temp_employee.id)

    # 3. Create upload record
    upload = ResumeUpload(
        employee_id=temp_employee.id,
        source=UploadSource.PDF.value,
        file_path=file_path,
        raw_text=raw_text if is_good else None,
        status=UploadStatus.PROCESSING.value,
    )
    session.add(upload)
    await session.flush()

    await session.commit()

    # 4. Run AI extraction pipeline (imported here to avoid circular deps at module load)
    try:
        from app.ai.pipelines.extraction import run_extraction_pipeline
        await run_extraction_pipeline(
            session=session,
            upload_id=upload.id,
            raw_text=raw_text,
            pdf_bytes=pdf_bytes if not is_good else None,  # pass bytes only for vision fallback
        )
    except Exception as exc:
        log.exception("Extraction pipeline failed for upload %s", upload.id)
        # Update status to failed so review queue can surface the error
        result = await session.execute(select(ResumeUpload).where(ResumeUpload.id == upload.id))
        upload_row = result.scalar_one_or_none()
        if upload_row:
            upload_row.status = UploadStatus.FAILED.value
            upload_row.error = str(exc)
            await session.commit()

    return UploadResponse(
        upload_id=upload.id,
        employee_id=temp_employee.id,
        status=upload.status,
        message="Resume received. Check review queue.",
    )


async def ingest_text(
    session: AsyncSession,
    raw_text: str,
    uploader_user_id: uuid.UUID | None = None,
) -> UploadResponse:
    """Entry point for plain-text (paste) uploads."""
    raw_text = sanitize_text(raw_text)

    temp_employee = Employee(
        name="Pending Review",
        email=f"pending-{uuid.uuid4().hex[:8]}@upload.local",
        user_id=uploader_user_id,
    )
    session.add(temp_employee)
    await session.flush()

    upload = ResumeUpload(
        employee_id=temp_employee.id,
        source=UploadSource.TEXT.value,
        raw_text=raw_text,
        status=UploadStatus.PROCESSING.value,
    )
    session.add(upload)
    await session.flush()
    await session.commit()

    try:
        from app.ai.pipelines.extraction import run_extraction_pipeline
        await run_extraction_pipeline(
            session=session,
            upload_id=upload.id,
            raw_text=raw_text,
        )
    except Exception as exc:
        log.exception("Extraction pipeline failed for upload %s", upload.id)
        result = await session.execute(select(ResumeUpload).where(ResumeUpload.id == upload.id))
        upload_row = result.scalar_one_or_none()
        if upload_row:
            upload_row.status = UploadStatus.FAILED.value
            upload_row.error = str(exc)
            await session.commit()

    return UploadResponse(
        upload_id=upload.id,
        employee_id=temp_employee.id,
        status=upload.status,
        message="Resume received. Check review queue.",
    )


async def get_upload_status(session: AsyncSession, upload_id: uuid.UUID) -> ResumeUpload | None:
    result = await session.execute(
        select(ResumeUpload).where(ResumeUpload.id == upload_id)
    )
    return result.scalar_one_or_none()
