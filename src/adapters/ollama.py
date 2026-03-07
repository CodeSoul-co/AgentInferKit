from typing import Any, List

from src.adapters.base import BaseModelAdapter
from src.api.schemas import GenerateResult, Message


class OllamaAdapter(BaseModelAdapter):
    """Adapter for Ollama local models. Skeleton for phase 2 implementation."""

    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError("OllamaAdapter is not yet implemented (phase 2).")

    async def generate(
        self, messages: List[Message], **kwargs: Any
    ) -> GenerateResult:
        raise NotImplementedError("OllamaAdapter.generate() is not yet implemented (phase 2).")
