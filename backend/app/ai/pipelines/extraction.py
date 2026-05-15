"""Resume extraction pipeline — provider-agnostic implementation.

Flow:
  1. Load canonical skill names from DB (for normalization in system prompt)
  2. Call ai_manager.chat(task="extraction", ...) with EXTRACT_PROFILE_TOOL
     - Fallback: if text quality is poor, send PDF images as vision content
  3. Call inference pipeline → inferred skills appended
  4. Upsert Employee + Skills + Projects + Certs (repos/employees.py)
  5. Trigger embedding update via ai_manager.embed
  6. Mark upload status → pending_review

All LLM calls flow through `app.ai.providers.ai_manager`. The provider and
model used here are controlled by EXTRACTION_PROVIDER / EXTRACTION_MODEL
(falling back to LLM_PROVIDER / LLM_MODEL) in the environment.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts.extract_resume import (
    EXTRACT_PROFILE_TOOL,
    build_system_prompt,
    build_user_message,
)
from app.ai.providers import ChatRequest, ProviderError, ai_manager
from app.db.models import ResumeUpload, Skill, UploadStatus
from app.db.repos.employees import upsert_from_extraction
from app.schemas.extraction import StructuredProfile

log = logging.getLogger(__name__)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _profile_from_response(resp) -> StructuredProfile:
    """Parse the manager's normalized tool call into a StructuredProfile."""
    call = resp.first_tool_call()
    if call is None:
        raise ProviderError(
            f"{resp.provider}: model did not call extract_profile tool "
            f"(stop_reason={resp.finish_reason})"
        )
    return StructuredProfile.model_validate(call.arguments)


# ─── LLM calls (text + vision) ───────────────────────────────────────────────


async def _call_extraction(raw_text: str, canonical_skills: list[str]) -> StructuredProfile:
    request = ChatRequest(
        system=build_system_prompt(canonical_skills),
        messages=[{"role": "user", "content": build_user_message(raw_text)}],
        tools=[EXTRACT_PROFILE_TOOL],
        tool_choice="any",
        max_tokens=4096,
        cache_system_prompt=True,  # provider-supported caching (Anthropic)
    )
    resp = await ai_manager.chat(request, task="extraction")
    return _profile_from_response(resp)


async def _call_extraction_vision(
    pdf_bytes: bytes, canonical_skills: list[str]
) -> StructuredProfile:
    """Vision fallback for scanned/image-based PDFs.

    Sends the first 3 pages as base64 images. The content blocks use the
    canonical Anthropic-style shape; providers translate as needed.
    """
    import base64
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    content: list[dict] = []

    for i, page in enumerate(reader.pages[:3]):
        images = list(page.images) if hasattr(page, "images") else []
        for img in images[:2]:
            img_b64 = base64.standard_b64encode(img.data).decode()
            content.append(
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": img_b64},
                }
            )
        text = page.extract_text() or ""
        if text.strip():
            content.append({"type": "text", "text": f"Page {i + 1} text:\n{text.strip()}"})

    if not content:
        raise ValueError("PDF has no extractable text or images")

    content.append(
        {
            "type": "text",
            "text": (
                "Please extract the structured profile from this resume. "
                "Call the extract_profile tool."
            ),
        }
    )

    request = ChatRequest(
        system=build_system_prompt(canonical_skills),
        messages=[{"role": "user", "content": content}],
        tools=[EXTRACT_PROFILE_TOOL],
        tool_choice="any",
        max_tokens=4096,
        cache_system_prompt=True,
    )
    resp = await ai_manager.chat(request, task="extraction")
    return _profile_from_response(resp)


# ─── Main pipeline ───────────────────────────────────────────────────────────


async def run_extraction_pipeline(
    session: AsyncSession,
    upload_id: UUID,
    raw_text: str,
    pdf_bytes: bytes | None = None,
) -> None:
    """Full extraction pipeline. Called by services/ingestion.py after file save."""
    log.info("Extraction pipeline started for upload %s", upload_id)

    # 1. Load skill catalog names for normalization hint
    result = await session.execute(select(Skill.name))
    canonical_skills = [row[0] for row in result.all()]

    # 2. Extract structured profile (text or vision fallback)
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

    # 3. Inference pipeline
    inferred: list[dict] = []
    try:
        from app.ai.pipelines.inference import run_inference

        inferred = await run_inference(profile.skills)
    except Exception as exc:
        log.warning("Inference skipped for upload %s: %s", upload_id, exc)

    # 4. Persist to DB
    upload_res = await session.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id))
    upload = upload_res.scalar_one_or_none()
    if upload is None:
        raise ValueError(f"Upload {upload_id} not found")

    upload.extracted_payload = profile.model_dump()
    await session.flush()

    await upsert_from_extraction(
        session=session,
        employee_id=upload.employee_id,
        profile=profile,
        inferred_skills=inferred,
    )

    # 5. Compute and store embedding
    try:
        from app.ai.pipelines.search import embed_employee

        await embed_employee(session, upload.employee_id)
    except Exception as exc:
        log.warning("Embedding skipped for upload %s: %s", upload_id, exc)

    # 6. Mark upload ready for review
    upload.status = UploadStatus.PENDING_REVIEW.value
    await session.commit()

    log.info("Upload %s → pending_review ✓", upload_id)
