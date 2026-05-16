"""Resume upload endpoints."""

import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.deps import CurrentUser, SessionDep, require_hr
from app.schemas.upload import (
    BulkUploadResponse,
    BulkUploadResult,
    TextUploadRequest,
    UploadResponse,
    UploadStatusResponse,
)
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


@router.post(
    "/bulk",
    response_model=BulkUploadResponse,
    status_code=202,
    dependencies=[Depends(require_hr)],
)
async def bulk_upload_resumes(
    files: list[UploadFile],
    session: SessionDep,
    user: CurrentUser,
) -> BulkUploadResponse:
    """Upload up to 20 PDF resumes at once. Each processed sequentially."""
    if len(files) > 20:
        raise HTTPException(status_code=422, detail="Maximum 20 files per bulk upload")

    results: list[BulkUploadResult] = []
    for file in files:
        fname = file.filename or "resume.pdf"
        try:
            ct = file.content_type or ""
            if (
                ct not in _ALLOWED_CONTENT_TYPES
                and not ct.startswith("application/pdf")
                and not fname.lower().endswith(".pdf")
            ):
                results.append(BulkUploadResult(filename=fname, status="failed", error="Not a PDF"))
                continue
            pdf_bytes = await file.read()
            if len(pdf_bytes) > _MAX_PDF_BYTES:
                results.append(
                    BulkUploadResult(filename=fname, status="failed", error="File exceeds 10 MB limit")
                )
                continue
            if len(pdf_bytes) < 100:
                results.append(
                    BulkUploadResult(filename=fname, status="failed", error="File appears empty or corrupt")
                )
                continue
            upload_resp = await svc.ingest_pdf(
                session=session,
                pdf_bytes=pdf_bytes,
                original_filename=fname,
                uploader_user_id=user.id,
            )
            results.append(
                BulkUploadResult(
                    filename=fname,
                    upload_id=upload_resp.upload_id,
                    employee_id=upload_resp.employee_id,
                    status="queued",
                )
            )
        except Exception as exc:
            results.append(BulkUploadResult(filename=fname, status="failed", error=str(exc)))

    queued = sum(1 for r in results if r.status == "queued")
    return BulkUploadResponse(total=len(results), queued=queued, failed=len(results) - queued, results=results)


@router.post(
    "/csv",
    response_model=BulkUploadResponse,
    status_code=202,
    dependencies=[Depends(require_hr)],
)
async def bulk_import_csv(
    file: UploadFile,
    session: SessionDep,
) -> BulkUploadResponse:
    """Import employees from CSV. Required columns: name, email, password. Optional: title, location."""
    content = await file.read()
    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="CSV must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(text_content))
    results: list[BulkUploadResult] = []

    from app.schemas.employee import CreateEmployeeRequest
    from app.services.employees import create_employee_with_account

    for i, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip()
        password = (row.get("password") or "").strip()
        title = (row.get("title") or "").strip() or None
        location = (row.get("location") or "").strip() or None
        label = f"Row {i}"

        if not name or not email or not password:
            results.append(
                BulkUploadResult(
                    filename=label,
                    status="failed",
                    error="Missing required field: name, email, or password",
                )
            )
            continue
        if len(password) < 6:
            results.append(
                BulkUploadResult(
                    filename=label, status="failed", error="Password must be at least 6 characters"
                )
            )
            continue
        try:
            emp = await create_employee_with_account(
                session,
                CreateEmployeeRequest(
                    name=name, email=email, password=password, title=title, location=location
                ),
            )
            results.append(BulkUploadResult(filename=label, employee_id=emp.id, status="queued"))
        except ValueError as exc:
            results.append(BulkUploadResult(filename=label, status="failed", error=str(exc)))
        except Exception as exc:
            results.append(
                BulkUploadResult(filename=label, status="failed", error=f"Unexpected error: {exc}")
            )

    queued = sum(1 for r in results if r.status == "queued")
    return BulkUploadResponse(total=len(results), queued=queued, failed=len(results) - queued, results=results)


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
