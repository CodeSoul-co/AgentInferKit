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
- Pluggable reasoning strategies such as **Direct Prompting**, **CoT**, **Long-CoT**, and **ToT**
- Built-in **RAG pipeline** with chunking, indexing, retrieval, and evidence tracking
- Support for **API / function calling** and **tool-use simulation**
- Batch inference, single-sample debugging, logging, retry, and resume
- Configurable evaluation with metrics for text, retrieval, and agent tasks
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

---

## Architecture

### Platform Layer
The engineering foundation of the project, including:

- model adapters
- reasoning strategies
- RAG pipeline
- task runners
- tool simulation
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

## Repository Structure

```text
project/
  configs/
  src/
    adapters/
    strategies/
    rag/
    runners/
    evaluators/
    toolsim/
    visualization/
    utils/
  data/
    raw/
    processed/
    indexes/
  outputs/
  webui/
  docs/
  scripts/
```

---

## Roadmap

### Phase 1
- Unified model adapters
- Task runners
- Basic evaluator
- Batch inference pipeline
- Single-sample debugging UI

### Phase 2
- QA-to-chunk pipeline
- Image data transformation pipeline
- Function-calling dataset and tool schema alignment

### Phase 3
- Stable evaluation scripts
- Visualization and analysis panels
- Result export for papers and reports

### Phase 4
- Open-source polishing
- Example configs
- Documentation and contribution guidelines

### Future
- Agent reasoning extensions
- Training-ready interfaces
- Trajectory storage
- Reward modeling hooks
- RL-based optimization loops

---

## Design Principles

- **Modular**
- **Config-driven**
- **Traceable**
- **Extensible**
- **Research-oriented**

---

## Status

AgentInferKit is currently under active development.

Current focus:
- platform layer implementation
- unified data layer construction
- inference and evaluation pipeline stabilization

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
  author={Your Name or Team Name},
  year={2026},
  howpublished={GitHub repository}
}
```
