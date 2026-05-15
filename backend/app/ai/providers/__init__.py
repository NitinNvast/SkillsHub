"""Provider-agnostic AI integration layer.

Public surface:
    from app.ai.providers import ai_manager, ChatRequest, ToolSpec

The manager routes tasks to the configured providers, handles retries, fallback,
and structured logging. Callers should never instantiate provider classes directly.
"""

from .base import (
    ChatProvider,
    ChatRequest,
    ChatResponse,
    EmbeddingProvider,
    ProviderError,
    ProviderInvocationError,
    ProviderUnavailableError,
    ToolCall,
    ToolSpec,
    Usage,
)
from .manager import AIManager, get_ai_manager

# Module-level singleton — created lazily on first access.
ai_manager: AIManager = get_ai_manager()

__all__ = [
    "AIManager",
    "ChatProvider",
    "ChatRequest",
    "ChatResponse",
    "EmbeddingProvider",
    "ProviderError",
    "ProviderInvocationError",
    "ProviderUnavailableError",
    "ToolCall",
    "ToolSpec",
    "Usage",
    "ai_manager",
    "get_ai_manager",
]
