"""API tests for /employees/* endpoints."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_employee_model, make_result, make_user


def _mock_employee_skill(name="Python"):
    es = MagicMock()
    es.id = uuid.uuid4()
    es.skill_id = uuid.uuid4()
    es.proficiency = "expert"
    es.years = Decimal("3.0")
    es.source = "extracted"
    es.confidence = Decimal("0.95")
    es.evidence = None
    es.skill = MagicMock()
    es.skill.name = name
    es.skill.category = "language"
    return es


class TestListEmployees:
    async def test_hr_can_list_employees(self, hr_client, mock_session):
        emp = make_employee_model(skills=[_mock_employee_skill()])
        mock_session.execute.return_value = make_result(scalars_list=[emp])

        response = await hr_client.get("/employees")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["name"] == emp.name

    async def test_employee_can_list_employees(self, emp_client, mock_session):
        mock_session.execute.return_value = make_result(scalars_list=[])

        response = await emp_client.get("/employees")

        assert response.status_code == 200

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.get("/employees")
        assert response.status_code == 401

    async def test_search_query_param_accepted(self, hr_client, mock_session):
        mock_session.execute.return_value = make_result(scalars_list=[])

        response = await hr_client.get("/employees?q=Python")

        assert response.status_code == 200


class TestGetEmployeeMe:
    async def test_returns_own_profile(self, emp_client, mock_session, employee_user):
        emp = make_employee_model(user_id=employee_user.id)
        skill = _mock_employee_skill()
        emp.skills = [skill]

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=emp)  # find by user_id
            return make_result(scalar=emp)  # get_employee detail

        mock_session.execute.side_effect = _execute

        response = await emp_client.get("/employees/me")

        assert response.status_code == 200
        assert response.json()["name"] == emp.name

    async def test_returns_404_when_no_profile(self, emp_client, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        response = await emp_client.get("/employees/me")

        assert response.status_code == 404

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.get("/employees/me")
        assert response.status_code == 401


class TestGetEmployeeById:
    async def test_hr_can_get_any_employee(self, hr_client, mock_session):
        emp = make_employee_model()
        emp.skills = [_mock_employee_skill()]
        mock_session.execute.return_value = make_result(scalar=emp)

        response = await hr_client.get(f"/employees/{emp.id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(emp.id)

    async def test_not_found_returns_404(self, hr_client, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        response = await hr_client.get(f"/employees/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_employee_can_view_profiles(self, emp_client, mock_session):
        emp = make_employee_model()
        emp.skills = []
        mock_session.execute.return_value = make_result(scalar=emp)

        response = await emp_client.get(f"/employees/{emp.id}")

        assert response.status_code == 200


class TestCreateEmployee:
    async def test_hr_can_create_employee(self, hr_client, mock_session):
        new_emp = make_employee_model(email="new@test.com")
        new_emp.skills = []

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return make_result(scalar=None)  # uniqueness checks pass
            return make_result(scalar=new_emp)  # get_employee call

        mock_session.execute.side_effect = _execute

        response = await hr_client.post(
            "/employees",
            json={
                "name": "New Hire",
                "email": "new@test.com",
                "password": "securepass",
                "title": "Engineer",
                "location": "NYC",
            },
        )

        assert response.status_code == 201
        assert response.json()["email"] == "new@test.com"

    async def test_employee_cannot_create_employee(self, emp_client, mock_session):
        response = await emp_client.post(
            "/employees",
            json={
                "name": "New Hire",
                "email": "new@test.com",
                "password": "securepass",
            },
        )

        assert response.status_code == 403

    async def test_duplicate_email_returns_409(self, hr_client, mock_session):
        from tests.conftest import make_user

        existing_user = make_user(role="employee")
        mock_session.execute.return_value = make_result(scalar=existing_user)

        response = await hr_client.post(
            "/employees",
            json={
                "name": "Dup",
                "email": "existing@test.com",
                "password": "securepass",
            },
        )

        assert response.status_code == 409

    async def test_missing_required_fields_returns_422(self, hr_client):
        response = await hr_client.post("/employees", json={"name": "No Email"})
        assert response.status_code == 422


class TestUpdateEmployee:
    async def test_hr_can_update_any_employee(self, hr_client, mock_session):
        emp = make_employee_model()

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=emp)  # find employee
            return make_result(scalar=emp)  # get_employee for response

        mock_session.execute.side_effect = _execute

        response = await hr_client.patch(
            f"/employees/{emp.id}", json={"title": "Senior Engineer"}
        )

        assert response.status_code == 200

    async def test_employee_can_update_own_profile(self, emp_client, mock_session, employee_user):
        emp = make_employee_model(user_id=employee_user.id)

        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=emp)  # own employee check
            if call_count == 2:
                return make_result(scalar=emp)  # find employee for update
            return make_result(scalar=emp)  # get_employee for response

        mock_session.execute.side_effect = _execute

        response = await emp_client.patch(
            f"/employees/{emp.id}", json={"title": "Lead Engineer"}
        )

        assert response.status_code == 200

    async def test_employee_cannot_update_another_profile(self, emp_client, mock_session, employee_user):
        other_emp = make_employee_model(user_id=uuid.uuid4())

        # Own employee check returns different id
        own_emp = make_employee_model(user_id=employee_user.id, id=uuid.uuid4())

        mock_session.execute.return_value = make_result(scalar=own_emp)

        response = await emp_client.patch(
            f"/employees/{other_emp.id}", json={"title": "Lead"}
        )

        assert response.status_code == 403

    async def test_not_found_returns_404(self, hr_client, mock_session):
        call_count = 0

        async def _execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return make_result(scalar=None)  # employee not found by id

        mock_session.execute.side_effect = _execute

        response = await hr_client.patch(
            f"/employees/{uuid.uuid4()}", json={"title": "Engineer"}
        )

        assert response.status_code == 404


class TestDeleteEmployee:
    async def test_hr_can_delete_employee(self, hr_client, mock_session):
        emp = make_employee_model()
        mock_session.execute.return_value = make_result(scalar=emp)

        response = await hr_client.delete(f"/employees/{emp.id}")

        assert response.status_code == 204
        mock_session.delete.assert_called_once_with(emp)
        mock_session.commit.assert_called()

    async def test_employee_cannot_delete(self, emp_client, mock_session):
        response = await emp_client.delete(f"/employees/{uuid.uuid4()}")
        assert response.status_code == 403

    async def test_delete_not_found_returns_404(self, hr_client, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        response = await hr_client.delete(f"/employees/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.delete(f"/employees/{uuid.uuid4()}")
        assert response.status_code == 401
