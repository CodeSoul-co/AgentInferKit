# AgentInferKit 项目阶段进展

## 一、Stateful 工具环境系统建设进展

本项目目前完成的核心工作，是把原本更接近“工具调用模拟器”的工具层，扩展成一个具有共享状态、状态转移、跨工具依赖、环境扰动、轨迹记录和最终状态评估能力的 stateful tool environment。也就是说，当前系统不只是判断某一次工具调用参数是否正确，而是能够模拟一个持续变化的外部世界：工具调用会读写同一个 `WorldState`，后续工具会受到前面调用结果的影响，环境可以产生延迟副作用或故障，最终评价也不只看最后一句回答，而是检查世界状态是否真的被修改到目标状态。

工具环境应包含共享世界状态、状态转移、工具间依赖、副作用、异步更新、扰动注入、快照回滚、轨迹复现、不同后端和多粒度评估。目前代码中已经形成了一套比较完整的实现，主要分布在 `src/toolsim/core`、`src/toolsim/execution`、`src/toolsim/backends`、`src/toolsim/tools`、`src/toolsim/faults`、`src/toolsim/evaluation`、`src/toolsim/reporting` 等模块中。

### 1.1 共享世界状态：WorldState

系统的核心状态对象是 `WorldState`，位于 `src/toolsim/core/world_state.py`。它把环境状态抽象成几个部分：

| 状态部分 | 作用 |
|:--|---|
| `entities` | 存储文件、搜索索引、日历事件、issue、联系人、消息、设备设置等实体。 |
| `relations` | 预留实体之间的关系表达，例如依赖关系、归属关系。 |
| `resources` | 预留资源类状态，例如额度、外部资源句柄、环境资源。 |
| `policies` | 存储权限、阻塞动作、只读日历、只读项目等策略规则。 |
| `clock` | 模拟环境时间，用于触发延迟副作用。 |
| `version` | 状态版本号，每次实体或状态变化后递增。 |
| `pending_effects` | 存储尚未触发的异步副作用，例如文件写入后延迟重建搜索索引。 |

这一设计让工具调用不再是孤立函数，而是发生在一个可演化的世界中。比如 `file.write` 写入文件后会改变 `file` 实体，`search.query` 不是直接读文件内容，而是读取 `search_index`；如果中间没有 `search.index` 或延迟 reindex 没有完成，搜索就可能失败或返回旧结果。这个机制是后续四个实验的基础。

`WorldState` 还实现了序列化、反序列化、稳定哈希、快照、回滚等能力。状态哈希用于判断一次调用前后状态是否改变；快照和回滚用于实验复现、后端迁移和错误恢复。代码中 `create_snapshot`、`rollback_to`、`stable_hash` 等能力已经可以支撑 case 级复现。

### 1.2 工具抽象：ToolSpec、ExecutionContext 与 ToolExecutionResult

工具定义集中在 `src/toolsim/core/tool_spec.py`。每个工具不只是一个普通函数，而是一个带元数据、前置条件、后置条件和状态访问逻辑的 `ToolSpec`。

| 抽象 | 当前作用 |
|---|---|
| `ToolMetadata` | 记录工具名、版本、描述、是否 stateful、是否会修改状态、权限需求、超时时间等。 |
| `PreconditionSpec` | 描述调用前必须满足的条件，例如事件必须存在、issue 必须先分配负责人。 |
| `PostconditionSpec` | 描述调用后应该满足的状态，例如文件实体存在、状态哈希改变、issue 状态变为 closed。 |
| `ExecutionContext` | 把当前状态、调用 id、环境时间、权限、后端、重试次数等传给工具实现。 |
| `ToolExecutionResult` | 统一表示成功、失败、部分成功、异步 pending、观察结果、错误信息和待调度副作用。 |

这套抽象的意义是：工具调用可以被统一执行、统一记录、统一评估。它也让系统可以区分“工具函数返回成功”和“最终状态真的正确”这两件事。例如一个工具调用可能返回了 observation，但没有产生预期状态变化；也可能因为故障注入出现 timeout，但重试后最终状态正确。

### 1.3 StatefulExecutor：有状态执行入口

`src/toolsim/execution/stateful_executor.py` 中的 `StatefulExecutor` 是当前系统的执行核心。它负责把一次工具调用完整包起来：

1. 调用前让环境推进时间并应用已经到期的副作用。
2. 记录调用前状态哈希和状态快照。
3. 查找工具注册表，判断工具是否存在。
4. 构造 `ExecutionContext` 并执行工具函数。
5. 根据配置注入 timeout、schema drift、stale observation、vague observation 等扰动。
6. 把工具返回的副作用加入 `pending_effects`。
7. 调用后再次推进环境，应用可触发副作用。
8. 检查后置条件。
9. 记录完整 `ExecutionRecord`，包括 observation、error、状态前后快照、状态哈希、后端名、耗时、重试次数、应用的副作用等。

这意味着目前系统已经具备“可追踪的有状态执行”。每一条轨迹不仅知道调用了什么工具，也知道状态怎么变、是否变、为什么失败、是否触发副作用。这对于做 agent benchmark 很重要，因为传统 stateless benchmark 往往只能看到最后答案，不能解释工具调用在环境中到底造成了什么。

### 1.4 ToolEnvironment 与副作用调度

`src/toolsim/core/environment.py` 提供 `ToolEnvironment`，用于组合 `WorldState`、backend 和 `SideEffectScheduler`。它的作用是把世界状态和执行环境行为分开：执行器负责调用工具，环境负责时间推进、ready effects 应用、快照和回滚。

`src/toolsim/core/side_effects.py` 实现了副作用调度器。目前最典型的副作用是文件写入后的搜索索引更新。系统支持把某个 effect 安排在未来某个 `execute_after` 时间点执行，当环境时间推进后再应用。这让我们能够模拟真实系统里常见的异步可见性问题：文件已经写入，但搜索系统还没更新；issue 已经改变，但某些查询结果还停留在旧状态；后续工具必须理解这种延迟，不能假设所有状态立即一致。

