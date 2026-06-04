# Cross-tool Dependency Difficulty Curve Report

## Strategy Degradation

| Strategy | L1 Success | L2 Success | L3 Success | L1->L3 Drop | AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| direct | 100.0% | 0.0% | 0.0% | 100.0% | 0.333 |
| cot | 100.0% | 100.0% | 12.5% | 87.5% | 0.708 |
| react | 100.0% | 100.0% | 50.0% | 50.0% | 0.833 |
| self_refine | 100.0% | 100.0% | 100.0% | 0.0% | 1.000 |

## Metrics By Difficulty

| Strategy | Difficulty | Final Correct | Call Success | Invalid Calls | Recovery | Avg Steps | Dependency Completion | Missing Prereq | Side-effect Awareness |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| direct | L1_SINGLE_TOOL | 100.0% | 100.0% | 0.0% | 0.0% | 2.00 | 100.0% | 0.0% | - |
| direct | L2_EXPLICIT_DEP | 0.0% | 100.0% | 0.0% | 0.0% | 1.25 | 0.0% | 100.0% | - |
| direct | L3_IMPLICIT_SIDE_EFFECT | 0.0% | 100.0% | 0.0% | 0.0% | 1.75 | 12.5% | 87.5% | 0.0% |
| cot | L1_SINGLE_TOOL | 100.0% | 100.0% | 0.0% | 0.0% | 2.00 | 100.0% | 0.0% | - |
| cot | L2_EXPLICIT_DEP | 100.0% | 81.8% | 0.0% | 100.0% | 2.75 | 100.0% | 0.0% | - |
| cot | L3_IMPLICIT_SIDE_EFFECT | 12.5% | 100.0% | 0.0% | 0.0% | 3.00 | 50.0% | 75.0% | 12.5% |
| react | L1_SINGLE_TOOL | 100.0% | 100.0% | 0.0% | 0.0% | 2.00 | 100.0% | 0.0% | - |
| react | L2_EXPLICIT_DEP | 100.0% | 81.8% | 0.0% | 100.0% | 2.75 | 100.0% | 0.0% | - |
| react | L3_IMPLICIT_SIDE_EFFECT | 50.0% | 100.0% | 0.0% | 0.0% | 3.38 | 75.0% | 50.0% | 50.0% |
| self_refine | L1_SINGLE_TOOL | 100.0% | 100.0% | 0.0% | 0.0% | 2.00 | 100.0% | 0.0% | - |
| self_refine | L2_EXPLICIT_DEP | 100.0% | 81.8% | 0.0% | 100.0% | 2.75 | 100.0% | 0.0% | - |
| self_refine | L3_IMPLICIT_SIDE_EFFECT | 100.0% | 100.0% | 0.0% | 0.0% | 3.88 | 100.0% | 0.0% | 100.0% |

## Interpretation
The lowest L1-to-L3 degradation is observed for `self_refine`, while `direct` degrades the most as cross-tool dependencies become implicit and side-effect-driven. This supports using trajectory-level dependency metrics in addition to final state correctness.
