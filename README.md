# AgentInferKit

**A Modular Platform for Agent Inference, Evaluation, and Training**

AgentInferKit is an open-source platform for building, running, and analyzing LLM/VLM/Agent systems across text, multimodal, RAG, and tool-use settings. It is designed for **agent inference** today, and built to extend toward **agent reasoning**, **agent training**, and **RL-based optimization** in the future.

---

## Overview

AgentInferKit follows a three-layer design:

- **Platform Layer**: unified model access, inference execution, tool simulation, batch evaluation, visualization, and engineering management
- **Data Layer**: dataset organization, preprocessing, standardization, versioning, and custom data loading
- **Experiment Layer**: benchmark protocols, controlled comparisons, and research-oriented analysis

At the current stage, the project mainly focuses on the **platform layer** and **data layer**.

---

## Features

- Unified access to **API models**, **local models**, and **multimodal models**
- Pluggable reasoning strategies: **Direct**, **CoT**, **Long-CoT**, **ToT**, **ReAct**, **Self-Refine**, **Self-Consistency**
- Built-in **RAG pipeline** with chunking, indexing, retrieval, and evidence tracking
- Stateful **tool simulation environment** with world state, registry, and side-effect replay
- Tool categories: file search, calendar, issue tracking — all with in-process sandbox execution
- Batch inference, single-sample debugging, logging, retry, and resume
- Configurable evaluation with metrics for text, retrieval, and agent tasks
- Experiment runners for stateful agent flows and stateless baselines
- Research-friendly visualization for predictions, traces, evidence, and errors
- Modular architecture for future extension to **training** and **RL**

---

## Current Scope

AgentInferKit currently targets the following task types:

- Text QA
- Knowledge-oriented text exam
- Image understanding
- API / function calling
- Retrieval-augmented reasoning
- Prompt-based reasoning strategy comparison
- Stateful tool-use agent evaluation

---

## Architecture

### Platform Layer
The engineering foundation of the project, including:

- model adapters
- reasoning strategies
- RAG pipeline
- task runners
- **tool simulation** (`toolsim/`)
  - `core/` — world state, environment, registry, constants, side effects
  - `execution/` — stateful executor and tracer
  - `tools/` — file, search, calendar, issue tools
  - `evaluators/` — call-level and state-level evaluators
  - `runners/` — experiment and comparison runners
  - `backends/` — mock and sandbox backends
  - `adapters/` — stateful runtime adapter
  - `legacy/` — legacy executor and tracer
- evaluators
- visualization dashboard
- config and logging system

### Data Layer
Standardizes heterogeneous data into reusable benchmark assets, including:

- QA data
- text-exam data
- image understanding data
- agent API function calling data

The data layer is designed to make data **runnable**, **evaluable**, **traceable**, and **versioned**.

---

## Quick Start

### 1. Environment Setup

```bash
# Clone the repo
git clone https://github.com/CodeSoul-co/AgentInferKit.git
cd AgentInferKit

# Create conda environment
conda create -n benchmark python=3.11 -y
conda activate benchmark
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and fill in your DEEPSEEK_API_KEY
```

### 2. Start API Server

```bash
PYTHONPATH=$(pwd) uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Open browser: http://localhost:8000/docs to see all API endpoints.

### 3. Chat with AI (Terminal)

**Direct mode** (fast, concise):
```bash
curl -s -X POST http://localhost:8000/chat/complete \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "deepseek-chat",
    "strategy": "direct",
    "messages": [{"role": "user", "content": "What is machine learning?"}]
  }' | python3 -m json.tool
```

**Chain-of-Thought mode** (step-by-step reasoning):
```bash
curl -s -X POST http://localhost:8000/chat/complete \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "deepseek-chat",
    "strategy": "cot",
    "messages": [{"role": "user", "content": "A train travels 120km in 2 hours. What is its speed?"}]
  }' | python3 -m json.tool
```

**Streaming mode** (token-by-token output):
```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "deepseek-chat",
    "strategy": "direct",
    "messages": [{"role": "user", "content": "Write a short poem about spring"}]
  }'
```

### 4. Run Tool Simulation Experiment

```bash
PYTHONPATH=$(pwd) python -m toolsim.runners.experiment_runner \
  --backend sandbox \
  --config configs/toolsim/demo_flow.yaml
```

### 5. Run Batch Experiment

```bash
PYTHONPATH=$(pwd) python scripts/run_experiment.py \
  --config configs/experiments/demo_exam_direct.yaml
