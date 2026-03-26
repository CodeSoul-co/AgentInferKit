# Stateful Tool Environment 改造说明

本文档说明本轮在 `D:\Agent 2\AgentInferKit` 中完成的状态化工具环境改造，重点说明：

- 改了什么
- 为什么这样改
- 改动落在哪些文件
- 当前已经打通到什么程度
- 还有哪些边界和后续建议

---

## 一、改造目标

本轮改造的核心目标不是继续增加工具数量，而是把原来的 mock tool 调用体系，推进为一个可以正式参与实验主路径的 `stateful tool runtime`。

具体来说，目标分成四层：

1. 在 `toolsim` 内部建立稳定的 `WorldState` / `ToolEnvironment` / `StatefulExecutor` 主干。
2. 补齐新的强状态域 `issue-tracker`，验证状态转移、权限、恢复能力和终态评测。
3. 提供一个可复用的 session 级 runtime adapter，让外部入口可以共享状态，而不是每次工具调用重新建环境。
4. 把 stateful runtime 从内部能力接入到正式实验路径，使其不再只是 demo，而是可以通过实验配置实际运行。

---

## 二、总体结果

截至本文档写入时，本项目已经具备以下能力：

- `toolsim` 内部支持 `WorldState`、`ToolEnvironment`、`StatefulExecutor`
- 已有状态域：`file-search`、`calendar`、`issue-tracker`
- 支持 `MockBackend` 与 `SandboxBackend`
- 支持 call-level / state-level / 部分 trajectory-level 评测
- 支持 `custom_agent` 通过可选开关使用 stateful runtime
- 支持 `AgentRunner + ReActStrategy` 通过可选开关使用 stateful runtime
- 支持在正式 `experiments` 配置中指定：
  - `tool_runtime`
  - `tool_backend`
  - `tool_permissions`

这意味着：

对于 `api_calling` 任务，`WorldState` 模式已经进入正式实验主路径，可以作为平台中的正式运行模式使用。

---

## 三、本轮新增与修改内容

### 1. 新增 `issue-tracker` 域

新增文件：

- `src/toolsim/tools/issue_tools.py`

新增工具：

- `issue.create`
- `issue.assign`
- `issue.comment`
- `issue.close`
- `issue.reopen`

该域的设计目标是验证：

- 显式状态转移
- 权限控制
- 策略约束
- 恢复模式
- 终态评测

#### 1.1 Issue 实体模型

主实体类型：

- `issue`
- `issue_comment`

`issue` 主要字段：

- `issue_id`
- `title`
- `description`
- `reporter`
- `assignee`
- `status`
- `resolution`
- `labels`
- `comment_count`
- `created_at`
- `updated_at`
- `closed_at`
- `project_id`

#### 1.2 状态流转

状态集合：

- `open`
- `in_progress`
- `closed`

关键规则：

- `issue.create` 创建后进入 `open`
- `issue.assign` 会把 issue 推进到 `in_progress`
- `issue.close` 需要满足前置规则后进入 `closed`
- `issue.reopen` 可把 `closed` 恢复到 `open`

#### 1.3 策略字段

通过 `state.policies["issue"]` 支持：

- `require_assignee_before_close`
- `allow_comment_on_closed`
- `allow_reopen_closed`
- `read_only_projects`

---

### 2. 扩展默认工具注册表

修改文件：

- `src/toolsim/execution/stateful_executor.py`

改动内容：

- 在 `create_default_tool_registry()` 中加入 `ISSUE_TOOLS`

效果：

- `StatefulExecutor(create_default_tool_registry())` 现在默认即可识别 issue 域工具
- `ExperimentRunner` 等上层模块无需手工额外注册 issue 域

---

### 3. 扩展 toolsim 包导出

修改文件：

- `src/toolsim/tools/__init__.py`
- `src/toolsim/__init__.py`

改动内容：

- 导出 `ISSUE_TOOLS`
- 导出 `IssueCreateTool` / `IssueAssignTool` / `IssueCommentTool` / `IssueCloseTool` / `IssueReopenTool`
- 导出新的 demo builder 和 trajectory pattern 检测函数

