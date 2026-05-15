"""Resume extraction pipeline — production implementation.

Flow:
  1. Load canonical skill names from DB (for normalization in system prompt)
  2. Call Claude Sonnet via tool_use → StructuredProfile JSON
     - Fallback: if text quality is poor, send PDF bytes as Claude vision
  3. Call inference pipeline (Step 8) → inferred skills appended
  4. Upsert Employee + Skills + Projects + Certs (repos/employees.py)
  5. Trigger embedding update (Step 9)
  6. Mark upload status → pending_review
"""
from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.client import get_client
from app.ai.prompts.extract_resume import (
    EXTRACT_PROFILE_TOOL,
    build_system_prompt,
    build_user_message,
)
from app.core.config import settings
from app.db.models import ResumeUpload, Skill, UploadStatus
from app.db.repos.employees import upsert_from_extraction
from app.schemas.extraction import StructuredProfile

log = logging.getLogger(__name__)


# ─── Raw LLM call ─────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
async def _call_extraction(
    raw_text: str,
    canonical_skills: list[str],
) -> StructuredProfile:
    """
    Call Claude Sonnet with tool_use to get a StructuredProfile.
    Retries once on transient API errors.
    """
    client = get_client()
    system = build_system_prompt(canonical_skills)
    user_msg = build_user_message(raw_text)

    response = await client.messages.create(
        model=settings.extraction_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
        tools=[EXTRACT_PROFILE_TOOL],
        tool_choice={"type": "any"},  # force tool use
    )

    # Extract the tool_use block
    tool_block = next(
        (b for b in response.content if b.type == "tool_use"),
        None,
    )
    if tool_block is None:
        raise ValueError("Claude did not call extract_profile tool")

    raw = tool_block.input
    if isinstance(raw, str):
        raw = json.loads(raw)

    return StructuredProfile.model_validate(raw)


async def _call_extraction_vision(pdf_bytes: bytes, canonical_skills: list[str]) -> StructuredProfile:
    """
    Vision fallback for scanned/image-based PDFs.
    Sends the first 3 pages as base64 images to Claude.
    """
    import base64
    import io

    from pypdf import PdfReader

    client = get_client()
    system = build_system_prompt(canonical_skills)

    # Build image content blocks (first 3 pages max)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    content: list[dict] = []

    for i, page in enumerate(reader.pages[:3]):
        # Try to extract images from page
        images = list(page.images) if hasattr(page, "images") else []
        if images:
            for img in images[:2]:
                img_b64 = base64.standard_b64encode(img.data).decode()
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": img_b64},
                })
        # Always include any text present on the page
        text = page.extract_text() or ""
        if text.strip():
            content.append({"type": "text", "text": f"Page {i+1} text:\n{text.strip()}"})

    if not content:
        raise ValueError("PDF has no extractable text or images")

    content.append({
        "type": "text",
        "text": "Please extract the structured profile from this resume. Call the extract_profile tool.",
    })

    response = await client.messages.create(
        model=settings.extraction_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": content}],
        tools=[EXTRACT_PROFILE_TOOL],
        tool_choice={"type": "any"},
    )

    tool_block = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise ValueError("Claude vision did not call extract_profile tool")

    raw = tool_block.input
    if isinstance(raw, str):
        raw = json.loads(raw)
    return StructuredProfile.model_validate(raw)


# ─── Main pipeline ────────────────────────────────────────────────────────────

async def run_extraction_pipeline(
    session: AsyncSession,
    upload_id: UUID,
    raw_text: str,
    pdf_bytes: bytes | None = None,
) -> None:
    """
    Full extraction pipeline. Called by services/ingestion.py after file save.
    Updates the upload row and employee record in-place.
    """
    log.info("Extraction pipeline started for upload %s", upload_id)

    # ── 1. Load skill catalog names for normalization hint ─────
    result = await session.execute(select(Skill.name))
    canonical_skills = [row[0] for row in result.all()]

    # ── 2. Extract structured profile ─────────────────────────
    is_poor_quality = len(raw_text.strip()) < 200

    if is_poor_quality and pdf_bytes:
        log.info("Upload %s: text quality poor, using vision fallback", upload_id)
        profile = await _call_extraction_vision(pdf_bytes, canonical_skills)
    else:
        profile = await _call_extraction(raw_text, canonical_skills)

    log.info(
        "Extraction complete for upload %s: %d skills, %d projects",
        upload_id,
        len(profile.skills),
        len(profile.projects),
    )

    # ── 3. Inference pipeline (Step 8 — stubs until that step) ─
    inferred: list[dict] = []
    try:
        from app.ai.pipelines.inference import run_inference
        inferred = await run_inference(profile.skills)
    except Exception as exc:
        log.warning("Inference skipped for upload %s: %s", upload_id, exc)

    # ── 4. Persist to DB ───────────────────────────────────────
    upload_res = await session.execute(
        select(ResumeUpload).where(ResumeUpload.id == upload_id)
    )
    upload = upload_res.scalar_one_or_none()
    if upload is None:
        raise ValueError(f"Upload {upload_id} not found")

    # Store raw LLM output for diff view in review queue
    upload.extracted_payload = profile.model_dump()
    await session.flush()

    await upsert_from_extraction(
        session=session,
        employee_id=upload.employee_id,
        profile=profile,
        inferred_skills=inferred,
    )

    # ── 5. Compute and store embedding ─────────────────────────
    try:
        from app.ai.pipelines.search import embed_employee
        await embed_employee(session, upload.employee_id)
    except Exception as exc:
        log.warning("Embedding skipped for upload %s: %s", upload_id, exc)

    # ── 6. Mark upload ready for review ───────────────────────
    upload.status = UploadStatus.PENDING_REVIEW.value
    await session.commit()

    log.info("Upload %s → pending_review ✓", upload_id)
