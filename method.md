# AgentInferKit — Method & Design Document

> **This document serves as the canonical specification for the AgentInferKit project.**  
> All modules, data formats, experiment protocols, and contribution conventions must conform to the definitions herein.

---

## 1. Project Positioning

This project builds a unified, open-source benchmark platform for large language models (LLMs) and intelligent agent systems. It supports multiple task types — open-domain question answering (QA), knowledge-based examination, image understanding, and API function calling — and evaluates the effectiveness, boundaries, and cost of reasoning-augmentation methods such as RAG, CoT, and ToT within a single unified framework.

The platform follows a three-layer architecture: **Platform Layer · Data Layer · Experiment Layer**.

- The **Platform Layer** handles unified model integration, inference execution, tool simulation, batch evaluation, and interactive visualization.
- The **Data Layer** manages the organization, processing, standardization, and versioning of benchmark data assets.
- The **Experiment Layer** designs evaluation protocols, controlled comparisons, and analysis frameworks to answer: *which reasoning augmentation methods are effective on which tasks, why they work, and at what cost.*

---

## 2. Overall Goals

### 2.1 Engineering Goals

1. Provide a unified LLM / VLM / Agent inference and evaluation framework.
2. Support API-based models, locally-deployed models, multimodal models, and tool-use tasks.
3. Support batch testing, single-sample debugging, visual analysis, and result export.
4. Maintain a modular design that facilitates multi-person collaborative development and future extension.
5. Provide a reproducible experimental foundation for benchmark research papers.

### 2.2 Research Goals

1. Build a composite benchmark covering text, vision, retrieval-augmented, and tool-calling scenarios.
2. Study the mechanism by which RAG affects performance on knowledge-based text-exam tasks.
3. Transform raw image-description data into standardized, automatically evaluable image MCQ tasks.
4. Study the performance gains and computational costs of CoT and ToT on API function calling tasks.

### 2.3 Open-Source Goals

1. Clear code structure to facilitate community contributions.
2. Standardized data protocols, evaluation protocols, and experiment scripts.
3. Provide documentation, example configurations, reproducible experiment templates, and extensible interfaces.
4. Future support for additional task sets, reasoning strategies, and evaluation metrics.

---

## 3. Three-Layer Architecture

### 3.1 Platform Layer

The Platform Layer is the engineering foundation of the entire project. It unifies models, data, reasoning strategies, tools, evaluation, and visualization into a runnable, extensible, debuggable, and reproducible benchmark system. The initial focus is on LLM and Agent inference; later stages will integrate training support for agent systems.

### 3.2 Data Layer

The Data Layer organizes and standardizes heterogeneous raw data into a unified benchmark data schema, supporting standard and custom data loading and version management across text tasks, image tasks, retrieval-augmented tasks, and tool-calling tasks.

### 3.3 Experiment Layer

The Experiment Layer designs experiment workflows, control groups, evaluation metrics, and analysis protocols around specific research questions. Its purpose is to answer: *which reasoning augmentation methods are effective, why they work, and what tradeoffs they involve.*

---

## 4. Platform Layer — Development Specification

### 4.1 Platform Layer Objectives

The Platform Layer must implement the following core capabilities:

1. Unified model integration and invocation.
2. Unified task execution and data-flow management.
3. Pluggable inference strategy switching.
4. Unified evaluation and logging.
5. Unified tool simulation and agent testing.
6. Unified visualization and result presentation.
7. Unified engineering interfaces and module boundaries.

**Design principles:** loose coupling · fixed interfaces · configuration-driven · traceable results · extensibility.

---

### 4.2 Functional Modules

#### 4.2.1 Model Integration Module

**Goal:** Integrate different types of large models and multimodal models under a consistent invocation interface.

**Requirements:**
1. Support API-based model integration.
2. Support locally deployed model inference.
3. Support text-only and multimodal (text + image) models.
4. Support unified configuration of model parameters: `temperature`, `top_p`, `max_tokens`, `seed`, `system_prompt`, etc.
5. Support batch inference and concurrent scheduling.
6. Support inference logging: requests, responses, latency, token consumption, and error messages.

