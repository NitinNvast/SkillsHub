"""API tests for /auth/* endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.security import hash_password
from tests.conftest import make_result, make_user


class TestLoginJson:
    async def test_login_success_returns_token_and_user(self, hr_client, mock_session, hr_user):
        mock_session.execute.return_value = make_result(scalar=hr_user)

        response = await hr_client.post(
            "/auth/login", json={"email": "hr@test.com", "password": "password123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == hr_user.email

    async def test_login_wrong_password_returns_401(self, anon_client, mock_session, hr_user):
        mock_session.execute.return_value = make_result(scalar=hr_user)

        response = await anon_client.post(
            "/auth/login", json={"email": "hr@test.com", "password": "wrongpass"}
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    async def test_login_unknown_email_returns_401(self, anon_client, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        response = await anon_client.post(
            "/auth/login", json={"email": "nobody@test.com", "password": "pass"}
        )

        assert response.status_code == 401

    async def test_login_missing_email_returns_422(self, anon_client):
        response = await anon_client.post("/auth/login", json={"password": "pass"})
        assert response.status_code == 422

    async def test_login_missing_password_returns_422(self, anon_client):
        response = await anon_client.post("/auth/login", json={"email": "test@test.com"})
        assert response.status_code == 422

    async def test_login_employee_role_reflected_in_token(self, anon_client, mock_session):
        emp_user = make_user(role="employee")
        mock_session.execute.return_value = make_result(scalar=emp_user)

        response = await anon_client.post(
            "/auth/login", json={"email": "emp@test.com", "password": "password123"}
        )

        assert response.status_code == 200
        assert response.json()["user"]["role"] == "employee"


class TestRegister:
    async def test_register_new_user_returns_201_and_token(self, anon_client, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)  # email not taken

        new_user = make_user(role="employee", email="new@test.com", name="New User")

        async def _refresh(obj):
            obj.id = new_user.id
            obj.email = new_user.email
            obj.name = new_user.name
            obj.role = "employee"

        mock_session.refresh.side_effect = _refresh

        response = await anon_client.post(
            "/auth/register",
            json={"name": "New User", "email": "new@test.com", "password": "securepass"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

    async def test_register_duplicate_email_returns_409(self, anon_client, mock_session):
        existing = make_user(role="employee")
        mock_session.execute.return_value = make_result(scalar=existing)

        response = await anon_client.post(
            "/auth/register",
            json={"name": "Dup", "email": "existing@test.com", "password": "pass1234"},
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_register_missing_name_returns_422(self, anon_client):
        response = await anon_client.post(
            "/auth/register", json={"email": "test@test.com", "password": "pass1234"}
        )
        assert response.status_code == 422

    async def test_register_invalid_email_returns_422(self, anon_client):
        response = await anon_client.post(
            "/auth/register",
            json={"name": "User", "email": "not-an-email", "password": "pass1234"},
        )
        assert response.status_code == 422


class TestMe:
    async def test_me_returns_current_user(self, hr_client, hr_user):
        response = await hr_client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == hr_user.email
        assert data["role"] == "hr"

    async def test_me_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.get("/auth/me")
        assert response.status_code == 401

    async def test_me_employee_returns_employee_role(self, emp_client, employee_user):
        response = await emp_client.get("/auth/me")

        assert response.status_code == 200
        assert response.json()["role"] == "employee"


class TestLoginForm:
    async def test_form_login_success(self, anon_client, mock_session, hr_user):
        mock_session.execute.return_value = make_result(scalar=hr_user)

        response = await anon_client.post(
            "/auth/token",
            data={"username": "hr@test.com", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_form_login_wrong_password_returns_401(self, anon_client, mock_session, hr_user):
        mock_session.execute.return_value = make_result(scalar=hr_user)

        response = await anon_client.post(
            "/auth/token",
            data={"username": "hr@test.com", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401
