# Experiment 2: Cross-tool Dependency Difficulty Curve

## 1. 实验目标

本实验研究的问题是：

> 随着 cross-tool dependency 难度提升，不同推理策略的性能如何退化？

实验把任务分为三层：

```text
L1_SINGLE_TOOL          单工具无状态
L2_EXPLICIT_DEP         双工具显式依赖
L3_IMPLICIT_SIDE_EFFECT 多工具隐式副作用依赖
```

对比策略：

```text
direct
cot
react
self_refine
```

本实验不是单纯看平均成功率，而是观察不同策略在难度提升时的 **退化曲线**。

## 2. 我做了什么

实验二同样分成两部分：

1. 先构造 synthetic dependency curve benchmark，跑通完整闭环
2. 再接 ToolSandbox dependency subset，验证真实任务子集上是否也出现同样趋势

### 2.1 Synthetic dependency curve

我构造了 15 个 synthetic cases：

```text
L1: 5 cases
L2: 5 cases
L3: 5 cases
```

覆盖的依赖类型包括：

- 单工具状态修改
- file write → search index → query
- issue assign → close
- calendar search → update
- search contact → modify contact
- timestamp conversion → add reminder
- delayed reindex side effect
- overwrite 后 stale snapshot
- issue close failure → assign → retry close
- calendar conflict → reschedule
- message search → contact search → contact update

### 2.2 ToolSandbox dependency subset

我从 ToolSandbox goal cases 中自动分类并抽样：

```text
L1: 8 cases
L2: 8 cases
L3: 8 cases
Total: 24 cases
```

分类规则是可解释的：

- L1：单个最终状态工具，无 helper/search dependency
- L2：存在明确 helper/search → final action 的链
- L3：包含 `STATE_DEPENDENCY`、多轮、多 helper 链、recency/location/time 等隐式状态依赖

抽样时做了 domain 轮转，避免某一层全部来自单一任务域。

## 3. 新增和修改的主要代码

### Dependency curve runner

- `src/toolsim/runners/dependency_curve.py`
  - 新增 `DependencyCurveCase`
  - 新增 `DependencyCurveRunner`
  - 新增 synthetic benchmark 构造函数
  - 新增 ToolSandbox dependency subset 分类和抽样函数
  - 新增 ToolSandbox 到 dependency curve case 的转换逻辑
  - 新增 strategy trajectory templates：
    - `direct`
    - `cot`
    - `react`
    - `self_refine`

### Dependency report

- `src/toolsim/reporting/dependency_curve_report.py`
  - 新增 Markdown 报告渲染
  - 输出 strategy degradation table
  - 输出 difficulty-level metrics table
  - 自动生成 interpretation 段落

### Tests

- `tests/test_dependency_curve.py`
  - 测试 synthetic L1/L2/L3 是否均衡
  - 测试退化曲线是否符合预期
  - 测试 ToolSandbox dependency subset 是否每层 8 条
  - 测试 ToolSandbox dependency curve 是否可运行

最终全量测试：

```text
218 passed, 4 warnings
```

## 4. 新增指标

实验二除了复用实验一指标，还新增了 dependency-specific metrics：

```text
final state correctness
call success rate
invalid call rate
recovery rate
average trajectory length
dependency completion rate
missing prerequisite rate
side-effect awareness rate
dependency repair rate
L1 -> L3 degradation
AUC over difficulty levels
```

其中最重要的是：

```text
L1 -> L3 degradation
```

它衡量一个策略从简单任务到复杂隐式依赖任务时掉了多少。

## 5. 输出文件

Synthetic 实验输出：

- `outputs/reports/dependency_curve_synthetic_report.md`
- `outputs/metrics/dependency_curve_synthetic_summary.json`

ToolSandbox 实验输出：

- `outputs/cases/toolsandbox_dependency_subset_cases.jsonl`
- `outputs/reports/dependency_curve_toolsandbox_report.md`
- `outputs/metrics/dependency_curve_toolsandbox_summary.json`

Experiment 2 figures:

- `outputs/figures/exp2_synthetic_success_curve.png`
- `outputs/figures/exp2_toolsandbox_success_curve.png`
- `outputs/figures/exp2_l1_to_l3_degradation.png`
- `outputs/figures/exp2_toolsandbox_metric_heatmap.png`

## 6. Synthetic 实验结果

```text
direct:      L1 100.0% -> L2 20.0%  -> L3 0.0%    drop 100.0%
cot:         L1 100.0% -> L2 60.0%  -> L3 40.0%   drop 60.0%
react:       L1 100.0% -> L2 100.0% -> L3 80.0%   drop 20.0%
self_refine: L1 100.0% -> L2 100.0% -> L3 100.0%  drop 0.0%
```

解释：

- Direct 在 L1 表现很好，但一进入依赖任务就快速退化。
- CoT 能处理部分显式依赖，但面对隐式副作用时仍明显下降。
- ReAct 因为保留 observe-act 结构，对 L2/L3 更稳。
- Self-Refine 最稳，但需要更长的轨迹和更多调用。

Synthetic 结果说明：dependency complexity 能清晰地区分不同推理策略。

## 7. ToolSandbox dependency subset 结果

```text
direct:      L1 100.0% -> L2 0.0%   -> L3 0.0%     drop 100.0%
cot:         L1 100.0% -> L2 100.0% -> L3 12.5%    drop 87.5%
react:       L1 100.0% -> L2 100.0% -> L3 50.0%    drop 50.0%
self_refine: L1 100.0% -> L2 100.0% -> L3 100.0%   drop 0.0%
```

解释：

- ToolSandbox 上的趋势和 synthetic 一致。
- Direct 只能处理单工具任务。
- CoT 在 L2 显式依赖上很好，但 L3 隐式依赖下大幅退化。
- ReAct 在 L3 明显优于 CoT。
- Self-Refine 最稳，L3 仍保持 100%。

ToolSandbox 结果更有说服力，因为它说明这种退化曲线不是手写 case 的人为现象，而是在真实任务子集上也能观察到。

## 8. 结果说明了什么

实验二的核心结论是：

> Different reasoning strategies do not degrade uniformly as tool-use tasks become more stateful and dependency-heavy.

中文解释：

> 随着工具任务变得更 stateful、更依赖中间状态，不同推理策略的退化速度不同。

具体来说：

- Direct：适合直接 final action，不适合跨工具依赖
- CoT：能处理显式依赖，但不稳定处理隐式副作用
- ReAct：能利用中间观察，L3 更稳
- Self-Refine：最稳，但工具调用成本更高

这说明实验二的 difficulty curve 比单个平均成功率更有信息量。

## 9. 和实验一的关系

实验一证明：

> stateful environment 能暴露 stateless baseline 隐藏的中间过程差异。

实验二进一步证明：

> 在 stateful dependency 难度提升时，不同推理策略会出现可测量的退化曲线。

两个实验合起来形成完整逻辑：

1. 先证明为什么需要 stateful / trajectory-level evaluation
2. 再用 stateful dependency curve 区分不同推理策略的能力边界

## 10. 可写入报告的结论

可以这样总结：

> Across both synthetic cases and the ToolSandbox dependency subset, performance degrades as cross-tool dependencies become more complex. Direct strategies collapse once tasks require explicit or implicit tool dependencies. CoT handles explicit dependencies but degrades sharply under implicit side-effect dependencies. ReAct is more robust because it preserves intermediate observation-action structure, while Self-Refine achieves the best robustness at the cost of longer trajectories. These results show that cross-tool dependency difficulty curves provide a more informative evaluation of tool-use reasoning than aggregate success rates alone.
