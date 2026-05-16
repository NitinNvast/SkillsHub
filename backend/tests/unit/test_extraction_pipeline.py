"""Unit tests for app.ai.pipelines.extraction."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.providers.base import ChatResponse, ProviderError, ToolCall, Usage
from app.schemas.extraction import StructuredProfile
from tests.conftest import make_result, make_upload


def _make_chat_response(tool_name: str, arguments: dict) -> ChatResponse:
    return ChatResponse(
        text="",
        tool_calls=[ToolCall(name=tool_name, arguments=arguments, id="tc-1")],
        usage=Usage(input_tokens=100, output_tokens=50),
        model="claude-sonnet-4-6",
        provider="anthropic",
        finish_reason="tool_use",
    )


def _make_empty_response() -> ChatResponse:
    return ChatResponse(
        text="I cannot extract.",
        tool_calls=[],
        usage=Usage(input_tokens=50, output_tokens=20),
        model="claude-sonnet-4-6",
        provider="anthropic",
        finish_reason="end_turn",
    )


_VALID_PROFILE_ARGS = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "location": "San Francisco, CA",
    "title": "Senior Software Engineer",
    "total_years_exp": 7.0,
    "summary": "Experienced engineer with strong Python and cloud skills.",
    "skills": [
        {"name": "Python", "proficiency": "expert", "years": 5.0, "confidence": 0.95}
    ],
    "projects": [
        {
            "name": "API Service",
            "role": "Lead",
            "description": "Built scalable REST API",
            "start_date": "2021-01",
            "end_date": "2022-06",
            "technologies": ["Python", "FastAPI"],
        }
    ],
    "certifications": [{"name": "AWS SAA", "issuer": "Amazon", "year": 2021}],
}


# ─── _profile_from_response ──────────────────────────────────────────────────


class TestProfileFromResponse:
    def test_valid_tool_call_returns_structured_profile(self):
        from app.ai.pipelines.extraction import _profile_from_response

        resp = _make_chat_response("extract_profile", _VALID_PROFILE_ARGS)
        profile = _profile_from_response(resp)

        assert isinstance(profile, StructuredProfile)
        assert profile.name == "Jane Doe"
        assert profile.email == "jane@example.com"
        assert len(profile.skills) == 1
        assert profile.skills[0].name == "Python"

    def test_no_tool_call_raises_provider_error(self):
        from app.ai.pipelines.extraction import _profile_from_response

        resp = _make_empty_response()

        with pytest.raises(ProviderError, match="did not call extract_profile"):
            _profile_from_response(resp)

    def test_profile_includes_projects_and_certs(self):
        from app.ai.pipelines.extraction import _profile_from_response

        resp = _make_chat_response("extract_profile", _VALID_PROFILE_ARGS)
        profile = _profile_from_response(resp)

        assert len(profile.projects) == 1
        assert profile.projects[0].name == "API Service"
        assert len(profile.certifications) == 1
        assert profile.certifications[0].name == "AWS SAA"


# ─── run_extraction_pipeline ─────────────────────────────────────────────────


class TestRunExtractionPipeline:
    async def test_happy_path_full_pipeline(self, mock_session):
        from app.ai.pipelines.extraction import run_extraction_pipeline

        upload_id = uuid.uuid4()
        employee_id = uuid.uuid4()
        upload = make_upload(id=upload_id, employee_id=employee_id)

        # DB: skills catalog, then upload lookup
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalars_list=[])  # empty skill catalog
            return make_result(scalar=upload)  # upload lookup

        mock_session.execute.side_effect = _execute

        mock_resp = _make_chat_response("extract_profile", _VALID_PROFILE_ARGS)

        with (
            patch(
                "app.ai.pipelines.extraction.ai_manager"
            ) as mock_ai,
            patch(
                "app.ai.pipelines.extraction.upsert_from_extraction", new_callable=AsyncMock
            ) as mock_upsert,
            patch(
                "app.ai.pipelines.inference.run_inference", new_callable=AsyncMock
            ) as mock_infer,
            patch(
                "app.ai.pipelines.search.embed_employee", new_callable=AsyncMock
            ) as mock_embed,
        ):
            mock_ai.chat = AsyncMock(return_value=mock_resp)
            mock_infer.return_value = []
            mock_upsert.return_value = None
            mock_embed.return_value = None

            await run_extraction_pipeline(mock_session, upload_id, "A" * 300)

        mock_upsert.assert_called_once()
        assert upload.status == "pending_review"
        mock_session.commit.assert_called()

    async def test_poor_quality_text_uses_vision_fallback(self, mock_session):
        from app.ai.pipelines.extraction import run_extraction_pipeline

        upload_id = uuid.uuid4()
        upload = make_upload(id=upload_id)

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalars_list=[])
            return make_result(scalar=upload)

        mock_session.execute.side_effect = _execute

        mock_resp = _make_chat_response("extract_profile", _VALID_PROFILE_ARGS)
        fake_pdf = b"%PDF fake pdf bytes for vision"

        with (
            patch(
                "app.ai.pipelines.extraction._call_extraction_vision", new_callable=AsyncMock
            ) as mock_vision,
            patch(
                "app.ai.pipelines.extraction._call_extraction", new_callable=AsyncMock
            ) as mock_text,
            patch(
                "app.ai.pipelines.extraction.upsert_from_extraction", new_callable=AsyncMock
            ),
            patch(
                "app.ai.pipelines.inference.run_inference", new_callable=AsyncMock, return_value=[]
            ),
            patch(
                "app.ai.pipelines.search.embed_employee", new_callable=AsyncMock
            ),
        ):
            mock_vision.return_value = StructuredProfile(**_VALID_PROFILE_ARGS)
            mock_text.return_value = StructuredProfile(**_VALID_PROFILE_ARGS)

            # Short text (< 200 chars) + pdf_bytes provided → vision path
            await run_extraction_pipeline(
                mock_session, upload_id, "Short", pdf_bytes=fake_pdf
            )

        mock_vision.assert_called_once()
        mock_text.assert_not_called()

    async def test_good_quality_text_uses_text_extraction(self, mock_session):
        from app.ai.pipelines.extraction import run_extraction_pipeline

        upload_id = uuid.uuid4()
        upload = make_upload(id=upload_id)

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalars_list=[])
            return make_result(scalar=upload)

        mock_session.execute.side_effect = _execute

        with (
            patch(
                "app.ai.pipelines.extraction._call_extraction_vision", new_callable=AsyncMock
            ) as mock_vision,
            patch(
                "app.ai.pipelines.extraction._call_extraction", new_callable=AsyncMock
            ) as mock_text,
            patch(
                "app.ai.pipelines.extraction.upsert_from_extraction", new_callable=AsyncMock
            ),
            patch(
                "app.ai.pipelines.inference.run_inference", new_callable=AsyncMock, return_value=[]
            ),
            patch(
                "app.ai.pipelines.search.embed_employee", new_callable=AsyncMock
            ),
        ):
            mock_text.return_value = StructuredProfile(**_VALID_PROFILE_ARGS)

            await run_extraction_pipeline(mock_session, upload_id, "A" * 300)

        mock_text.assert_called_once()
        mock_vision.assert_not_called()

    async def test_upload_not_found_raises_value_error(self, mock_session):
        from app.ai.pipelines.extraction import run_extraction_pipeline

        upload_id = uuid.uuid4()

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalars_list=[])  # catalog
            return make_result(scalar=None)  # upload not found

        mock_session.execute.side_effect = _execute

        with (
            patch(
                "app.ai.pipelines.extraction._call_extraction", new_callable=AsyncMock
            ) as mock_text,
            patch(
                "app.ai.pipelines.inference.run_inference", new_callable=AsyncMock, return_value=[]
            ),
        ):
            mock_text.return_value = StructuredProfile(**_VALID_PROFILE_ARGS)

            with pytest.raises(ValueError, match="not found"):
                await run_extraction_pipeline(mock_session, upload_id, "A" * 300)

    async def test_inference_failure_is_non_fatal(self, mock_session):
        from app.ai.pipelines.extraction import run_extraction_pipeline

        upload_id = uuid.uuid4()
        upload = make_upload(id=upload_id)

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalars_list=[])
            return make_result(scalar=upload)

        mock_session.execute.side_effect = _execute

        with (
            patch(
                "app.ai.pipelines.extraction._call_extraction", new_callable=AsyncMock
            ) as mock_text,
            patch(
                "app.ai.pipelines.inference.run_inference", new_callable=AsyncMock
            ) as mock_infer,
            patch(
                "app.ai.pipelines.extraction.upsert_from_extraction", new_callable=AsyncMock
            ),
            patch(
                "app.ai.pipelines.search.embed_employee", new_callable=AsyncMock
            ),
        ):
            mock_text.return_value = StructuredProfile(**_VALID_PROFILE_ARGS)
            mock_infer.side_effect = RuntimeError("LLM error")

            # Should not raise — inference failure is logged but pipeline continues
            await run_extraction_pipeline(mock_session, upload_id, "A" * 300)

        assert upload.status == "pending_review"

    async def test_canonical_skills_loaded_from_db(self, mock_session):
        from app.ai.pipelines.extraction import run_extraction_pipeline

        upload_id = uuid.uuid4()
        upload = make_upload(id=upload_id)

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(rows=[("Python",)])  # catalog: select(Skill.name) returns tuples
            return make_result(scalar=upload)

        mock_session.execute.side_effect = _execute

        with (
            patch(
                "app.ai.pipelines.extraction._call_extraction", new_callable=AsyncMock
            ) as mock_text,
            patch(
                "app.ai.pipelines.inference.run_inference", new_callable=AsyncMock, return_value=[]
            ),
            patch(
                "app.ai.pipelines.extraction.upsert_from_extraction", new_callable=AsyncMock
            ),
            patch(
                "app.ai.pipelines.search.embed_employee", new_callable=AsyncMock
            ),
        ):
            captured_args = {}

            async def _capture(raw_text, canonical_skills):
                captured_args["canonical_skills"] = canonical_skills
                return StructuredProfile(**_VALID_PROFILE_ARGS)

            mock_text.side_effect = _capture

            await run_extraction_pipeline(mock_session, upload_id, "A" * 300)

        assert "Python" in captured_args.get("canonical_skills", [])
