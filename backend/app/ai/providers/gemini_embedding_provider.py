"""Google Gemini embeddings provider.

Uses the v1beta batchEmbedContents REST endpoint:
    POST /v1beta/models/{model}:batchEmbedContents?key=API_KEY
"""

from __future__ import annotations

from typing import Literal

import httpx

from .base import EmbeddingProvider, ProviderInvocationError, ProviderUnavailableError

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

_TASK_TYPE = {
    "document": "RETRIEVAL_DOCUMENT",
    "query": "RETRIEVAL_QUERY",
}


class GeminiEmbeddingProvider(EmbeddingProvider):
    name = "gemini"

    def __init__(self, api_key: str | None, *, timeout: float = 60.0) -> None:
        if not api_key:
            raise ProviderUnavailableError("GEMINI_API_KEY is not set")
        self._api_key = api_key
        self._timeout = timeout

    async def embed(
        self,
        texts: list[str],
        *,
        model: str,
        input_type: Literal["document", "query"] = "document",
    ) -> list[list[float]]:
        if not texts:
            return []

        task = _TASK_TYPE.get(input_type, "RETRIEVAL_DOCUMENT")
        url = f"{_BASE_URL}/models/{model}:batchEmbedContents?key={self._api_key}"
        payload = {
            "requests": [
                {
                    "model": f"models/{model}",
                    "content": {"parts": [{"text": t}]},
                    "taskType": task,
                }
                for t in texts
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
        except httpx.HTTPError as e:
            raise ProviderInvocationError(f"gemini-embeddings: {e}") from e

        if resp.status_code >= 400:
            raise ProviderInvocationError(
                f"gemini-embeddings: HTTP {resp.status_code} — {resp.text[:300]}"
            )

        data = resp.json()
        return [row.get("values", []) for row in data.get("embeddings", [])]
