"""Voyage AI embedding provider (uses the official voyageai SDK)."""

from __future__ import annotations

from typing import Literal

import voyageai

from .base import (
    EmbeddingProvider,
    ProviderInvocationError,
    ProviderUnavailableError,
    RateLimitError,
)


class VoyageEmbeddingProvider(EmbeddingProvider):
    name = "voyage"

    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise ProviderUnavailableError("VOYAGE_API_KEY is not set")
        self._client = voyageai.AsyncClient(api_key=api_key)

    async def embed(
        self,
        texts: list[str],
        *,
        model: str,
        input_type: Literal["document", "query"] = "document",
    ) -> list[list[float]]:
        if not texts:
            return []
        try:
            result = await self._client.embed(texts, model=model, input_type=input_type)
        except voyageai.error.RateLimitError as e:
            raise RateLimitError(f"voyage: rate limited — {e}") from e
        except Exception as e:
            raise ProviderInvocationError(f"voyage: {e}") from e
        return result.embeddings
