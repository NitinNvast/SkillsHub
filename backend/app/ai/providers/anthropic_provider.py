"""Anthropic Messages API provider.

Wraps `anthropic.AsyncAnthropic` and:
  - Preserves prompt caching via `cache_control=ephemeral` on the system block
  - Forces tool_use (`tool_choice={"type": "any"}`) when callers request it
  - Normalizes content blocks back into our canonical `ChatResponse`
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

from .base import (
    ChatProvider,
    ChatRequest,
    ChatResponse,
    ProviderInvocationError,
    ProviderUnavailableError,
    ToolCall,
    Usage,
)


class AnthropicProvider(ChatProvider):
    name = "anthropic"
    supports_prompt_caching = True
    supports_vision = True

    def __init__(self, api_key: str | None, *, timeout: float = 60.0) -> None:
        if not api_key:
            raise ProviderUnavailableError("ANTHROPIC_API_KEY is not set")
        self._client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout)

    async def chat(self, request: ChatRequest, model: str) -> ChatResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": request.max_tokens,
            "messages": request.messages,
            "temperature": request.temperature,
        }

        if request.system:
            if request.cache_system_prompt:
                kwargs["system"] = [
                    {
                        "type": "text",
                        "text": request.system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                kwargs["system"] = request.system

        if request.tools:
            kwargs["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema,
                }
                for t in request.tools
            ]
            if request.tool_choice == "any":
                kwargs["tool_choice"] = {"type": "any"}
            elif request.tool_choice == "auto":
                kwargs["tool_choice"] = {"type": "auto"}

        try:
            resp = await self._client.messages.create(**kwargs)
        except anthropic.AnthropicError as e:
            raise ProviderInvocationError(f"anthropic: {e}") from e

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in resp.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(block.text)
            elif btype == "tool_use":
                args = block.input
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool_calls.append(ToolCall(name=block.name, arguments=args or {}, id=block.id))

        usage = Usage(
            input_tokens=getattr(resp.usage, "input_tokens", 0) or 0,
            output_tokens=getattr(resp.usage, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
        )

        return ChatResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
            model=model,
            provider=self.name,
            finish_reason=getattr(resp, "stop_reason", None),
            raw=resp,
        )
