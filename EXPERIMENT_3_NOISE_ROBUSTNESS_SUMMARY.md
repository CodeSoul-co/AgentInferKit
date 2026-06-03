# Experiment 3: Noise Robustness Summary

## Objective

Experiment 3 evaluates whether stateful tool agents remain reliable when the environment becomes noisy. The injected noise covers both execution-level failures and observation-level corruption:

- `timeout`
- `schema_drift`
- `stale_state`
- `vague_observation`
- `misleading_observation`

The experiment has two layers. The fixed-trajectory layer measures whether a known oracle trajectory can recover from injected faults. The agent-policy layer measures whether different decision policies can continue correctly when noisy observations influence the next action.

## Implemented Components

Core implementation:

- `src/toolsim/faults/injector.py`
  - Added timeout failures.
  - Added schema drift failures.
  - Added bounded stale observation replay.
  - Added bounded vague observation injection.
  - Added misleading observation injection.

- `src/toolsim/runners/fault_robustness.py`
  - Builds fixed-trajectory noise cases from the Experiment 1 dataset.
  - Reports success@1, pass^k, recovery rate, cost increase, and state corruption rate.

- `src/toolsim/runners/policy_noise_robustness.py`
  - Adds closed-loop deterministic policy templates for `direct`, `cot`, `react`, and `self_refine`.
  - Expands synthetic policy cases across 5 task templates and 3 noise-intensity levels.
  - Adds a balanced ToolSandbox policy subset with 8 cases per domain.

Run scripts:

- `scripts/run_noise_robustness.py`
- `scripts/run_policy_noise_robustness.py`

Generated outputs:

- `outputs/reports/noise_robustness_report.md`
- `outputs/metrics/noise_robustness_summary.json`
- `outputs/cases/noise_robustness_cases.jsonl`
- `outputs/reports/policy_noise_robustness_report.md`
- `outputs/metrics/policy_noise_robustness_summary.json`

## Dataset Setup

Fixed-trajectory robustness reuses the Experiment 1 data setup:

- Synthetic Experiment 1 cases
- ToolSandbox comparison subset
- Total fixed-trajectory noise cases: 136

Agent-policy robustness now uses:

- Synthetic policy cases: 75
- ToolSandbox policy cases: 40
- Total policy cases: 115
- Strategies: 4
- Total policy runs: 460

The ToolSandbox policy subset is domain-balanced:

- contacts: 8 cases
- device_settings: 8 cases
- external_search: 8 cases
- messaging: 8 cases
- reminders: 8 cases

## Fixed-Trajectory Results

The fixed-trajectory layer produced:

- Success@1: 52.9%
- Pass^k: 100.0%
- Recovery rate: 100.0%
- Average cost increase: 0.50 extra calls
- State corruption rate: 0.0%

Interpretation:

- `timeout` and `schema_drift` sharply reduce first-attempt success.
- Simple retry recovers all fixed-trajectory cases.
- `stale_state` and `vague_observation` have weak final-state impact in this layer because later tool calls are fixed and do not actually depend on the corrupted observation.

This layer mainly validates the noise injector and separates execution recovery from policy decision recovery.

## Agent-Policy Results

The closed-loop policy layer is the main robustness result. Here, noisy observations affect future decisions.

Aggregate pass^k by strategy and noise:

| Strategy | timeout | schema_drift | stale_state | vague_observation | misleading_observation |
|---|---:|---:|---:|---:|---:|
| direct | 0.0% | 0.0% | 30.4% | 4.3% | 4.3% |
| cot | 65.2% | 78.3% | 30.4% | 91.3% | 100.0% |
| react | 65.2% | 78.3% | 95.7% | 73.9% | 69.6% |
| self_refine | 65.2% | 78.3% | 95.7% | 91.3% | 100.0% |

State corruption remains high for `direct`:

- timeout: 100.0%
- schema_drift: 100.0%
- vague_observation: 95.7%
- misleading_observation: 95.7%
- stale_state: 69.6%

Key strategy-level observations:

- `direct` has almost no recovery mechanism. It fails under both execution-level and observation-level noise.
- `cot` recovers vague and misleading observations well, but remains weak under stale state because it does not actively verify freshness.
- `react` is strongest on stale state because repeated observation can expose the fresh state.
- `self_refine` is the strongest overall. It matches `react` on stale state while also matching or exceeding `cot` on vague and misleading observations.
- ToolSandbox expansion makes the results less idealized: timeout and schema_drift are no longer fully recoverable for the stronger policies because some real trajectories contain dependencies where one failed call blocks later progress.

## Noise Intensity Curve

The agent-policy suite includes three intensity levels:

- `level_1`: one injected failure or noisy observation
- `level_2`: two consecutive injected failures or noisy observations
- `level_3`: three consecutive injected failures or noisy observations

Observed trends:

- timeout and schema_drift increase recovery cost as intensity rises.
- react spends more calls on observation-level noise because it tries to re-query.
- cot and self_refine often recover vague or misleading observations through fallback behavior without extra tool calls.
- stale_state specifically rewards policies that verify freshness through repeated observation.

## Main Takeaway

Experiment 3 shows that stateful robustness is not only about retrying failed tools. Explicit execution failures such as timeout and schema drift can often be recovered through retry, but observation-level noise is more subtle.

`stale_state`, `vague_observation`, and `misleading_observation` can lead the agent to make the wrong next decision even when the underlying state is not corrupted. This is why fixed oracle trajectories are insufficient for measuring noise robustness.

The closed-loop policy results support the main claim:

Robust stateful agents need observation validation, re-querying, and self-correction. Among the tested deterministic policy templates, `self_refine` is the most robust overall, `react` is especially strong for stale state, `cot` handles vague and misleading observations well, and `direct` is fragile across all noise types.

## Verification

The full test suite passes:

- 218 tests passed
- 4 warnings