### 1.5 多后端设计：mock、sandbox、live-like

项目已经实现了三类后端，代码在 `src/toolsim/backends`：

| 后端 | 实现文件 | 当前能力 |
|---|---|---|
| `MockBackend` | `mock_backend.py` | 完全内存中的状态读写，速度快、确定性强，适合单元测试和合成实验。 |
| `SandboxBackend` | `sandbox_backend.py` | 在隔离 session 中运行，会把文件和搜索索引写入 `tmp/toolsim_sandbox/...` 下的真实 artifact，更接近真实文件系统。 |
| `LiveLikeBackend` | `live_like_backend.py` | 基于 sandbox，但叠加 live-like 的延迟和故障，用于模拟真实 API 或真实服务的不稳定性。 |

这个设计已经回答了项目文档中“mock/sandbox/live backend 分层”的第一步。当前 live-like 还不是接入真实第三方 API，而是一个带故障和延迟的拟真后端；但接口层已经为以后接真实 API 留出了位置。

### 1.6 已实现工具域

当前系统已经实现了多个工具域，不只是单一 toy tool。

| 工具域 | 代表工具 | Stateful 行为 |
|---|---|---|
| 文件工具 | `file.write`、`file.read` | 写入和读取文件实体，维护 revision、metadata、updated_at，并可写入 sandbox 文件 artifact。 |
| 搜索工具 | `search.index`、`search.query` | 搜索只读取索引状态，不直接读取最新文件内容，因此可以制造 index stale、query before index 等依赖。 |
| 日历工具 | `calendar.create_event`、`calendar.search_events`、`calendar.update_event`、`calendar.delete_event` | 维护日历事件，检测时间重叠和参与者冲突，支持只读 calendar 策略。 |
| Issue 工具 | `issue.create`、`issue.assign`、`issue.comment`、`issue.close`、`issue.reopen` | 维护 issue 生命周期，例如 close 前必须 assign，reopen 前必须处于 closed 状态。 |
| ToolSandbox 工具 | `add_contact`、`modify_contact`、`search_contacts`、`send_message_with_phone_number`、`set_cellular_service_status` 等 | 把 ToolSandbox 的联系人、消息、提醒、设备设置等任务转成统一的 `WorldState` 实体和目标状态。 |

其中 ToolSandbox 接入非常关键。项目并没有只停留在合成 case，而是把真实 benchmark 中的任务转换为本项目自己的 stateful 执行和评估格式。比如联系人添加、根据最近消息修改联系人、按电话号码删除联系人、发送消息、修改设备设置等，都已经被转成 `WorldState` 初始状态、oracle tool calls 和 final state goals。

### 1.7 故障注入与 observation 污染

`src/toolsim/faults/injector.py` 中实现了 `FaultInjector` 和 `FaultProfile`。当前支持的扰动包括：

| 扰动类型 | 作用 |
|---|---|
| `timeout` | 在调用前模拟超时失败。 |
| `schema_drift` | 模拟工具 schema 变化，导致原参数格式不再可用。 |
| `stale_state` / stale observation | 返回旧 observation，使 agent 以为状态还停留在过去。 |
| `vague_observation` | 返回模糊或不完整 observation，使 agent 无法精确判断状态。 |
| `misleading_observation` | 返回误导性 observation，用于更强的 policy-level 噪声测试。 |
| latency | 模拟 live-like 环境中的调用延迟。 |

这一部分使环境从“确定性模拟器”变成“可控扰动环境”。实验三和实验四都依赖这一能力。

### 1.8 评估、轨迹分析与报告输出

评估模块主要在 `src/toolsim/evaluation`：

| 模块 | 功能 |
|---|---|
| `evaluator.py` | 计算调用级指标和状态级指标，如 success rate、invalid call rate、final state correctness。 |
| `trajectory_evaluator.py` | 分析轨迹模式，如 query-before-index、explicit dependency resolution、issue close recovery、calendar conflict recovery。 |
| `overview_summary.py` | 聚合 stateful/stateless 对比指标，如 recovery rate、trajectory length、final state correctness。 |

报告模块包括 `src/toolsim/reporting/trace_report.py` 和多个实验 runner 的报告生成逻辑。当前输出已经整理到 `outputs/cases`、`outputs/metrics`、`outputs/reports`、`outputs/figures` 等子目录.

### 1.9 当前 stateful 系统本身的完成度

总体来看，stateful 工具环境系统已经完成了一个可运行、可复现、可扩展的原型。它的核心价值不在于某个单独工具，而在于建立了统一的 stateful execution abstraction：工具读写共享状态，状态变化可追踪，环境可注入扰动，后端可切换，最终结果可通过状态目标自动评估。

但系统本身仍有几个需要继续完善的地方。第一，live-like 后端目前仍是模拟真实 API 行为，还没有真正接入外部服务；第二，异步、副作用和并发冲突目前主要集中在搜索索引和少量 workflow 规则上，还可以进一步增加真实系统中的 eventually consistent、partial commit、permission race 等行为；第三，当前 token cost 主要用 trajectory length 或额外调用数近似，还没有接入真实 LLM token 统计；第四，τ-bench 和 API-Bank 还没有系统接入，目前真实 benchmark 主要是 ToolSandbox。

## 二、实验一：Stateful vs Stateless 对比实验

### 2.1 实验目的

实验一要回答的问题是：在工具调用 benchmark 中，引入 stateful 环境到底改变了什么？换句话说，如果 stateless baseline 只按单次调用或最终 oracle 判断任务是否完成，它是否会高估 agent 的能力？stateful 环境是否能暴露出跨调用状态依赖、恢复行为和轨迹差异？

这个实验不是单纯追求哪一组成功率更高，而是比较两种评估范式的差异：

