# Backend Migration Report

## Backend Migration Metrics

| Strategy | Backend | Cases | Final Correct | Migration Gap | State Divergence | Invalid Calls | Recovery | Avg Steps | Avg Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | mock | 40 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2.08 | 0.32 |
| direct | sandbox | 40 | 92.5% | 7.5% | 7.5% | 0.0% | 0.0% | 2.08 | 10.36 |
| direct | live_like | 40 | 0.0% | 100.0% | 100.0% | 0.0% | 0.0% | 2.08 | 9.92 |
| cot | mock | 40 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3.08 | 0.38 |
| cot | sandbox | 40 | 92.5% | 7.5% | 7.5% | 0.0% | 0.0% | 3.08 | 15.76 |
| cot | live_like | 40 | 50.0% | 50.0% | 50.0% | 0.0% | 50.0% | 3.08 | 17.80 |
| react | mock | 40 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 4.05 | 0.51 |
| react | sandbox | 40 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 4.05 | 21.96 |
| react | live_like | 40 | 85.0% | 15.0% | 15.0% | 0.0% | 85.0% | 4.05 | 26.53 |
| self_refine | mock | 40 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 4.05 | 0.48 |
| self_refine | sandbox | 40 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 4.05 | 20.66 |
| self_refine | live_like | 40 | 85.0% | 15.0% | 15.0% | 0.0% | 85.0% | 4.05 | 26.35 |

## Live-like Fault Breakdown

| Strategy | Fault Type | Cases | Final Correct | Recovery | Avg Steps | Avg Latency ms |
|---|---|---:|---:|---:|---:|---:|
| direct | hard_schema_drift | 6 | 0.0% | 0.0% | 1.83 | 10.72 |
| direct | persistent_timeout | 11 | 0.0% | 0.0% | 2.18 | 9.21 |
| direct | schema_drift | 10 | 0.0% | 0.0% | 2.20 | 10.40 |
| direct | semantic_validation | 3 | 0.0% | 0.0% | 1.00 | 5.28 |
| direct | timeout | 10 | 0.0% | 0.0% | 2.30 | 11.14 |
| cot | hard_schema_drift | 6 | 0.0% | 0.0% | 2.83 | 14.25 |
| cot | persistent_timeout | 11 | 0.0% | 0.0% | 3.18 | 15.66 |
| cot | schema_drift | 10 | 100.0% | 100.0% | 3.20 | 20.10 |
| cot | semantic_validation | 3 | 0.0% | 0.0% | 2.00 | 16.41 |
| cot | timeout | 10 | 100.0% | 100.0% | 3.30 | 20.40 |
| react | hard_schema_drift | 6 | 0.0% | 0.0% | 3.83 | 19.97 |
| react | persistent_timeout | 11 | 100.0% | 100.0% | 4.18 | 27.04 |
| react | schema_drift | 10 | 100.0% | 100.0% | 4.20 | 28.75 |
| react | semantic_validation | 3 | 100.0% | 100.0% | 2.67 | 20.17 |
| react | timeout | 10 | 100.0% | 100.0% | 4.30 | 29.58 |
| self_refine | hard_schema_drift | 6 | 0.0% | 0.0% | 3.83 | 20.36 |
| self_refine | persistent_timeout | 11 | 100.0% | 100.0% | 4.18 | 26.10 |
| self_refine | schema_drift | 10 | 100.0% | 100.0% | 4.20 | 28.41 |
| self_refine | semantic_validation | 3 | 100.0% | 100.0% | 2.67 | 23.90 |
| self_refine | timeout | 10 | 100.0% | 100.0% | 4.30 | 28.89 |

## Interpretation
The largest mock-to-live-like migration gap appears for `direct`, while `react` transfers most robustly. This suggests that backend realism can reveal failures hidden by purely in-memory mock execution.
