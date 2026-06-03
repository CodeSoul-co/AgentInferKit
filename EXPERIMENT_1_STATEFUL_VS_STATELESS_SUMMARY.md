# Experiment 1: Stateful vs Stateless Tool-use Evaluation

## 1. 实验目标

本实验验证的问题是：

> 仅看 final state correctness 是否足以评估 tool-use agent？

实验结论是：**不够**。

Stateful 和 stateless 在很多任务上都能达到相同的最终状态正确率，但它们的工具调用过程、依赖处理、失败恢复和中间状态语义明显不同。Stateless baseline 往往把真实工具环境中的中间依赖压缩掉，因此容易高估 agent 的工具使用能力。

## 2. 我做了什么

本实验分成两部分：

1. 手工构造 synthetic stateful/stateless 对照 benchmark
2. 接入 ToolSandbox subset，构造真实任务子集上的 stateful/stateless 对照实验

### 2.1 Synthetic 对照案例

我把原来的 4 个 stateful/stateless case 扩展到了 9 个 case，覆盖以下机制：

- 写文件后不 index 就 search
- 显式 `search.index` 依赖
- 覆盖文件后不重新 index 的 snapshot stale 语义
- 多文件部分索引
- 覆盖后重新 index
- issue close 前必须 assign
- issue reopen 前必须处于 closed 状态
- calendar 创建冲突后重试
- calendar update 冲突后恢复

### 2.2 ToolSandbox subset 对照案例

我从 ToolSandbox 中构造了 comparison 专用 subset：

- 5 个 domain，每类 8 条
- 共 40 条 ToolSandbox comparison cases
- 过滤掉只验证 helper tool trace、没有 final-state goal 的样本
- Stateful 保留完整 oracle trajectory
- Stateless 压缩成 final-state trajectory

也就是说，stateful 会保留：

- search
- timestamp conversion
- helper tool call
- external query
- intermediate tool trace

而 stateless 主要保留：

- 最终状态修改
- 最终用户可见输出

这使得两者在 final state 上可比，同时能观察到 trajectory 层面的差异。

## 3. 新增和修改的主要代码

### Core runner

- `src/toolsim/runners/comparison_runner.py`
  - 扩展 `ComparisonCase`
  - 支持 case 自带 initial state
  - 新增 synthetic stateful/stateless cases
  - 新增 ToolSandbox 到 comparison case 的转换逻辑
  - 新增 ToolSandbox comparison subset 选择逻辑

- `src/toolsim/runners/stateless_baseline.py`
  - 补充 stateless calendar 工具语义
  - 接入 ToolSandbox 工具
  - 让 stateless baseline 能运行 ToolSandbox 压缩轨迹

### Metrics and reporting

- `src/toolsim/evaluators/overview_summary.py`
  - 新增核心指标：
    - success rate
    - invalid call rate
    - recovery rate
    - trajectory length
    - final state correctness

- `src/toolsim/evaluators/trajectory_evaluator.py`
  - 新增/修正 trajectory pattern 检测：
    - explicit dependency
    - overwrite without re-index
    - issue close recovery
    - issue reopen recovery
    - calendar conflict recovery

- `src/toolsim/reporting/reporting.py`
  - 更新 Markdown report
  - 增加 ToolSandbox case 的差异描述
  - 报告中展示新增指标

### ToolSandbox subset

- `src/toolsim/adapters/toolsandbox_adapter.py`
  - 新增 deterministic subset sampler
  - 支持按 domain/category 抽样
  - 支持每类 5-10 条 case

### Tests

- `tests/test_stateless_vs_stateful.py`
- `tests/test_reporting.py`
- `tests/test_overview_summary.py`
- `tests/test_toolsandbox_benchmark.py`

最终全量测试：

```text
218 passed, 4 warnings
```

## 4. 输出文件

主要实验输出包括：

- `outputs/reports/stateless_vs_stateful_report.md`
- `outputs/reports/toolsandbox_subset_stateless_vs_stateful_report.md`
- `outputs/metrics/toolsandbox_subset_stateless_vs_stateful_summary.json`
- `outputs/cases/toolsandbox_comparison_subset_cases.jsonl`

## 5. 实验结果

### 5.1 Synthetic 9-case benchmark

```text
Total cases: 9
Stateful success rate: 88.24%
Stateless success rate: 100.00%
Stateful recovery rate: 100.00%
Stateless recovery rate: 0.00%
Stateful average steps: 3.78
Stateless average steps: 2.44
Stateful final state correctness: 100.00%
Stateless final state correctness: 100.00%
```

解释：

- 两者最终状态都是 100% 正确。
- Stateful 的 call-level success rate 更低，是因为它暴露了真实环境中应该失败的中间调用。
- Stateful 的 recovery rate 是 100%，说明失败后可以通过补依赖、修复状态、重试等方式恢复。
- Stateless 没有 recovery，是因为它没有暴露失败机会。
- Stateful 平均轨迹更长，因为它保留了 index、assign、reschedule、retry 等真实步骤。

### 5.2 ToolSandbox 40-case subset

```text
Total cases: 40
Stateful success rate: 96.83%
Stateless success rate: 100.00%
Stateful recovery rate: 100.00%
Stateless recovery rate: 0.00%
Stateful average steps: 3.15
Stateless average steps: 1.50
Stateful final state correctness: 100.00%
Stateless final state correctness: 100.00%
Trajectory divergence: 38 / 40
```

解释：

- ToolSandbox 真实任务子集上也出现了同样现象。
- Stateless 平均只需要 1.50 步，因为它直接执行最终状态操作。
- Stateful 平均需要 3.15 步，因为它保留了搜索、时间转换、外部查询等中间过程。
- 40 条 case 中有 38 条出现 trajectory divergence，说明两种环境不是“结果一样所以过程也一样”。

## 6. 结果说明了什么

实验一的核心结论是：

> final state correctness alone is insufficient for evaluating tool-use agents.

中文解释：

> 只看最终状态正确率，不足以评估工具调用 agent 的真实能力。

因为在两个实验子集里，stateful 和 stateless 都能达到 100% final state correctness，但 trajectory-level 指标明显不同：

- Stateful 暴露中间失败
- Stateful 测到 recovery 行为
- Stateful 保留工具依赖和状态语义
- Stateless 跳过中间依赖
- Stateless 更短、更顺，但更容易高估 agent

## 7. 可写入报告的结论

可以这样总结：

> Across both the synthetic benchmark and the ToolSandbox subset, stateful and stateless environments achieve identical final state correctness, but differ substantially in trajectory-level behavior. Stateful execution exposes dependency management, intermediate failures, recovery behavior, snapshot semantics, and workflow constraints, while the stateless baseline collapses many of these requirements into direct final-state updates. These results show that final state correctness alone is insufficient for evaluating tool-use agents; trajectory-level metrics are necessary to measure whether an agent can operate correctly in realistic stateful tool environments.
