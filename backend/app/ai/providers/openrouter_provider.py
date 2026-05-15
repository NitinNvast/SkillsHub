"""OpenRouter provider — OpenAI-compatible aggregator at openrouter.ai/api/v1.

Supports `model` strings in the form "<vendor>/<model>" (e.g. "anthropic/claude-3.5-sonnet").
"""

from __future__ import annotations

from .openai_provider import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"
    # Vision support depends on the routed model; treat conservatively.
    supports_vision = True

    def __init__(self, api_key: str | None, *, timeout: float = 60.0) -> None:
        super().__init__(
            api_key,
            timeout=timeout,
            # OpenRouter accepts these optional attribution headers.
            extra_headers={
                "HTTP-Referer": "https://skillshub.local",
                "X-Title": "SkillsHub",
            },
        )
