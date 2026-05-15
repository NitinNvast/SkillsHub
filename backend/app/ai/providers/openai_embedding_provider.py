"""OpenAI embeddings provider (also covers Azure-style OpenAI deployments).

POST {base_url}/embeddings with {"model": ..., "input": [...]}.
"""

from __future__ import annotations

from typing import Literal

import httpx

from .base import EmbeddingProvider, ProviderInvocationError, ProviderUnavailableError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str | None,
        *,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise ProviderUnavailableError("OPENAI_API_KEY is not set")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def embed(
        self,
        texts: list[str],
        *,
        model: str,
        input_type: Literal["document", "query"] = "document",
    ) -> list[list[float]]:
        # OpenAI embeddings don't use input_type — kept for interface parity.
        if not texts:
            return []

        url = f"{self._base_url}/embeddings"
        payload = {"model": model, "input": texts}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as e:
            raise ProviderInvocationError(f"openai-embeddings: {e}") from e

        if resp.status_code >= 400:
            raise ProviderInvocationError(
                f"openai-embeddings: HTTP {resp.status_code} — {resp.text[:300]}"
            )

        data = resp.json()
        return [row["embedding"] for row in data.get("data", [])]
