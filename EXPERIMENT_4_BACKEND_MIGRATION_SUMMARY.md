# 实验四：Backend Migration 详细报告

## 1. 实验目的

实验四关注的问题是：一个工具使用策略如果在理想化的 `mock` 环境中表现很好，它是否能够迁移到更真实的后端环境中继续保持稳定？

前三个实验主要研究的是 stateful 机制、跨工具依赖、噪声鲁棒性；实验四单独把后端真实性作为变量，比较同一批任务在三类后端中的表现：

| Backend | 含义 | 作用 |
|---|---|---|
| `mock` | 乐观 `WorldState` 执行 | 最理想、最快、会尽量写入目标状态 |
| `sandbox` | strict deterministic backend | 无随机故障，但执行 API-Bank/ToolSandbox 的真实语义约束 |
| `live_like` | sandbox + benchmark runtime replica + 故障注入 | 更接近真实 API/工具后端 |

实验要回答的问题不是“哪个策略在 mock 中最高”，而是：

> 当后端从 mock/sandbox 迁移到 live-like 后，策略成功率会下降多少？哪些策略更能恢复？

这也是本实验与前三个实验的核心区别：实验四把 backend realism 作为主要研究对象。

## 2. 本次新增内容

本轮实验四做了三类重要增强：API-Bank runtime 扩展、ToolSandbox official-style runtime 接入，以及 sandbox/backend 层级重构。

### 2.1 新增 API-Bank 本地 runtime

新增文件：

- `src/toolsim/tools/apibank_runtime.py`
- `src/toolsim/tools/apibank_tools.py`

实现内容：

| API-Bank 类型 | 支持 API | 状态行为 |
|---|---|---|
| Account/Auth | `CheckToken`, `GetUserToken` | 检查 token、用户名和密码 |
| Password | `ModifyPassword`, `ForgotPassword` | 修改账号密码；忘记密码需要两阶段验证码流程 |
| Agenda | `AddAgenda`, `QueryAgenda`, `ModifyAgenda` | 新增、查询、修改日程数据库 |
| Meeting | `AddMeeting`, `QueryMeeting`, `ModifyMeeting` | 新增、查询、修改会议数据库 |

其中 `ForgotPassword` 是一个典型的 stateful API：

1. 第一次调用 `ForgotPassword(status="Forgot Password")`；
2. 系统检查 `username + email`；
3. 后端写入 `password_reset.current`；
4. 返回验证码 `970420`；
5. 第二次调用 `ForgotPassword(status="Verification Code")`；
6. 系统检查验证码；
7. 修改 `account.foo.password`；
8. 标记 reset session 已消费。

这使 API-Bank case 不再是简单单步工具调用，而是带有中间状态和副作用的多步 API workflow。

### 2.2 新增 ToolSandbox official-style runtime

新增文件：

- `src/toolsim/tools/toolsandbox_runtime.py`

重写/扩展文件：

- `src/toolsim/tools/toolsandbox_tools.py`
- `src/toolsim/adapters/toolsandbox_adapter.py`

此前项目里已经有一套 `toolsandbox_tools.py`，但它是轻量兼容层，很多行为比较宽松。例如：

- `modify_contact` 找不到联系人时会自动创建；
- `send_message_with_phone_number` 不检查 cellular；
- `set_low_battery_mode_status` 不会影响 wifi/cellular/location；
- reminder/contact 缺少官方式校验。

本轮将其改成更接近官方 ToolSandbox 的本地 runtime。

新增 ToolSandbox 语义如下：

| 模块 | 新增 official-style 行为 |
|---|---|
| Setting | `low_battery_mode=True` 会关闭 `cellular/wifi/location_service`；低电量模式下不能重新开启这些服务 |
| Contact | 校验 phone number；`is_self=True` 的联系人只能有一个；修改/删除不存在的联系人会失败 |
| Messaging | 发送短信必须 cellular 开启；必须存在且仅存在一个 self contact；消息会记录 sender/recipient 信息 |
| Reminder | 校验 timestamp/latitude/longitude；修改/删除不存在的 reminder 会失败；search 支持内容和时间范围过滤 |
| Sandbox | 工具调用会写入 sandbox trace 记录，用于 milestone/evaluator 检查 |

