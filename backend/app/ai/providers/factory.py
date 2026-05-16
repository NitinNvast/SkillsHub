"""Provider factory — builds concrete provider instances from Settings.

Only Groq (chat) and Voyage (embeddings) are supported.
Providers are constructed lazily (only when first requested).
"""

from __future__ import annotations

from app.core.config import Settings

from .base import (
    ChatProvider,
    EmbeddingProvider,
    ProviderUnavailableError,
)
from .groq_provider import GroqProvider
from .voyage_provider import VoyageEmbeddingProvider

# ─── Registries ──────────────────────────────────────────────────────────────


def _build_chat_provider(name: str, settings: Settings) -> ChatProvider:
    name_lc = name.lower()
    timeout = settings.ai_request_timeout

    if name_lc == "groq":
        return GroqProvider(settings.groq_api_key, timeout=timeout)

    raise ProviderUnavailableError(f"Unknown chat provider: {name!r}. Only 'groq' is supported.")


def _build_embedding_provider(name: str, settings: Settings) -> EmbeddingProvider:
    name_lc = name.lower()

    if name_lc == "voyage":
        return VoyageEmbeddingProvider(settings.voyage_api_key)

    raise ProviderUnavailableError(
        f"Unknown embedding provider: {name!r}. Only 'voyage' is supported."
    )


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
