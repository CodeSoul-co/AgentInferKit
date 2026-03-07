from typing import Any, List

from src.adapters.base import BaseModelAdapter
from src.api.schemas import GenerateResult, Message


class HuggingFaceAdapter(BaseModelAdapter):
    """Adapter for HuggingFace models. Skeleton for phase 2 implementation."""

    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError("HuggingFaceAdapter is not yet implemented (phase 2).")

    async def generate(
        self, messages: List[Message], **kwargs: Any
    ) -> GenerateResult:
        raise NotImplementedError("HuggingFaceAdapter.generate() is not yet implemented (phase 2).")
