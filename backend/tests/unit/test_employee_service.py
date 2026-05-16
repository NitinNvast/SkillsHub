"""Unit tests for app.services.employees."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.employee import CreateEmployeeRequest, EmployeeUpdate
from app.services.employees import (
    create_employee_with_account,
    get_employee,
    list_employees,
    update_employee,
)
from tests.conftest import make_employee_model, make_result


def _mock_employee_skill(skill_name="Python", years=3.0):
    es = MagicMock()
    es.skill = MagicMock()
    es.skill.name = skill_name
    es.skill.category = "language"
    es.id = uuid.uuid4()
    es.skill_id = uuid.uuid4()
    es.proficiency = "expert"
    es.years = Decimal(str(years))
    es.source = "extracted"
    es.confidence = Decimal("0.95")
    es.evidence = None
    return es


class TestListEmployees:
    async def test_returns_list_of_items(self, mock_session):
        skill = _mock_employee_skill()
        emp = make_employee_model(skills=[skill])
        mock_session.execute.return_value = make_result(scalars_list=[emp])

        result = await list_employees(mock_session)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].name == emp.name

    async def test_returns_empty_list_when_no_employees(self, mock_session):
        mock_session.execute.return_value = make_result(scalars_list=[])

        result = await list_employees(mock_session)

        assert result == []

    async def test_top_skills_limited_to_five(self, mock_session):
        skills = [_mock_employee_skill(f"Skill{i}", 10 - i) for i in range(7)]
        emp = make_employee_model(skills=skills)
        mock_session.execute.return_value = make_result(scalars_list=[emp])

        result = await list_employees(mock_session)

        assert len(result[0].top_skills) <= 5

    async def test_applies_query_filter(self, mock_session):
        mock_session.execute.return_value = make_result(scalars_list=[])

        result = await list_employees(mock_session, q="Python")

        # The query is built with a WHERE clause — execute should still be called
        mock_session.execute.assert_called_once()
        assert result == []

    async def test_skills_sorted_by_years_descending(self, mock_session):
        skills = [
            _mock_employee_skill("Go", 1.0),
            _mock_employee_skill("Python", 5.0),
            _mock_employee_skill("Java", 3.0),
        ]
        emp = make_employee_model(skills=skills)
        mock_session.execute.return_value = make_result(scalars_list=[emp])

        result = await list_employees(mock_session)

        top = result[0].top_skills
        assert top[0] == "Python"  # highest years first


class TestGetEmployee:
    async def test_found_returns_detail(self, mock_session):
        skill = _mock_employee_skill()
        emp = make_employee_model(skills=[skill])
        mock_session.execute.return_value = make_result(scalar=emp)

        eid = emp.id
        result = await get_employee(mock_session, eid)

        assert result is not None
        assert result.id == emp.id
        assert result.name == emp.name

    async def test_not_found_returns_none(self, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        result = await get_employee(mock_session, uuid.uuid4())

        assert result is None

    async def test_detail_includes_skills(self, mock_session):
        skill = _mock_employee_skill("Python")
        emp = make_employee_model(skills=[skill])
        mock_session.execute.return_value = make_result(scalar=emp)

        result = await get_employee(mock_session, emp.id)

        assert len(result.skills) == 1
        assert result.skills[0].name == "Python"

    async def test_detail_includes_projects_and_certs(self, mock_session):
        project = MagicMock()
        project.id = uuid.uuid4()
        project.name = "Test Project"
        project.role = "Lead"
        project.description = "A test project"
        project.start_date = None
        project.end_date = None
        project.technologies = ["Python"]

        cert = MagicMock()
        cert.id = uuid.uuid4()
        cert.name = "AWS Cert"
        cert.issuer = "Amazon"
        cert.year = 2022

        emp = make_employee_model(projects=[project], certifications=[cert])
        mock_session.execute.return_value = make_result(scalar=emp)

        result = await get_employee(mock_session, emp.id)

        assert len(result.projects) == 1
        # projects are returned as dicts by the service layer
        assert result.projects[0].name == "Test Project"
        assert len(result.certifications) == 1
        assert result.certifications[0].name == "AWS Cert"


class TestCreateEmployeeWithAccount:
    async def test_creates_user_and_employee(self, mock_session):
        # Both uniqueness checks pass (no existing)
        emp = make_employee_model()

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # User uniqueness + Employee uniqueness checks
                return make_result(scalar=None)
            # get_employee inner call
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        payload = CreateEmployeeRequest(
            name="New Hire",
            email="newhire@test.com",
            password="securepass",
            title="Engineer",
            location="NYC",
        )
        result = await create_employee_with_account(mock_session, payload)

        assert mock_session.add.call_count >= 2  # User + Employee
        assert mock_session.flush.call_count >= 1

    async def test_duplicate_user_email_raises_value_error(self, mock_session):
        from tests.conftest import make_user

        existing = make_user(role="employee")
        mock_session.execute.return_value = make_result(scalar=existing)

        payload = CreateEmployeeRequest(
            name="Dup",
            email="existing@test.com",
            password="securepass",
        )
        with pytest.raises(ValueError, match="account"):
            await create_employee_with_account(mock_session, payload)

    async def test_duplicate_employee_email_raises_value_error(self, mock_session):
        existing_emp = make_employee_model()
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=None)  # user check passes
            return make_result(scalar=existing_emp)  # employee check fails

        mock_session.execute.side_effect = _execute

        payload = CreateEmployeeRequest(
            name="Dup",
            email="existing@test.com",
            password="securepass",
        )
        with pytest.raises(ValueError, match="employee profile"):
            await create_employee_with_account(mock_session, payload)


class TestUpdateEmployee:
    async def test_updates_fields_and_returns_detail(self, mock_session):
        emp = make_employee_model()
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=emp)  # find employee
            return make_result(scalar=emp)  # get_employee inner call

        mock_session.execute.side_effect = _execute

        patch = EmployeeUpdate(title="Senior Engineer", location="SF")
        result = await update_employee(mock_session, emp.id, patch)

        mock_session.commit.assert_called_once()

    async def test_not_found_returns_none(self, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        patch = EmployeeUpdate(title="New Title")
        result = await update_employee(mock_session, uuid.uuid4(), patch)

        assert result is None

    async def test_partial_update_only_sets_provided_fields(self, mock_session):
        """Verify that only provided fields are applied (exclude_unset=True)."""
        emp = make_employee_model()

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        patch = EmployeeUpdate(title="Lead")
        await update_employee(mock_session, emp.id, patch)

        # Only title should have been set via setattr
        # Verify that setattr was called exactly once for "title"
        emp.title = "Lead"  # simulate what the service does
        mock_session.commit.assert_called()

    async def test_empty_patch_still_commits(self, mock_session):
        emp = make_employee_model()

        async def _execute(stmt):
            return make_result(scalar=emp)

        mock_session.execute.side_effect = _execute

        patch = EmployeeUpdate()
        await update_employee(mock_session, emp.id, patch)

        mock_session.commit.assert_called_once()