- stateless：工具调用更像独立函数，后续调用可以直接看到理想化的结果。
- stateful：工具调用必须经过共享状态，后续调用只能看到当前世界状态，缺少中间动作会导致状态目标不满足。

因此实验一重点看 `success rate`、`invalid call rate`、`recovery rate`、`trajectory length`、`final state correctness` 和 `trajectory divergence`。

### 2.2 实验使用的数据

实验一使用了两类数据。

第一类是合成 case，由 `src/toolsim/experiments/comparison_runner.py` 中的 `build_stateless_vs_stateful_cases` 构造。这些 case 专门覆盖 stateful 环境中常见的状态依赖。例如：

| 示例 | 任务含义 | Stateful 难点 |
|---|---|---|
| `write_then_query` | 写入文件后搜索内容。 | 如果没有显式索引，搜索无法命中新文件。 |
| `overwrite_without_reindex` | 覆盖文件后再次搜索。 | 搜索索引可能仍是旧内容，必须重新 index。 |
| `issue_close_requires_assignment` | 关闭 issue。 | issue 必须先 assign 才能 close。 |
| `calendar_conflict_requires_reschedule` | 创建日历事件。 | 时间和参与者冲突会导致创建失败，需要调整时间。 |

第二类是 ToolSandbox subset case，由 `outputs/cases/toolsandbox_comparison_subset_cases.jsonl` 保存，来源于 ToolSandbox 转换器和 subset selection 逻辑。抽样时覆盖了联系人、消息、设备设置等不同类别。实际案例包括：

| 示例 | 用户请求 | 工具链/目标 |
|---|---|---|
| `add_contact_with_name_and_phone_number` | “Add Stephen Sondheim to my contact, his phone_number is +19876543210” | 调用 `add_contact`，最终 `contact` 中存在对应姓名和电话，并向用户结束对话。 |
| `modify_contact_with_message_recency_alt` | “Find whoever I contacted last, change his cell to +10293847563.” | 需要 `get_current_timestamp`、`search_contacts`、`search_messages`、`modify_contact`，最终修改最近联系人的号码。 |
| `remove_contact_by_phone_ambiguous_alt` | “Get rid of +12453344098” | 先 `search_contacts` 定位联系人，再 `remove_contact`，最终该联系人记录不存在。 |

这些 ToolSandbox case 的意义在于：它们不是人为构造的单一文件搜索问题，而是来自更真实的移动设备/个人助理任务，包含联系人、消息、设置和自然语言歧义。

### 2.3 实验过程

实验一的核心 runner 是 `ComparisonRunner`。实验流程如下：

1. 构造或读取 case。合成 case 由脚本生成，ToolSandbox case 由转换器转为统一格式，包含 `initial_state`、`oracle_tool_calls` 和 `goals`。
2. 对每个 case 分别运行 stateful 轨迹和 stateless 轨迹。stateful 轨迹通过 `StatefulExecutor` 执行真实状态变化；stateless 轨迹会压缩或理想化部分中间状态，使其更接近传统 benchmark 的评估方式。
3. 每条轨迹执行后，用 `CallLevelEvaluator` 统计工具调用成功率、失败率、invalid call 等调用级指标。
4. 用 `StateLevelEvaluator` 检查最终状态是否满足目标。例如文件是否存在、搜索是否命中、issue 状态是否正确、ToolSandbox contact/message/setting 是否达到目标。
5. 用 `TrajectoryEvaluator` 分析轨迹是否出现恢复行为和状态依赖行为，例如 query-before-index、issue close recovery、calendar conflict recovery。
6. 聚合输出到 `outputs/reports/stateless_vs_stateful_report.md`、`outputs/reports/toolsandbox_subset_stateless_vs_stateful_report.md` 和对应 metrics 文件。

这个过程的关键点是：实验不是只看工具调用返回值，而是检查最终 `WorldState`。这使得“看似调用成功但状态不正确”的问题能够被发现。

### 2.4 实验结果

| Dataset | Mode | Cases | Success Rate | Invalid Call Rate | Recovery Rate | Avg. Trajectory Length | Final State Correctness | Trajectory Divergence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Synthetic | Stateful | 9 | 88.2% | - | 100.0% | 3.78 | 100.0% | - |
| Synthetic | Stateless | 9 | 100.0% | - | 0.0% | 2.44 | 100.0% | - |
| ToolSandbox Subset | Stateful | 40 | 96.8% | 0.0% | 100.0% | 3.15 | 100.0% | 38/40 |
| ToolSandbox Subset | Stateless | 40 | 100.0% | 0.0% | 0.0% | 1.50 | 100.0% | 38/40 |

### 2.5 实验结论

实验一说明，stateless 评估确实会把很多状态依赖“抹平”。在 stateless 模式下，任务更容易被压缩成较短轨迹，因此 success rate 往往更高、trajectory length 更短。但这并不意味着 agent 真的理解了环境状态，只是评估方式没有要求它显式处理状态转移。

stateful 模式下，轨迹更长，恢复率显著更高，说明 agent 或预设策略必须处理失败、冲突、过期索引、前置条件等问题。ToolSandbox subset 中 38/40 个 case 出现 stateful/stateless 轨迹差异，这说明即使是看似简单的联系人、消息、设置任务，引入状态环境后也会改变评估对象。

### 2.6 当前不足与下一步

实验一目前仍有三个不足。第一，虽然已经接入 ToolSandbox，但运行轨迹主要来自 oracle 或规则化策略，还不是由真实 LLM 自主生成。第二，stateless baseline 是项目内定义的压缩/理想化 baseline，后续可以加入更多已有 benchmark 的原生 stateless evaluator 作为对照。第三，合成 case 虽然能精准验证机制，但数量和自然语言多样性有限。

下一步建议：选取 20-50 个 ToolSandbox case，用真实 LLM API 生成工具调用轨迹，再分别放入 stateless 和 stateful evaluator 中评估；同时记录 token cost、错误类型和 case-level failure analysis。这样实验一会更能说明“真实 agent 在 stateful 环境中会遇到什么问题”。