效果：

- 外部代码可以通过统一包接口直接访问 issue 域与相关 helper

---

### 4. 扩展 state-level evaluator

修改文件：

- `src/toolsim/evaluators/evaluator.py`

新增 goal type：

- `issue_exists`
- `issue_field_equals`
- `issue_status_is`
- `issue_has_assignee`
- `issue_comment_count_is`

效果：

- issue 域可以像 file-search 和 calendar 一样被纳入终态评测
- `ExperimentRunner(..., goals=...)` 可以直接评估 issue 任务是否成功达成目标

---

### 5. 增加 issue demo builder

修改文件：

- `src/toolsim/runners/experiment_runner.py`

新增 helper：

- `build_issue_tracker_demo_calls()`
- `build_issue_tracker_demo_goals()`

设计思路：

这个 demo 不只是演示“成功流程”，还专门包含了一个恢复模式：

1. `issue.create`
2. `issue.close` 首次失败
3. `issue.assign`
4. `issue.close` 再次成功
5. `issue.comment`

这样能验证：

- 无效调用是否被记录
- 失败后是否进行了恢复
- 最终状态是否达到目标

---

### 6. 扩展 trajectory evaluator

修改文件：

- `src/toolsim/evaluators/trajectory_evaluator.py`

新增字段：

- `issue_close_recovery_detected`

新增检测函数：

- `detect_issue_close_recovery_pattern()`

检测逻辑：

- 先出现一次 `issue.close` 失败
- 随后出现对同一 issue 的成功 `issue.assign`
- 再随后出现对同一 issue 的成功 `issue.close`

效果：

- trajectory 评测现在不仅能分析 file-search 的依赖模式，也能识别 issue 域的“失败后恢复”轨迹

---

### 7. 新增 session 级 stateful runtime adapter

新增目录与文件：

- `src/toolsim/adapters/__init__.py`
- `src/toolsim/adapters/stateful_runtime.py`

核心类型：

- `StatefulToolRuntime`
- `ToolRuntimeResponse`

#### 7.1 设计目的

这个 adapter 的目标是：

让外部调用方不直接操作 `StatefulExecutor + ToolEnvironment + WorldState`，而是只关心：

- session id
- tool id
- parameters
- permissions
- backend

由 adapter 在内部维护：

- session -> `ToolEnvironment`
- session -> `WorldState`
- backend 选择
- 统一返回格式

#### 7.2 主要能力

- `execute_tool_call(session_id, tool_id, parameters, permissions, backend)`
- `get_or_create_environment(session_id, backend)`
- `get_environment(session_id)`
- `reset_session(session_id)`
- `advance_time(session_id, delta)`

#### 7.3 结果意义

这层 adapter 是 stateful runtime 接入外部系统的关键桥梁。

后续无论是：

- `custom_agent`
- `AgentRunner`
- 未来的 API 或 WebUI

都可以通过这层统一接入，而不用分别理解底层 world state 执行细节。

---

### 8. 给 `custom_agent` 增加可选 stateful runtime

修改文件：

- `src/api/custom_agent.py`

新增 session 配置字段：

- `tool_runtime`
- `tool_backend`
- `tool_permissions`

默认值：

- `tool_runtime = legacy`
- `tool_backend = mock`
- `tool_permissions = []`

#### 8.1 `/tool_call` 行为变化

如果 session 配置为：

- `tool_runtime = legacy`

则继续走旧路径：

- `ToolRegistry`
- `MockExecutor`

如果 session 配置为：

- `tool_runtime = stateful`

则改走：

- `StatefulToolRuntime`

#### 8.2 设计原则

这里采用的是“增量接入，不强制替换”的方式：

- 默认仍是 legacy
- stateful 通过 session 级显式配置启用

这样不会破坏已有 agent 使用方式，但新路径已经可用。

---

### 9. 给 `AgentRunner` 与 `ReActStrategy` 增加可选 stateful runtime

修改文件：

- `src/runners/agent_runner.py`
- `src/strategies/react.py`

#### 9.1 AgentRunner 的改动

`AgentRunner` 现在会读取 runtime 相关配置：

