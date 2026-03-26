"""Focused tests for experiment-level stateful runtime configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api.schemas import RunnerConfig
from runners.agent_runner import AgentRunner


class DummyAdapter:
    async def generate(self, messages, **kwargs):
        raise AssertionError("generate() should not be called in this test")


class DummyStrategy:
    def __init__(self):
        self._strategy_name = "react"
        self._runtime_cfg = {}
        self.calls = []

    def get_model_overrides(self):
        return {}

    def run_react_loop(self, sample, model_config, tool_schemas, **kwargs):
        self.calls.append(kwargs)
        return {
            "raw_output": "ok",
            "parsed_answer": "ok",
            "reasoning_trace": [],
            "tool_trace": [],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0},
        }


def test_runner_config_accepts_stateful_runtime_fields():
    cfg = RunnerConfig(tool_runtime="stateful", tool_backend="sandbox", tool_permissions=["issue.create"])

    assert cfg.tool_runtime == "stateful"
    assert cfg.tool_backend == "sandbox"
    assert cfg.tool_permissions == ["issue.create"]


def test_agent_runner_prefers_runner_config_for_stateful_runtime():
    import asyncio

    strategy = DummyStrategy()
    runner = AgentRunner(
        DummyAdapter(),
        strategy,
        model_config={"model": "test-model"},
        runner_config={
            "tool_runtime": "stateful",
            "tool_backend": "sandbox",
            "tool_permissions": ["issue.create", "issue.assign"],
        },
    )

    result = asyncio.run(runner.run_single({"sample_id": "exp_s1", "task_type": "api_calling", "tool_index": []}))

    assert result["parsed_answer"] == "ok"
    kwargs = strategy.calls[0]
    assert kwargs["tool_runtime"] == "stateful"
    assert kwargs["tool_backend"] == "sandbox"
    assert kwargs["tool_permissions"] == {"issue.create", "issue.assign"}
