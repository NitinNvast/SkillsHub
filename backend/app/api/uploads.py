"""Resume upload endpoints."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.deps import CurrentUser, SessionDep
from app.schemas.upload import TextUploadRequest, UploadResponse, UploadStatusResponse
from app.services import ingestion as svc

router = APIRouter()

_MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


@router.post("/resume", response_model=UploadResponse, status_code=202)
async def upload_resume(
    file: UploadFile,
    session: SessionDep,
    user: CurrentUser,
) -> UploadResponse:
    """
    Upload a PDF resume. Extraction runs synchronously; the response returns
    once the profile is ready in the review queue (or failed).

    Max 10 MB. Accepts application/pdf.
    """
    # Validation
    ct = file.content_type or ""
    if ct not in _ALLOWED_CONTENT_TYPES and not ct.startswith("application/pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > _MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")
    if len(pdf_bytes) < 100:
        raise HTTPException(status_code=422, detail="File appears to be empty or corrupt")

    return await svc.ingest_pdf(
        session=session,
        pdf_bytes=pdf_bytes,
        original_filename=file.filename or "resume.pdf",
        uploader_user_id=user.id,
    )


@router.post("/text", response_model=UploadResponse, status_code=202)
async def upload_text(
    payload: TextUploadRequest,
    session: SessionDep,
    user: CurrentUser,
) -> UploadResponse:
    """Upload resume as plain text (paste from LinkedIn, etc.)."""
    return await svc.ingest_text(
        session=session,
        raw_text=payload.text,
        uploader_user_id=user.id,
    )


@router.get("/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: UUID,
    session: SessionDep,
    _user: CurrentUser,
) -> UploadStatusResponse:
    """Poll the status of an in-progress or completed upload."""
    upload = await svc.get_upload_status(session, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    return UploadStatusResponse(
        upload_id=upload.id,
        status=upload.status,
        extracted_payload=upload.extracted_payload,
        error=upload.error,
    )