## 三、实验二：Cross-tool Dependency 难度曲线

### 3.1 实验目的

实验二要回答的问题是：当任务从单工具无状态，逐步升级到双工具显式依赖、多工具隐式副作用依赖时，不同推理策略的性能会如何退化？

项目把任务复杂度分成三层：

| 难度层级 | 含义 |
|---|---|
| Level 1：单工具无状态 | 一个工具调用即可完成目标，基本不需要跨工具依赖。 |
| Level 2：双工具显式依赖 | 后一个工具显式依赖前一个工具的结果，例如先搜索再修改。 |
| Level 3：多工具隐式副作用依赖 | 需要理解环境副作用或隐式状态，例如写文件后索引延迟、关闭 issue 前必须 assign、日历冲突后 reschedule。 |

对比的策略包括 `direct`、`cot`、`react`、`self_refine`。实验重点不是比较 prompt 文本，而是比较不同“推理/恢复策略模板”在依赖变复杂时的退化趋势。

### 3.2 实验使用的数据

实验二同样使用合成 case 和 ToolSandbox dependency subset。

合成 case 由 `src/toolsim/experiments/dependency_curve.py` 中的 `build_synthetic_dependency_curve_cases` 构造。例如：

| 示例 | 难度 | 任务含义 |
|---|---|---|
| 单工具文件写入 | Level 1 | 直接 `file.write`，检查文件内容。 |
| 写入-索引-查询 | Level 2 | 需要先写文件，再建立索引，再查询。 |
| issue assign 后 close | Level 3 | 关闭 issue 前必须满足隐式 workflow 条件。 |
| 日历冲突恢复 | Level 3 | 创建事件遇到冲突后，需要根据状态反馈换时间。 |

ToolSandbox dependency subset 存在于 `outputs/cases/toolsandbox_dependency_subset_cases.jsonl`。实际样例包括：

| 示例 | 用户请求 | 难点 |
|---|---|---|
| `add_contact_with_name_and_phone_number` | 添加 Stephen Sondheim 联系人。 | 单工具或低依赖任务，主要验证基础状态写入。 |
| `send_message_with_phone_number_and_content_10_distraction_tools` | 给某手机号发送消息，同时存在 10 个 distractor tools。 | 工具选择干扰强，但最终目标是发送消息记录存在。 |
| `cellular_off` | 关闭 cellular。 | 设备设置状态必须从 true 改成 false。 |

此外，dependency subset 还包含多工具联系人搜索、消息搜索、修改联系人等 case，用于覆盖显式依赖和多步骤依赖。

### 3.3 实验过程

实验二的核心 runner 是 `DependencyCurveRunner`。具体流程如下：

1. 构造 synthetic dependency cases，并从 ToolSandbox 中选择 dependency subset。
2. 使用 `classify_toolsandbox_dependency_level` 等逻辑将 ToolSandbox case 分层到 Level 1、Level 2、Level 3。
3. 为每个策略生成不同工具调用轨迹。`direct` 更短、更少恢复；`cot` 增加一部分中间步骤；`react` 更强调观察后再行动；`self_refine` 更保守，包含更多检查和修正。
4. 用同一 stateful executor 执行这些轨迹，确保不同策略面对的是同一个世界状态和同一套工具规则。
5. 统计每个策略在每个复杂度层级上的 success rate，并计算从 Level 1 到 Level 3 的 performance drop 和 AUC。
6. 生成结果报告和图，包括 `outputs/reports/dependency_curve_synthetic_report.md`、`outputs/reports/dependency_curve_toolsandbox_report.md`、`outputs/figures/exp2_synthetic_success_curve.png`、`outputs/figures/exp2_toolsandbox_success_curve.png`。

### 3.4 实验结果

| Dataset | Strategy | Level 1 Success | Level 2 Success | Level 3 Success | L1-to-L3 Drop | AUC |
|---|---:|---:|---:|---:|---:|---:|
| Synthetic | direct | 100.0% | 20.0% | 0.0% | 100.0 | 0.400 |
| Synthetic | cot | 100.0% | 60.0% | 40.0% | 60.0 | 0.667 |
| Synthetic | react | 100.0% | 100.0% | 80.0% | 20.0 | 0.933 |
| Synthetic | self_refine | 100.0% | 100.0% | 100.0% | 0.0 | 1.000 |
| ToolSandbox | direct | 100.0% | 0.0% | 0.0% | 100.0 | 0.333 |
| ToolSandbox | cot | 100.0% | 100.0% | 12.5% | 87.5 | 0.708 |
| ToolSandbox | react | 100.0% | 100.0% | 50.0% | 50.0 | 0.833 |
| ToolSandbox | self_refine | 100.0% | 100.0% | 100.0% | 0.0 | 1.000 |

### 3.5 实验结论

实验二说明，任务复杂度提升后，策略退化趋势非常明显。`direct` 在 Level 1 表现很好，但一旦进入显式依赖或隐式副作用依赖，成功率快速下降。`cot` 能改善显式依赖，但在 ToolSandbox Level 3 上只剩 12.5%，说明仅仅多一步“思考式”调用并不足以处理隐式环境状态。`react` 在复杂任务上明显更稳，因为它会利用 observation 继续行动。`self_refine` 在当前规则化实验中最强，因为它包含更充分的检查和修正步骤。

这个实验说明，stateful 工具任务的困难是可以被分层刻画，而且难度曲线能够清楚地区分不同推理策略的退化速度。它也说明，未来论文中可以把“跨工具依赖复杂度”作为一个核心实验变量，而不是只报告一个总成功率。

### 3.6 当前不足与下一步

