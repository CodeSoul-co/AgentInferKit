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

## Citation

```bibtex
@misc{agentinferkit,
  title={AgentInferKit: A Modular Platform for Agent Inference, Evaluation, and Training},
  author={CodeSoul-co},
  year={2026},
  howpublished={GitHub repository}
}
```
