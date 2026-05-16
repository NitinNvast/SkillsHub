"""API tests for /skills/* endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import make_result


def _mock_skill(name="Python", category="language"):
    s = MagicMock()
    s.id = uuid.uuid4()
    s.name = name
    s.category = category
    s.aliases = []
    return s


class TestSkillsCatalog:
    async def test_hr_can_get_catalog(self, hr_client, mock_session):
        skill = _mock_skill("Python", "language")
        mock_session.execute.return_value = make_result(scalars_list=[skill])

        response = await hr_client.get("/skills/catalog")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["name"] == "Python"
        assert data[0]["category"] == "language"

    async def test_employee_can_get_catalog(self, emp_client, mock_session):
        mock_session.execute.return_value = make_result(scalars_list=[])

        response = await emp_client.get("/skills/catalog")

        assert response.status_code == 200

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.get("/skills/catalog")
        assert response.status_code == 401

    async def test_empty_catalog_returns_empty_list(self, hr_client, mock_session):
        mock_session.execute.return_value = make_result(scalars_list=[])

        response = await hr_client.get("/skills/catalog")

        assert response.status_code == 200
        assert response.json() == []

    async def test_catalog_entry_has_required_fields(self, hr_client, mock_session):
        skill = _mock_skill("TypeScript", "language")
        mock_session.execute.return_value = make_result(scalars_list=[skill])

        response = await hr_client.get("/skills/catalog")

        item = response.json()[0]
        assert "id" in item
        assert "name" in item
        assert "category" in item
        assert "aliases" in item

    async def test_multiple_skills_returned(self, hr_client, mock_session):
        skills = [_mock_skill("Python", "language"), _mock_skill("React", "framework"), _mock_skill("AWS", "platform")]
        mock_session.execute.return_value = make_result(scalars_list=skills)

        response = await hr_client.get("/skills/catalog")

        assert len(response.json()) == 3


class TestSkillGaps:
    async def test_hr_can_get_gaps(self, hr_client, mock_session):
        # Two execute calls: total employee count + skill gap query
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar_one=10)  # total employees
            # skill gap rows
            row = MagicMock()
            row.name = "Python"
            row.category = "language"
            row.employee_count = 3
            row.expert_count = 1
            row.intermediate_count = 2
            rows_result = MagicMock()
            rows_result.__iter__ = lambda s: iter([row])
            return rows_result

        mock_session.execute.side_effect = _execute

        response = await hr_client.get("/skills/gaps")

        assert response.status_code == 200
        data = response.json()
        assert "total_employees" in data
        assert "items" in data
        assert data["total_employees"] == 10

    async def test_employee_can_get_gaps(self, emp_client, mock_session):
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar_one=5)
            rows_result = MagicMock()
            rows_result.__iter__ = lambda s: iter([])
            return rows_result

        mock_session.execute.side_effect = _execute

        response = await emp_client.get("/skills/gaps")

        assert response.status_code == 200

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.get("/skills/gaps")
        assert response.status_code == 401

    async def test_gap_severity_critical_when_coverage_zero(self, hr_client, mock_session):
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar_one=10)
            row = MagicMock()
            row.name = "Rare Skill"
            row.category = "tool"
            row.employee_count = 0  # zero coverage
            row.expert_count = 0
            row.intermediate_count = 0
            rows_result = MagicMock()
            rows_result.__iter__ = lambda s: iter([row])
            return rows_result

        mock_session.execute.side_effect = _execute

        response = await hr_client.get("/skills/gaps")
        items = response.json()["items"]

        assert items[0]["gap_severity"] == "critical"

    async def test_gap_severity_healthy_when_high_coverage(self, hr_client, mock_session):
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar_one=10)
            row = MagicMock()
            row.name = "Common Skill"
            row.category = "language"
            row.employee_count = 8  # 80% coverage
            row.expert_count = 4
            row.intermediate_count = 3
            rows_result = MagicMock()
            rows_result.__iter__ = lambda s: iter([row])
            return rows_result

        mock_session.execute.side_effect = _execute

        response = await hr_client.get("/skills/gaps")
        items = response.json()["items"]

        assert items[0]["gap_severity"] == "healthy"
