from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.api.schemas import Message


class BaseStrategy(ABC):
    """Abstract base class for all inference strategies."""

    @abstractmethod
    def build_prompt(self, sample: Dict[str, Any]) -> List[Message]:
        """Build the prompt messages for a given sample.

        Args:
            sample: A dict representing one data sample (see SCHEMA.md).

        Returns:
            A list of Message objects to send to the model adapter.
        """
        ...

    @abstractmethod
    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the model's raw output into a structured result.

        Args:
            raw_output: The raw text output from the model.
            sample: The original sample dict for context.

        Returns:
            A dict with at least:
                - "parsed_answer": str
                - "reasoning_trace": str | None
        """
        ...