- `tool_runtime`
- `tool_backend`
- `tool_permissions`

并在执行 `react` 策略时，把这些配置传递给 `ReActStrategy.run_react_loop()`。

#### 9.2 ReActStrategy 的改动

`run_react_loop()` 现在支持新参数：

- `tool_runtime`
- `tool_backend`
- `tool_permissions`
- `session_id`
- `stateful_runtime`

执行逻辑变为双路径：

1. `legacy`
   - 继续使用 `MockExecutor`
2. `stateful`
   - 使用 `StatefulToolRuntime`
   - 共享 session 级状态
   - tool trace 中记录 runtime 类型和更丰富的执行信息

#### 9.3 设计结果

这一步完成后，stateful runtime 不再只存在于：

- toolsim demo
- custom agent 接口

它已经进入 `AgentRunner + ReActStrategy` 的正式执行路径中。

---

### 10. 把 stateful runtime 接入正式 `experiments` 配置

修改文件：

- `src/api/schemas.py`
- `src/api/experiments.py`
- `src/runners/agent_runner.py`

#### 10.1 新增 RunnerConfig 字段

在 `RunnerConfig` 中新增：

- `tool_runtime: Literal["legacy", "stateful"]`
- `tool_backend: Literal["mock", "sandbox"]`
- `tool_permissions: List[str]`

#### 10.2 experiments -> AgentRunner 传递链路

`experiments.py` 在创建 `AgentRunner` 时，开始显式传递：

- `runner_config=exp.get("runner", {})`

而 `AgentRunner` 现在优先读取 `runner_config` 来确定 stateful runtime 行为。

#### 10.3 这一步的意义

这是本轮最关键的一步。

因为它意味着：

stateful runtime 已经从“底层能力”进入“正式实验配置层”。

换句话说，`api_calling` 任务现在已经可以通过正式实验配置来启用 `WorldState` 模式，而不只是靠内部 demo 或手工调用。

---

### 11. 增加兼容 shim，修复旧 import 路径

新增文件：

- `src/toolsim/executor.py`
- `src/toolsim/registry.py`
- `src/toolsim/tracer.py`

作用：

- 为仓库中仍然使用旧 import 路径的代码提供兼容层

例如旧代码还可能写：

- `from src.toolsim.executor import MockExecutor`
- `from src.toolsim.registry import ToolRegistry`

而当前真实实现已经移动到：

- `toolsim.legacy.executor`
- `toolsim.core.registry`
- `toolsim.legacy.tracer`

这些 shim 的作用是避免旧路径立刻全部崩掉，为后续逐步清理留缓冲空间。

---

## 四、本轮新增或修改的主要文件

### 新增文件

- `src/toolsim/tools/issue_tools.py`
- `src/toolsim/adapters/__init__.py`
- `src/toolsim/adapters/stateful_runtime.py`
- `src/toolsim/executor.py`
- `src/toolsim/registry.py`
- `src/toolsim/tracer.py`
- `tests/test_issue_tools.py`
- `tests/test_stateful_runtime.py`
- `tests/test_custom_agent_runtime.py`
- `tests/test_agent_runner_runtime.py`
- `tests/test_experiment_runtime_config.py`

### 修改文件

- `src/toolsim/__init__.py`
- `src/toolsim/tools/__init__.py`
- `src/toolsim/execution/stateful_executor.py`
- `src/toolsim/evaluators/evaluator.py`
- `src/toolsim/evaluators/trajectory_evaluator.py`
- `src/toolsim/runners/experiment_runner.py`
- `src/api/custom_agent.py`
- `src/api/schemas.py`
- `src/api/experiments.py`
- `src/runners/agent_runner.py`
- `src/strategies/react.py`
- `tests/test_evaluator.py`
- `tests/test_experiment_runner.py`
- `tests/test_trajectory_evaluator.py`

---

## 五、测试与验证

本轮改动采用了分阶段 focused test 的方式验证，而不是一次性跑全仓测试。

### 1. issue 域与 evaluator / runner 验证

执行过：

