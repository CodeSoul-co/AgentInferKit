"""Legacy modules for backwards compatibility.

These modules are kept for reference but are not actively maintained.
"""

from __future__ import annotations

from toolsim.legacy.executor import MockExecutor
from toolsim.legacy.tracer import CallTrace, ToolCallTracer

__all__ = [
    "MockExecutor",
    "CallTrace",
    "ToolCallTracer",
]
