"""Anthropic client singleton with prompt caching enabled."""

import anthropic

from app.core.config import settings

# One client, reused across all AI calls. Prompt caching is per-request
# (set via cache_control on system blocks) — this client handles the transport.
_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client