```

Results are saved to `outputs/predictions/` and `outputs/metrics/`.

### 6. Demo Experiment Results

We ran 5 exam questions (math, physics, CS) with two strategies:

| Metric | Direct | CoT |
|--------|--------|-----|
| **Accuracy** | 80% (4/5) | **100% (5/5)** |
| **Avg Latency** | **2.2s** | 10.7s |
| **Avg Tokens** | **69.6** | 281.4 |

CoT reasoning improves accuracy at the cost of higher latency and token usage.

---

## Project Structure

```
AgentInferKit/
├── src/
│   ├── adapters/       # LLM provider adapters (DeepSeek, OpenAI, Anthropic, Qwen)
│   ├── strategies/     # Inference strategies (direct, cot, long_cot, tot, react, self_refine, self_consistency)
│   ├── rag/            # RAG pipeline (chunker, embedder, milvus_store, retriever, pipeline)
│   ├── runners/        # Task runners (qa, exam, batch, agent)
│   ├── evaluators/     # Metrics (text, choice, rag, efficiency)
│   ├── toolsim/        # Tool simulation environment
│   │   ├── core/       # World state, environment, registry, constants, side effects
│   │   ├── execution/  # Stateful executor and tracer
│   │   ├── tools/     # File, search, calendar, issue tools
│   │   ├── evaluators/ # Call-level and state-level evaluators
│   │   ├── runners/   # Experiment and comparison runners
│   │   ├── backends/   # Mock and sandbox backends
│   │   ├── adapters/   # Stateful runtime adapter
│   │   └── legacy/     # Legacy executor and tracer
│   ├── api/            # FastAPI routes (chat, datasets, results, system)
│   └── utils/          # Shared utilities
├── scripts/            # CLI scripts (run_experiment, build_chunks, build_index, build_mcq)
├── configs/           # YAML configs for models and experiments
├── data/               # Datasets and schemas
└── outputs/            # Experiment results (gitignored)
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat/complete` | POST | Single chat completion with strategy selection |
| `/chat/stream` | POST | Streaming chat completion (SSE) |
| `/datasets` | GET | List available datasets |
| `/datasets/upload` | POST | Upload a new dataset |
| `/results/{id}/metrics` | GET | Get experiment metrics |
| `/results/{id}/predictions` | GET | Get experiment predictions |
| `/results/compare` | POST | Compare multiple experiments |
| `/api/v1/system/health` | GET | Health check |

Full interactive docs at: `http://localhost:8000/docs`

---

## Tool Simulation (`toolsim`)

The `toolsim` module provides a fully in-process, deterministic simulation environment for tool-use agents. Each tool operates against an in-memory `WorldState` with simulated time, enabling reproducible experiments without external services.

| Component | Description |
|-----------|-------------|
| `WorldState` | In-memory entity store with time simulation |
| `Environment` | Tool registry, backend dispatch, execution context |
| `FileTools` | File snapshot and reindex with delayed search refresh |
| `SearchTools` | Entity-based search index (file, calendar, issue) |
| `CalendarTools` | CRUD for calendar events with status transitions |
| `IssueTools` | Issue lifecycle: create, assign, comment, close/reopen |
| `StatefulExecutor` | Executes tool calls with side-effect replay |
| `StatefulTracer` | Records full execution traces for evaluation |
| `SandboxBackend` | Sandboxed execution for untrusted tool code |

### Tool Evaluators

- **Call-level**: Success/failure counts, phase transitions, argument validation
- **State-level**: Entity existence, field values, indexed search hits, goal satisfaction

---

## Supported Models

| Provider | Model | Status |
|----------|-------|--------|
| DeepSeek | deepseek-chat | Verified |
| OpenAI | gpt-4o, gpt-4o-mini | Ready (needs API key) |
| Anthropic | claude-3.5-sonnet | Ready (needs API key) |
| Qwen | qwen-plus | Ready (needs API key) |

---

## Inference Strategies

| Strategy | Key | Description |
|----------|-----|-------------|
| Direct | `direct` | Simple prompt, fast response |
| Chain-of-Thought | `cot` | Step-by-step reasoning |
| Long CoT | `long_cot` | Extended multi-step reasoning |
| Tree-of-Thought | `tot` | Multiple reasoning paths + evaluation |
| ReAct | `react` | Reasoning + tool actions interleaved |
| Self-Refine | `self_refine` | Generate -> critique -> improve loop |
| Self-Consistency | `self_consistency` | Multiple paths + majority voting |

---

## Contributing

Contributions are welcome, especially in:

- model adapters
- task runners
- evaluators
- RAG pipelines
- tool simulation
- visualization
- data preprocessing
- documentation

---

## Code Review (dev)

This section tracks engineering quality issues and improvement opportunities found during review of the `toolsim` module. Items are labelled by severity.

---

### High Priority

**`execution/stateful_executor.py` — `ExecutionRecord.status` uses raw strings**
The `status` field on `ExecutionRecord` (line 50) is typed as `str` with values like `"failed"`, `"succeeded"` instead of the `ExecutionStatus` enum already defined in `core/constants.py`. Should be: `status: ExecutionStatus = ExecutionStatus.FAILED`.