实验二目前最大的不足是策略仍是规则模板，不是真实 LLM 在不同 prompt 下自然生成的轨迹。因此 `self_refine=100%` 更像是上界参考，而不是可直接声称真实模型一定达到的水平。第二，Level 3 的隐式副作用还可以更丰富，目前主要围绕搜索索引、issue workflow、日历冲突和 ToolSandbox 多步骤任务。第三，ToolSandbox 的分层规则还可以更细，例如区分“工具选择干扰”和“状态副作用依赖”。

下一步建议：在同一组 Level 1/2/3 case 上接入真实 LLM，使用 direct、CoT、ReAct、self-refine prompt 真实生成调用轨迹；同时对 Level 3 做 case-level error taxonomy，区分是工具选错、参数错误、状态理解错误，还是恢复失败。

## 四、实验三：Noise Robustness

### 4.1 实验目的

实验三要回答的问题是：stateful 工具环境在 observation 被污染或工具调用出现故障时，agent 的成功率、恢复能力、成本和状态破坏情况会如何变化？

实验关注五个指标：

| 指标 | 含义 |
|---|---|
| `success@1` | 第一次尝试是否直接成功。 |
| `pass^k` | 允许最多 k 次尝试或恢复后是否成功。 |
| `recovery rate` | 失败后是否通过重试或额外动作恢复成功。 |
| `cost increase` | 相比 clean run 增加了多少工具调用。 |
| `state corruption rate` | 最终状态是否被污染或没有达到目标。 |

最初版本使用固定轨迹测试 timeout、schema drift、stale state、vague observation。后来又增强了 agent-policy 版本，使 direct/cot/react/self_refine 在被污染 observation 后继续决策。这个增强很重要，因为 stale state 和 vague observation 只有影响后续决策时，才会真正拉低成功率；否则固定 oracle 轨迹可能会绕过 observation 污染。

### 4.2 实验使用的数据

实验三的数据与实验一保持一致，并在此基础上注入噪声。case 由 `src/toolsim/experiments/fault_robustness.py`、`src/toolsim/experiments/policy_noise_robustness.py` 和脚本 `scripts/run_noise_robustness.py`、`scripts/run_policy_noise_robustness.py` 生成。

实际 case 存在于 `outputs/cases/noise_robustness_cases.jsonl`。示例包括：

| 示例 | 噪声类型 | 任务与扰动 |
|---|---|---|
| `experiment1_synthetic::write_then_query::timeout` | timeout | `file.write` 首次超时，pass^k 轨迹通过重试写文件恢复。 |
| `experiment1_synthetic::write_then_query::schema_drift` | schema drift | `file.write` 首次因参数 schema 变化失败，后续重试验证恢复。 |
| `experiment1_synthetic::write_then_query::stale_state` | stale state | `search.query` 返回旧状态 observation，测试 agent 是否会被误导。 |

policy subset 还扩展到 ToolSandbox，例如联系人添加、消息发送、设备设置等任务，在 observation 被污染后继续决策。

### 4.3 实验过程

实验三分成两个阶段。

第一阶段是 fixed-trajectory robustness。流程是：

1. 从实验一的 synthetic 和 ToolSandbox case 中构造噪声 case。
2. 对每个 case 指定目标工具和噪声类型，例如对 `file.write` 注入 timeout，对 `search.query` 注入 stale observation。
3. 运行 clean trajectory，确认原始任务可成功。
4. 运行 success@1 trajectory，不做恢复，统计第一次尝试是否成功。
5. 运行 pass^k trajectory，在目标调用后插入重试或恢复步骤。
6. 比较 clean、success@1、pass^k 的最终状态，计算恢复率、成本增加和状态污染。

第二阶段是 agent-policy robustness。流程是：

1. 为 `direct`、`cot`、`react`、`self_refine` 设置不同恢复策略。
2. 每一步调用后读取 observation，再由策略决定下一步工具调用。
3. 对 stale、vague、misleading observation 进行更真实的闭环测试，因为错误 observation 会影响下一步决策。
4. 按策略、噪声类型、强度和数据来源聚合指标。

这一阶段的输出包括 `outputs/metrics/noise_robustness_summary.json`、`outputs/metrics/policy_noise_robustness_summary.json`、`outputs/reports/noise_robustness_report.md`、`outputs/reports/policy_noise_robustness_report.md`。

### 4.4 实验结果

| Runner / Strategy | Runs | Success@1 | Pass^k | Recovery Rate | Avg. Cost Increase | State Corruption Rate | Timeout Recovery | Stale Recovery | Vague Recovery | Misleading Recovery |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed trajectory | 136 | 52.9% | 100.0% | 100.0% | 0.50 | 0.0% | 100.0% | 100.0% | 100.0% | N/A |
| Policy direct | 115 | 7.8% | 7.8% | 0.0% | 0.00 | 92.2% | 0.0% | 30.4% | 4.3% | 4.3% |
| Policy cot | 115 | 7.8% | 73.0% | 66.9% | 0.53 | 27.0% | 65.2% | 30.4% | 91.3% | 100.0% |
| Policy react | 115 | 7.8% | 76.5% | 75.6% | 1.20 | 23.5% | 65.2% | 95.7% | 73.9% | 69.6% |
| Policy self_refine | 115 | 7.8% | 86.1% | 85.6% | 0.66 | 13.9% | 65.2% | 95.7% | 91.3% | 100.0% |

### 4.5 实验结论

实验三说明，固定轨迹版本可以验证故障注入和恢复机制是否工作，但说服力有限，因为 oracle 轨迹知道该怎么恢复，所以 pass^k 可以达到 100%。增强后的 policy 版本更有价值：当 observation 污染会影响下一步决策时，direct 策略几乎无法恢复，state corruption rate 高达 92.2%；而 react 和 self_refine 由于会根据 observation 进行检查、重试和修正，pass^k 明显更高，状态污染显著更低。

