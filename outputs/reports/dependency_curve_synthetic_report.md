# Cross-tool Dependency Difficulty Curve Report

## Strategy Degradation

| Strategy | L1 Success | L2 Success | L3 Success | L1->L3 Drop | AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| direct | 100.0% | 20.0% | 0.0% | 100.0% | 0.400 |
| cot | 100.0% | 60.0% | 40.0% | 60.0% | 0.667 |
| react | 100.0% | 100.0% | 80.0% | 20.0% | 0.933 |
| self_refine | 100.0% | 100.0% | 100.0% | 0.0% | 1.000 |

## Metrics By Difficulty

| Strategy | Difficulty | Final Correct | Call Success | Invalid Calls | Recovery | Avg Steps | Dependency Completion | Missing Prereq | Side-effect Awareness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| direct | L1_SINGLE_TOOL | 100.0% | 100.0% | 0.0% | 0.0% | 1.00 | 100.0% | 0.0% | - |
| direct | L2_EXPLICIT_DEP | 20.0% | 87.5% | 0.0% | 0.0% | 1.60 | 0.0% | 100.0% | - |
| direct | L3_IMPLICIT_SIDE_EFFECT | 0.0% | 81.8% | 0.0% | 0.0% | 2.20 | 60.0% | 40.0% | 0.0% |
| cot | L1_SINGLE_TOOL | 100.0% | 100.0% | 0.0% | 0.0% | 1.00 | 100.0% | 0.0% | - |
| cot | L2_EXPLICIT_DEP | 60.0% | 100.0% | 0.0% | 0.0% | 2.20 | 60.0% | 40.0% | - |
| cot | L3_IMPLICIT_SIDE_EFFECT | 40.0% | 100.0% | 0.0% | 0.0% | 2.60 | 90.0% | 20.0% | 40.0% |
| react | L1_SINGLE_TOOL | 100.0% | 100.0% | 0.0% | 0.0% | 1.00 | 100.0% | 0.0% | - |
| react | L2_EXPLICIT_DEP | 100.0% | 100.0% | 0.0% | 0.0% | 2.60 | 100.0% | 0.0% | - |
| react | L3_IMPLICIT_SIDE_EFFECT | 80.0% | 100.0% | 0.0% | 0.0% | 2.80 | 100.0% | 0.0% | 80.0% |
| self_refine | L1_SINGLE_TOOL | 100.0% | 100.0% | 0.0% | 0.0% | 1.00 | 100.0% | 0.0% | - |
| self_refine | L2_EXPLICIT_DEP | 100.0% | 100.0% | 0.0% | 0.0% | 2.60 | 100.0% | 0.0% | - |
| self_refine | L3_IMPLICIT_SIDE_EFFECT | 100.0% | 88.9% | 0.0% | 100.0% | 3.60 | 100.0% | 0.0% | 100.0% |

## Interpretation
The lowest L1-to-L3 degradation is observed for `self_refine`, while `direct` degrades the most as cross-tool dependencies become implicit and side-effect-driven. This supports using trajectory-level dependency metrics in addition to final state correctness.
