"""API tests for /uploads/* endpoints."""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_result, make_upload


def _minimal_pdf() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"
        + b"A" * 200  # pad to pass the 100-byte minimum
    )


class TestUploadResume:
    async def test_pdf_upload_returns_202(self, hr_client, mock_session):
        upload = make_upload()
        emp_id = upload.employee_id

        with patch(
            "app.services.ingestion.ingest_pdf", new_callable=AsyncMock
        ) as mock_ingest:
            from app.schemas.upload import UploadResponse

            mock_ingest.return_value = UploadResponse(
                upload_id=upload.id,
                employee_id=emp_id,
                status="processing",
                message="Resume received. Check review queue.",
            )

            response = await hr_client.post(
                "/uploads/resume",
                files={"file": ("resume.pdf", _minimal_pdf(), "application/pdf")},
            )

        assert response.status_code == 202
        data = response.json()
        assert "upload_id" in data
        assert "employee_id" in data

    async def test_non_pdf_content_type_returns_415(self, hr_client):
        response = await hr_client.post(
            "/uploads/resume",
            files={"file": ("resume.txt", b"some text content here", "text/plain")},
        )
        assert response.status_code == 415

    async def test_empty_file_returns_422(self, hr_client):
        response = await hr_client.post(
            "/uploads/resume",
            files={"file": ("resume.pdf", b"tiny", "application/pdf")},
        )
        assert response.status_code == 422

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.post(
            "/uploads/resume",
            files={"file": ("resume.pdf", _minimal_pdf(), "application/pdf")},
        )
        assert response.status_code == 401

    async def test_large_file_returns_413(self, hr_client):
        big_bytes = b"A" * (10 * 1024 * 1024 + 1)  # > 10 MB
        response = await hr_client.post(
            "/uploads/resume",
            files={"file": ("resume.pdf", big_bytes, "application/pdf")},
        )
        assert response.status_code == 413


class TestUploadText:
    async def test_text_upload_returns_202(self, hr_client, mock_session):
        upload = make_upload()

        with patch(
            "app.services.ingestion.ingest_text", new_callable=AsyncMock
        ) as mock_ingest:
            from app.schemas.upload import UploadResponse

            mock_ingest.return_value = UploadResponse(
                upload_id=upload.id,
                employee_id=upload.employee_id,
                status="processing",
                message="Resume received. Check review queue.",
            )

            response = await hr_client.post(
                "/uploads/text",
                json={"text": "A" * 200, "name": "John Doe"},
            )

        assert response.status_code == 202
        assert "upload_id" in response.json()

    async def test_employee_can_upload_text(self, emp_client, mock_session):
        upload = make_upload()

        with patch(
            "app.services.ingestion.ingest_text", new_callable=AsyncMock
        ) as mock_ingest:
            from app.schemas.upload import UploadResponse

            mock_ingest.return_value = UploadResponse(
                upload_id=upload.id,
                employee_id=upload.employee_id,
                status="processing",
                message="Resume received. Check review queue.",
            )

            response = await emp_client.post(
                "/uploads/text",
                json={"text": "Resume content here " * 20},
            )

        assert response.status_code == 202

    async def test_unauthenticated_text_upload_returns_401(self, anon_client):
        response = await anon_client.post(
            "/uploads/text", json={"text": "Some resume text"}
        )
        assert response.status_code == 401


class TestBulkUpload:
    async def test_hr_can_bulk_upload(self, hr_client, mock_session):
        upload = make_upload()

        with patch(
            "app.services.ingestion.ingest_pdf", new_callable=AsyncMock
        ) as mock_ingest:
            from app.schemas.upload import UploadResponse

            mock_ingest.return_value = UploadResponse(
                upload_id=upload.id,
                employee_id=upload.employee_id,
                status="processing",
                message="Resume received. Check review queue.",
            )

            response = await hr_client.post(
                "/uploads/bulk",
                files=[("files", ("r1.pdf", _minimal_pdf(), "application/pdf"))],
            )

        assert response.status_code == 202
        data = response.json()
        assert "total" in data
        assert "queued" in data

    async def test_employee_cannot_bulk_upload(self, emp_client, mock_session):
        response = await emp_client.post(
            "/uploads/bulk",
            files=[("files", ("r1.pdf", _minimal_pdf(), "application/pdf"))],
        )
        assert response.status_code == 403

    async def test_too_many_files_returns_422(self, hr_client):
        files = [("files", (f"r{i}.pdf", _minimal_pdf(), "application/pdf")) for i in range(21)]
        response = await hr_client.post("/uploads/bulk", files=files)
        assert response.status_code == 422

    async def test_non_pdf_file_in_bulk_marked_failed(self, hr_client, mock_session):
        with patch("app.services.ingestion.ingest_pdf", new_callable=AsyncMock):
            response = await hr_client.post(
                "/uploads/bulk",
                files=[("files", ("doc.docx", b"word doc content here!!", "application/msword"))],
            )

        assert response.status_code == 202
        data = response.json()
        assert data["failed"] >= 1


class TestGetUploadStatus:
    async def test_found_returns_status(self, hr_client, mock_session):
        upload = make_upload()
        mock_session.execute.return_value = make_result(scalar=upload)

        response = await hr_client.get(f"/uploads/{upload.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == str(upload.id)
        assert "status" in data

    async def test_not_found_returns_404(self, hr_client, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        response = await hr_client.get(f"/uploads/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_employee_can_check_own_upload_status(self, emp_client, mock_session):
        upload = make_upload()
        mock_session.execute.return_value = make_result(scalar=upload)

        response = await emp_client.get(f"/uploads/{upload.id}")

        assert response.status_code == 200

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.get(f"/uploads/{uuid.uuid4()}")
        assert response.status_code == 401

    async def test_response_includes_extracted_payload_when_present(self, hr_client, mock_session):
        upload = make_upload(extracted_payload={"name": "Jane Doe", "skills": []})
        mock_session.execute.return_value = make_result(scalar=upload)

        response = await hr_client.get(f"/uploads/{upload.id}")

        assert response.json()["extracted_payload"] is not None
