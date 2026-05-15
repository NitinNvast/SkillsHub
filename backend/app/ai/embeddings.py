"""Voyage AI embedding client."""

from __future__ import annotations

import voyageai

from app.core.config import settings

_client: voyageai.AsyncClient | None = None


def get_embed_client() -> voyageai.AsyncClient:
    global _client
    if _client is None:
        _client = voyageai.AsyncClient(api_key=settings.voyage_api_key)
    return _client


async def embed_texts(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """Embed a batch of texts. input_type: 'document' for indexing, 'query' for search."""
    client = get_embed_client()
    result = await client.embed(texts, model=settings.embedding_model, input_type=input_type)
    return result.embeddings


async def embed_single(text: str, input_type: str = "document") -> list[float]:
    vecs = await embed_texts([text], input_type=input_type)
    return vecs[0]
