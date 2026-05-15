"""Groq provider — OpenAI-compatible API at api.groq.com/openai/v1."""

from __future__ import annotations

from .openai_provider import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    name = "groq"
    base_url = "https://api.groq.com/openai/v1"
    # Most Groq-hosted models are text-only.
    supports_vision = False
