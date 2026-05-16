"""API tests for POST /search endpoint."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.providers.base import ProviderError, RateLimitError
from tests.conftest import make_result


def _mock_search_result(emp_id=None):
    return {
        "employee_id": str(emp_id or uuid.uuid4()),
        "name": "Alice Smith",
        "title": "Senior Engineer",
        "location": "NYC",
        "availability": "available",
        "total_years_exp": 7.0,
        "match_score": 88,
        "reasoning": "Strong Python and FastAPI skills match the requirements.",
        "strengths": ["Python", "FastAPI"],
        "gaps": ["Kubernetes"],
        "top_skills": [],
        "similarity": 0.92,
    }


def _mock_search_raw(results=None):
    return {
        "parsed_query": {
            "semantic_text": "Python developer",
            "required_skills": ["Python"],
            "min_years_per_skill": {},
            "availability": [],
            "location": None,
            "seniority_hint": None,
        },
        "results": results or [_mock_search_result()],
        "total_candidates_retrieved": 1,
    }


class TestSearchEndpoint:
    async def test_hr_can_search(self, hr_client, mock_session):
        with patch(
            "app.api.search.run_semantic_search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = _mock_search_raw()

            response = await hr_client.post(
                "/search",
                json={"query": "Find a senior Python developer", "limit": 8},
            )

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "parsed_query" in data
        assert "results" in data
        assert "total_candidates_retrieved" in data

    async def test_employee_cannot_search(self, emp_client, mock_session):
        response = await emp_client.post(
            "/search",
            json={"query": "Find a developer"},
        )
        assert response.status_code == 403

    async def test_unauthenticated_returns_401(self, anon_client):
        response = await anon_client.post(
            "/search",
            json={"query": "Find a developer"},
        )
        assert response.status_code == 401

    async def test_results_include_match_score_and_reasoning(self, hr_client, mock_session):
        with patch(
            "app.api.search.run_semantic_search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = _mock_search_raw()

            response = await hr_client.post(
                "/search",
                json={"query": "Python developer with 5 years experience"},
            )

        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["match_score"] == 88
        assert "Python" in results[0]["reasoning"] or results[0]["reasoning"] != ""

    async def test_empty_results_returned_when_no_match(self, hr_client, mock_session):
        with patch(
            "app.api.search.run_semantic_search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = {
                "parsed_query": {
                    "semantic_text": "COBOL developer",
                    "required_skills": [],
                    "min_years_per_skill": {},
                    "availability": [],
                    "location": None,
                    "seniority_hint": None,
                },
                "results": [],
                "total_candidates_retrieved": 0,
            }

            response = await hr_client.post(
                "/search", json={"query": "Find a COBOL developer"}
            )

        assert response.status_code == 200
        assert response.json()["results"] == []
        assert response.json()["total_candidates_retrieved"] == 0

    async def test_rate_limit_error_returns_429(self, hr_client, mock_session):
        with patch(
            "app.api.search.run_semantic_search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.side_effect = RateLimitError("Rate limited")

            response = await hr_client.post(
                "/search", json={"query": "Find a developer"}
            )

        assert response.status_code == 429

    async def test_provider_error_returns_503(self, hr_client, mock_session):
        with patch(
            "app.api.search.run_semantic_search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.side_effect = ProviderError("AI unavailable")

            response = await hr_client.post(
                "/search", json={"query": "Find a developer"}
            )

        assert response.status_code == 503

    async def test_missing_query_returns_422(self, hr_client):
        response = await hr_client.post("/search", json={"limit": 5})
        assert response.status_code == 422

    async def test_conversation_history_accepted(self, hr_client, mock_session):
        with patch(
            "app.api.search.run_semantic_search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = _mock_search_raw()

            response = await hr_client.post(
                "/search",
                json={
                    "query": "Also needs Node.js",
                    "conversation_history": [
                        {"role": "user", "content": "Find a React developer"},
                        {"role": "assistant", "content": "I found 3 React developers."},
                    ],
                },
            )

        assert response.status_code == 200
        # verify history was passed to search
        call_args = mock_search.call_args
        assert call_args.kwargs.get("conversation_history") is not None

    async def test_parsed_query_in_response(self, hr_client, mock_session):
        with patch(
            "app.api.search.run_semantic_search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = _mock_search_raw()

            response = await hr_client.post(
                "/search", json={"query": "Find a Python dev"}
            )

        parsed = response.json()["parsed_query"]
        assert "semantic_text" in parsed
        assert "required_skills" in parsed
