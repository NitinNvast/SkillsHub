"""API tests for /review-queue/* endpoints (HR-only)."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_employee_model, make_result, make_upload


def _mock_review_item(upload_id=None, emp_id=None):
    from app.schemas.review import ReviewQueueItem

    return ReviewQueueItem(
        upload_id=upload_id or uuid.uuid4(),
        employee_id=emp_id or uuid.uuid4(),
        candidate_name="Jane Doe",
        source="text",
        status="pending_review",
        created_at=datetime.now(UTC),
        skill_count=5,
        inferred_count=2,
    )


def _mock_review_detail(upload_id=None, emp_id=None):
    from app.schemas.review import ReviewQueueDetail

    return ReviewQueueDetail(
        upload_id=upload_id or uuid.uuid4(),
        employee_id=emp_id or uuid.uuid4(),
        source="text",
        status="pending_review",
        created_at=datetime.now(UTC),
        raw_text_preview="Resume text preview...",
        current_profile=None,
        extracted_payload=None,
        inferred_skills=[],
        error=None,
    )


class TestListReviewQueue:
    async def test_hr_can_list_queue(self, hr_client, mock_session):
        with patch(
            "app.services.review.list_pending", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = [_mock_review_item()]

            response = await hr_client.get("/review-queue")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["candidate_name"] == "Jane Doe"

    async def test_employee_cannot_access_queue(self, emp_client):
        response = await emp_client.get("/review-queue")
        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.get("/review-queue")
        assert response.status_code == 401

    async def test_empty_queue_returns_empty_list(self, hr_client, mock_session):
        with patch(
            "app.services.review.list_pending", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = []

            response = await hr_client.get("/review-queue")

        assert response.status_code == 200
        assert response.json() == []

    async def test_queue_items_have_required_fields(self, hr_client, mock_session):
        with patch(
            "app.services.review.list_pending", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = [_mock_review_item()]

            response = await hr_client.get("/review-queue")

        item = response.json()[0]
        assert "upload_id" in item
        assert "candidate_name" in item
        assert "status" in item
        assert "skill_count" in item


class TestGetReviewDetail:
    async def test_hr_can_get_detail(self, hr_client, mock_session):
        detail = _mock_review_detail()

        with patch(
            "app.services.review.get_review_detail", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = detail

            response = await hr_client.get(f"/review-queue/{detail.upload_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == str(detail.upload_id)

    async def test_not_found_returns_404(self, hr_client, mock_session):
        with patch(
            "app.services.review.get_review_detail", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            response = await hr_client.get(f"/review-queue/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_employee_cannot_get_detail(self, emp_client):
        response = await emp_client.get(f"/review-queue/{uuid.uuid4()}")
        assert response.status_code == 403


class TestApproveUpload:
    async def test_hr_can_approve_upload(self, hr_client, mock_session):
        from app.schemas.review import ApproveResponse

        upload_id = uuid.uuid4()
        approve_resp = ApproveResponse(
            upload_id=upload_id,
            employee_id=uuid.uuid4(),
            status="approved",
            message="Profile approved and indexed for search.",
        )

        with patch(
            "app.services.review.approve", new_callable=AsyncMock
        ) as mock_approve:
            mock_approve.return_value = approve_resp

            response = await hr_client.post(f"/review-queue/{upload_id}/approve")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert "approved" in data["message"].lower()

    async def test_approve_not_found_returns_404(self, hr_client, mock_session):
        with patch(
            "app.services.review.approve", new_callable=AsyncMock
        ) as mock_approve:
            mock_approve.return_value = None

            response = await hr_client.post(f"/review-queue/{uuid.uuid4()}/approve")

        assert response.status_code == 404

    async def test_employee_cannot_approve(self, emp_client):
        response = await emp_client.post(f"/review-queue/{uuid.uuid4()}/approve")
        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.post(f"/review-queue/{uuid.uuid4()}/approve")
        assert response.status_code == 401


class TestRejectUpload:
    async def test_hr_can_reject_upload(self, hr_client, mock_session):
        from app.schemas.review import RejectResponse

        upload_id = uuid.uuid4()
        reject_resp = RejectResponse(
            upload_id=upload_id,
            status="rejected",
            message="Upload rejected and removed from queue.",
        )

        with patch(
            "app.services.review.reject", new_callable=AsyncMock
        ) as mock_reject:
            mock_reject.return_value = reject_resp

            response = await hr_client.post(
                f"/review-queue/{upload_id}/reject",
                json={"reason": "Duplicate profile"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    async def test_reject_not_found_returns_404(self, hr_client, mock_session):
        with patch(
            "app.services.review.reject", new_callable=AsyncMock
        ) as mock_reject:
            mock_reject.return_value = None

            response = await hr_client.post(
                f"/review-queue/{uuid.uuid4()}/reject",
                json={"reason": "Not valid"},
            )

        assert response.status_code == 404

    async def test_reject_without_reason_still_works(self, hr_client, mock_session):
        from app.schemas.review import RejectResponse

        upload_id = uuid.uuid4()
        with patch(
            "app.services.review.reject", new_callable=AsyncMock
        ) as mock_reject:
            mock_reject.return_value = RejectResponse(
                upload_id=upload_id,
                status="rejected",
                message="Rejected.",
            )

            response = await hr_client.post(
                f"/review-queue/{upload_id}/reject", json={"reason": None}
            )

        assert response.status_code == 200

    async def test_employee_cannot_reject(self, emp_client):
        response = await emp_client.post(
            f"/review-queue/{uuid.uuid4()}/reject", json={"reason": "bad"}
        )
        assert response.status_code == 403


class TestEditReviewItem:
    async def test_hr_can_edit_profile(self, hr_client, mock_session):
        detail = _mock_review_detail()

        with patch(
            "app.services.review.edit_profile", new_callable=AsyncMock
        ) as mock_edit:
            mock_edit.return_value = detail

            response = await hr_client.patch(
                f"/review-queue/{detail.upload_id}",
                json={"name": "Corrected Name", "title": "Senior Engineer"},
            )

        assert response.status_code == 200

    async def test_edit_not_found_returns_404(self, hr_client, mock_session):
        with patch(
            "app.services.review.edit_profile", new_callable=AsyncMock
        ) as mock_edit:
            mock_edit.return_value = None

            response = await hr_client.patch(
                f"/review-queue/{uuid.uuid4()}",
                json={"name": "Updated Name"},
            )

        assert response.status_code == 404

    async def test_employee_cannot_edit_review_item(self, emp_client):
        response = await emp_client.patch(
            f"/review-queue/{uuid.uuid4()}",
            json={"name": "New Name"},
        )
        assert response.status_code == 403
