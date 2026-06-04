# Backend Migration Report

## Backend Migration Metrics

| Strategy | Backend | Cases | Final Correct | Migration Gap | State Divergence | Invalid Calls | Recovery | Avg Steps | Avg Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | mock | 17 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 1.82 | 0.28 |
| direct | sandbox | 17 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 1.82 | 3.12 |
| direct | live_like | 17 | 0.0% | 100.0% | 100.0% | 0.0% | 0.0% | 1.82 | 5.54 |
| cot | mock | 17 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2.82 | 0.50 |
| cot | sandbox | 17 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2.82 | 6.02 |
| cot | live_like | 17 | 47.1% | 52.9% | 52.9% | 0.0% | 47.1% | 2.82 | 11.11 |
| react | mock | 17 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3.82 | 0.70 |
| react | sandbox | 17 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3.82 | 8.32 |
| react | live_like | 17 | 76.5% | 23.5% | 23.5% | 0.0% | 76.5% | 3.82 | 16.84 |
| self_refine | mock | 17 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3.82 | 0.70 |
| self_refine | sandbox | 17 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 3.82 | 7.92 |
| self_refine | live_like | 17 | 76.5% | 23.5% | 23.5% | 0.0% | 76.5% | 3.82 | 16.60 |

## Live-like Fault Breakdown

| Strategy | Fault Type | Cases | Final Correct | Recovery | Avg Steps | Avg Latency ms |
|---|---|---:|---:|---:|---:|---:|
| direct | hard_schema_drift | 4 | 0.0% | 0.0% | 1.75 | 5.43 |
| direct | persistent_timeout | 5 | 0.0% | 0.0% | 1.80 | 5.92 |
| direct | schema_drift | 4 | 0.0% | 0.0% | 1.75 | 5.42 |
| direct | timeout | 4 | 0.0% | 0.0% | 2.00 | 5.27 |
| cot | hard_schema_drift | 4 | 0.0% | 0.0% | 2.75 | 11.27 |
| cot | persistent_timeout | 5 | 0.0% | 0.0% | 2.80 | 11.17 |
| cot | schema_drift | 4 | 100.0% | 100.0% | 2.75 | 11.11 |
| cot | timeout | 4 | 100.0% | 100.0% | 3.00 | 10.87 |
| react | hard_schema_drift | 4 | 0.0% | 0.0% | 3.75 | 16.02 |
| react | persistent_timeout | 5 | 100.0% | 100.0% | 3.80 | 17.48 |
| react | schema_drift | 4 | 100.0% | 100.0% | 3.75 | 16.87 |
| react | timeout | 4 | 100.0% | 100.0% | 4.00 | 16.84 |
| self_refine | hard_schema_drift | 4 | 0.0% | 0.0% | 3.75 | 15.94 |
| self_refine | persistent_timeout | 5 | 100.0% | 100.0% | 3.80 | 16.93 |
| self_refine | schema_drift | 4 | 100.0% | 100.0% | 3.75 | 16.40 |
| self_refine | timeout | 4 | 100.0% | 100.0% | 4.00 | 17.04 |

## Interpretation
The largest mock-to-live-like migration gap appears for `direct`, while `react` transfers most robustly. This suggests that backend realism can reveal failures hidden by purely in-memory mock execution.
