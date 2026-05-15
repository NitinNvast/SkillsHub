"""DEPRECATED — thin shim over `app.ai.providers.ai_manager`.

Existing code (e.g. `app/seed/seed_employees.py`) imports embed_single /
embed_texts from here. New code should call `ai_manager.embed(...)` directly.
"""

from __future__ import annotations

from typing import Literal

from app.ai.providers import ai_manager


async def embed_texts(
    texts: list[str],
    input_type: Literal["document", "query"] = "document",
) -> list[list[float]]:
    """Embed a batch of texts. input_type: 'document' for indexing, 'query' for search."""
    return await ai_manager.embed(texts, input_type=input_type)


async def embed_single(
    text: str,
    input_type: Literal["document", "query"] = "document",
) -> list[float]:
    return await ai_manager.embed_single(text, input_type=input_type)
