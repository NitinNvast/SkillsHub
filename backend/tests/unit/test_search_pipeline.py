"""Unit tests for app.ai.pipelines.search."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.providers.base import ChatResponse, ProviderError, RateLimitError, ToolCall, Usage
from tests.conftest import make_employee_model, make_result


def _make_chat_response(tool_name: str, arguments: dict) -> ChatResponse:
    return ChatResponse(
        text="",
        tool_calls=[ToolCall(name=tool_name, arguments=arguments, id="tc-1")],
        usage=Usage(input_tokens=100, output_tokens=50),
        model="test-model",
        provider="test",
        finish_reason="tool_use",
    )


def _make_empty_response() -> ChatResponse:
    return ChatResponse(
        text="No result.",
        tool_calls=[],
        usage=Usage(input_tokens=50, output_tokens=10),
        model="test-model",
        provider="test",
        finish_reason="end_turn",
    )


# ─── _parse_query ─────────────────────────────────────────────────────────────


class TestParseQuery:
    async def test_returns_structured_parsed_query(self):
        from app.ai.pipelines.search import _parse_query

        parsed_args = {
            "semantic_text": "senior Python developer",
            "required_skills": ["Python"],
            "min_years_per_skill": {"Python": 3},
            "location": "NYC",
            "availability": ["available"],
            "seniority_hint": "senior",
        }
        mock_resp = _make_chat_response("parse_query", parsed_args)

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(return_value=mock_resp)
            result = await _parse_query("Find a senior Python dev in NYC")

        assert result["semantic_text"] == "senior Python developer"
        assert "Python" in result["required_skills"]
        assert result["location"] == "NYC"

    async def test_provider_error_falls_back_to_raw_query(self):
        from app.ai.pipelines.search import _parse_query

        query = "Find React developers"

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(side_effect=ProviderError("LLM down"))
            result = await _parse_query(query)

        assert result["semantic_text"] == query
        assert result["required_skills"] == []

    async def test_no_tool_call_falls_back_to_raw_query(self):
        from app.ai.pipelines.search import _parse_query

        query = "Backend engineer with Java"

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(return_value=_make_empty_response())
            result = await _parse_query(query)

        assert result["semantic_text"] == query

    async def test_includes_conversation_history_in_messages(self):
        from app.ai.pipelines.search import _parse_query

        history = [{"role": "user", "content": "Find a React dev"}, {"role": "assistant", "content": "OK"}]
        mock_resp = _make_chat_response(
            "parse_query",
            {"semantic_text": "React developer", "required_skills": [], "min_years_per_skill": {}, "availability": []},
        )

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(return_value=mock_resp)
            await _parse_query("Also needs Node.js", conversation_history=history)

            call_args = mock_ai.chat.call_args
            request = call_args[0][0]
            assert any(m["role"] == "user" and "Find a React dev" in m["content"] for m in request.messages)


# ─── _rerank_candidates ───────────────────────────────────────────────────────


class TestRerankCandidates:
    async def test_empty_candidates_returns_empty(self):
        from app.ai.pipelines.search import _rerank_candidates

        result = await _rerank_candidates("query", [], limit=5)
        assert result == []

    async def test_returns_ranked_results_with_score_and_reasoning(self):
        from app.ai.pipelines.search import _rerank_candidates

        emp_id = str(uuid.uuid4())
        candidates = [{"employee_id": emp_id, "name": "Alice", "similarity": 0.9, "summary_text": "Alice is a skilled developer."}]
        ranked_args = {
            "ranked": [
                {
                    "employee_id": emp_id,
                    "match_score": 85,
                    "reasoning": "Strong Python background",
                    "strengths": ["Python", "FastAPI"],
                    "gaps": ["Kubernetes"],
                }
            ]
        }
        mock_resp = _make_chat_response("rerank_candidates", ranked_args)

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(return_value=mock_resp)
            result = await _rerank_candidates("Find Python dev", candidates, limit=5)

        assert len(result) == 1
        assert result[0]["match_score"] == 85
        assert result[0]["reasoning"] == "Strong Python background"
        assert "Python" in result[0]["strengths"]

    async def test_match_score_clamped_to_0_100(self):
        from app.ai.pipelines.search import _rerank_candidates

        emp_id = str(uuid.uuid4())
        candidates = [{"employee_id": emp_id, "name": "Bob", "similarity": 0.5, "summary_text": "Bob is a developer."}]
        ranked_args = {
            "ranked": [{"employee_id": emp_id, "match_score": 150, "reasoning": "Excellent match"}]
        }
        mock_resp = _make_chat_response("rerank_candidates", ranked_args)

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(return_value=mock_resp)
            result = await _rerank_candidates("query", candidates, limit=5)

        assert result[0]["match_score"] == 100

    async def test_provider_error_falls_back_to_similarity_order(self):
        from app.ai.pipelines.search import _rerank_candidates

        emp_id = str(uuid.uuid4())
        candidates = [{"employee_id": emp_id, "name": "Carol", "similarity": 0.75, "summary_text": "Carol profile."}]

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(side_effect=ProviderError("LLM down"))
            result = await _rerank_candidates("query", candidates, limit=5)

        assert len(result) == 1
        assert result[0]["match_score"] == int(0.75 * 100)
        assert result[0]["employee_id"] == emp_id

    async def test_no_tool_call_falls_back_to_similarity_order(self):
        from app.ai.pipelines.search import _rerank_candidates

        emp_id = str(uuid.uuid4())
        candidates = [{"employee_id": emp_id, "name": "Dan", "similarity": 0.60, "summary_text": "Dan profile."}]

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(return_value=_make_empty_response())
            result = await _rerank_candidates("query", candidates, limit=5)

        assert result[0]["match_score"] == int(0.60 * 100)

    async def test_respects_limit(self):
        from app.ai.pipelines.search import _rerank_candidates

        ids = [str(uuid.uuid4()) for _ in range(5)]
        candidates = [{"employee_id": eid, "name": f"Person{i}", "similarity": 0.9 - i * 0.1, "summary_text": f"Person {i} profile."} for i, eid in enumerate(ids)]
        ranked_args = {
            "ranked": [
                {"employee_id": eid, "match_score": 90 - i * 5, "reasoning": "Good"}
                for i, eid in enumerate(ids)
            ]
        }
        mock_resp = _make_chat_response("rerank_candidates", ranked_args)

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.chat = AsyncMock(return_value=mock_resp)
            result = await _rerank_candidates("query", candidates, limit=3)

        assert len(result) <= 3


# ─── run_semantic_search ──────────────────────────────────────────────────────


class TestRunSemanticSearch:
    async def test_returns_empty_results_when_no_vector_matches(self, mock_session):
        from app.ai.pipelines.search import run_semantic_search

        with (
            patch("app.ai.pipelines.search._parse_query", new_callable=AsyncMock) as mock_parse,
            patch("app.ai.providers.ai_manager") as mock_ai,
            patch("app.db.repos.embeddings.vector_search", new_callable=AsyncMock) as mock_vs,
        ):
            mock_parse.return_value = {
                "semantic_text": "Python developer",
                "required_skills": [],
                "min_years_per_skill": {},
                "availability": [],
                "location": None,
            }
            mock_ai.embed_single = AsyncMock(return_value=[0.1] * 1024)
            mock_vs.return_value = []

            result = await run_semantic_search(mock_session, "Find a Python dev")

        assert result["results"] == []
        assert result["total_candidates_retrieved"] == 0

    async def test_returns_ranked_results(self, mock_session):
        from app.ai.pipelines.search import run_semantic_search

        emp_id = str(uuid.uuid4())
        emp = make_employee_model()
        emp.id = uuid.UUID(emp_id)
        emp.skills = []

        with (
            patch("app.ai.pipelines.search._parse_query", new_callable=AsyncMock) as mock_parse,
            patch("app.ai.providers.ai_manager") as mock_ai,
            patch("app.db.repos.embeddings.vector_search", new_callable=AsyncMock) as mock_vs,
            patch("app.db.repos.embeddings.load_employee_for_rerank", new_callable=AsyncMock) as mock_load,
            patch("app.db.repos.embeddings.render_profile_summary") as mock_summary,
            patch("app.ai.pipelines.search._rerank_candidates", new_callable=AsyncMock) as mock_rerank,
        ):
            mock_parse.return_value = {
                "semantic_text": "Python dev",
                "required_skills": [],
                "min_years_per_skill": {},
                "availability": [],
                "location": None,
            }
            mock_ai.embed_single = AsyncMock(return_value=[0.1] * 1024)
            mock_vs.return_value = [
                {"employee_id": emp_id, "name": "Alice", "similarity": 0.9, "title": "Engineer", "location": "NYC", "availability": "available", "total_years_exp": 5.0}
            ]
            mock_load.return_value = emp
            mock_summary.return_value = "Alice is a Python developer."
            mock_rerank.return_value = [
                {
                    "employee_id": emp_id,
                    "name": "Alice",
                    "title": "Engineer",
                    "location": "NYC",
                    "availability": "available",
                    "total_years_exp": 5.0,
                    "match_score": 88,
                    "reasoning": "Strong Python background",
                    "strengths": ["Python"],
                    "gaps": [],
                    "similarity": 0.9,
                    "top_skills_raw": [],
                }
            ]

            result = await run_semantic_search(mock_session, "Python dev", limit=8)

        assert result["total_candidates_retrieved"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["match_score"] == 88

    async def test_parsed_query_included_in_result(self, mock_session):
        from app.ai.pipelines.search import run_semantic_search

        with (
            patch("app.ai.pipelines.search._parse_query", new_callable=AsyncMock) as mock_parse,
            patch("app.ai.providers.ai_manager") as mock_ai,
            patch("app.db.repos.embeddings.vector_search", new_callable=AsyncMock) as mock_vs,
        ):
            mock_parse.return_value = {
                "semantic_text": "backend engineer",
                "required_skills": ["Python"],
                "min_years_per_skill": {"Python": 3},
                "availability": ["available"],
                "location": "NYC",
            }
            mock_ai.embed_single = AsyncMock(return_value=[0.1] * 1024)
            mock_vs.return_value = []

            result = await run_semantic_search(mock_session, "backend engineer in NYC")

        assert result["parsed_query"]["semantic_text"] == "backend engineer"
        assert "Python" in result["parsed_query"]["required_skills"]


# ─── embed_employee ───────────────────────────────────────────────────────────


class TestEmbedEmployee:
    async def test_embeds_and_stores_vector(self, mock_session):
        from app.ai.pipelines.search import embed_employee

        emp = make_employee_model()
        emp.skills = []

        mock_session.execute.return_value = make_result(scalar=emp)

        with (
            patch("app.ai.providers.ai_manager") as mock_ai,
            patch("app.db.repos.embeddings.render_profile_summary") as mock_summary,
            patch("app.db.repos.embeddings.upsert_employee_embedding", new_callable=AsyncMock) as mock_upsert,
        ):
            mock_summary.return_value = "Alice is a Python developer with 5 years experience."
            mock_ai.embed_single = AsyncMock(return_value=[0.1] * 1024)

            await embed_employee(mock_session, emp.id)

        mock_ai.embed_single.assert_called_once()
        mock_upsert.assert_called_once()

    async def test_skips_if_employee_not_found(self, mock_session):
        from app.ai.pipelines.search import embed_employee

        mock_session.execute.return_value = make_result(scalar=None)

        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.embed_single = AsyncMock(return_value=[0.1] * 1024)
            await embed_employee(mock_session, uuid.uuid4())

        mock_ai.embed_single.assert_not_called()

    async def test_skips_if_summary_is_empty(self, mock_session):
        from app.ai.pipelines.search import embed_employee

        emp = make_employee_model()
        emp.skills = []

        mock_session.execute.return_value = make_result(scalar=emp)

        with (
            patch("app.ai.providers.ai_manager") as mock_ai,
            patch("app.db.repos.embeddings.render_profile_summary") as mock_summary,
            patch("app.db.repos.embeddings.upsert_employee_embedding", new_callable=AsyncMock) as mock_upsert,
        ):
            mock_summary.return_value = "   "
            mock_ai.embed_single = AsyncMock(return_value=[0.1] * 1024)

            await embed_employee(mock_session, emp.id)

        mock_ai.embed_single.assert_not_called()
        mock_upsert.assert_not_called()