**Output:**
- Unified `ModelAdapter` interface.
- Adapter internals are transparent to task runners.
- Configuration-file-based model loading and switching.

---

#### 4.2.2 Inference Strategy Module

**Goal:** Design different prompting/reasoning methods as pluggable strategies, enabling rapid switching and comparison on the same task.

**Requirements:**
1. Direct prompting.
2. Chain-of-Thought (CoT).
3. Long-CoT.
4. Tree-of-Thought (ToT).
5. Reserved extension points for: ReAct, self-refine, reflection, self-consistency.
6. Prompt template management, distinguishing batch-experiment templates from single-sample dialogue templates.
7. Per-task assignment of different inference templates.
8. Record reasoning traces for downstream visualization and error analysis.

**Output:**
- Unified `Strategy` interface.
- Each reasoning method has independent configuration.
- Directly callable from any task runner.

---

#### 4.2.3 RAG Module

**Goal:** Support knowledge base construction, retrieval, evidence visualization, and RAG inference experiments.

**Requirements:**
1. Upload text-based knowledge data.
2. Chunk, embed, and index knowledge data.
3. Support multiple chunking strategies, top-k settings, and retriever configurations.
4. Query, retrieve, display evidence, and export evidence.
5. Insert retrieval results into unified prompt templates.
6. Support two experimental modes: **Oracle evidence** and **Retrieved evidence**.
7. Knowledge base version management and index rebuilding.
8. Visualize chunk content, source, retrieval scores, and hit status.

**Output:**
- RAG pipeline runs independently.
- Seamless integration with the text-exam experiment.
- Retrieval results and final answer processes are fully traceable.

---

#### 4.2.4 Task Runner Module

**Goal:** Provide a unified abstraction for batch execution logic across all benchmark task types.

**Requirements:**
1. Text generation task execution.
2. Multiple-choice question execution (with prompt-managed output formatting).
3. Image understanding task execution.
4. Image-text mixed task execution.
5. API function calling task execution.
6. Batch dataset inference.
7. Single-sample debug mode with an interactive agent dialogue interface.
8. Failure retry, exception logging, and checkpoint resume.
9. Experiment configuration persistence and rerun support.

**Output:**
- Unified `TaskRunner` abstraction.
- Each task type only needs to implement its own data parsing and result post-processing logic.

---

#### 4.2.5 Tool Simulation Module

**Goal:** Provide a controllable tool-use testing environment for agent-class benchmarks, supporting real, custom, and mock tool execution.

**Requirements:**
1. Upload custom tool description files.
2. Upload corresponding index / schema / mock data files.
3. Simulate return values upon tool invocation.
4. Record tool call chains, parameters, return values, and call status.
5. Evaluate: correct tool selection, correct parameters, and valid call order.
6. Support multi-tool combination scenarios.
7. Support fine-grained analysis of cases where tool calls succeed but the final answer fails.

**Output:**
- `ToolRegistry` and `MockExecutor`.
- Linked with the API function calling dataset.

---

#### 4.2.6 Evaluation Module

**Goal:** Support unified and configurable benchmark metric computation and analysis.

**Requirements:**
1. Basic metrics: `accuracy`, `EM`, `F1`, `choice accuracy`, `BLEU`, `ROUGE-L`.
2. Agent metrics: `tool-call success rate`, `parameter accuracy`, `end-to-end success rate`, `win rate`.
3. RAG metrics: `retrieval recall`, `evidence hit rate`, `answer-evidence alignment`.
4. Efficiency metrics: `latency`, `token cost`, `average tool calls`, `reasoning trace length`.
5. User-defined evaluation matrices.
6. Decouple inference and evaluation: generate predictions first, evaluate independently afterward.
7. Extension interface for judge-based evaluation (LLM-as-judge).
8. Statistics by task type, model, strategy, and sub-category.

