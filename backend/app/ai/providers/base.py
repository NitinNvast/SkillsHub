"""Provider-neutral abstractions for chat and embeddings.

Every concrete provider (Anthropic, OpenAI, Groq, Gemini, OpenRouter, Voyage)
translates these canonical types into and out of its native API format.

Design notes:
  - `ToolSpec` uses raw JSON Schema for `input_schema`. JSON Schema is the
    common denominator across all four chat APIs we target.
  - `ChatRequest.messages` content uses Anthropic-style content blocks
    ({"type": "text", "text": ...} / {"type": "image", "source": {...}})
    as the canonical multimodal shape. Providers translate as needed.
  - `cache_system_prompt` is a hint, not a guarantee. Providers without
    native prompt caching simply ignore it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

# ─── Tool / function calling ─────────────────────────────────────────────────


@dataclass
class ToolSpec:
    """Provider-neutral tool/function definition.

    `input_schema` is a JSON Schema object describing the tool's arguments.
    Every chat API in use today accepts JSON Schema, so this is portable.
    """

    name: str
    description: str
    input_schema: dict


@dataclass
class ToolCall:
    """A tool invocation parsed from a provider response."""

    name: str
    arguments: dict
    id: str | None = None


# ─── Request / response ──────────────────────────────────────────────────────


@dataclass
class Usage:
    """Token accounting in canonical form."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ChatRequest:
    """A provider-agnostic chat request.

    `messages` follows the standard role/content shape. `content` may be either
    a plain string OR a list of canonical content blocks (text, image).
    """

    messages: list[dict]
    system: str | None = None
    tools: list[ToolSpec] | None = None
    tool_choice: Literal["any", "auto", "none"] | None = None
    max_tokens: int = 4096
    temperature: float = 0.0
    # Hint: provider should cache the system prompt where supported (Anthropic).
    cache_system_prompt: bool = False


@dataclass
class ChatResponse:
    """A normalized chat response. `raw` retains the provider-native object."""

    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    model: str = ""
    provider: str = ""
    finish_reason: str | None = None
    raw: Any = None

    def first_tool_call(self) -> ToolCall | None:
        return self.tool_calls[0] if self.tool_calls else None


# ─── Errors ──────────────────────────────────────────────────────────────────


class ProviderError(Exception):
    """Base class for provider-side failures."""


class ProviderUnavailableError(ProviderError):
    """Provider is missing credentials or otherwise unhealthy."""


class ProviderInvocationError(ProviderError):
    """Provider returned an error or unparseable response."""


class RateLimitError(ProviderInvocationError):
    """Provider returned HTTP 429 — caller should retry with backoff."""


# ─── Abstract providers ──────────────────────────────────────────────────────


class ChatProvider(ABC):
    """Synchronous interface for chat/completion providers."""

    name: str = "abstract"
    supports_tool_use: bool = True
    supports_prompt_caching: bool = False
    supports_vision: bool = False

    @abstractmethod
    async def chat(self, request: ChatRequest, model: str) -> ChatResponse:
        """Execute a chat request and return a normalized response."""

    async def health(self) -> bool:
        """Cheap liveness check. Default: configuration-only (has API key)."""
        return True


class EmbeddingProvider(ABC):
    """Embedding generation interface."""

    name: str = "abstract"

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        *,
        model: str,
        input_type: Literal["document", "query"] = "document",
    ) -> list[list[float]]:
        """Embed a batch of texts. input_type hints query vs. corpus encoding."""

    async def health(self) -> bool:
        return True
