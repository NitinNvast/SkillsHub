"""Google Gemini chat provider (generateContent REST API).

Uses the v1beta endpoint:
    POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent

Tool calling:
  - ToolSpec → tools[0].function_declarations[i]
  - tool_choice "any"  → toolConfig.function_calling_config.mode = "ANY"
  - tool_choice "auto" → mode = "AUTO"

JSON Schema notes — Gemini accepts a subset; we strip unsupported keys defensively
(additionalProperties, $schema, etc.) but pass through enums, types, required.
"""

from __future__ import annotations

from typing import Any

import httpx

from .base import (
    ChatProvider,
    ChatRequest,
    ChatResponse,
    ProviderInvocationError,
    ProviderUnavailableError,
    ToolCall,
    Usage,
)

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_SCHEMA_DROP_KEYS = {"$schema", "additionalProperties", "$id", "$ref"}


def _clean_schema(node: Any) -> Any:
    """Strip JSON Schema keys Gemini's parameters validator rejects."""
    if isinstance(node, dict):
        return {k: _clean_schema(v) for k, v in node.items() if k not in _SCHEMA_DROP_KEYS}
    if isinstance(node, list):
        return [_clean_schema(v) for v in node]
    return node


class GeminiProvider(ChatProvider):
    name = "gemini"
    supports_vision = True

    def __init__(self, api_key: str | None, *, timeout: float = 60.0) -> None:
        if not api_key:
            raise ProviderUnavailableError("GEMINI_API_KEY is not set")
        self._api_key = api_key
        self._timeout = timeout

    # ─── Content translation ─────────────────────────────────────────────

    @staticmethod
    def _translate_content(content: Any) -> list[dict]:
        if isinstance(content, str):
            return [{"text": content}]
        if not isinstance(content, list):
            return [{"text": str(content)}]

        parts: list[dict] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append({"text": block.get("text", "")})
            elif btype == "image":
                src = block.get("source", {})
                if src.get("type") == "base64":
                    parts.append(
                        {
                            "inline_data": {
                                "mime_type": src.get("media_type", "image/png"),
                                "data": src.get("data", ""),
                            }
                        }
                    )
        return parts

    def _build_payload(self, request: ChatRequest) -> dict:
        contents: list[dict] = []
        for msg in request.messages:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(
                {"role": role, "parts": self._translate_content(msg.get("content", ""))}
            )

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        if request.system:
            payload["systemInstruction"] = {"parts": [{"text": request.system}]}

        if request.tools:
            payload["tools"] = [
                {
                    "function_declarations": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "parameters": _clean_schema(t.input_schema),
                        }
                        for t in request.tools
                    ]
                }
            ]
            if request.tool_choice in {"any", "auto"}:
                mode = "ANY" if request.tool_choice == "any" else "AUTO"
                payload["toolConfig"] = {"function_calling_config": {"mode": mode}}

        return payload

    # ─── Request ─────────────────────────────────────────────────────────

    async def chat(self, request: ChatRequest, model: str) -> ChatResponse:
        url = f"{_BASE_URL}/models/{model}:generateContent?key={self._api_key}"
        payload = self._build_payload(request)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload)
        except httpx.HTTPError as e:
            raise ProviderInvocationError(f"gemini: HTTP error {e}") from e

        if resp.status_code >= 400:
            raise ProviderInvocationError(f"gemini: HTTP {resp.status_code} — {resp.text[:300]}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ProviderInvocationError("gemini: invalid JSON response") from e

        return self._parse_response(data, model)

    # ─── Response ─────────────────────────────────────────────────────────

    def _parse_response(self, data: dict, model: str) -> ChatResponse:
        candidates = data.get("candidates") or []
        if not candidates:
            raise ProviderInvocationError("gemini: no candidates in response")

        candidate = candidates[0]
        content = candidate.get("content", {}) or {}
        parts = content.get("parts") or []

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for part in parts:
            if "text" in part:
                text_parts.append(part["text"])
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    ToolCall(
                        name=fc.get("name", ""),
                        arguments=fc.get("args", {}) or {},
                        id=None,
                    )
                )

        usage_obj = data.get("usageMetadata") or {}
        usage = Usage(
            input_tokens=usage_obj.get("promptTokenCount", 0) or 0,
            output_tokens=usage_obj.get("candidatesTokenCount", 0) or 0,
            cache_read_tokens=usage_obj.get("cachedContentTokenCount", 0) or 0,
        )

        return ChatResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
            model=model,
            provider=self.name,
            finish_reason=candidate.get("finishReason"),
            raw=data,
        )
