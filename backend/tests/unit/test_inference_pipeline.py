"""Unit tests for app.ai.pipelines.inference."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.extraction import ExtractedSkill


def make_skill(name: str, proficiency: str = "expert", years: float = 3.0) -> ExtractedSkill:
    return ExtractedSkill(
        name=name,
        proficiency=proficiency,
        years=years,
        evidence=f"Used {name} extensively",
        confidence=0.95,
    )


# ─── _apply_proficiency_rule ─────────────────────────────────────────────────


class TestApplyProficiencyRule:
    def test_same_rule_returns_same_proficiency(self):
        from app.ai.pipelines.inference import _apply_proficiency_rule

        assert _apply_proficiency_rule("expert", "same") == "expert"
        assert _apply_proficiency_rule("intermediate", "same") == "intermediate"
        assert _apply_proficiency_rule("novice", "same") == "novice"

    def test_one_below_expert_gives_intermediate(self):
        from app.ai.pipelines.inference import _apply_proficiency_rule

        assert _apply_proficiency_rule("expert", "one_below") == "intermediate"

    def test_one_below_intermediate_gives_novice(self):
        from app.ai.pipelines.inference import _apply_proficiency_rule

        assert _apply_proficiency_rule("intermediate", "one_below") == "novice"

    def test_one_below_novice_stays_novice(self):
        from app.ai.pipelines.inference import _apply_proficiency_rule

        assert _apply_proficiency_rule("novice", "one_below") == "novice"

    def test_literal_novice_rule_returns_novice(self):
        from app.ai.pipelines.inference import _apply_proficiency_rule

        assert _apply_proficiency_rule("expert", "novice") == "novice"

    def test_literal_intermediate_rule_returns_intermediate(self):
        from app.ai.pipelines.inference import _apply_proficiency_rule

        assert _apply_proficiency_rule("expert", "intermediate") == "intermediate"

    def test_unknown_proficiency_in_one_below_defaults_to_novice(self):
        from app.ai.pipelines.inference import _apply_proficiency_rule

        # index not found → max(0, -1) = 0 → novice
        result = _apply_proficiency_rule("unknown_level", "one_below")
        assert result == "novice"


# ─── _deterministic_inferences ───────────────────────────────────────────────


class TestDeterministicInferences:
    def test_nextjs_implies_react(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("Next.js")]
        results = _deterministic_inferences(skills)

        names = [r["name"] for r in results]
        assert "React" in names

    def test_nextjs_implies_javascript(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("Next.js")]
        results = _deterministic_inferences(skills)

        names = [r["name"] for r in results]
        assert "JavaScript" in names

    def test_react_implies_javascript(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("React")]
        results = _deterministic_inferences(skills)

        names = [r["name"] for r in results]
        assert "JavaScript" in names

    def test_django_implies_python(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("Django")]
        results = _deterministic_inferences(skills)

        names = [r["name"] for r in results]
        assert "Python" in names

    def test_fastapi_implies_python(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("FastAPI")]
        results = _deterministic_inferences(skills)

        names = [r["name"] for r in results]
        assert "Python" in names

    def test_typescript_implies_javascript(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("TypeScript")]
        results = _deterministic_inferences(skills)

        names = [r["name"] for r in results]
        assert "JavaScript" in names

    def test_kubernetes_implies_docker_with_one_below_proficiency(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("Kubernetes", proficiency="expert")]
        results = _deterministic_inferences(skills)

        docker_result = next((r for r in results if r["name"] == "Docker"), None)
        assert docker_result is not None
        assert docker_result["proficiency"] == "intermediate"  # one_below expert

    def test_postgresql_implies_sql(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("PostgreSQL")]
        results = _deterministic_inferences(skills)

        names = [r["name"] for r in results]
        assert "SQL" in names

    def test_no_inference_when_skill_already_extracted(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        # If JavaScript is already in the extracted set, it should NOT be inferred
        skills = [make_skill("React"), make_skill("JavaScript")]
        results = _deterministic_inferences(skills)

        names = [r["name"] for r in results]
        assert names.count("JavaScript") == 0  # already extracted, not inferred

    def test_empty_input_returns_empty(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        assert _deterministic_inferences([]) == []

    def test_no_duplicate_inferences(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        # Both Next.js and React.js imply JavaScript — should only appear once
        skills = [make_skill("Next.js"), make_skill("React Native")]
        results = _deterministic_inferences(skills)

        js_count = sum(1 for r in results if r["name"] == "JavaScript")
        assert js_count <= 1

    def test_years_scaled_by_fraction(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("Kubernetes", years=4.0)]
        results = _deterministic_inferences(skills)

        docker_result = next((r for r in results if r["name"] == "Docker"), None)
        assert docker_result is not None
        # years_frac = 0.8 for kubernetes → docker rule
        assert docker_result["years"] == pytest.approx(3.2, abs=0.01)

    def test_confidence_is_set(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("Django")]
        results = _deterministic_inferences(skills)

        python_result = next((r for r in results if r["name"] == "Python"), None)
        assert python_result is not None
        assert python_result["confidence"] == pytest.approx(0.97, abs=0.001)

    def test_reasoning_mentions_trigger_skill(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("Django")]
        results = _deterministic_inferences(skills)

        python_result = next((r for r in results if r["name"] == "Python"), None)
        assert "Django" in python_result["reasoning"]

    def test_no_rules_for_unrecognized_skill(self):
        from app.ai.pipelines.inference import _deterministic_inferences

        skills = [make_skill("Cobol")]
        results = _deterministic_inferences(skills)

        assert results == []


# ─── run_inference ────────────────────────────────────────────────────────────


class TestRunInference:
    async def test_empty_skills_returns_empty(self):
        from app.ai.pipelines.inference import run_inference

        result = await run_inference([])
        assert result == []

    async def test_returns_deterministic_inferences(self):
        from app.ai.pipelines.inference import run_inference

        skills = [make_skill("Django")]

        with patch(
            "app.ai.pipelines.inference._llm_inferences", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = []
            result = await run_inference(skills)

        names = [r["name"] for r in result]
        assert "Python" in names

    async def test_merges_llm_inferences(self):
        from app.ai.pipelines.inference import run_inference

        skills = [make_skill("Django")]
        llm_extras = [
            {"name": "REST APIs", "proficiency": "expert", "years": 3.0, "confidence": 0.80}
        ]

        with patch(
            "app.ai.pipelines.inference._llm_inferences", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = llm_extras
            result = await run_inference(skills)

        names = [r["name"] for r in result]
        assert "REST APIs" in names
        assert "Python" in names

    async def test_llm_failure_falls_back_to_rules_only(self):
        from app.ai.pipelines.inference import run_inference

        skills = [make_skill("Django")]

        with patch(
            "app.ai.pipelines.inference._llm_inferences", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.side_effect = RuntimeError("LLM down")
            result = await run_inference(skills)

        # Should still return deterministic results
        names = [r["name"] for r in result]
        assert "Python" in names

    async def test_deduplication_keeps_highest_confidence(self):
        from app.ai.pipelines.inference import run_inference

        skills = [make_skill("FastAPI")]

        # LLM also infers Python but with lower confidence
        llm_extras = [
            {"name": "Python", "proficiency": "intermediate", "years": 2.0, "confidence": 0.50}
        ]

        with patch(
            "app.ai.pipelines.inference._llm_inferences", new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = llm_extras
            result = await run_inference(skills)

        python_results = [r for r in result if r["name"].lower() == "python"]
        assert len(python_results) == 1
        # Deterministic rule has confidence 0.97, LLM has 0.50 → keep 0.97
        assert python_results[0]["confidence"] == pytest.approx(0.97, abs=0.01)

    async def test_single_skill_skips_llm(self):
        """LLM inference requires at least 2 skills."""
        from app.ai.pipelines.inference import _llm_inferences

        skills = [make_skill("Python")]
        result = await _llm_inferences(skills, set())

        assert result == []
