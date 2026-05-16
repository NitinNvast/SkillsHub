"""
Shared pytest fixtures for the SkillsHub test suite.

pytest_configure MUST be at the very top so env vars are set before any app
module is imported — app.core.config.Settings() runs at import time and
requires DATABASE_URL and JWT_SECRET.
"""

import os


def pytest_configure(config):
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/testdb")
    os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-tests-only-minimum32chars")
    os.environ.setdefault("LLM_PROVIDER", "groq")
    os.environ.setdefault("LLM_MODEL", "llama-3.3-70b-versatile")
    os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
    os.environ.setdefault("VOYAGE_API_KEY", "test-voyage-key")
    os.environ.setdefault("EMBEDDING_PROVIDER", "voyage")
    os.environ.setdefault("EMBEDDING_MODEL", "voyage-3-large")


# ── All app imports AFTER env vars are set ────────────────────────────────────
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.db.models import Employee, ResumeUpload, Skill, UploadSource, UploadStatus, User, UserRole


# ─── Mock session helpers ─────────────────────────────────────────────────────


def make_result(scalar=None, scalars_list=None, scalar_one=None, rows=None):
    """Build a fake SQLAlchemy result that behaves like a real execute() return."""
    r = MagicMock()
    r.scalar_one_or_none.return_value = scalar
    r.scalar_one.return_value = scalar_one if scalar_one is not None else scalar
    if scalars_list is not None:
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = scalars_list
        unique_mock = MagicMock()
        unique_mock.all.return_value = scalars_list
        scalars_mock.unique.return_value = unique_mock
        r.scalars.return_value = scalars_mock
    if rows is not None:
        r.all.return_value = rows
    return r


# ─── User factory ─────────────────────────────────────────────────────────────


def make_user(role: str = "hr", **kwargs) -> MagicMock:
    u = MagicMock(spec=User)
    u.id = kwargs.get("id", uuid.uuid4())
    u.email = kwargs.get("email", f"{role}@test.com")
    u.name = kwargs.get("name", f"Test {role.upper()}")
    u.role = role
    u.password_hash = hash_password("password123")
    u.created_at = datetime.now(UTC)
    return u


# ─── Employee factory ─────────────────────────────────────────────────────────


def make_employee_model(**kwargs) -> MagicMock:
    emp = MagicMock(spec=Employee)
    emp.id = kwargs.get("id", uuid.uuid4())
    emp.user_id = kwargs.get("user_id", uuid.uuid4())
    emp.name = kwargs.get("name", "Test Employee")
    emp.email = kwargs.get("email", "emp@test.com")
    emp.title = kwargs.get("title", "Engineer")
    emp.location = kwargs.get("location", "NYC")
    emp.summary = kwargs.get("summary", "Professional summary")
    emp.total_years_exp = kwargs.get("total_years_exp", Decimal("5.0"))
    emp.availability = kwargs.get("availability", "available")
    emp.current_project = None
    emp.last_project_end_date = None
    emp.github_username = None
    emp.skills = kwargs.get("skills", [])
    emp.projects = kwargs.get("projects", [])
    emp.certifications = kwargs.get("certifications", [])
    emp.created_at = datetime.now(UTC)
    emp.updated_at = datetime.now(UTC)
    return emp


# ─── ResumeUpload factory ─────────────────────────────────────────────────────


def make_upload(**kwargs) -> MagicMock:
    upload = MagicMock(spec=ResumeUpload)
    upload.id = kwargs.get("id", uuid.uuid4())
    upload.employee_id = kwargs.get("employee_id", uuid.uuid4())
    upload.source = kwargs.get("source", UploadSource.TEXT.value)
    upload.status = kwargs.get("status", UploadStatus.PENDING_REVIEW.value)
    upload.raw_text = kwargs.get("raw_text", "Some resume text content here.")
    upload.file_path = kwargs.get("file_path", None)
    upload.extracted_payload = kwargs.get("extracted_payload", None)
    upload.notes = kwargs.get("notes", None)
    upload.error = kwargs.get("error", None)
    upload.created_at = datetime.now(UTC)
    upload.reviewed_at = None
    upload.reviewed_by = None
    return upload


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def hr_user():
    return make_user(role="hr", email="hr@test.com", name="Test HR")


@pytest.fixture
def employee_user():
    return make_user(role="employee", email="emp@test.com", name="Test Employee")


@pytest.fixture
def hr_token(hr_user):
    return create_access_token(user_id=hr_user.id, role="hr")


@pytest.fixture
def employee_token(employee_user):
    return create_access_token(user_id=employee_user.id, role="employee")


@pytest.fixture
def app():
    from app.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
async def hr_client(app, mock_session, hr_user):
    from app.core.deps import get_current_user
    from app.db.session import get_session

    async def _session():
        yield mock_session

    async def _user():
        return hr_user

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_current_user] = _user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def emp_client(app, mock_session, employee_user):
    from app.core.deps import get_current_user
    from app.db.session import get_session

    async def _session():
        yield mock_session

    async def _user():
        return employee_user

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_current_user] = _user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def anon_client(app, mock_session):
    """Client with no authentication override (tests 401 scenarios)."""
    from app.db.session import get_session

    async def _session():
        yield mock_session

    app.dependency_overrides[get_session] = _session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