这一步非常关键，因为 ToolSandbox 的核心价值就在于 stateful world state 和隐式依赖。现在 live-like 中的 ToolSandbox subset 不再只是宽松模拟，而是包含真实状态约束。

### 2.3 重构 mock/sandbox/live-like 三层语义

修改文件：

- `src/toolsim/backends/mock_backend.py`
- `src/toolsim/backends/sandbox_backend.py`
- `src/toolsim/backends/live_like_backend.py`

此前 `sandbox` 与 `mock` 的差别主要是 session 隔离和 artifact 持久化，因此在实验四中二者最终正确率几乎完全相同。现在三层后端被重新定义为：

| Backend | 当前语义 |
|---|---|
| `mock` | optimistic baseline。API-Bank/ToolSandbox 调用尽量直接写入目标状态，不严格检查 token、old password、缺失 contact、非法时间等约束 |
| `sandbox` | strict deterministic simulator。复用 API-Bank 和 ToolSandbox runtime，严格检查认证、参数格式、前置状态、副作用约束，但不注入 timeout/schema drift |
| `live_like` | strict runtime + session database persistence + fault injection。用于模拟更接近真实部署的后端迁移压力 |

同时在 synthetic backend cases 中新增了 3 条 semantic recovery probes，用来测试 mock 与 strict sandbox 的差异，以及更强策略是否能通过修复轨迹恢复：

| Case | direct/cot | react/self_refine |
|---|---|---|
| `semantic_modify_password_recovery` | 重复错误 `old_password`，strict backend 失败 | 获取有效上下文后用正确 `old_password` 修改 |
| `semantic_modify_missing_contact_recovery` | 重复修改不存在 contact，strict backend 失败 | 先 `add_contact`，再 `modify_contact` |
| `semantic_add_agenda_time_recovery` | 重复非法时间格式，strict backend 失败 | 修复为 `%Y-%m-%d %H:%M:%S` 时间格式 |

这一步解决了“sandbox 看起来像 mock”的问题，使实验四能同时观察两个迁移阶段：

```text
mock -> sandbox: 语义约束迁移
sandbox -> live-like: 故障鲁棒性迁移
```

### 2.4 扩展 live-like 后端

修改文件：

- `src/toolsim/backends/live_like_backend.py`

当前 `live_like` 后端会同时支持：

| Runtime | 数据库 |
|---|---|
| API-Bank runtime | `Account`, `Agenda`, `Meeting` |
| ToolSandbox runtime | `Setting`, `Contact`, `Messaging`, `Reminder`, `Sandbox` |

并将这些数据库持久化为 session artifact：

| 数据库 | 持久化文件 |
|---|---|
| Account | `Account.json` |
| Agenda | `Agenda.json` |
| Meeting | `Meeting.json` |
| Setting | `Setting.json` |
| Contact | `Contact.json` |
| Messaging | `Messaging.json` |
| Reminder | `Reminder.json` |
| Sandbox | `Sandbox.json` |

所以现在的 `live_like` 环境不是简单的 timeout 模拟，而是：

> sandbox 隔离 + API-Bank 本地官方逻辑 replica + ToolSandbox official-style 本地 runtime + 故障注入。

### 2.5 修正 ToolSandbox adapter

修改文件：

- `src/toolsim/adapters/toolsandbox_adapter.py`

ToolSandbox 导出的 scenario metadata 中有 milestone target，但不一定完整保存官方 base database。为了让 strict runtime 能执行 update/remove 类任务，本轮 adapter 新增了初始记录恢复逻辑：

- 对 `update_similarity` / `removal_similarity` milestone 中出现的 contact/reminder id 进行预置；
- 给 ToolSandbox 初始状态补默认 device settings；
- 补唯一 self contact，满足官方 messaging 工具约束。

