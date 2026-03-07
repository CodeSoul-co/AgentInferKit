from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """A single chat message used across the platform."""
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class GenerateResult:
    """Result returned by every model adapter's generate() call."""
    content: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None
