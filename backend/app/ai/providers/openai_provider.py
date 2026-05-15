"""OpenAI / OpenAI-compatible provider.

Implements the OpenAI Chat Completions schema, which is also served by Groq
(api.groq.com/openai/v1) and OpenRouter (openrouter.ai/api/v1). Subclasses
just override `base_url`, `name`, and any extra headers.

Tool calling translation:
  - ToolSpec → {"type": "function", "function": {name, description, parameters}}
  - tool_choice "any"  → "required"
  - tool_choice "auto" → "auto"
  - tool_choice "none" → "none"
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from .base import (
    ChatProvider,
    ChatRequest,
    ChatResponse,
    ProviderInvocationError,
    ProviderUnavailableError,
    RateLimitError,
    ToolCall,
    Usage,
)


class OpenAICompatibleProvider(ChatProvider):
    """Base class for any OpenAI-compatible REST endpoint."""

    name = "openai"
    base_url = "https://api.openai.com/v1"
    supports_vision = True

    def __init__(
        self,
        api_key: str | None,
        *,
        base_url: str | None = None,
        timeout: float = 60.0,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        if not api_key:
            raise ProviderUnavailableError(f"{self.name}: API key is not set")
        self._api_key = api_key
        self._base_url = (base_url or self.base_url).rstrip("/")
        self._timeout = timeout
        self._extra_headers = extra_headers or {}

    # ─── Schema translation ─────────────────────────────────────────────
    # OpenAI-compatible strict validators (notably Groq) reject `null` for
    # any field whose type is a single string. The portable fix is to expand
    # the type of every property NOT in its parent's `required` list to
    # ["<type>", "null"]. Anthropic also accepts this form, so the rewritten
    # schemas remain portable.

    @classmethod
    def _make_optional_fields_nullable(cls, node: Any) -> Any:
        if not isinstance(node, dict):
            return node

        out: dict[str, Any] = dict(node)

        if out.get("type") == "object" and isinstance(out.get("properties"), dict):
            required = set(out.get("required") or [])
            new_props: dict[str, Any] = {}
            for name, prop in out["properties"].items():
                clean = cls._make_optional_fields_nullable(prop)
                if (
                    name not in required
                    and isinstance(clean, dict)
                    and isinstance(clean.get("type"), str)
                    and clean["type"] != "null"
                ):
                    clean = {**clean, "type": [clean["type"], "null"]}
                new_props[name] = clean
            out["properties"] = new_props

        if isinstance(out.get("items"), dict):
            out["items"] = cls._make_optional_fields_nullable(out["items"])

        for combinator in ("anyOf", "oneOf", "allOf"):
            if isinstance(out.get(combinator), list):
                out[combinator] = [
                    cls._make_optional_fields_nullable(v) for v in out[combinator]
                ]

        return out

    # ─── Content translation ─────────────────────────────────────────────

    @staticmethod
    def _translate_content(content: Any) -> Any:
        """Anthropic-style content blocks → OpenAI content parts."""
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return content

        parts: list[dict] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append({"type": "text", "text": block.get("text", "")})
            elif btype == "image":
                src = block.get("source", {})
                if src.get("type") == "base64":
                    media = src.get("media_type", "image/png")
                    data = src.get("data", "")
                    parts.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media};base64,{data}"},
                        }
                    )
        return parts or content

    def _translate_messages(self, request: ChatRequest) -> list[dict]:
        out: list[dict] = []
        if request.system:
            out.append({"role": "system", "content": request.system})
        for msg in request.messages:
            out.append(
                {
                    "role": msg.get("role", "user"),
                    "content": self._translate_content(msg.get("content", "")),
                }
            )
        return out

    # ─── Request ─────────────────────────────────────────────────────────

    async def chat(self, request: ChatRequest, model: str) -> ChatResponse:
        payload: dict[str, Any] = {
            "model": model,
            "messages": self._translate_messages(request),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": self._make_optional_fields_nullable(t.input_schema),
                    },
                }
                for t in request.tools
            ]
            if request.tool_choice == "any":
                payload["tool_choice"] = "required"
            elif request.tool_choice == "auto":
                payload["tool_choice"] = "auto"
            elif request.tool_choice == "none":
                payload["tool_choice"] = "none"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            **self._extra_headers,
        }

        url = f"{self._base_url}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                http_resp = await client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as e:
            raise ProviderInvocationError(f"{self.name}: HTTP error {e}") from e

        if http_resp.status_code == 429:
            raise RateLimitError(
                f"{self.name}: rate limited — {http_resp.text[:200]}"
            )
        if http_resp.status_code >= 400:
            raise ProviderInvocationError(
                f"{self.name}: HTTP {http_resp.status_code} — {http_resp.text[:300]}"
            )

        try:
            data = http_resp.json()
        except ValueError as e:
            raise ProviderInvocationError(f"{self.name}: invalid JSON response") from e

        return self._parse_response(data, model)

    # ─── Response ─────────────────────────────────────────────────────────

    def _parse_response(self, data: dict, model: str) -> ChatResponse:
        choices = data.get("choices") or []
        if not choices:
            raise ProviderInvocationError(f"{self.name}: no choices in response")
        message = choices[0].get("message", {}) or {}

        text = message.get("content") or ""
        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls") or []:
            fn = tc.get("function", {}) or {}
            raw_args = fn.get("arguments", "{}")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(name=fn.get("name", ""), arguments=args, id=tc.get("id")))

        usage_obj = data.get("usage") or {}
        usage = Usage(
            input_tokens=usage_obj.get("prompt_tokens", 0) or 0,
            output_tokens=usage_obj.get("completion_tokens", 0) or 0,
            cache_read_tokens=(
                (usage_obj.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
            ),
        )

        return ChatResponse(
            text=text if isinstance(text, str) else "",
            tool_calls=tool_calls,
            usage=usage,
            model=model,
            provider=self.name,
            finish_reason=choices[0].get("finish_reason"),
            raw=data,
        )