这个实验说明，stateful 环境下的 robustness 不是只等于“重试一次”。timeout 和 schema drift 可以通过重试缓解，但 stale/vague/misleading observation 会影响 agent 的 belief state，必须通过观察、验证和自我修正来恢复。也就是说，stateful benchmark 可以评估 agent 的错误恢复和抗干扰能力，而不只是评估一次性工具选择。

### 4.6 当前不足与下一步

实验三当前的问题是，policy 仍是手写策略模板，不是真实 LLM 的自然决策；噪声分布也是人为设定的，还没有来自真实 API 日志或真实工具平台的统计分布。其次，cost increase 目前主要用额外调用次数衡量，没有统计真实 token cost 和 wall-clock cost。再次，state corruption 的定义目前偏最终目标状态，未来可以细分为错误写入、重复写入、遗漏写入、误删、不可逆副作用等。

下一步建议：接入真实 LLM，在同样的噪声 case 上运行 direct/CoT/ReAct/self-refine prompt；同时加入更真实的 partial success、delayed visibility、permission denied、rate limit、duplicate operation 等噪声类型，并把成本扩展为 tool call cost、latency cost 和 token cost。

## 五、实验四：Mock/Sandbox/Live-like 后端迁移实验

### 5.1 实验目的

实验四要回答的问题是：同一个 agent 策略在不同真实度的工具后端中是否还能保持稳定？也就是说，从 mock 环境迁移到 sandbox，再迁移到 live-like 环境时，成功率、状态一致性、恢复率和成本会如何变化？

这个实验对应项目文档中的 backend realism 目标。很多工具使用 benchmark 在 mock 环境中表现很好，但真实环境会出现文件系统 artifact、调用延迟、timeout、schema drift、重复调用副作用、状态数据库约束、权限约束、token 校验、外部服务格式漂移等问题。实验四试图刻画这种迁移 gap：如果一个策略只在理想内存环境中被评估，它的鲁棒性是否会被高估？

本轮实验四相较之前有较大升级。此前 `sandbox` 和 `mock` 的差别主要是 session 隔离与 artifact 持久化，因此二者在结果上很接近；现在已经将三层后端重新区分为：`mock` 是 optimistic baseline，会尽量写入目标状态；`sandbox` 是 strict deterministic backend，会严格执行 API-Bank/ToolSandbox 的语义约束但不注入随机故障；`live_like` 则是在 strict runtime 基础上加入数据库持久化、调用延迟、timeout、schema drift 等扰动。因此实验四现在可以同时观察 `mock -> sandbox` 的语义约束迁移，以及 `sandbox -> live_like` 的故障鲁棒性迁移。

### 5.2 实验使用的数据

实验四的数据由 `src/toolsim/runners/backend_migration.py` 和 `scripts/run_backend_migration.py` 构造，输出到 `outputs/cases/backend_migration_cases.jsonl`。当前版本共包含 40 个 case：

| 数据来源 | 数量 | 作用 |
|---|---:|---|
| Synthetic backend cases | 8 | 手工构造的最小可控迁移任务，覆盖 file、settings、contact、search、message，并包含 3 条 semantic recovery probes。 |
| API-Bank backend subset | 20 | API-Bank 本地 runtime case，覆盖 account、agenda、meeting。 |
| ToolSandbox backend subset | 12 | 从 ToolSandbox scenario 转换得到的 benchmark subset，覆盖 contact、message、reminder、utility 等任务。 |

也就是说，实验四当前不是单一 synthetic 实验，而是 synthetic + API-Bank + ToolSandbox 的混合后端迁移实验。每个 case 都会在 `mock`、`sandbox`、`live_like` 三个后端，以及 `direct`、`cot`、`react`、`self_refine` 四种策略下运行，因此总运行数为：

```text
40 cases × 3 backends × 4 strategies = 480 runs
```

API-Bank subset 主要包括：

| 类型 | 涉及 API | 状态行为 |
|---|---|---|
| 账户认证 | `CheckToken`, `GetUserToken` | 校验 token、用户名和密码。 |
| 密码修改 | `ModifyPassword`, `ForgotPassword` | 修改账号密码；忘记密码需要两阶段验证码流程。 |
| 日程 | `AddAgenda`, `QueryAgenda`, `ModifyAgenda` | 新增、查询、修改日程数据库。 |
| 会议 | `AddMeeting`, `QueryMeeting`, `ModifyMeeting` | 新增、查询、修改会议数据库。 |

ToolSandbox subset 接入 official-style local runtime，主要包括：

| 类型 | 涉及工具 | 新增状态约束 |
|---|---|---|
| Settings | `set_wifi_status`, `set_cellular_service_status`, `set_location_service_status`, `set_low_battery_mode_status` | 低电量模式会关闭 cellular/wifi/location，并禁止重新开启。 |
| Contacts | `add_contact`, `modify_contact`, `remove_contact`, `search_contacts` | 校验手机号；self contact 只能有一个；修改/删除不存在 id 会失败。 |
| Messaging | `send_message_with_phone_number`, `search_messages` | 发短信必须 cellular 开启，并且必须存在唯一 self contact。 |
| Reminders | `add_reminder`, `modify_reminder`, `remove_reminder`, `search_reminder` | 校验 timestamp、latitude、longitude；缺失 id 会失败。 |

实际样例包括：

| 示例 | 来源 | 任务与后端扰动 |
|---|---|---|
| `synthetic_backend::file_write` | synthetic | 写入 `mig_file`，live-like 对 `file.write` 注入一次 timeout。 |
| `apibank_backend::forgot_password_persistent_timeout` | API-Bank | 先请求验证码，再用验证码修改密码，目标工具连续 timeout 两次。 |
| `apibank_backend::add_modify_agenda_schema_drift` | API-Bank | 新增日程后修改时间和地点，修改阶段注入 schema drift。 |
| `apibank_backend::preseeded_modify_meeting_persistent_timeout` | API-Bank | 在已有会议记录上修改会议时间，目标工具连续 timeout 两次。 |
| `toolsandbox_backend::add_contact_with_name_and_phone_number` | ToolSandbox | 在联系人数据库中添加联系人，live-like 注入 timeout。 |
| `toolsandbox_backend::search_message_with_recency_latest` | ToolSandbox | 查询短信并完成后续任务，涉及 ToolSandbox sandbox trace 和消息状态。 |
| `synthetic_backend::send_message` | synthetic / ToolSandbox-like | 发送短信，当前 live-like 会检查 cellular 和 self contact 约束。 |