**Output:**
- Configurable `Evaluator`.
- Standardized evaluation artifacts suitable for paper writing and figure generation.

---

#### 4.2.7 Visualization Platform Module

**Goal:** Provide an interactive engineering interface for running experiments, viewing samples, analyzing results, and debugging inference processes.

**Requirements:**
1. Batch task launch with progress display.
2. Single-sample dialogue test window.
3. Unified display of text, images, tool traces, and RAG evidence.
4. Preview and visualize uploaded data.
5. Joint display of inference results, ground-truth answers, evaluation results, and error types.
6. Multi-experiment result comparison visualization.
7. Export: charts, logs, prediction results.
8. Statistical panel for paper figure generation.

**Output:**
- A researcher-friendly dashboard.
- Supports both engineering debugging and experimental analysis.

---

#### 4.2.8 Configuration & Engineering Management Module

**Goal:** Ensure the entire project supports modular collaborative development and long-term maintenance.

**Requirements:**
1. All modules use configuration-driven design wherever possible.
2. Separate configuration management for models, data, experiments, evaluation, tools, and visualization.
3. Define unified input/output schemas.
4. Unified management of run logs, version info, and random seeds.
5. Experiment reproducibility.
6. Directory structure and interface conventions for multi-person collaboration.
7. Plugin-style addition of new tasks or strategies.

**Output:**
- Fixed interfaces; minimal coupling.
- Suitable for open-source community collaboration and PR management.

---

### 4.3 Platform Layer Directory Structure

```
project/
  configs/
    models/
    datasets/
    strategies/
    eval/
    tools/
    experiments/
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
    predictions/
    metrics/
    logs/
    figures/
  webui/
  docs/
  scripts/
```

---

## 5. Data Layer — Development Specification

### 5.1 Data Layer Objectives

The Data Layer organizes heterogeneous source data into a unified benchmark data asset. The focus is not simply on storing data, but on making data **runnable, evaluable, traceable, and versionable**.

The Data Layer serves three goals simultaneously:
1. **Serve the platform runtime** — task runners can read data with a standard loader.
2. **Serve experimental comparison** — different experiments use the same protocol and data.
3. **Serve future extension** — new tasks, new fields, and new labels can be added naturally.

---

### 5.2 Data Composition

The current benchmark data comprises four main parts:

1. **Q&A data**
2. **Text-exam data**
3. **Image understanding + corresponding text data**
4. **Agent API function calling data**

Notes:
- Image data is currently descriptive; the Experiment Layer will process it into MCQ format.
- Q&A data must be reorganized into knowledge chunks to support RAG experiments.
- Image-text pairs need LLM-based reprocessing to generate MCQ-format image understanding tasks.

---

### 5.3 Data Standardization Requirements

#### 5.3.1 Universal Sample Fields

Every sample must have:

| Field | Description |
|---|---|
| `sample_id` | Unique identifier |
| `task_type` | `qa` / `text_exam` / `image_mcq` / `api_calling` |
| `split` | `train` / `dev` / `test` |
| `source` | Origin dataset tag |
| `difficulty` | (optional) `easy` / `medium` / `hard` |
| `modality` | `text` / `image` |
| `version` | Dataset version string |
| `metadata` | Task-specific extension fields |

Purpose: enable data tracking, filtering, analysis, and version management.

#### 5.3.2 Unified Input/Output Structure

Every sample must clearly define:
- What the **input** is.
- What the **model must output**.
- What the **correct / reference answer** is.
- **How to evaluate** the output.
- Whether the sample **depends on external knowledge or tools**.

#### 5.3.3 Version Management

Distinguish between:
- `raw` — original source data.
- `cleaned` — after cleaning.
- `processed` — after transformation.
- `benchmark_release` — the version used in experiments.

This prevents experiments from being unable to trace data origins or processing history.

---

### 5.4 Q&A Data

