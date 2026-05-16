"""Unit tests for app.db.repos.employees and app.db.repos.embeddings."""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_employee_model, make_result


# ─── _infer_category ─────────────────────────────────────────────────────────


class TestInferCategory:
    def test_aws_is_platform(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("AWS Lambda") == "platform"

    def test_docker_is_platform(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("Docker") == "platform"

    def test_postgres_is_platform(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("PostgreSQL") == "platform"

    def test_react_is_framework(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("React") == "framework"

    def test_django_is_framework(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("Django") == "framework"

    def test_fastapi_is_framework(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("FastAPI") == "framework"

    def test_python_is_language(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("Python") == "language"

    def test_javascript_is_language(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("JavaScript") == "language"

    def test_sql_is_language(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("SQL") == "language"

    def test_machine_learning_is_domain(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("Machine Learning") == "domain"

    def test_devops_is_domain(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("DevOps") == "domain"

    def test_unknown_defaults_to_tool(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("Some Obscure Tool") == "tool"

    def test_case_insensitive_matching(self):
        from app.db.repos.employees import _infer_category

        assert _infer_category("PYTHON") == "language"
        assert _infer_category("django") == "framework"


# ─── _parse_date ─────────────────────────────────────────────────────────────


class TestParseDate:
    def test_four_digit_year_returns_jan_1(self):
        from app.db.repos.employees import _parse_date

        result = _parse_date("2020")
        assert result == date(2020, 1, 1)

    def test_year_month_format(self):
        from app.db.repos.employees import _parse_date

        result = _parse_date("2021-06")
        assert result == date(2021, 6, 1)

    def test_none_returns_none(self):
        from app.db.repos.employees import _parse_date

        assert _parse_date(None) is None

    def test_empty_string_returns_none(self):
        from app.db.repos.employees import _parse_date

        assert _parse_date("") is None

    def test_invalid_format_returns_none(self):
        from app.db.repos.employees import _parse_date

        assert _parse_date("not-a-date") is None
        assert _parse_date("13-2020") is None

    def test_valid_date_returns_date_object(self):
        from app.db.repos.employees import _parse_date

        result = _parse_date("2023-03")
        assert isinstance(result, date)
        assert result.year == 2023
        assert result.month == 3


# ─── load_skill_catalog ───────────────────────────────────────────────────────


class TestLoadSkillCatalog:
    async def test_returns_lowercase_name_map(self, mock_session):
        from app.db.models import Skill, SkillCategory
        from app.db.repos.employees import load_skill_catalog

        skill = MagicMock(spec=Skill)
        skill.name = "Python"
        skill.category = SkillCategory.LANGUAGE.value
        skill.aliases = []

        mock_session.execute.return_value = make_result(scalars_list=[skill])

        catalog = await load_skill_catalog(mock_session)

        assert "python" in catalog
        assert catalog["python"] is skill

    async def test_aliases_are_indexed(self, mock_session):
        from app.db.models import Skill
        from app.db.repos.employees import load_skill_catalog

        skill = MagicMock(spec=Skill)
        skill.name = "JavaScript"
        skill.aliases = ["js", "ECMAScript"]

        mock_session.execute.return_value = make_result(scalars_list=[skill])

        catalog = await load_skill_catalog(mock_session)

        assert "js" in catalog
        assert "ecmascript" in catalog
        assert catalog["js"] is skill

    async def test_empty_catalog_returns_empty_dict(self, mock_session):
        from app.db.repos.employees import load_skill_catalog

        mock_session.execute.return_value = make_result(scalars_list=[])

        catalog = await load_skill_catalog(mock_session)

        assert catalog == {}


# ─── find_or_create_skill ────────────────────────────────────────────────────


class TestFindOrCreateSkill:
    async def test_returns_existing_skill_from_catalog(self, mock_session):
        from app.db.models import Skill
        from app.db.repos.employees import find_or_create_skill

        skill = MagicMock(spec=Skill)
        skill.name = "Python"
        catalog = {"python": skill}

        result = await find_or_create_skill(mock_session, "Python", catalog)

        assert result is skill
        mock_session.add.assert_not_called()

    async def test_creates_new_skill_when_not_in_catalog(self, mock_session):
        from app.db.repos.employees import find_or_create_skill

        catalog = {}
        created = []
        mock_session.add.side_effect = lambda obj: created.append(obj)

        result = await find_or_create_skill(mock_session, "Rust", catalog)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert "rust" in catalog  # catalog updated in-place

    async def test_new_skill_infers_category(self, mock_session):
        from app.db.repos.employees import find_or_create_skill

        catalog = {}
        created = []
        mock_session.add.side_effect = lambda obj: created.append(obj)

        await find_or_create_skill(mock_session, "Python", catalog)

        assert len(created) == 1
        assert created[0].category == "language"

    async def test_lookup_is_case_insensitive(self, mock_session):
        from app.db.models import Skill
        from app.db.repos.employees import find_or_create_skill

        skill = MagicMock(spec=Skill)
        catalog = {"react": skill}

        result = await find_or_create_skill(mock_session, "REACT", catalog)

        assert result is skill


# ─── render_profile_summary ──────────────────────────────────────────────────


class TestRenderProfileSummary:
    def test_includes_title_in_header(self):
        from app.db.repos.embeddings import render_profile_summary

        emp = make_employee_model(title="Staff Engineer", location="Austin")
        emp.skills = []
        emp.projects = []
        emp.certifications = []

        summary = render_profile_summary(emp)

        assert "Staff Engineer" in summary
        assert "Austin" in summary

    def test_includes_title_and_location(self):
        from app.db.repos.embeddings import render_profile_summary

        emp = make_employee_model(title="Senior Engineer", location="New York")
        emp.skills = []
        emp.projects = []
        emp.certifications = []

        summary = render_profile_summary(emp)

        assert "Senior Engineer" in summary
        assert "New York" in summary

    def test_includes_skills(self):
        from app.db.repos.embeddings import render_profile_summary

        skill = MagicMock()
        skill.skill = MagicMock()
        skill.skill.name = "Python"
        skill.proficiency = "expert"
        skill.years = Decimal("5.0")
        skill.source = "extracted"  # render_profile_summary filters by source

        emp = make_employee_model()
        emp.skills = [skill]
        emp.projects = []
        emp.certifications = []

        summary = render_profile_summary(emp)

        assert "Python" in summary

    def test_returns_non_empty_string(self):
        from app.db.repos.embeddings import render_profile_summary

        emp = make_employee_model()
        emp.skills = []
        emp.projects = []
        emp.certifications = []

        summary = render_profile_summary(emp)

        assert isinstance(summary, str)
        assert len(summary) > 0
