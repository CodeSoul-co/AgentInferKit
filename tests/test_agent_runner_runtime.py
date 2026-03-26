"""Focused tests for AgentRunner runtime switching."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from runners.agent_runner import AgentRunner


class DummyAdapter:
    async def generate(self, messages, **kwargs):
        raise AssertionError("generate() should not be called in this test")


class DummyReactStrategy:
    def __init__(self, runtime_cfg):
        self._strategy_name = "react"
        self._runtime_cfg = runtime_cfg
        self.calls = []

    def get_model_overrides(self):
        return {}

    def run_react_loop(self, sample, model_config, tool_schemas, **kwargs):
        self.calls.append({
            "sample": sample,
            "model_config": model_config,
            "tool_schemas": tool_schemas,
            "kwargs": kwargs,
        })
        return {
            "raw_output": "done",
            "parsed_answer": "done",
            "reasoning_trace": [],
            "tool_trace": [],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0},
        }


def test_agent_runner_passes_stateful_runtime_options_into_react_strategy():
    strategy = DummyReactStrategy(
        {
            "tool_runtime": "stateful",
            "tool_backend": "sandbox",
            "tool_permissions": ["issue.create"],
        }
    )
    runner = AgentRunner(DummyAdapter(), strategy, model_config={"model": "test-model"})

    result = asyncio.run(runner.run_single({"sample_id": "s1", "task_type": "api_calling", "tool_index": []}))

    assert result["parsed_answer"] == "done"
    assert len(strategy.calls) == 1
    kwargs = strategy.calls[0]["kwargs"]
    assert kwargs["tool_runtime"] == "stateful"
    assert kwargs["tool_backend"] == "sandbox"
    assert kwargs["tool_permissions"] == {"issue.create"}
    assert kwargs["session_id"] == "s1"
    assert kwargs["stateful_runtime"] is not None
