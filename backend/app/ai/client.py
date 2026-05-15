"""DEPRECATED — kept only for backward compatibility.

New code MUST use `app.ai.providers.ai_manager` instead. This shim forwards
to the provider registry so any external script that still imports
`get_client()` keeps working, but the result is the underlying anthropic
SDK client (only available when LLM_PROVIDER=anthropic).
"""

from __future__ import annotations

import warnings

import anthropic

from app.ai.providers import ai_manager
from app.ai.providers.anthropic_provider import AnthropicProvider


def get_client() -> anthropic.AsyncAnthropic:
    """Return the underlying Anthropic SDK client.

    Deprecated. Prefer `app.ai.providers.ai_manager.chat(...)` which is
    provider-agnostic.
    """
    warnings.warn(
        "app.ai.client.get_client() is deprecated — use app.ai.providers.ai_manager",
        DeprecationWarning,
        stacklevel=2,
    )
    provider = ai_manager._registry.chat("anthropic")  # noqa: SLF001
    if not isinstance(provider, AnthropicProvider):
        raise RuntimeError("get_client() requires the Anthropic provider to be configured")
    return provider._client  # noqa: SLF001
