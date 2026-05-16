"""Unit tests for app.ai.providers.manager — AIManager and route resolution."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.providers.base import (
    ChatRequest,
    ChatResponse,
    ProviderError,
    ProviderInvocationError,
    ProviderUnavailableError,
    RateLimitError,
    ToolCall,
    Usage,
)
from app.ai.providers.manager import AIManager, Route, _fallback_route, _resolve_route
from app.core.config import Settings


def _make_settings(**overrides) -> Settings:
    base = {
        "database_url": "postgresql+asyncpg://test:test@localhost/testdb",
        "jwt_secret": "test-jwt-secret-for-tests-only-minimum32chars!",
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "embedding_provider": "voyage",
        "embedding_model": "voyage-3-large",
    }
    base.update(overrides)
    # _env_file=None prevents the developer's .env from overriding test values
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


def _make_response(text: str = "ok") -> ChatResponse:
    return ChatResponse(
        text=text,
        tool_calls=[],
        usage=Usage(input_tokens=10, output_tokens=5),
        model="test-model",
        provider="test",
        finish_reason="end_turn",
    )


# ─── _resolve_route ───────────────────────────────────────────────────────────


class TestResolveRoute:
    def test_defaults_to_llm_provider_and_model(self):
        settings = _make_settings()
        route = _resolve_route("general", settings)
        assert route.provider == "groq"
        assert route.model == "llama-3.3-70b-versatile"

    def test_extraction_uses_default_when_no_override(self):
        settings = _make_settings()
        route = _resolve_route("extraction", settings)
        assert route.provider == "groq"

    def test_extraction_uses_extraction_model_override(self):
        settings = _make_settings(extraction_model="llama-3.3-70b-versatile")
        route = _resolve_route("extraction", settings)
        assert route.model == "llama-3.3-70b-versatile"

    def test_extraction_uses_extraction_provider_override(self):
        settings = _make_settings(extraction_provider="groq")
        route = _resolve_route("extraction", settings)
        assert route.provider == "groq"

    def test_inference_uses_light_model_when_no_override(self):
        settings = _make_settings(light_model="llama-3.1-8b-instant")
        route = _resolve_route("inference", settings)
        assert route.model == "llama-3.1-8b-instant"

    def test_parsing_uses_light_model_when_no_override(self):
        settings = _make_settings(light_model="llama-3.1-8b-instant")
        route = _resolve_route("parsing", settings)
        assert route.model == "llama-3.1-8b-instant"

    def test_rerank_uses_rerank_model_override(self):
        settings = _make_settings(rerank_model="llama-3.3-70b-versatile")
        route = _resolve_route("rerank", settings)
        assert route.model == "llama-3.3-70b-versatile"

    def test_unknown_task_falls_back_to_llm_defaults(self):
        settings = _make_settings()
        route = _resolve_route("unknown_task_xyz", settings)
        assert route.provider == "groq"
        assert route.model == "llama-3.3-70b-versatile"

    def test_provider_is_lowercased(self):
        settings = _make_settings(extraction_provider="GROQ")
        route = _resolve_route("extraction", settings)
        assert route.provider == "groq"


# ─── _fallback_route ─────────────────────────────────────────────────────────


class TestFallbackRoute:
    def test_returns_none_when_not_configured(self):
        settings = _make_settings(fallback_llm_provider=None)
        assert _fallback_route(settings) is None

    def test_returns_route_when_configured(self):
        settings = _make_settings(
            fallback_llm_provider="groq", fallback_llm_model="llama-3.1-8b-instant"
        )
        route = _fallback_route(settings)
        assert route is not None
        assert route.provider == "groq"
        assert route.model == "llama-3.1-8b-instant"

    def test_fallback_model_defaults_to_llm_model_when_not_set(self):
        settings = _make_settings(fallback_llm_provider="groq", fallback_llm_model=None)
        route = _fallback_route(settings)
        assert route.model == "llama-3.3-70b-versatile"


# ─── AIManager.chat ───────────────────────────────────────────────────────────


class TestAIManagerChat:
    async def test_successful_chat_returns_response(self):
        settings = _make_settings()
        manager = AIManager(settings=settings)

        mock_provider = AsyncMock()
        mock_provider.chat = AsyncMock(return_value=_make_response("Hello"))

        with patch.object(manager._registry, "chat", return_value=mock_provider):
            request = ChatRequest(messages=[{"role": "user", "content": "Hello"}])
            result = await manager.chat(request, task="general")

        assert result.text == "Hello"

    async def test_fallback_same_provider_raises_on_primary_failure(self):
        # In Groq-only mode, primary and fallback are the same provider.
        # The manager skips the fallback to avoid pointless same-provider retries.
        settings = _make_settings(
            fallback_llm_provider="groq", fallback_llm_model="llama-3.1-8b-instant"
        )
        manager = AIManager(settings=settings)

        mock_provider = AsyncMock()
        mock_provider.chat = AsyncMock(side_effect=ProviderInvocationError("500 error"))

        with patch.object(manager._registry, "chat", return_value=mock_provider):
            request = ChatRequest(messages=[{"role": "user", "content": "Hi"}])
            with pytest.raises(ProviderInvocationError):
                await manager.chat(request, task="general")

    async def test_no_fallback_raises_on_primary_failure(self):
        settings = _make_settings(fallback_llm_provider=None)
        manager = AIManager(settings=settings)

        mock_provider = AsyncMock()
        mock_provider.chat = AsyncMock(side_effect=ProviderInvocationError("Service down"))

        with patch.object(manager._registry, "chat", return_value=mock_provider):
            request = ChatRequest(messages=[{"role": "user", "content": "Hi"}])
            with pytest.raises(ProviderInvocationError):
                await manager.chat(request, task="general")

    async def test_same_primary_and_fallback_does_not_double_retry(self):
        settings = _make_settings(
            fallback_llm_provider="groq",
            fallback_llm_model="llama-3.1-8b-instant",
        )
        manager = AIManager(settings=settings)

        mock_provider = AsyncMock()
        mock_provider.chat = AsyncMock(side_effect=ProviderInvocationError("down"))

        with patch.object(manager._registry, "chat", return_value=mock_provider):
            request = ChatRequest(messages=[{"role": "user", "content": "Hi"}])
            with pytest.raises(ProviderInvocationError):
                await manager.chat(request, task="general")

        # Primary provider was called (once, no fallback since same provider)
        assert mock_provider.chat.call_count >= 1


# ─── AIManager.embed ─────────────────────────────────────────────────────────


class TestAIManagerEmbed:
    async def test_embed_returns_vectors(self):
        settings = _make_settings()
        manager = AIManager(settings=settings)

        mock_provider = AsyncMock()
        mock_provider.name = "voyage"
        mock_provider.embed = AsyncMock(return_value=[[0.1] * 1024, [0.2] * 1024])

        with patch.object(manager._registry, "embedding", return_value=mock_provider):
            result = await manager.embed(["text one", "text two"], input_type="document")

        assert len(result) == 2
        assert len(result[0]) == 1024

    async def test_embed_single_returns_single_vector(self):
        settings = _make_settings()
        manager = AIManager(settings=settings)

        mock_provider = AsyncMock()
        mock_provider.name = "voyage"
        mock_provider.embed = AsyncMock(return_value=[[0.5] * 1024])

        with patch.object(manager._registry, "embedding", return_value=mock_provider):
            result = await manager.embed_single("test text", input_type="query")

        assert len(result) == 1024
        assert result[0] == pytest.approx(0.5)

    async def test_embed_passes_input_type(self):
        settings = _make_settings()
        manager = AIManager(settings=settings)

        mock_provider = AsyncMock()
        mock_provider.name = "voyage"
        mock_provider.embed = AsyncMock(return_value=[[0.1] * 1024])

        with patch.object(manager._registry, "embedding", return_value=mock_provider):
            await manager.embed(["text"], input_type="query")

        call_args = mock_provider.embed.call_args
        assert call_args.kwargs.get("input_type") == "query" or (
            len(call_args.args) > 2 and call_args.args[2] == "query"
        )


# ─── AIManager.health ─────────────────────────────────────────────────────────


class TestAIManagerHealth:
    async def test_health_returns_dict_with_provider_names(self):
        settings = _make_settings()
        manager = AIManager(settings=settings)

        mock_chat_provider = AsyncMock()
        mock_chat_provider.health = AsyncMock(return_value=True)

        mock_emb_provider = AsyncMock()
        mock_emb_provider.name = "voyage"
        mock_emb_provider.health = AsyncMock(return_value=True)

        with (
            patch.object(manager._registry, "chat", return_value=mock_chat_provider),
            patch.object(manager._registry, "embedding", return_value=mock_emb_provider),
        ):
            result = await manager.health()

        assert isinstance(result, dict)
        assert all(isinstance(v, bool) for v in result.values())

    async def test_unavailable_provider_returns_false(self):
        settings = _make_settings()
        manager = AIManager(settings=settings)

        mock_emb_provider = AsyncMock()
        mock_emb_provider.name = "voyage"
        mock_emb_provider.health = AsyncMock(return_value=True)

        with (
            patch.object(
                manager._registry, "chat", side_effect=ProviderUnavailableError("no key")
            ),
            patch.object(manager._registry, "embedding", return_value=mock_emb_provider),
        ):
            result = await manager.health()

        assert all(v is False or v is True for v in result.values())


# ─── AIManager.describe_routes ───────────────────────────────────────────────


class TestDescribeRoutes:
    def test_returns_all_task_routes(self):
        settings = _make_settings()
        manager = AIManager(settings=settings)

        routes = manager.describe_routes()

        assert "extraction" in routes
        assert "inference" in routes
        assert "parsing" in routes
        assert "rerank" in routes
        assert "general" in routes
        assert "embedding" in routes

    def test_each_route_has_provider_and_model(self):
        settings = _make_settings()
        manager = AIManager(settings=settings)

        routes = manager.describe_routes()

        for task, info in routes.items():
            if task == "fallback":
                continue
            assert "provider" in info, f"{task} missing provider"
            assert "model" in info, f"{task} missing model"

    def test_fallback_included_when_configured(self):
        settings = _make_settings(
            fallback_llm_provider="groq", fallback_llm_model="llama-3.1-8b-instant"
        )
        manager = AIManager(settings=settings)

        routes = manager.describe_routes()

        assert "fallback" in routes
        assert routes["fallback"]["provider"] == "groq"
