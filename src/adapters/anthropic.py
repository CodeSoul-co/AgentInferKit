import time
from typing import Any, Dict, List, Optional

import anthropic

from src.adapters.base import BaseModelAdapter
from src.api.schemas import GenerateResult, Message
from src.config import settings


class AnthropicAdapter(BaseModelAdapter):
    """Adapter for the Anthropic (Claude) API.

    Anthropic uses a different API format from OpenAI, so this adapter
    has its own implementation rather than inheriting OpenAICompatAdapter.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        system_prompt: str = "",
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 2048,
        request_timeout_s: int = 60,
    ) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.anthropic_api_key,
            timeout=request_timeout_s,
        )
        self._model = model
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens

    def _build_messages(
        self, messages: List[Message]
    ) -> tuple:
        """Separate system prompt and conversation messages for Anthropic API.

        Returns:
            A tuple of (system_text, api_messages).
        """
        system_text = self._system_prompt
        api_messages: List[Dict[str, str]] = []
        for m in messages:
            if m.role == "system":
                system_text = m.content
            else:
                api_messages.append({"role": m.role, "content": m.content})
        return system_text, api_messages

    async def generate(
        self, messages: List[Message], **kwargs: Any
    ) -> GenerateResult:
        """Call the Anthropic messages endpoint."""
        start = time.perf_counter()
        try:
            system_text, api_messages = self._build_messages(messages)
            create_kwargs: Dict[str, Any] = {
                "model": self._model,
                "messages": api_messages,
                "max_tokens": kwargs.get("max_tokens", self._max_tokens),
                "temperature": kwargs.get("temperature", self._temperature),
                "top_p": kwargs.get("top_p", self._top_p),
            }
            if system_text:
                create_kwargs["system"] = system_text

            response = await self._client.messages.create(**create_kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text

            return GenerateResult(
                content=content,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                latency_ms=elapsed_ms,
                error=None,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return GenerateResult(
                content="",
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=elapsed_ms,
                error=str(e),
            )
