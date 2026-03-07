import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from src.api.schemas import GenerateResult, Message


class BaseModelAdapter(ABC):
    """Abstract base class for all model adapters."""

    @abstractmethod
    async def generate(
        self, messages: List[Message], **kwargs: Any
    ) -> GenerateResult:
        """Send messages to the model and return a GenerateResult.

        Args:
            messages: List of Message objects forming the conversation.
            **kwargs: Additional provider-specific parameters.

        Returns:
            A GenerateResult with content, token counts, latency, and error.
        """
        ...

    async def batch_generate(
        self,
        messages_list: List[List[Message]],
        concurrency: int = 5,
        **kwargs: Any,
    ) -> List[GenerateResult]:
        """Run generate() on multiple message lists with bounded concurrency.

        Args:
            messages_list: A list where each element is a conversation (List[Message]).
            concurrency: Maximum number of concurrent requests.
            **kwargs: Passed through to generate().

        Returns:
            A list of GenerateResult in the same order as messages_list.
        """
        semaphore = asyncio.Semaphore(concurrency)
        results: List[GenerateResult] = [GenerateResult()] * len(messages_list)

        async def _run(index: int, messages: List[Message]) -> None:
            async with semaphore:
                results[index] = await self.generate(messages, **kwargs)

        tasks = [_run(i, msgs) for i, msgs in enumerate(messages_list)]
        await asyncio.gather(*tasks)
        return results
