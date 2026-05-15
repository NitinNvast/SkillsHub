"""Provider factory — builds concrete provider instances from Settings.

Providers are constructed lazily (only when first requested) so an .env that
only configures Anthropic doesn't fail trying to read OPENAI_API_KEY.
"""

from __future__ import annotations

from app.core.config import Settings

from .anthropic_provider import AnthropicProvider
from .base import (
    ChatProvider,
    EmbeddingProvider,
    ProviderUnavailableError,
)
from .gemini_embedding_provider import GeminiEmbeddingProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .openai_embedding_provider import OpenAIEmbeddingProvider
from .openai_provider import OpenAICompatibleProvider
from .openrouter_provider import OpenRouterProvider
from .voyage_provider import VoyageEmbeddingProvider

# ─── Registries ──────────────────────────────────────────────────────────────


def _build_chat_provider(name: str, settings: Settings) -> ChatProvider:
    name_lc = name.lower()
    timeout = settings.ai_request_timeout

    if name_lc == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key, timeout=timeout)
    if name_lc == "openai":
        return OpenAICompatibleProvider(settings.openai_api_key, timeout=timeout)
    if name_lc == "groq":
        return GroqProvider(settings.groq_api_key, timeout=timeout)
    if name_lc == "gemini":
        return GeminiProvider(settings.gemini_api_key, timeout=timeout)
    if name_lc == "openrouter":
        return OpenRouterProvider(settings.openrouter_api_key, timeout=timeout)

    raise ProviderUnavailableError(f"Unknown chat provider: {name!r}")


def _build_embedding_provider(name: str, settings: Settings) -> EmbeddingProvider:
    name_lc = name.lower()
    timeout = settings.ai_request_timeout

    if name_lc == "voyage":
        return VoyageEmbeddingProvider(settings.voyage_api_key)
    if name_lc == "openai":
        return OpenAIEmbeddingProvider(settings.openai_api_key, timeout=timeout)
    if name_lc == "gemini":
        return GeminiEmbeddingProvider(settings.gemini_api_key, timeout=timeout)

    raise ProviderUnavailableError(f"Unknown embedding provider: {name!r}")


# ─── Cache ───────────────────────────────────────────────────────────────────


class ProviderRegistry:
    """Lazy, per-process cache of constructed providers."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._chat: dict[str, ChatProvider] = {}
        self._embed: dict[str, EmbeddingProvider] = {}

    def chat(self, name: str) -> ChatProvider:
        key = name.lower()
        if key not in self._chat:
            self._chat[key] = _build_chat_provider(key, self._settings)
        return self._chat[key]

    def embedding(self, name: str) -> EmbeddingProvider:
        key = name.lower()
        if key not in self._embed:
            self._embed[key] = _build_embedding_provider(key, self._settings)
        return self._embed[key]
