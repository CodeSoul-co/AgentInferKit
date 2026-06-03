# Experiment 4: Backend Migration Summary

## Objective

Experiment 4 evaluates whether tool-use performance transfers across backend realism levels. The question is:

Can an agent or strategy that succeeds in an in-memory mock environment still succeed when the same task is executed under sandbox or live-like backend conditions?

The experiment compares three backend levels:

- `mock`: in-memory `WorldState` execution.
- `sandbox`: isolated session backend with deterministic latency and artifact-backed file/search execution.
- `live_like`: sandbox-style isolation plus deterministic live-like execution faults.

The current version is still reproducible and does not call external services, but it is stronger than the first pilot version because sandbox execution now writes real local file/search artifacts, and live-like execution includes multiple fault classes and fault intensities.

## Implemented Components

Core implementation:

- `src/toolsim/backends/live_like_backend.py`
  - Adds a reproducible live-like backend marker on top of sandbox semantics.

- `src/toolsim/backends/sandbox_backend.py`
  - Adds per-session artifact roots under `tmp/toolsim_sandbox`.
  - Persists `file.write` outputs as real text artifacts.
  - Persists `search.index` snapshots as real JSON artifacts.

- `src/toolsim/tools/file_tools.py` and `src/toolsim/tools/search_tools.py`
  - Keep WorldState compatibility for evaluators.
  - Prefer backend artifacts for sandbox/live-like file reads and search queries.
  - Expose artifact paths in observations and trace metadata.

- `src/toolsim/runners/backend_migration.py`
  - Builds synthetic and ToolSandbox backend migration cases.
  - Runs each case across `mock`, `sandbox`, and `live_like`.
  - Compares `direct`, `cot`, `react`, and `self_refine`.
  - Reports final state correctness, migration gap, state divergence, invalid call rate, recovery rate, trajectory length, latency, and live-like fault breakdown.

Run script:

- `scripts/run_backend_migration.py`

Generated outputs:

- `outputs/reports/backend_migration_report.md`
- `outputs/metrics/backend_migration_summary.json`
- `outputs/cases/backend_migration_cases.jsonl`
- `outputs/figures/exp4_backend_migration_curve.png`
- `outputs/figures/exp4_backend_migration_gap.png`

## Dataset Setup

The benchmark contains:

- Synthetic backend migration cases: 5
- ToolSandbox backend migration cases: 12
- Total backend migration cases: 17
- Strategies: 4
- Backends: 3
- Total runs: 204

The live-like backend injects four fault classes:

- `timeout`: one transient timeout
- `schema_drift`: one transient schema mismatch
- `persistent_timeout`: two consecutive timeouts
- `hard_schema_drift`: three consecutive schema mismatches

Recovery budgets differ by strategy:

- `direct`: no retry
- `cot`: one retry
- `react`: two retries
- `self_refine`: two retries

This creates a more informative migration curve than the initial pilot version.

The sandbox backend now also has a more realistic IO boundary for file/search cases: file contents and search snapshots are materialized on disk, while WorldState remains the canonical state used by existing correctness checks. This gives traces concrete artifacts without weakening comparability across the four experiments.

## Main Results

Aggregate final state correctness:

| Strategy | Mock | Sandbox | Live-like | Mock -> Live-like Gap |
|---|---:|---:|---:|---:|
| direct | 100.0% | 100.0% | 0.0% | 100.0% |
| cot | 100.0% | 100.0% | 47.1% | 52.9% |
| react | 100.0% | 100.0% | 76.5% | 23.5% |
| self_refine | 100.0% | 100.0% | 76.5% | 23.5% |

Latency and execution substrate both increase with backend realism:

- `mock`: fastest in-memory execution.
- `sandbox`: target-tool latency is added, and file/search tasks cross a local artifact boundary.
- `live_like`: higher latency plus execution faults.

## Live-like Fault Breakdown

Live-like fault-level results show where each strategy fails:

| Strategy | timeout | schema_drift | persistent_timeout | hard_schema_drift |
|---|---:|---:|---:|---:|
| direct | 0.0% | 0.0% | 0.0% | 0.0% |
| cot | 100.0% | 100.0% | 0.0% | 0.0% |
| react | 100.0% | 100.0% | 100.0% | 0.0% |
| self_refine | 100.0% | 100.0% | 100.0% | 0.0% |

Interpretation:

- `direct` fails under every live-like fault because it has no recovery path.
- `cot` recovers single transient faults but fails when the fault persists for two or more attempts.
- `react` and `self_refine` recover persistent timeouts because they have a larger retry budget.
- No strategy recovers `hard_schema_drift` in this minimal implementation because the schema mismatch persists beyond the retry budget.

## Why This Is More Useful Than the Pilot Version

The first minimal version only had a single retryable timeout. That made the result too simple:

- `direct` failed.
- all other strategies recovered.

The enhanced version introduces graduated backend realism:

- artifact-backed sandbox IO
- transient fault
- persistent fault
- schema drift
- unrecoverable schema drift

This makes the migration gap more informative:

- `direct`: 100.0% gap
- `cot`: 52.9% gap
- `react`: 23.5% gap
- `self_refine`: 23.5% gap

Now the result shows not only whether retry exists, but how much recovery budget and robustness each strategy has.

## Main Takeaway

Experiment 4 supports the following claim:

Mock-only evaluation can overestimate deployment robustness. Even when all strategies reach 100% final-state correctness under mock and sandbox backends, live-like backend faults expose migration gaps.

Backend realism therefore matters as a separate evaluation axis:

- Experiment 1: stateful vs stateless environment semantics
- Experiment 2: cross-tool dependency difficulty
- Experiment 3: noise robustness under stateful execution
- Experiment 4: backend migration under increasing execution realism

Together, the four experiments form a coherent evaluation story for stateful tool-use agents.

## Current Limitation

This version remains deterministic and local. It does not yet include:

- real external APIs
- persistent SQLite-backed sandbox state for every domain
- partial completion
- stale live-like observations
- race-like backend behavior

Those can be added later, but the current version is already sufficient as a minimal, reportable backend migration experiment.