**Goal:** Q&A data serves both as an independent task source and as the background knowledge source for text-exam tasks.

**Requirements:**
1. Clean and standardize raw QA data.
2. Annotate each QA with topic, domain, entities, or knowledge points.
3. Aggregate related QA pairs into **background knowledge chunks**.
4. Support multiple chunking granularities (by topic, entity, document, or knowledge point).
5. Record source QA lists for each chunk (traceability).
6. Generate knowledge base files ready for RAG indexing.
7. Maintain both QA-task view and chunked-knowledge view.

**Deliverables:**
- QA benchmark dataset.
- Chunked knowledge base.
- Index-ready data files for RAG.

---

### 5.5 Text-Exam Data

**Goal:** Build knowledge examination data that supports RAG vs. no-RAG comparison experiments.

**Requirements:**
1. Standardize question format: stem, options, answer, explanation, knowledge topic.
2. Annotate potential mappings between each question and QA chunks.
3. Define three evaluable protocols: `closed-book`, `oracle-rag`, `retrieved-rag`.
4. Annotate question type, knowledge dependency level, reasoning depth, and difficulty.
5. Ensure proper train/dev/test splits with no knowledge leakage.
6. Support standard automatic evaluation.

**Deliverables:**
- Text-exam benchmark dataset.
- Mapping table: text-exam questions ↔ knowledge chunks.
- RAG experiment protocol data files.

---

### 5.6 Image Understanding Data

**Goal:** Transform descriptive image-text samples into stable, automatically evaluable image MCQ data.

**Requirements:**
1. Preserve original images and original description text.
2. Design a question-generation pipeline to rewrite samples as MCQs.
3. Support diverse question types: object recognition, attribute recognition, relation judgment, scene understanding, OCR, chart comprehension, etc.
4. Generate high-quality distractors; avoid obviously incorrect options.
5. Apply consistency filtering to auto-generated questions.
6. Introduce human spot-check procedures for quality assurance.
7. Retain both original-description version and MCQ version for each sample.
8. Support standard fields: image path, question, options, answer, difficulty, question type.

**Deliverables:**
- Image understanding MCQ benchmark dataset.
- Question generation and quality-control scripts.
- Alignment table: original description ↔ MCQ version.

---

### 5.7 Agent API Function Calling Data

**Goal:** Build a structured dataset for agent reasoning and tool-use evaluation. Existing API files and index tables can be used; future support for auto-generating index tables from uploaded API files is optional.

**Requirements:**
1. Each sample specifies user goal, available tool set, and expected output.
2. Support task types: single-tool, multi-tool, multi-step, parameter-sensitive, and ambiguous calls.
3. Define standard tool schemas for each task.
4. Support mock return values and execution states.
5. Annotate standard call paths, correct parameters, and final answers.
6. Annotate: explicit planning required, ambiguity present, multi-tool required.
7. Support both end-to-end task success evaluation and intermediate call evaluation.

**Deliverables:**
- Function calling benchmark dataset.
- Tool schema files.
- Mock response files.
- Call trajectory annotation files.

---

### 5.8 Data Layer Directory Structure

```
data/
  raw/
    qa/
    text_exam/
    image/
    api_calling/
  processed/
    qa/
    knowledge_chunks/
    text_exam/
    image_mcq/
    api_calling/
  mappings/
    qa_to_chunk/
    exam_to_chunk/
    image_desc_to_mcq/
  schemas/
    sample_schemas/
    tool_schemas/
  indexes/
    rag/
```

---

## 6. Experiment Layer — Design Specification

The Experiment Layer is organized around three core experiments. Each experiment must have a clearly stated research question, data preparation method, control groups, core metrics, and analysis dimensions.

---

### 6.1 Experiment A — RAG vs. No-RAG on Text-Exam

#### 6.1.1 Research Objective

Study whether reorganizing QA data into a background knowledge base allows RAG to improve performance on text-exam tasks, and further analyze whether performance gains come from retrieval capability or evidence utilization capability.