```powershell
conda activate benchmark
$env:PYTHONPATH='D:\Agent 2\AgentInferKit'
pytest tests/test_issue_tools.py tests/test_evaluator.py tests/test_experiment_runner.py -q
```

结果：

- `32 passed`

### 2. issue demo / trajectory / runtime adapter 验证

执行过：

```powershell
conda activate benchmark
$env:PYTHONPATH='D:\Agent 2\AgentInferKit'
pytest tests/test_stateful_runtime.py tests/test_trajectory_evaluator.py tests/test_experiment_runner.py -q
```

结果：

- `25 passed`

### 3. custom_agent stateful runtime 验证

执行过：

```powershell
conda activate benchmark
$env:PYTHONPATH='D:\Agent 2\AgentInferKit'
pytest tests/test_custom_agent_runtime.py -q
```

结果：

- `2 passed`

### 4. AgentRunner + custom_agent runtime switch 验证

执行过：

```powershell
conda activate benchmark
$env:PYTHONPATH='D:\Agent 2\AgentInferKit'
pytest tests/test_agent_runner_runtime.py tests/test_custom_agent_runtime.py -q
```

结果：

- `3 passed`

### 5. experiments 正式配置层验证

执行过：

```powershell
conda activate benchmark
$env:PYTHONPATH='D:\Agent 2\AgentInferKit'
pytest tests/test_experiment_runtime_config.py tests/test_agent_runner_runtime.py tests/test_custom_agent_runtime.py -q
```

结果：

- `5 passed`

---

## 六、当前可以怎么使用

### 1. 在 toolsim 内部直接运行

可以直接使用：

- `StatefulExecutor(create_default_tool_registry())`
- `ExperimentRunner(...)`

来运行：

- file-search
- calendar
- issue-tracker

### 2. 在 custom_agent 接口中启用 stateful runtime

创建 session 时指定：

- `tool_runtime = stateful`
- `tool_backend = mock` 或 `sandbox`
- `tool_permissions = [...]`

之后 `/tool_call` 会自动共享 session 对应的 `WorldState`。

### 3. 在正式 experiments 配置中启用 stateful runtime

对 `api_calling` 实验，在 `runner` 配置中指定：

- `tool_runtime`
- `tool_backend`
- `tool_permissions`

这样 `AgentRunner + ReActStrategy` 就会走 stateful runtime。

---

## 七、当前边界与未完成项

虽然 stateful runtime 已经进入正式实验主路径，但仍有一些增强项尚未完成。

### 1. 还未完成的计划项

- `LiveBackend`
- fault injection 模块
- observation shaping 模块
- 更完整的 trajectory / agent-level 指标
- WebUI 对 stateful 结果的专门展示

### 2. 当前的“正式可用”含义

目前可以说：

对于 `api_calling` 主实验路径，`WorldState` / stateful runtime 已经正式可用。

但这不等于：

- 全部入口都默认切到 stateful
- 全平台所有增强能力都已经完工

更准确地说：

stateful runtime 已经是平台中的正式运行模式之一，但还不是系统最终完整形态。

---

## 八、后续建议

建议下一阶段重点做下面三件事中的一到两件：

### 方案 A：继续强化实验研究价值

优先做：

- faults
- observation shaping
- richer trajectory metrics
- recovery rate / invalid transition / state corruption 等指标

适合论文主线推进。

### 方案 B：继续强化平台产品化可用性

优先做：

- experiments API 返回更明确的 runtime 信息
- 结果页展示 stateful trace / backend / state hash / effects
- WebUI 暴露 `tool_runtime` / `tool_backend` / `tool_permissions`

适合平台落地与可视化。

### 方案 C：继续扩展工具域

优先做：

- issue search/filter
- comment query
- 更复杂的 issue workflow
- sandbox persistence

适合补充更丰富的 benchmark 任务。

---

## 九、一句话总结

本轮改造已经把 `WorldState` 模式从 `toolsim` 内部能力，推进成了可以通过正式实验配置启用的 `api_calling` 运行模式；并以 `issue-tracker` 域、session runtime adapter、custom_agent 接入、AgentRunner 接入和 experiments 配置接入，完成了这条主链路的打通。