**`core/world_state.py` — `list_pending_effects(status=...)` accepts `str` instead of `EffectStatus`**
The `status` parameter on line 227 is `str | None`, but the method compares `effect.status == status` where `effect.status` is `EffectStatus`. This causes type mismatch and relies on `EffectStatus.value` coercion. Should be typed as `EffectStatus | None`.

**`evaluators/trajectory_evaluator.py` — Late runtime import causes `ComparisonResult` to be unknown at static-analysis time**
`overview_summary.py` imports `ComparisonResult` via `TYPE_CHECKING` but then calls `summarize_trajectory_difference(result)` inside a loop. If `result` is typed loosely, static type checkers cannot validate field access. Ensure `ComparisonResult` is fully resolved before use.

---

### Medium Priority

**`evaluators/trajectory_evaluator.py` — Mixed lowercase/uppercase type hints**
File imports `Dict` and `List` (line 5: `from typing import Dict, List`) alongside `__future__ annotations`. Should migrate all to modern `dict[...]` / `list[...]` syntax, consistent with the rest of the codebase.

**`evaluators/trajectory_evaluator.py` — Chinese comment in English source**
Line 77 contains a Chinese comment (`对 trace 做最小 trajectory-level 统计和模式检测。`). Should be replaced with an English equivalent for codebase consistency.

**`backends/base.py`, `backends/mock_backend.py`, `backends/sandbox_backend.py` — Module-level docstrings absent**
All three backends lack module docstrings. Add a one-line description of each backend's purpose.

**`reporting/reporting.py` — `_build_key_difference` hardcodes `"file"` entity type**
Line 220: `result.stateful_result.final_state.get_entity("file", "f1")` uses `"file"` as a raw string. Should use `EntityType.FILE` from `core/constants.py`.

**`evaluators/overview_summary.py` — Late `from dict import tuple` in `_normalize_hits`**
Line 182 uses a local import `from typing import Any, Dict, List` which is redundant since the module already imports from `typing` at the top. Remove the duplicate import and use the existing names.

---

### Low Priority / Style

**`execution/stateful_executor.py` — `ExecutionRecord` dataclass lacks docstring**
The `ExecutionRecord` dataclass (line 42) has no class-level docstring. Should document its purpose and the meaning of each field.

**`evaluators/trajectory_evaluator.py` — `TrajectoryMetrics` and `TrajectoryComparisonSummary` dataclasses lack docstrings**
Both dataclasses have no class docstrings. Add one-line descriptions.

**`runners/experiment_runner.py` — Demo helper functions lack docstrings**
`build_file_search_demo_calls`, `build_file_search_demo_goals`, `build_issue_tracker_demo_calls`, and `build_issue_tracker_demo_goals` have no docstrings. Should document their return value and purpose.

**`core/environment.py` — `ToolEnvironment.run_until_idle` lacks docstring**
The method on line 48 should have a docstring explaining `max_steps` cap and what constitutes "idle".

**`backends/base.py` — Abstract methods lack docstrings**
All `@abstractmethod` definitions (`get_backend_name`, `create_state`, etc.) lack docstrings. Add at minimum a one-line description for each.

**`reporting/reporting.py` — Magic string `"file"` and `"f1"` in `_build_key_difference`**
Lines 220–221 hardcode `"file"` entity type and `"f1"` as the example file ID. These are test fixture values leaking into production code and should be parameterized or replaced with constants.

**`comparison_runner.py` — Module docstring style**
Uses `"""..."""` on a single line (line 1–3) rather than a clean single-line module docstring. Should be: `"""Stateless vs Stateful comparison runner."""`.

---

### Already Good

- `core/constants.py`: Clean separation of enums, effect kinds, and numeric defaults. No magic strings elsewhere in the module.
- `core/world_state.py`: Comprehensive `to_dict`/`from_dict` serialization, `__repr__` implemented, `copy.deepcopy` used consistently.
- `tool_spec.py`: Well-structured abstract base class with `TYPE_CHECKING` guard for runtime-safe imports.
- `tools/`: All four tool files (`file_tools.py`, `search_tools.py`, `calendar_tools.py`, `issue_tools.py`) have module docstrings, class docstrings, helper functions with docstrings, and use constants from `core/constants.py`.
- `backends/__init__.py`, `core/__init__.py`, `adapters/__init__.py`: All have proper `__all__` exports and docstrings.
- `evaluators/evaluator.py`: `CallLevelEvaluator` and `StateLevelEvaluator` have proper docstrings; `StateLevelEvaluator._evaluate_goal` handles all goal types with clear messages.
- `__init__.py` (root): Comprehensive `__all__` with 80+ public symbols; Quick Start example in module docstring.
- Circular import chain: Resolved via `TYPE_CHECKING` guards in `evaluator.py` and `overview_summary.py`.

---

## Citation