#### 6.1.2 Experiment Input

- Background knowledge chunks aggregated from QA data.
- Text-exam question data.

#### 6.1.3 Experimental Conditions

Three conditions:

1. **No RAG (closed-book):** Model answers directly from parametric knowledge; no external context.
2. **Oracle RAG:** Ground-truth (or annotated) correct knowledge chunks are provided. *(May be replaced with random few-shot examples.)*
3. **Retrieved RAG:** Model retrieves top-k chunks from the knowledge base automatically before answering.

#### 6.1.4 Comparison Factors

1. Different models.
2. Different chunk granularities.
3. Different top-k settings.
4. Different prompt templates.
5. Different retrievers or embedding models.

#### 6.1.5 Evaluation Metrics

1. Text-exam accuracy.
2. Retrieval recall@k.
3. Evidence hit rate.
4. Answer-evidence consistency.
5. Hallucination rate.
6. Latency and token cost.

#### 6.1.6 Expected Analysis Questions

1. Does RAG consistently improve knowledge-exam performance?
2. Does the performance ceiling come from knowledge availability or from the model's reasoning capacity?
3. Which is more common: retrieval failure or evidence misuse?
4. Which question types benefit most from external knowledge?

#### 6.1.7 Expected Deliverables

- Systematic comparison table: RAG vs. no-RAG.
- Sensitivity analysis charts: chunk granularity and top-k.
- Error analysis case library.

---

### 6.2 Experiment B — Image MCQ Benchmark After Data Transformation

#### 6.2.1 Research Objective

Transform raw image-description data into standardized MCQs, building a more stable, automatically evaluable, and cross-comparable image understanding benchmark. Analyze model performance characteristics on this transformed task.

#### 6.2.2 Experiment Input

- Original images.
- Original description text.
- MCQ data generated via API-based transformation.

#### 6.2.3 Experimental Settings

1. Structured extraction from images and descriptions.
2. MCQ and distractor generation by model or rule.
3. Automatic filtering and human spot-check on generated samples.
4. Batch evaluation of different VLMs on the final image MCQ dataset.

#### 6.2.4 Comparison Settings

1. Original open-ended description task.
2. Transformed MCQ task.
3. Different image question types: object, attribute, relation, OCR, chart, etc.
4. Different difficulty levels. *(Difficulty labels should be generated by LLM during data processing.)*

#### 6.2.5 Evaluation Metrics

1. Choice accuracy.
2. Per-question-type accuracy.
3. Per-difficulty accuracy.
4. Option bias distribution.
5. Image grounding error rate.

#### 6.2.6 Expected Analysis Questions

1. Does MCQ conversion improve evaluation stability and automation?
2. What is the difficulty distribution across visual sub-task types?
3. Do model errors stem mainly from visual recognition, relation understanding, or distractor confusion?

#### 6.2.7 Expected Deliverables

- Image task transformation pipeline description.
- Image MCQ benchmark statistics table.
- Comparative results across VLMs with error-type analysis.

---

### 6.3 Experiment C — CoT / ToT on API Function Calling

#### 6.3.1 Research Objective

Study whether explicit reasoning strategies (CoT, ToT) improve agent performance on tool selection, parameter construction, and multi-step planning in function calling tasks; analyze the performance gains and computational cost tradeoffs. Tool selection is grounded in **business scenarios**, targeting **key capabilities** and **core functions**.

#### 6.3.2 Experiment Input

- Agent API function calling dataset.
- Tool schemas and mock execution environment.

#### 6.3.3 Experimental Conditions

At minimum:

1. Direct prompting (baseline).
2. CoT.
3. Long-CoT.
4. ToT.
5. *(Optional)* ReAct or self-refine.

#### 6.3.4 Task Sub-categories

1. Single-tool, single-round call.
2. Single-tool, multi-step call.
3. Multi-tool combination call.
4. Parameter-sensitive call.
5. Ambiguous tool selection.
6. Post-call result integration.