这些 case 的特点是：同一目标会在 mock、sandbox、live-like 三个后端分别运行，比较状态是否一致、是否发生迁移失败、是否需要恢复。

### 5.3 实验过程

实验四的流程如下：

1. 构造 backend migration case，每个 case 包含目标工具、初始状态、目标状态和 live-like fault 配置。
2. 为 `direct`、`cot`、`react`、`self_refine` 生成不同长度和恢复能力的工具调用轨迹。
3. 在 `MockBackend` 中运行，得到理想内存状态下的结果。
4. 在 `SandboxBackend` 中运行，文件等 artifact 会写入真实隔离目录，并检查 artifact-backed 状态是否仍正确。
5. 在 `LiveLikeBackend` 中运行。当前 live-like 不只是注入故障，还会执行 API-Bank 和 ToolSandbox 的本地 stateful runtime，并持久化相关数据库。
6. 比较 sandbox/live-like 与 mock 的状态差异，计算 final state correctness、mock-to-live gap、state divergence、recovery rate、avg trajectory length 和 latency。
7. 生成 `outputs/reports/backend_migration_report.md`，以及 `outputs/figures/exp4_backend_migration_curve.png` 和 `outputs/figures/exp4_backend_migration_gap.png`。

当前 `LiveLikeBackend` 会持久化以下数据库 artifact：

| Runtime | 持久化文件 |
|---|---|
| API-Bank | `Account.json`, `Agenda.json`, `Meeting.json` |
| ToolSandbox | `Setting.json`, `Contact.json`, `Messaging.json`, `Reminder.json`, `Sandbox.json` |

live-like 中使用四种 fault：

| Fault Type | 含义 |
|---|---|
| `timeout` | 目标工具第一次调用 timeout。 |
| `schema_drift` | 目标工具第一次调用发生 schema mismatch。 |
| `persistent_timeout` | 目标工具连续 timeout 两次。 |
| `hard_schema_drift` | 目标工具连续 schema drift 三次。 |

不同策略的恢复预算不同：

| Strategy | 恢复能力设计 |
|---|---|
| `direct` | 不重试，直接执行原始轨迹。 |
| `cot` | 对目标工具增加 1 次重试。 |
| `react` | 对目标工具增加 2 次重试。 |
| `self_refine` | 对目标工具增加 2 次重试，并代表更强的修正式策略上界。 |

### 5.4 实验结果

