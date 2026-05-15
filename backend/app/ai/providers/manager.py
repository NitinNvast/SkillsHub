"""Central AI manager.

Public surface:
    ai_manager.chat(task="extraction", request=ChatRequest(...))
    ai_manager.embed(["..."], input_type="document")
    ai_manager.health()  -> {provider_name: bool}

Responsibilities:
  - Resolve `task` to a (provider, model) pair using Settings overrides
  - Retry transient failures with exponential backoff (tenacity)
  - Fall back to the secondary provider if the primary fails after retries
  - Emit structured logs with timing + token usage
  - Cache provider instances via ProviderRegistry

Task names: "extraction", "inference", "parsing", "rerank", "general".
Unknown task names fall back to the LLM_PROVIDER/LLM_MODEL defaults.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Literal

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.ai.logging import get_ai_logger
from app.core.config import Settings
from app.core.config import settings as global_settings

from .base import (
    ChatRequest,
    ChatResponse,
    ProviderError,
    ProviderInvocationError,
    ProviderUnavailableError,
    RateLimitError,
)
from .factory import ProviderRegistry

log = get_ai_logger("skillshub.ai.manager")


# ─── Task → (provider, model) resolution ─────────────────────────────────────

TaskName = Literal["extraction", "inference", "parsing", "rerank", "general"]


@dataclass(frozen=True)
class Route:
    provider: str
    model: str


def _resolve_route(task: str, settings: Settings) -> Route:
    """Resolve the configured (provider, model) for a task."""
    overrides: dict[str, tuple[str | None, str | None]] = {
        "extraction": (settings.extraction_provider, settings.extraction_model),
        "rerank": (settings.rerank_provider, settings.rerank_model),
        "inference": (
            settings.inference_provider,
            settings.inference_model or settings.light_model,
        ),
        "parsing": (settings.parsing_provider, settings.parsing_model or settings.light_model),
    }
    provider_override, model_override = overrides.get(task, (None, None))
    return Route(
        provider=(provider_override or settings.llm_provider).lower(),
        model=model_override or settings.llm_model,
    )


def _fallback_route(settings: Settings) -> Route | None:
    if not settings.fallback_llm_provider:
        return None
    return Route(
        provider=settings.fallback_llm_provider.lower(),
        model=settings.fallback_llm_model or settings.llm_model,
    )


# ─── Manager ─────────────────────────────────────────────────────────────────


class AIManager:
    """Provider-agnostic façade for chat and embeddings."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or global_settings
        self._registry = ProviderRegistry(self._settings)

    # ─── Chat ─────────────────────────────────────────────────────────

    async def chat(
        self,
        request: ChatRequest,
        *,
        task: str = "general",
    ) -> ChatResponse:
        """Route a chat request through the configured provider for `task`.

        On primary-provider failure (after retries), retries once on the
        fallback provider if FALLBACK_LLM_PROVIDER is set.
        """
        primary = _resolve_route(task, self._settings)
        fallback = _fallback_route(self._settings)

        try:
            return await self._chat_with_retries(primary, request, task=task)
        except ProviderError as primary_err:
            if fallback is None or fallback.provider == primary.provider:
                raise
            log.warning(
                "ai.chat.fallback",
                task=task,
                primary=primary.provider,
                fallback=fallback.provider,
                error=str(primary_err),
            )
            return await self._chat_with_retries(fallback, request, task=task)

    async def _chat_with_retries(
        self,
        route: Route,
        request: ChatRequest,
        *,
        task: str,
    ) -> ChatResponse:
        provider = self._registry.chat(route.provider)
        attempts = max(1, self._settings.ai_max_retries)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=2, min=15, max=45),
            retry=retry_if_exception_type(RateLimitError),
            reraise=True,
        ):
            with attempt:
                start = time.perf_counter()
                resp = await provider.chat(request, route.model)
                duration_ms = int((time.perf_counter() - start) * 1000)
                log.info(
                    "ai.chat",
                    task=task,
                    provider=resp.provider,
                    model=resp.model,
                    input_tokens=resp.usage.input_tokens,
                    output_tokens=resp.usage.output_tokens,
                    cache_read=resp.usage.cache_read_tokens,
                    duration_ms=duration_ms,
                    tool_calls=len(resp.tool_calls),
                )
                return resp
        raise ProviderInvocationError("unreachable")  # pragma: no cover

    # ─── Embeddings ───────────────────────────────────────────────────

    async def embed(
        self,
        texts: list[str],
        *,
        input_type: Literal["document", "query"] = "document",
    ) -> list[list[float]]:
        provider = self._registry.embedding(self._settings.embedding_provider)
        model = self._settings.embedding_model

        attempts = max(1, self._settings.ai_max_retries)
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=2, min=20, max=60),
            retry=retry_if_exception_type(RateLimitError),
            reraise=True,
        ):
            with attempt:
                start = time.perf_counter()
                vectors = await provider.embed(texts, model=model, input_type=input_type)
                duration_ms = int((time.perf_counter() - start) * 1000)
                log.info(
                    "ai.embed",
                    provider=provider.name,
                    model=model,
                    n_texts=len(texts),
                    input_type=input_type,
                    duration_ms=duration_ms,
                )
                return vectors
        raise ProviderInvocationError("unreachable")  # pragma: no cover

    async def embed_single(
        self,
        text: str,
        *,
        input_type: Literal["document", "query"] = "document",
    ) -> list[float]:
        vectors = await self.embed([text], input_type=input_type)
        return vectors[0]

    # ─── Health ───────────────────────────────────────────────────────

    async def health(self) -> dict[str, bool]:
        """Best-effort health check for every configured route.

        Reports provider-availability only (i.e. whether the provider could
        be constructed with the credentials provided). A live ping per provider
        would multiply demo cost; this is the cheap sane default.
        """
        routes = [
            _resolve_route("extraction", self._settings),
            _resolve_route("inference", self._settings),
            _resolve_route("parsing", self._settings),
            _resolve_route("rerank", self._settings),
            _resolve_route("general", self._settings),
        ]
        fb = _fallback_route(self._settings)
        if fb:
            routes.append(fb)

        unique = {r.provider for r in routes}
        results: dict[str, bool] = {}

        async def _check(name: str) -> tuple[str, bool]:
            try:
                provider = self._registry.chat(name)
                ok = await provider.health()
                return name, bool(ok)
            except ProviderUnavailableError:
                return name, False
            except Exception:
                return name, False

        for name, ok in await asyncio.gather(*(_check(n) for n in unique)):
            results[name] = ok

        # And the embedding provider:
        try:
            emb = self._registry.embedding(self._settings.embedding_provider)
            results[f"embedding:{emb.name}"] = await emb.health()
        except ProviderUnavailableError:
            results[f"embedding:{self._settings.embedding_provider}"] = False

        return results

    # ─── Introspection ────────────────────────────────────────────────

    def describe_routes(self) -> dict[str, dict[str, str]]:
        """Surface the current task → (provider, model) mapping for /health."""
        tasks = ["extraction", "inference", "parsing", "rerank", "general"]
        info = {t: _resolve_route(t, self._settings).__dict__ for t in tasks}
        info["embedding"] = {
            "provider": self._settings.embedding_provider,
            "model": self._settings.embedding_model,
        }
        fb = _fallback_route(self._settings)
        if fb:
            info["fallback"] = fb.__dict__
        return info


# ─── Module-level singleton ──────────────────────────────────────────────────

_manager_singleton: AIManager | None = None


def get_ai_manager() -> AIManager:
    global _manager_singleton
    if _manager_singleton is None:
        _manager_singleton = AIManager()
    return _manager_singleton