#### 6.3.5 Evaluation Metrics

1. Tool selection accuracy.
2. Parameter accuracy.
3. Invalid call rate.
4. Tool-call success rate.
5. End-to-end task success rate.
6. Average number of tool calls.
7. Latency and token cost.
8. Reasoning trace length.

#### 6.3.6 Expected Analysis Questions

1. Do explicit reasoning strategies help across all function calling sub-tasks?
2. Do longer reasoning chains justify their computational cost?
3. Where do tool-use failures most often occur: tool selection, parameter filling, post-execution integration, or final answer generation?

#### 6.3.7 Expected Deliverables

- Function calling comparison results across reasoning strategies.
- Sub-task dimension analysis table.
- Cost-benefit analysis charts.
- Representative call trajectory visualization cases.

---

## 7. Development & Research Coordination Plan

### Phase 1 — Minimum Viable Loop

Priority:

1. Model integration module.
2. Task runner.
3. Basic evaluator.
4. Single-sample test interface.
5. Batch prediction and result persistence.

**Goal:** A minimum runnable version where text, image, and tool-calling tasks all execute end-to-end.

### Phase 2 — Complete the Data Processing Pipeline

Priority:

1. QA → chunk construction workflow.
2. Image description → MCQ transformation workflow.
3. Function calling dataset ↔ tool schema alignment.

### Phase 3 — Solidify Experiment Protocols

Priority:

1. RAG / no-RAG experiment scripts.
2. Image MCQ batch evaluation scripts.
3. Unified CoT / ToT comparison scripts on API calling.
4. Metric aggregation and paper figure export scripts.

### Phase 4 — Open-Source Polish

Priority:

1. Documentation system.
2. Example configurations.
3. Quickstart scripts.
4. Data schema specification.
5. Module contribution guidelines.

---

## 8. Team Structure & Responsibilities

| Group / Role | Headcount | Scope | Key Tasks | Deliverables |
|---|---|---|---|---|
| **Experiment Group A** — QA → RAG / no-RAG text-exam | 2–4 | Experiment Layer + Data | (1) Clean QA data; (2) Aggregate QA into background knowledge chunks; (3) Build text-exam ↔ chunk mapping; (4) Design closed/oracle/retrieved experiment protocols; (5) Run experiments across models and retrieval settings; (6) Error analysis and visualization | QA standardized dataset; knowledge chunk library; text-exam data; RAG comparison results; metric tables and analysis figures |
| **Experiment Group B** — Image MCQ transformation | 2–3 | Experiment Layer + Data | (1) Organize raw image-text data; (2) Rewrite descriptive samples into MCQs via API; (3) Generate high-quality distractors; (4) Filtering and spot-check; (5) Build image MCQ benchmark; (6) Batch test VLMs and analyze errors | Image MCQ dataset; generation & filtering scripts; question-type statistics; model test results; error case library |
| **Experiment Group C** — Agent API calling + CoT/ToT | 2–3 | Experiment Layer + Data | (1) Organize API function calling data; (2) Standardize tool schemas, parameter formats, and mock responses; (3) Divide sub-tasks; (4) Design direct/CoT/long-CoT/ToT comparison; (5) Compute tool selection, parameter accuracy, task success metrics; (6) Reasoning trace analysis | API calling benchmark; tool schema & mock data; reasoning comparison results; call chain analysis; cost-benefit figures |
| **Developer Role D** — Platform & Data infrastructure | 1 | Platform Layer + Data Layer | (1) Unified model adapter (API / local / multimodal); (2) Task runner, batch inference, logging system; (3) Unified data schema, data loader, version management; (4) RAG module integration; (5) Tool simulation and evaluation interface; (6) Basic visualization UI / dialogue debug window; (7) Engineering structure, config files, module interfaces | Benchmark framework; data loading & management module; batch inference & evaluation pipeline; visualization prototype; config system; project engineering documentation |

---

*End of METHOD.md — last updated March 2026*