这样可以在不放松 runtime 的前提下，让转换后的 ToolSandbox case 更接近官方场景。

## 3. 数据集设置

当前实验四共使用 40 个 case：

| 数据来源 | 数量 | 说明 |
|---|---:|---|
| Synthetic backend cases | 8 | 手工构造的小型迁移任务，覆盖 file/settings/contact/search/message，并加入 3 条 semantic recovery probes |
| API-Bank subset | 20 | 本轮扩充的 API-Bank 本地 runtime case |
| ToolSandbox subset | 12 | 从 ToolSandbox scenario 转换得到的 subset case |
| **Total** | **40** | 每个 case 都在 3 个 backend 和 4 个 strategy 下运行 |

总运行数为：

```text
40 cases × 3 backends × 4 strategies = 480 runs
```

### 3.1 API-Bank subset

API-Bank subset 从最小 3 条 `ForgotPassword` 扩展到 20 条，覆盖：

| 类别 | Case 类型 |
|---|---|
| 账户认证 | token 检查、登录取 token |
| 密码修改 | `ModifyPassword`, `ForgotPassword` |
| 日程 | add/query/modify agenda |
| 会议 | add/query/modify meeting |

例子：

- `apibank_backend::forgot_password_persistent_timeout`
- `apibank_backend::modify_password_timeout`
- `apibank_backend::add_modify_agenda_schema_drift`
- `apibank_backend::preseeded_modify_meeting_persistent_timeout`

### 3.2 ToolSandbox subset

ToolSandbox subset 包含 12 条，从本地 `Toolsandbox/tool_sandbox_scenarios.json` 转换而来，覆盖：

| 类型 | 示例 |
|---|---|
| Contact | `add_contact`, `modify_contact`, `search_contacts` |
| Messaging | `search_messages`, `send_message_with_phone_number` |
| Reminder | `datetime_info_to_timestamp`, `add_reminder` |
| Utility | `convert_currency` |

例子：

- `toolsandbox_backend::add_contact_with_name_and_phone_number`
- `toolsandbox_backend::convert_currency`
- `toolsandbox_backend::search_message_with_recency_latest`
- `toolsandbox_backend::add_reminder_content_and_date_and_time`

### 3.3 Synthetic cases

Synthetic cases 主要用于保证最小可控覆盖：

- `synthetic_backend::file_write`
- `synthetic_backend::wifi_setting`
- `synthetic_backend::contact_modify`
- `synthetic_backend::write_index_query`
- `synthetic_backend::send_message`

这些 case 能帮助确认迁移框架本身是否正常。

## 4. 实验过程

每个 case 都按照以下过程运行：

1. 构造初始 `WorldState`；
2. 根据 case 定义生成 oracle tool calls；
3. 按 strategy 生成不同轨迹：
   - `direct`: 不重试；
   - `cot`: 对目标工具增加 1 次重试；
   - `react`: 对目标工具增加 2 次重试；
   - `self_refine`: 对目标工具增加 2 次重试；
4. 在 `mock`、`sandbox`、`live_like` 三个后端分别运行；
5. 对最终 state 进行 goal evaluation；
6. 统计 final correctness、migration gap、state divergence、recovery、trajectory length、latency。

### 4.1 Live-like 故障注入

live-like 后端为目标工具注入四种故障：

| Fault Type | 含义 |
|---|---|
| `timeout` | 第一次调用目标工具 timeout |
| `schema_drift` | 第一次调用目标工具发生 schema mismatch |
| `persistent_timeout` | 目标工具连续 timeout 两次 |
| `hard_schema_drift` | 目标工具连续 schema drift 三次 |

故障强度对应策略的恢复能力：

| Strategy | 恢复预算 |
|---|---|
| `direct` | 0 次重试 |
| `cot` | 1 次重试 |
| `react` | 2 次重试 |
| `self_refine` | 2 次重试 |

