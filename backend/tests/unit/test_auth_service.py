"""Unit tests for app.services.auth — authenticate, issue_token, register_employee."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.security import hash_password, verify_password
from app.db.models import User, UserRole
from app.services.auth import authenticate, issue_token, register_employee
from tests.conftest import make_result, make_user


class TestAuthenticate:
    async def test_valid_credentials_returns_user(self, mock_session):
        user = make_user(role="hr")
        mock_session.execute.return_value = make_result(scalar=user)

        result = await authenticate(mock_session, "hr@test.com", "password123")

        assert result is user

    async def test_wrong_password_returns_none(self, mock_session):
        user = make_user(role="hr")
        # password_hash is for "password123", try "wrongpass"
        mock_session.execute.return_value = make_result(scalar=user)

        result = await authenticate(mock_session, "hr@test.com", "wrongpass")

        assert result is None

    async def test_unknown_email_returns_none(self, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        result = await authenticate(mock_session, "nobody@test.com", "anypass")

        assert result is None

    async def test_calls_session_execute(self, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)

        await authenticate(mock_session, "user@test.com", "pass")

        mock_session.execute.assert_called_once()

    async def test_employee_can_authenticate(self, mock_session):
        user = make_user(role="employee")
        mock_session.execute.return_value = make_result(scalar=user)

        result = await authenticate(mock_session, "emp@test.com", "password123")

        assert result is user

    async def test_empty_password_returns_none(self, mock_session):
        user = make_user(role="hr")
        mock_session.execute.return_value = make_result(scalar=user)

        result = await authenticate(mock_session, "hr@test.com", "")

        assert result is None


class TestIssueToken:
    def test_returns_string(self):
        user = make_user(role="hr")
        token = issue_token(user)
        assert isinstance(token, str)

    def test_token_contains_user_id(self):
        from app.core.security import decode_token

        user = make_user(role="hr")
        token = issue_token(user)
        payload = decode_token(token)
        assert payload["sub"] == str(user.id)

    def test_token_contains_role(self):
        from app.core.security import decode_token

        emp = make_user(role="employee")
        token = issue_token(emp)
        payload = decode_token(token)
        assert payload["role"] == "employee"

    def test_hr_token_has_hr_role(self):
        from app.core.security import decode_token

        hr = make_user(role="hr")
        token = issue_token(hr)
        payload = decode_token(token)
        assert payload["role"] == "hr"


class TestRegisterEmployee:
    async def test_new_user_is_created_and_returned(self, mock_session):
        # First execute: no existing user found
        mock_session.execute.return_value = make_result(scalar=None)

        # The User object added via session.add gets refreshed — simulate the refresh
        created_user = MagicMock(spec=User)
        created_user.id = uuid.uuid4()
        created_user.email = "new@test.com"
        created_user.name = "New User"
        created_user.role = "employee"

        async def _refresh(obj):
            obj.id = created_user.id
            obj.email = created_user.email
            obj.name = created_user.name
            obj.role = created_user.role

        mock_session.refresh.side_effect = _refresh

        result = await register_employee(mock_session, "New User", "new@test.com", "password123")

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    async def test_duplicate_email_returns_none(self, mock_session):
        existing_user = make_user(role="employee")
        mock_session.execute.return_value = make_result(scalar=existing_user)

        result = await register_employee(mock_session, "Dup", "dup@test.com", "password123")

        assert result is None
        mock_session.add.assert_not_called()

    async def test_password_is_hashed(self, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)
        added_users = []

        def _capture_add(obj):
            added_users.append(obj)

        mock_session.add.side_effect = _capture_add
        mock_session.refresh = AsyncMock()

        await register_employee(mock_session, "User", "u@test.com", "plaintext")

        assert len(added_users) == 1
        user_obj = added_users[0]
        assert hasattr(user_obj, "password_hash")
        assert user_obj.password_hash != "plaintext"
        assert verify_password("plaintext", user_obj.password_hash)

    async def test_role_is_employee(self, mock_session):
        mock_session.execute.return_value = make_result(scalar=None)
        added_users = []
        mock_session.add.side_effect = lambda obj: added_users.append(obj)
        mock_session.refresh = AsyncMock()

        await register_employee(mock_session, "User", "u@test.com", "pass1234")

        assert added_users[0].role == UserRole.EMPLOYEE.value
