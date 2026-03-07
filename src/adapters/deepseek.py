from typing import Optional

from src.adapters.openai_compat import OpenAICompatAdapter
from src.config import settings


class DeepSeekAdapter(OpenAICompatAdapter):
    """Adapter for the DeepSeek API (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-chat",
        system_prompt: str = "",
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 2048,
        seed: Optional[int] = None,
        request_timeout_s: int = 60,
    ) -> None:
        super().__init__(
            api_key=api_key or settings.deepseek_api_key,
            base_url=base_url or settings.deepseek_base_url,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            seed=seed,
            request_timeout_s=request_timeout_s,
        )