因此实验四形成了一个清楚的难度梯度：

```text
single transient fault: cot/react/self_refine 应该能恢复
persistent fault: 只有 react/self_refine 应该能恢复
hard schema drift: 当前策略都无法恢复
```

## 5. 实验结果

### 5.1 总体结果

| Strategy | Backend | Cases | Final Correct | Migration Gap | Recovery | Avg Steps | Avg Latency ms |
|---|---|---:|---:|---:|---:|---:|---:|
| direct | mock | 40 | 100.0% | 0.0% | 0.0% | 2.08 | 0.39 |
| direct | sandbox | 40 | 92.5% | 7.5% | 0.0% | 2.08 | 10.36 |
| direct | live_like | 40 | 0.0% | 100.0% | 0.0% | 2.08 | 10.52 |
| cot | mock | 40 | 100.0% | 0.0% | 0.0% | 3.08 | 0.45 |
| cot | sandbox | 40 | 92.5% | 7.5% | 0.0% | 3.08 | 15.76 |
| cot | live_like | 40 | 50.0% | 50.0% | 50.0% | 3.08 | 17.80 |
| react | mock | 40 | 100.0% | 0.0% | 0.0% | 4.08 | 0.62 |
| react | sandbox | 40 | 100.0% | 0.0% | 0.0% | 4.05 | 21.96 |
| react | live_like | 40 | 85.0% | 15.0% | 85.0% | 4.05 | 26.53 |
| self_refine | mock | 40 | 100.0% | 0.0% | 0.0% | 4.08 | 0.67 |
| self_refine | sandbox | 40 | 100.0% | 0.0% | 0.0% | 4.05 | 20.66 |
| self_refine | live_like | 40 | 85.0% | 15.0% | 85.0% | 4.05 | 26.35 |

主要观察：

- 在 `mock` 中，四种策略全部达到 100% final correctness；
- 在升级后的 strict `sandbox` 中，`direct/cot` 降为 92.5%，而 `react/self_refine` 仍为 100.0%，说明 sandbox 已经能暴露 mock 忽略的语义错误，同时更强策略可以通过修复轨迹恢复；
- 一旦迁移到 `live_like`，策略差距立刻显现；
- `direct` 在 live-like 下完全失败，final correctness 为 0%；
- `cot` 能恢复一部分 transient fault，live-like correctness 为 50.0%；
- `react` 和 `self_refine` 表现最好，live-like correctness 为 85.0%；
- 更强策略带来更高 latency 和更长 trajectory，这是恢复能力的代价。

### 5.2 按数据来源拆分

| Source | direct | cot | react | self_refine |
|---|---:|---:|---:|---:|
| Synthetic backend | 0.0% | 25.0% | 87.5% | 87.5% |
| API-Bank subset | 0.0% | 60.0% | 90.0% | 90.0% |
| ToolSandbox subset | 0.0% | 50.0% | 75.0% | 75.0% |

这个结果说明：

- 退化现象不是 synthetic case 特有的；
- API-Bank 和 ToolSandbox 这两个 benchmark 风格数据集上也出现了同样趋势；
- API-Bank subset 中 `react/self_refine` 达到 90%，说明它们能恢复多数 API fault；
- ToolSandbox subset 中 `react/self_refine` 为 75%，说明 ToolSandbox official-style state constraints 更难一些。

### 5.3 按故障类型拆分

| Strategy | timeout | schema_drift | persistent_timeout | hard_schema_drift | semantic_validation |
|---|---:|---:|---:|---:|---:|
| direct | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| cot | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| react | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% |
| self_refine | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% |

解释：

- `timeout` 和 `schema_drift` 是单次 transient fault，`cot/react/self_refine` 都能恢复；
- `persistent_timeout` 连续失败两次，`cot` 的一次 retry 不够，只有 `react/self_refine` 能恢复；
- `hard_schema_drift` 连续失败三次，超过当前所有策略的恢复预算，因此所有策略都失败；
- `semantic_validation` 不是 transient fault，而是真实语义错误，单纯 retry 无法恢复，但 react/self-refine 的修复轨迹可以恢复；
- 这证明实验四不是简单地制造失败，而是构造了有区分度的后端难度曲线。

