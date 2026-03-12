import time
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from src.adapters.base import BaseModelAdapter
from src.api.schemas import GenerateResult, Message


class OpenAICompatAdapter(BaseModelAdapter):
    """Adapter for any OpenAI-compatible API (DeepSeek, OpenAI, Qwen, etc.).

    Args:
        api_key: API key for authentication.
        base_url: Base URL of the API endpoint.
        model: Model identifier string.
        system_prompt: Optional default system prompt.
        temperature: Sampling temperature.
        top_p: Nucleus sampling parameter.
        max_tokens: Maximum tokens to generate.
        seed: Random seed for reproducibility.
        request_timeout_s: Request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 2048,
        seed: Optional[int] = None,
        request_timeout_s: int = 60,
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=request_timeout_s,
        )
        self._model = model
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens
        self._seed = seed

    def _build_messages(
        self, messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """Convert Message objects to OpenAI-format dicts, prepending system prompt if set.

        When a message carries an ``image_url``, the content is formatted as a
        list of content parts (text + image_url) following the OpenAI Vision API
        spec, which is also supported by Qwen VL via DashScope compatible mode.
        """
        api_messages: List[Dict[str, Any]] = []
        if self._system_prompt:
            has_system = any(m.role == "system" for m in messages)
            if not has_system:
                api_messages.append(
                    {"role": "system", "content": self._system_prompt}
                )
        for m in messages:
            if m.image_url:
                content_parts = [
                    {"type": "image_url", "image_url": {"url": m.image_url}},
                    {"type": "text", "text": m.content},
                ]
                api_messages.append({"role": m.role, "content": content_parts})
            else:
                api_messages.append({"role": m.role, "content": m.content})
        return api_messages

    async def generate(
        self, messages: List[Message], **kwargs: Any
    ) -> GenerateResult:
        """Call the OpenAI-compatible chat completions endpoint."""
        start = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=self._build_messages(messages),
                temperature=kwargs.get("temperature", self._temperature),
                top_p=kwargs.get("top_p", self._top_p),
                max_tokens=kwargs.get("max_tokens", self._max_tokens),
                seed=kwargs.get("seed", self._seed),
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            choice = response.choices[0]
            usage = response.usage
            return GenerateResult(
                content=choice.message.content or "",
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
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