| Strategy | Mock Correctness | Sandbox Correctness | Live-like Correctness | Mock-to-Live Gap | Live State Divergence | Live Recovery Rate | Avg. Live Steps | Avg. Live Latency (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 100.0% | 92.5% | 0.0% | 100.0% | 100.0% | 0.0% | 2.08 | 9.92 |
| cot | 100.0% | 92.5% | 50.0% | 50.0% | 50.0% | 50.0% | 3.08 | 17.80 |
| react | 100.0% | 100.0% | 85.0% | 15.0% | 15.0% | 85.0% | 4.05 | 26.53 |
| self_refine | 100.0% | 100.0% | 85.0% | 15.0% | 15.0% | 85.0% | 4.05 | 26.35 |

按数据来源拆分，live-like 下的 final correctness 如下：

| Source | direct | cot | react | self_refine |
|---|---:|---:|---:|---:|
| Synthetic backend | 0.0% | 25.0% | 87.5% | 87.5% |
| API-Bank subset | 0.0% | 60.0% | 90.0% | 90.0% |
| ToolSandbox subset | 0.0% | 50.0% | 75.0% | 75.0% |

按故障类型拆分，live-like 下的 final correctness 如下：

| Strategy | timeout | schema_drift | persistent_timeout | hard_schema_drift | semantic_validation |
|---|---:|---:|---:|---:|---:|
| direct | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| cot | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| react | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% |
| self_refine | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% |

### 5.5 实验结论

实验四说明，mock-only evaluation 会明显高估 agent 的部署鲁棒性。`mock` 在当前 40 个 case 上仍然保持 100% final state correctness，但升级后的 strict `sandbox` 已经让 `direct/cot` 降到 92.5%，说明它能够暴露 mock 忽略的真实语义错误，例如错误 old password、修改不存在的 contact、非法时间格式等。与此同时，`react/self_refine` 在 sandbox 中恢复到 100.0%，说明更强策略可以通过补前置步骤或修正参数恢复语义错误。进入 `live_like` 后差距进一步扩大：`direct` 在 live-like 中完全失败，说明没有恢复机制的策略无法承受真实环境常见故障；`cot` 有一定恢复能力，live-like correctness 达到 50.0%，但仍有 50.0% 的 mock-to-live gap；`react` 和 `self_refine` 明显更稳，live-like correctness 达到 85.0%，但代价是更长轨迹和更高延迟。

按故障类型看，结果形成了清晰的难度梯度。`timeout` 和 `schema_drift` 是单次 transient fault，`cot/react/self_refine` 都能恢复；`persistent_timeout` 连续失败两次，`cot` 的一次 retry 不够，只有 `react/self_refine` 能恢复；`hard_schema_drift` 连续失败三次，超过当前所有策略的恢复预算，因此所有策略都失败；这说明实验四不是简单地制造失败，而是构造了能够区分语义正确性和故障恢复能力的后端难度曲线。

更重要的是，本轮新增 API-Bank 和 ToolSandbox runtime 后，实验四的结论不再只基于 synthetic case。API-Bank subset 中包含 token、password、agenda、meeting 等传统 API 状态逻辑；ToolSandbox subset 中包含 cellular/self contact、low battery side effect、contact/reminder missing-id failure 等移动设备式状态约束；synthetic subset 中的 semantic recovery probes 则专门检验 mock 与 strict sandbox 的语义差距。结果表明：即使一个策略在 mock 中 100% 成功，只要进入 strict sandbox 或带真实状态约束和后端扰动的 live-like 环境，策略之间的鲁棒性差异就会显现。

因此，实验四支持的核心结论是：mock-only evaluation 会高估 agent 的部署鲁棒性；strict sandbox 可以作为稳定、可复现的语义约束层；live-like 则进一步评估真实后端故障下的恢复能力。backend realism 应该作为 stateful tool-use benchmark 中独立且必要的评测维度。

### 5.6 当前不足与下一步

实验四目前最大的不足是，`live-like` 虽然已经接入 API-Bank 和 ToolSandbox 的本地 official-style runtime，但仍然是本地 replica，不是真实在线 API。这样做的优点是可复现、可控、便于比较；缺点是还没有真实网络环境中的认证过期、限流、服务端不稳定、真实返回格式漂移和外部状态清理问题。

第二，当前 `direct/cot/react/self_refine` 仍然是规则化轨迹模板，不是真实 LLM 根据 observation 自主决策。因此目前实验四更像是 backend migration 机制验证和策略上界/下界比较，而不是完整的 model evaluation。下一步最有价值的是加入 agent-policy 版本，让真实 LLM 在 live-like observation 下自行决定是否重试、如何改参数、是否换工具。

下一步建议：优先在实验四中加入真实 LLM policy evaluation，再选择一个低风险真实 API 做 pilot，例如 GitHub issue、日历测试账号、Notion/database 或本地 HTTP service。先接 5-10 个 case，不追求大规模，只验证当前 backend abstraction 是否真的能承载真实 API 的鉴权、幂等、回滚、清理和失败恢复。

## 六、总体总结、当前问题与下一步计划

### 6.1 总体进展

目前项目已经完成了一个比较完整的第一阶段：不仅实现了 stateful tool environment 的核心系统，还围绕这个系统完成了四个实验方向。

| 部分 | 当前状态 |
|---|---|
| Stateful 工具环境 | 已实现 `WorldState`、`ToolSpec`、`StatefulExecutor`、`ToolEnvironment`、副作用调度、快照回滚、状态哈希和执行 trace。 |
| 工具域 | 已实现文件、搜索、日历、issue、ToolSandbox 联系人/消息/设置等工具。 |
| 后端 | 已实现 mock、sandbox、live-like 三层后端。 |
| 故障注入 | 已支持 timeout、schema drift、stale observation、vague observation、misleading observation、latency 等。 |
| 评估 | 已支持调用级指标、状态级指标、轨迹分析、恢复检测、final state correctness。 |
| 实验一 | 完成 stateful vs stateless 对比，说明 stateful 评估暴露了传统 stateless 难以捕捉的状态依赖和恢复行为。 |
| 实验二 | 完成 cross-tool dependency 难度曲线，说明任务复杂度提升会让 direct/cot/react/self_refine 产生不同退化趋势。 |
| 实验三 | 完成 noise robustness，并增强为 agent-policy 版本，说明 observation 污染会显著影响闭环决策。 |
| 实验四 | 完成 mock/sandbox/live-like backend migration，说明 mock 成功率不能直接代表 live-like 表现。 |

从研究叙事上看，目前项目已经具备一条比较清楚的主线：先提出 stateful tool environment，再说明它和 stateless benchmark 的区别，然后从依赖复杂度、噪声鲁棒性、后端真实度三个角度系统检验 agent 在 stateful 环境中的能力退化。

### 6.2 目前最主要的问题

第一，真实 LLM API 还没有系统接入。当前四个实验大多使用 oracle trajectory 或规则化策略模板，因此它们更像 benchmark/system validation，而不是完整的 model evaluation。

第二，真实 benchmark 覆盖还不够。ToolSandbox 已经接入并扩展了 subset，这是一个重要进展。但项目文档里还提到 τ-bench、API-Bank，目前尚未完成。后续需要至少再接一个外部 benchmark，以证明框架不是只适配 ToolSandbox。

第三，live-like 后端仍是模拟真实 API。实验四已经说明后端真实度会影响结果，但如果能加入真实 API pilot，项目说服力会明显提高。即使只接 5-10 个真实 API case，也能证明系统的 backend abstraction 有现实可用性。

第四，成本指标还不完整。目前 cost increase 更多是额外工具调用数或轨迹长度，没有真实 token cost、真实 wall-clock latency 和真实 API cost。对于 agent benchmark 来说，成本是重要指标，后续应补齐。

第五，实验结果还需要更细的错误分析。现在表格已经能说明总体趋势，但还需要 case-level failure taxonomy，例如把失败分成工具选择错误、参数错误、状态读取错误、前置条件遗漏、恢复失败、重复副作用、最终状态污染等。

### 6.3 下一步优先级建议

建议下一步按以下顺序推进：

1. 接入真实 LLM API，先不要大规模跑，选择每个实验 10-20 个代表性 case，验证真实模型在 stateful 环境中的行为是否符合当前趋势。
2. 对实验一和实验二做 case-level error analysis，尤其分析 ToolSandbox Level 2/3 中真实 agent 为什么失败。
3. 做一个小规模真实 API backend pilot，优先选择可控、低风险、容易清理状态的 API，例如 GitHub issue 测试仓库或本地 HTTP service。
4. 扩展一个新的外部 benchmark，优先考虑 API-Bank 或 τ-bench 中较容易转换的一部分任务。
5. 完善论文级输出，包括统一总表、统一图、关键 trace 示例、错误类型分布图和系统架构图。
6. 把 cost 指标从“额外调用数”升级为“tool calls + token usage + latency + API failure/retry cost”。
