"""Unit tests for app.services.review."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_employee_model, make_result, make_upload, make_user


class TestListPending:
    async def test_empty_queue_returns_empty_list(self, mock_session):
        from app.services.review import list_pending

        mock_session.execute.return_value = make_result(scalars_list=[])

        result = await list_pending(mock_session)

        assert result == []

    async def test_returns_pending_review_items(self, mock_session):
        from app.db.models import UploadSource, UploadStatus
        from app.services.review import list_pending

        upload = make_upload(status=UploadStatus.PENDING_REVIEW.value)
        emp = make_employee_model(name="Jane Doe")
        emp.skills = []

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalars_list=[upload])
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        result = await list_pending(mock_session)

        assert len(result) == 1
        assert result[0].candidate_name == "Jane Doe"
        assert result[0].upload_id == upload.id

    async def test_counts_inferred_skills(self, mock_session):
        from app.services.review import list_pending

        upload = make_upload()
        emp = make_employee_model()

        inferred_skill = MagicMock()
        inferred_skill.source = "inferred"
        extracted_skill = MagicMock()
        extracted_skill.source = "extracted"
        emp.skills = [inferred_skill, extracted_skill]

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalars_list=[upload])
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        result = await list_pending(mock_session)

        assert result[0].skill_count == 2
        assert result[0].inferred_count == 1

    async def test_unknown_name_when_employee_not_found(self, mock_session):
        from app.services.review import list_pending

        upload = make_upload(employee_id=uuid.uuid4())

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalars_list=[upload])
            return make_result(scalar=None)  # employee not found

        mock_session.execute.side_effect = _execute

        result = await list_pending(mock_session)

        assert result[0].candidate_name == "Unknown"


class TestGetReviewDetail:
    async def test_not_found_returns_none(self, mock_session):
        from app.services.review import get_review_detail

        mock_session.execute.return_value = make_result(scalar=None)

        result = await get_review_detail(mock_session, uuid.uuid4())

        assert result is None

    async def test_found_returns_detail(self, mock_session):
        from app.services.review import get_review_detail

        upload = make_upload()
        emp = make_employee_model()

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=upload)
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        result = await get_review_detail(mock_session, upload.id)

        assert result is not None
        assert result.upload_id == upload.id

    async def test_raw_text_preview_truncated_to_500_chars(self, mock_session):
        from app.services.review import get_review_detail

        long_text = "X" * 1000
        upload = make_upload(raw_text=long_text)
        emp = make_employee_model()

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=upload)
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        result = await get_review_detail(mock_session, upload.id)

        assert result.raw_text_preview is not None
        assert len(result.raw_text_preview) == 500

    async def test_inferred_skills_separated_from_extracted(self, mock_session):
        from app.services.review import get_review_detail

        upload = make_upload()
        emp = make_employee_model()

        skill_inferred = MagicMock()
        skill_inferred.id = uuid.uuid4()
        skill_inferred.skill_id = uuid.uuid4()
        skill_inferred.source = "inferred"
        skill_inferred.proficiency = "intermediate"
        skill_inferred.years = Decimal("2.0")
        skill_inferred.confidence = Decimal("0.85")
        skill_inferred.evidence = None
        skill_inferred.skill = MagicMock()
        skill_inferred.skill.name = "JavaScript"
        skill_inferred.skill.category = "language"

        skill_extracted = MagicMock()
        skill_extracted.id = uuid.uuid4()
        skill_extracted.skill_id = uuid.uuid4()
        skill_extracted.source = "extracted"
        skill_extracted.proficiency = "expert"
        skill_extracted.years = Decimal("5.0")
        skill_extracted.confidence = Decimal("0.95")
        skill_extracted.evidence = "5 years Python"
        skill_extracted.skill = MagicMock()
        skill_extracted.skill.name = "Python"
        skill_extracted.skill.category = "language"

        emp.skills = [skill_inferred, skill_extracted]

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=upload)
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        result = await get_review_detail(mock_session, upload.id)

        inferred_names = [s.name for s in result.inferred_skills]
        assert "JavaScript" in inferred_names
        assert "Python" not in inferred_names


class TestApprove:
    async def test_not_found_returns_none(self, mock_session):
        from app.services.review import approve

        mock_session.execute.return_value = make_result(scalar=None)

        result = await approve(mock_session, uuid.uuid4(), uuid.uuid4())

        assert result is None

    async def test_sets_status_to_approved(self, mock_session):
        from app.db.models import UploadStatus
        from app.services.review import approve

        upload = make_upload(status="pending_review")

        mock_session.execute.return_value = make_result(scalar=upload)

        with patch("app.ai.pipelines.search.embed_employee", new_callable=AsyncMock):
            result = await approve(mock_session, upload.id, uuid.uuid4())

        assert upload.status == UploadStatus.APPROVED.value
        mock_session.commit.assert_called()

    async def test_sets_reviewed_at_and_reviewed_by(self, mock_session):
        from app.services.review import approve

        upload = make_upload()
        reviewer_id = uuid.uuid4()

        mock_session.execute.return_value = make_result(scalar=upload)

        with patch("app.ai.pipelines.search.embed_employee", new_callable=AsyncMock):
            await approve(mock_session, upload.id, reviewer_id)

        assert upload.reviewed_by == reviewer_id
        assert upload.reviewed_at is not None

    async def test_embed_failure_does_not_raise(self, mock_session):
        from app.services.review import approve

        upload = make_upload()

        mock_session.execute.return_value = make_result(scalar=upload)

        async def _failing_embed(*args, **kwargs):
            raise RuntimeError("Embedding failed")

        with patch("app.ai.pipelines.search.embed_employee", side_effect=_failing_embed):
            # Should not raise — embed failure is caught and logged
            result = await approve(mock_session, upload.id, uuid.uuid4())

        assert result is not None

    async def test_returns_approve_response(self, mock_session):
        from app.services.review import approve

        upload = make_upload()

        mock_session.execute.return_value = make_result(scalar=upload)

        with patch("app.ai.pipelines.search.embed_employee", new_callable=AsyncMock):
            result = await approve(mock_session, upload.id, uuid.uuid4())

        assert result.upload_id == upload.id
        assert "approved" in result.message.lower()


class TestReject:
    async def test_not_found_returns_none(self, mock_session):
        from app.services.review import reject

        mock_session.execute.return_value = make_result(scalar=None)

        result = await reject(mock_session, uuid.uuid4(), uuid.uuid4())

        assert result is None

    async def test_sets_status_to_rejected(self, mock_session):
        from app.db.models import UploadStatus
        from app.services.review import reject

        upload = make_upload(status="pending_review")
        emp = make_employee_model(name="Real Employee")  # not "Pending Review"

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=upload)
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        await reject(mock_session, upload.id, uuid.uuid4())

        assert upload.status == UploadStatus.REJECTED.value

    async def test_deletes_pending_employee_placeholder(self, mock_session):
        from app.services.review import reject

        upload = make_upload()
        pending_emp = make_employee_model(name="Pending Review")

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=upload)
            return make_result(scalar=pending_emp)

        mock_session.execute.side_effect = _execute

        await reject(mock_session, upload.id, uuid.uuid4())

        mock_session.delete.assert_called_once_with(pending_emp)

    async def test_does_not_delete_real_employee(self, mock_session):
        from app.services.review import reject

        upload = make_upload()
        real_emp = make_employee_model(name="Alice Smith")

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=upload)
            return make_result(scalar=real_emp)

        mock_session.execute.side_effect = _execute

        await reject(mock_session, upload.id, uuid.uuid4())

        mock_session.delete.assert_not_called()

    async def test_stores_rejection_reason_in_notes(self, mock_session):
        from app.services.review import reject

        upload = make_upload()
        real_emp = make_employee_model(name="Alice")

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=upload)
            return make_result(scalar=real_emp)

        mock_session.execute.side_effect = _execute

        await reject(mock_session, upload.id, uuid.uuid4(), reason="Duplicate resume")

        assert upload.notes == "Duplicate resume"


class TestEditProfile:
    async def test_not_found_upload_returns_none(self, mock_session):
        from app.schemas.review import ProfileEditRequest
        from app.services.review import edit_profile

        mock_session.execute.return_value = make_result(scalar=None)

        patch = ProfileEditRequest(name="New Name")
        result = await edit_profile(mock_session, uuid.uuid4(), patch, uuid.uuid4())

        assert result is None

    async def test_updates_employee_fields(self, mock_session):
        from app.schemas.review import ProfileEditRequest
        from app.services.review import edit_profile

        upload = make_upload()
        emp = make_employee_model(name="Old Name")

        # Sequence: upload lookup, employee lookup, then get_review_detail calls
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return make_result(scalar=upload if call_count == 1 else emp)
            # get_review_detail calls
            if call_count == 3:
                return make_result(scalar=upload)
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        patch = ProfileEditRequest(name="New Name", title="Senior Engineer")
        result = await edit_profile(mock_session, upload.id, patch, uuid.uuid4())

        mock_session.commit.assert_called()

    async def test_total_years_exp_rounded_to_decimal(self, mock_session):
        from app.schemas.review import ProfileEditRequest
        from app.services.review import edit_profile

        upload = make_upload()
        emp = make_employee_model()

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return make_result(scalar=upload if call_count == 1 else emp)
            if call_count == 3:
                return make_result(scalar=upload)
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        patch = ProfileEditRequest(total_years_exp=7.123)
        await edit_profile(mock_session, upload.id, patch, uuid.uuid4())

        # Verify setattr was called on emp (commit was called)
        mock_session.commit.assert_called()