## 6. 结果说明了什么

实验四的核心结论是：

> Mock-only evaluation 会高估 agent 的部署鲁棒性。sandbox 能揭示一部分语义约束错误，而 live-like 会进一步揭示故障恢复能力不足。

具体来说：

1. `direct` 在 mock 中看起来完美，但 strict sandbox 已经会因为语义约束降到 92.5%，live-like 中更是完全失败。这说明 mock baseline 明显过于乐观。

2. `sandbox` 现在成为真正的中间层：它没有 timeout/schema drift，却能拒绝错误 old password、缺失 contact、非法时间格式等无效调用；同时 react/self_refine 可以通过补前置步骤或修正参数恢复到 100.0%。

3. `cot` 能处理单次 transient failure，但不能处理持续失败。这说明简单 retry 可以提升一定鲁棒性，但恢复能力有限。

4. `react` 和 `self_refine` 在 live-like 中保持最高成功率，说明 observation-driven recovery 或多步修正策略更适合真实工具后端。

5. ToolSandbox official-style runtime 的加入让实验更有说服力。因为它引入了真实状态约束，例如 cellular/self contact 依赖、low battery side effect、缺失 id 失败等。这些不是简单 timeout 能表达的。

6. API-Bank runtime 的加入让 live-like 同时具备传统 API benchmark 的状态逻辑，例如 token、password、agenda、meeting 数据库。

因此，实验四说明 backend realism 是独立且必要的评测维度。

## 7. 当前局限

当前实验四已经比最小版本强很多，但仍然有几个限制：

1. **仍然是本地 replica，不是在线真实 API。**

   API-Bank 和 ToolSandbox 的逻辑是在本地复刻的，保证可复现，但没有真实网络环境中的认证、限流、服务端不稳定等因素。

2. **策略轨迹仍是规则化 retry，不是真实 LLM 自主决策。**

   现在 `direct/cot/react/self_refine` 的差异主要体现在 retry budget 和预设轨迹上。它能验证环境和 benchmark 机制，但还不能完全代表 LLM agent 在真实 observation 下的自主恢复能力。

3. **ToolSandbox RapidAPI search 暂未接入。**

   官方 ToolSandbox 中有 RapidAPI search tools，但需要外部 API key。为了保证实验可复现，当前没有把它作为默认 runtime。

4. **hard schema drift 当前是不可恢复上限。**

   这有利于形成难度边界，但后续如果加入真实 LLM policy，可以进一步研究模型是否能通过参数修复、工具替换、重新规划来恢复。

## 8. 下一步建议

如果继续增强实验四，优先级如下：

1. 加入真实 LLM agent-policy，让模型根据 observation 自己决定是否 retry、如何改参数、是否换工具；
2. 扩大 API-Bank API 覆盖面，加入更多业务类型；
3. 扩大 ToolSandbox dependency subset，尤其是 state dependency 和 insufficient information case；
4. 如果条件允许，单独做一个非默认的 RapidAPI search 版本，用于测试真实外部 API；
5. 将 live-like 中的 fault 从 deterministic fault 扩展到概率式 fault，更接近真实服务波动。

## 9. 输出文件

本实验生成的主要文件：

- `outputs/cases/backend_migration_cases.jsonl`
- `outputs/metrics/backend_migration_summary.json`
- `outputs/reports/backend_migration_report.md`
- `outputs/reports/experiment_4_backend_migration_detailed_report.md`
- `outputs/figures/exp4_backend_migration_curve.png`
- `outputs/figures/exp4_backend_migration_gap.png`

根目录同步报告：

- `EXPERIMENT_4_BACKEND_MIGRATION_SUMMARY.md`
