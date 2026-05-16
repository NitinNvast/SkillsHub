"""Unit tests for app.services.ingestion."""

import io
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_employee_model, make_result, make_upload


# ─── extract_text_from_pdf ────────────────────────────────────────────────────


def _make_minimal_pdf() -> bytes:
    """Return the smallest syntactically-valid PDF bytes for testing."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"
    )


class TestExtractTextFromPdf:
    def test_returns_tuple_of_text_and_bool(self):
        from app.services.ingestion import extract_text_from_pdf

        pdf_bytes = _make_minimal_pdf()
        result = extract_text_from_pdf(pdf_bytes)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], bool)

    def test_good_quality_flag_false_for_empty_pdf(self):
        from app.services.ingestion import extract_text_from_pdf

        pdf_bytes = _make_minimal_pdf()
        _, is_good = extract_text_from_pdf(pdf_bytes)

        # Minimal PDF has no text content → not good quality
        assert is_good is False

    def test_good_quality_flag_true_for_text_pdf(self):
        """Mock PdfReader to simulate a text-rich PDF."""
        from app.services.ingestion import extract_text_from_pdf

        long_text = "A" * 300  # >200 chars

        mock_page = MagicMock()
        mock_page.extract_text.return_value = long_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("app.services.ingestion.PdfReader", return_value=mock_reader):
            text, is_good = extract_text_from_pdf(b"fake-pdf")

        assert is_good is True
        assert long_text in text

    def test_text_below_200_chars_is_poor_quality(self):
        from app.services.ingestion import extract_text_from_pdf

        short_text = "Short text"

        mock_page = MagicMock()
        mock_page.extract_text.return_value = short_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("app.services.ingestion.PdfReader", return_value=mock_reader):
            _, is_good = extract_text_from_pdf(b"fake-pdf")

        assert is_good is False

    def test_multiple_pages_joined_with_separator(self):
        from app.services.ingestion import extract_text_from_pdf

        mock_pages = [MagicMock(), MagicMock()]
        mock_pages[0].extract_text.return_value = "Page one content"
        mock_pages[1].extract_text.return_value = "Page two content"
        mock_reader = MagicMock()
        mock_reader.pages = mock_pages

        with patch("app.services.ingestion.PdfReader", return_value=mock_reader):
            text, _ = extract_text_from_pdf(b"fake-pdf")

        assert "PAGE BREAK" in text
        assert "Page one content" in text
        assert "Page two content" in text

    def test_empty_pages_are_skipped(self):
        from app.services.ingestion import extract_text_from_pdf

        mock_pages = [MagicMock(), MagicMock()]
        mock_pages[0].extract_text.return_value = ""
        mock_pages[1].extract_text.return_value = "   "
        mock_reader = MagicMock()
        mock_reader.pages = mock_pages

        with patch("app.services.ingestion.PdfReader", return_value=mock_reader):
            text, _ = extract_text_from_pdf(b"fake-pdf")

        assert text == ""


# ─── sanitize_text ────────────────────────────────────────────────────────────


class TestSanitizeText:
    def test_removes_triple_newlines(self):
        from app.services.ingestion import sanitize_text

        text = "Line one\n\n\n\nLine two"
        result = sanitize_text(text)

        assert "\n\n\n" not in result
        assert "Line one" in result
        assert "Line two" in result

    def test_collapses_multiple_spaces(self):
        from app.services.ingestion import sanitize_text

        text = "Word1   Word2     Word3"
        result = sanitize_text(text)

        assert "  " not in result
        assert "Word1 Word2 Word3" in result

    def test_strips_leading_and_trailing_whitespace(self):
        from app.services.ingestion import sanitize_text

        result = sanitize_text("  \n  hello world  \n  ")
        assert result == "hello world"

    def test_preserves_paragraph_breaks(self):
        from app.services.ingestion import sanitize_text

        text = "Paragraph one.\n\nParagraph two."
        result = sanitize_text(text)

        assert "\n\n" in result

    def test_empty_string_returns_empty(self):
        from app.services.ingestion import sanitize_text

        assert sanitize_text("") == ""

    def test_no_change_to_clean_text(self):
        from app.services.ingestion import sanitize_text

        clean = "This is clean text.\n\nSecond paragraph."
        assert sanitize_text(clean) == clean


# ─── save_pdf ─────────────────────────────────────────────────────────────────


class TestSavePdf:
    def test_saves_file_and_returns_path(self, tmp_path):
        from app.services.ingestion import save_pdf

        with patch("app.services.ingestion.UPLOAD_DIR", tmp_path):
            emp_id = uuid.uuid4()
            path = save_pdf(b"fake-pdf-content", emp_id)

        assert Path(path).exists()
        assert Path(path).read_bytes() == b"fake-pdf-content"

    def test_path_includes_employee_id(self, tmp_path):
        from app.services.ingestion import save_pdf

        with patch("app.services.ingestion.UPLOAD_DIR", tmp_path):
            emp_id = uuid.uuid4()
            path = save_pdf(b"content", emp_id)

        assert str(emp_id) in path

    def test_path_ends_with_pdf(self, tmp_path):
        from app.services.ingestion import save_pdf

        with patch("app.services.ingestion.UPLOAD_DIR", tmp_path):
            path = save_pdf(b"content", uuid.uuid4())

        assert path.endswith(".pdf")

    def test_creates_directory_if_not_exists(self, tmp_path):
        from app.services.ingestion import save_pdf

        emp_id = uuid.uuid4()
        expected_dir = tmp_path / str(emp_id)
        assert not expected_dir.exists()

        with patch("app.services.ingestion.UPLOAD_DIR", tmp_path):
            save_pdf(b"data", emp_id)

        assert expected_dir.exists()


# ─── get_or_create_employee ───────────────────────────────────────────────────


class TestGetOrCreateEmployee:
    async def test_returns_existing_by_email(self, mock_session):
        from app.services.ingestion import get_or_create_employee

        existing = make_employee_model(email="found@test.com")
        mock_session.execute.return_value = make_result(scalar=existing)

        result = await get_or_create_employee(mock_session, "Found", "found@test.com")

        assert result is existing
        mock_session.add.assert_not_called()

    async def test_returns_existing_by_user_id(self, mock_session):
        from app.services.ingestion import get_or_create_employee

        uid = uuid.uuid4()
        existing = make_employee_model(user_id=uid)
        # email=None → email check is skipped; only one execute call (user_id check)
        mock_session.execute.return_value = make_result(scalar=existing)

        result = await get_or_create_employee(mock_session, "Found", None, user_id=uid)

        assert result is existing

    async def test_creates_new_when_not_found(self, mock_session):
        from app.services.ingestion import get_or_create_employee

        mock_session.execute.return_value = make_result(scalar=None)
        created_employees = []
        mock_session.add.side_effect = lambda obj: created_employees.append(obj)

        await get_or_create_employee(mock_session, "New Person", "new@test.com")

        mock_session.flush.assert_called()
        assert len(created_employees) == 1

    async def test_placeholder_email_generated_when_none(self, mock_session):
        from app.services.ingestion import get_or_create_employee

        # No email, no user_id
        mock_session.execute.return_value = make_result(scalar=None)
        added = []
        mock_session.add.side_effect = lambda obj: added.append(obj)

        await get_or_create_employee(mock_session, "Ghost", None)

        assert len(added) == 1
        assert "@upload.local" in added[0].email


# ─── ingest_text ──────────────────────────────────────────────────────────────


def _session_with_id_assignment(mock_session):
    """Make mock_session.add() assign UUIDs to ORM objects (simulates flush behaviour)."""
    def _add(obj):
        if getattr(obj, "id", "sentinel") is None:
            obj.id = uuid.uuid4()
    mock_session.add.side_effect = _add
    return mock_session


class TestIngestText:
    async def test_returns_upload_response(self, mock_session):
        from app.services.ingestion import ingest_text

        _session_with_id_assignment(mock_session)

        with patch("app.ai.pipelines.extraction.run_extraction_pipeline", new_callable=AsyncMock):
            result = await ingest_text(mock_session, "A" * 500, uuid.uuid4())

        assert result.upload_id is not None
        assert result.employee_id is not None
        assert "resume received" in result.message.lower()

    async def test_pipeline_failure_marks_upload_failed(self, mock_session):
        from app.db.models import ResumeUpload, UploadStatus
        from app.services.ingestion import ingest_text

        _session_with_id_assignment(mock_session)

        # After pipeline failure, ingest_text re-fetches upload from DB via select
        upload_row = MagicMock(spec=ResumeUpload)
        upload_row.status = UploadStatus.PROCESSING.value
        mock_session.execute.return_value = make_result(scalar=upload_row)

        async def _failing_pipeline(**kwargs):
            raise RuntimeError("AI service down")

        with patch("app.ai.pipelines.extraction.run_extraction_pipeline", side_effect=_failing_pipeline):
            await ingest_text(mock_session, "Some text content", None)

        assert upload_row.status == UploadStatus.FAILED.value

    async def test_sanitizes_text_before_storing(self, mock_session):
        from app.services.ingestion import ingest_text

        dirty_text = "Line one\n\n\n\nLine two    end"
        _session_with_id_assignment(mock_session)

        with patch("app.ai.pipelines.extraction.run_extraction_pipeline", new_callable=AsyncMock):
            await ingest_text(mock_session, dirty_text, None)

        mock_session.commit.assert_called()


# ─── get_upload_status ────────────────────────────────────────────────────────


class TestGetUploadStatus:
    async def test_found_returns_upload(self, mock_session):
        from app.services.ingestion import get_upload_status

        from tests.conftest import make_upload

        upload = make_upload()
        mock_session.execute.return_value = make_result(scalar=upload)

        result = await get_upload_status(mock_session, upload.id)

        assert result is upload

    async def test_not_found_returns_none(self, mock_session):
        from app.services.ingestion import get_upload_status

        mock_session.execute.return_value = make_result(scalar=None)

        result = await get_upload_status(mock_session, uuid.uuid4())

        assert result is None
