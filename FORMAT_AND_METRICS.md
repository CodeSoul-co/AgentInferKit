# 输入输出格式与评测指标速查（v2.0）

---

## 一、数据输入格式

### 1.1 统一基础字段

所有任务类型必须包含以下字段，缺失时平台行为如下：

| 字段 | 类型 | 必填 | 缺失行为 |
|------|------|------|----------|
| `sample_id` | string | ✅ | 拒绝上传，报错 |
| `task_type` | enum | ✅ | 拒绝上传，报错 |
| `split` | enum | ✅ | 自动填充 `test` + warning |
| `source` | string | ✅ | 自动填充 `unknown` + warning |
| `modality` | enum | ✅ | 自动填充 `text` + warning |
| `version` | string | ✅ | 自动填充 `1.0.0` + warning |
| `difficulty` | enum | ⚪ | 自动填充 `medium` |
| `metadata` | object | ✅ | 拒绝上传，报错 |
| `eval_type` | enum | ✅ | 按 task_type 自动推断 |

**字段枚举值：**
- `task_type`：`qa` / `text_exam` / `image_mcq` / `api_calling`
- `split`：`train` / `dev` / `test`
- `modality`：`text` / `image` / `text+image`
- `difficulty`：`easy` / `medium` / `hard`
- `eval_type` 默认推断：`qa` → `em_or_f1`，`text_exam` / `image_mcq` → `choice_accuracy`，`api_calling` → `function_calling`

---

### 1.2 各任务类型核心字段对照表

| 字段 | qa | text_exam | image_mcq | api_calling |
|------|----|-----------|-----------|-------------|
| `question` | ✅ | ✅ | ✅ | ❌ |
| `answer` (string) | ✅ | ❌ | ❌ | ❌ |
| `answer` (A/B/C/D) | ❌ | ✅ | ✅ | ❌ |
| `options` {A/B/C/D} | ❌ | ✅ | ✅ | ❌ |
| `answer_aliases` | ⚪ | ❌ | ❌ | ❌ |
| `context` | ⚪ | ❌ | ❌ | ❌ |
| `explanation` | ❌ | ⚪ | ⚪ | ❌ |
| `image_path` | ❌ | ❌ | ✅ | ❌ |
| `user_goal` | ❌ | ❌ | ❌ | ✅ |
| `available_tools` | ❌ | ❌ | ❌ | ✅ |
| `tool_index` | ❌ | ❌ | ❌ | ✅ |
| `ground_truth.call_sequence` | ❌ | ❌ | ❌ | ✅ |
| `ground_truth.final_answer` | ❌ | ❌ | ❌ | ✅ |
| `related_chunk_ids` | ❌ | ⚪ | ❌ | ❌ |
| `rag_protocol` | ❌ | ⚪ | ❌ | ❌ |
| `requires_knowledge` | ⚪ | ⚪ | ❌ | ❌ |
| `eval_type` | ✅ | ✅ | ✅ | ✅ |

✅ 必填  ⚪ 可选  ❌ 不适用

---

### 1.3 Tool Schema 输入字段结构

工具文件路径：`data/schemas/tool_schemas/{tool_id}.json`

| 字段 | 说明 | 注入给模型 | RAG 检索 |
|------|------|-----------|---------|
| `tool_id` | 工具唯一标识 | ✅ | ❌ |
| `category` | 所属大类 | ❌ | ❌ |
| `subcategory` | 业务小类 | ❌ | ❌ |
| `core_description` | 核心功能 + 关键能力（合并） | ✅ 直接注入 | ❌ |
| `business_scenario` | 业务场景文本 | ❌ 不注入 | ✅ 语义检索字段 |
| `parameters` | 输入参数规约（含类型、单位、必填） | ✅ | ❌ |
| `return_schema` | 返回字段说明（含类型、单位） | ⚪ 可选注入 | ❌ |
| `mock_responses` | 模拟执行返回值 | ❌ | ❌ |

**参数类型枚举：**

| 类型 | 说明 | 示例参数 |
|------|------|---------|
| `String` | 字符串标识符 | target_id |
| `Float` | 浮点数值 | oil_temp, voltage |
| `Integer` | 整数 | 次数、数量 |
| `Boolean` | 布尔值 | 开关状态 |
| `Enum` | 枚举，需列出 enum_values | switch_status [0,1] |
| `TimeSeries` | 时间序列数组 | partial_discharge |
| `Vector` | 固定维度向量 | current_harmonic（2~50次） |
| `Tensor` | 多维矩阵 | infrared_image |

---

### 1.4 现有工具参数速查

#### tool_elec_0001 输入 / 返回

| 输入参数 | 类型 | 单位 |
|----------|------|------|
| target_id | String | — |
| oil_temp | Float | ℃ |
| ground_current | Float | mA |
| voltage_phase_c | Float | kV |
| sf6_pressure | Float | MPa |

| 返回字段 | 类型 | 单位 |
|----------|------|------|
| pressure | Float | MPa |
| diff_pressure | Float | MPa |
| alarm_level | Enum | normal/warning/critical |
| voltage | Float | kV |
| current | Float | A |
| power_factor | Float | — |
| frequency | Float | Hz |

#### tool_elec_0002 输入 / 返回

| 输入参数 | 类型 | 单位 |
|----------|------|------|
| target_id | String | — |
| voltage_phase_c | Float | kV |
| partial_discharge | TimeSeries | — |
| oil_temp | Float | ℃ |
| ground_current | Float | mA |
| switch_status | Enum | [0,1] |

| 返回字段 | 类型 | 单位 |
|----------|------|------|
| pressure | Float | MPa |
| diff_pressure | Float | MPa |
| alarm_level | Enum | normal/warning/critical |

#### tool_elec_0003 输入 / 返回

| 输入参数 | 类型 | 单位 |
|----------|------|------|
| target_id | String | — |
| current_harmonic | Vector | — |
| load_ratio | Float | % |
| voltage_phase_b | Float | kV |
| voltage_phase_a | Float | kV |
| infrared_image | Tensor | — |
| partial_discharge | TimeSeries | — |

| 返回字段 | 类型 | 单位 |
|----------|------|------|
| pressure | Float | MPa |
| diff_pressure | Float | MPa |
| alarm_level | Enum | normal/warning/critical |
| voltage | Float | kV |
| current | Float | A |
| power_factor | Float | — |
| frequency | Float | Hz |

#### tool_elec_0004 输入 / 返回

| 输入参数 | 类型 | 单位 |
|----------|------|------|
| target_id | String | — |
| sf6_pressure | Float | MPa |
| oil_temp | Float | ℃ |
| ambient_temp | Float | ℃ |
| ground_current | Float | mA |
| load_ratio | Float | % |
| voltage_phase_b | Float | kV |

| 返回字段 | 类型 | 单位 |
|----------|------|------|
| pressure | Float | MPa |
| diff_pressure | Float | MPa |
| alarm_level | Enum | normal/warning/critical |
| raw_data | String | — |
| status | Enum | normal/abnormal/fault |

---

## 二、输出格式

### 2.1 Prediction 单条记录字段

文件路径：`outputs/predictions/{experiment_id}.jsonl`，每条推理完成后实时追加。

| 字段 | 类型 | 说明 |
|------|------|------|
| `sample_id` | string | 对应输入样本 ID |
| `experiment_id` | string | 所属实验 ID |
| `model` | string | 使用的模型名 |
| `strategy` | string | 推理策略名 |
| `timestamp` | string | 推理完成时间（ISO 8601） |
| `input_prompt` | string | 注入给模型的完整 prompt |
| `raw_output` | string | 模型原始输出全文 |
| `parsed_answer` | string | 解析后的最终答案 |
| `reasoning_trace` | List / [] | 结构化推理步骤列表，格式：`[{"step": 1, "thought": "...", "action": "..."}]`；direct 策略时为空列表 `[]` |
| `rag_context.mode` | enum / null | `oracle` / `retrieved` / null |
| `rag_context.retrieved_chunks` | array | 每条含 chunk_id、score、text |
| `tool_trace` | array | 每步工具调用记录（见下表） |
| `usage.prompt_tokens` | int | 输入 token 数 |
| `usage.completion_tokens` | int | 输出 token 数 |
| `usage.total_tokens` | int | 总 token 数 |
| `usage.latency_ms` | float | 单条推理耗时（毫秒） |
| `error` | string / null | 推理失败原因；成功时为 null |

**tool_trace 单步字段：**

| 字段 | 说明 |
|------|------|
| `step` | 调用顺序（从 1 开始） |
| `tool_id` | 调用的工具 ID |
| `parameters` | 实际传入的参数 dict |
| `response` | 工具返回的结果 dict |
| `status` | `success` / `param_error` / `tool_not_found` |
| `timestamp` | 调用时间 |

---

### 2.2 Metrics 整体评测结果字段

文件路径：`outputs/metrics/{experiment_id}.json`

| 字段 | 类型 | 说明 |
|------|------|------|
| `experiment_id` | string | 实验 ID |
| `evaluated_at` | string | 评测完成时间 |
| `model` | string | 模型名 |
| `strategy` | string | 策略名 |
| `dataset` | string | 数据集名 |
| `total_samples` | int | 样本总数 |
| `valid_samples` | int | 有效样本数（排除 error） |
| `overall` | object | 整体指标（见下节） |
| `by_difficulty` | object | 按 easy/medium/hard 分组统计 |
| `by_topic` | object | 按 metadata.topic 分组统计 |
| `by_strategy` | object | 跨实验对比时按策略分组 |
| `rag_metrics` | object / null | RAG 相关指标 |
| `agent_metrics` | object / null | Agent 相关指标 |
| `judge_metrics` | object / null | LLM 裁判评分 |
| `option_bias` | object / null | 各选项被选频次（仅选择题） |

**overall 字段：**

| 字段 | 说明 |
|------|------|
| `accuracy` | 整体准确率 |
| `f1` | 整体 F1（QA 任务） |
| `avg_latency_ms` | 平均推理耗时 |
| `avg_tokens` | 平均 token 消耗 |
| `total_cost_usd` | 本次实验总费用估算 |

---

## 三、评测指标总览

### 3.1 基础指标

| 指标 | 适用任务 | 说明 | 实现阶段 |
|------|----------|------|---------|
| `choice_accuracy` | text_exam, image_mcq | 选项字母完全匹配的样本比例 | 阶段一 |
| `exact_match` | qa | 答案与标准答案（含 aliases）完全一致 | 阶段一 |
| `token_f1` | qa | token 级别 Precision/Recall F1 | 阶段一 |
| `BLEU` | qa | n-gram 精确率加权平均 | 阶段一 |
| `ROUGE-L` | qa | 最长公共子序列覆盖率 | 阶段一 |
| `option_bias` | text_exam, image_mcq | 各选项（A/B/C/D）被选中频次分布，检测选项偏好 | 阶段一 |
| `win_rate` | 全部 | 目标实验答对、基线答错的样本占比，衡量策略独特贡献 | 阶段一 |
| `grounding_error_rate` | image_mcq | 按 question_type 分组统计错误率，重点关注 object_recognition / relation / ocr 三类，作为视觉 grounding 能力代理指标 | 阶段二 |

### 3.2 RAG 指标

| 指标 | 说明 | 实现阶段 |
|------|------|---------|
| `retrieval_recall_at_k` | 在 top-k 召回结果中包含相关 chunk 的样本比例 | 阶段二 |
| `evidence_hit_rate` | 召回 chunk 与样本 `related_chunk_ids` 的命中率 | 阶段二 |
| `answer_evidence_alignment` | 答案文本与 RAG 召回证据的字符串覆盖率 | 阶段二 |
| `hallucination_rate` | 答案与召回证据不一致的粗估比例（字符串匹配） | 阶段二 |

### 3.3 Agent 指标

| 指标 | 说明 | 实现阶段 |
|------|------|---------|
| `tool_selection_accuracy` | 预测的 tool_id 调用序列与 ground_truth.call_sequence 完全一致的比例 | 阶段三 |
| `parameter_accuracy` | 每个工具调用的参数 dict 与 ground_truth 参数完全匹配的比例 | 阶段三 |
| `end_to_end_success_rate` | 最终 parsed_answer 与 ground_truth.final_answer 一致的比例 | 阶段三 |
| `invalid_call_rate` | 调用了 available_tools 之外工具的样本比例 | 阶段三 |
| `avg_tool_calls` | 每条样本平均工具调用次数 | 阶段三 |

### 3.4 效率指标

| 指标 | 说明 | 实现阶段 |
|------|------|---------|
| `avg_latency_ms` | 平均单条推理耗时（毫秒） | 阶段一 |
| `avg_tokens` | 平均 token 消耗（prompt_tokens + completion_tokens） | 阶段一 |
| `total_cost_usd` | 整个实验的估算总费用（按模型定价计算） | 阶段一 |
| `avg_trace_tokens` | reasoning_trace 全文平均 token 数，衡量推理链计算成本；direct 策略时为 0 | 阶段一 |
| `avg_reasoning_steps` | reasoning_trace 列表平均步数，衡量推理深度；direct 策略时为 0 | 阶段三 |

### 3.5 Judge-based 指标

| 指标 | 说明 | 实现阶段 |
|------|------|---------|
| `avg_score` | LLM 裁判对所有样本的平均评分（1~5分） | 阶段三 |
| `score_dist` | 各分值对应的样本数量分布 | 阶段三 |

---

### 3.6 各任务类型适用指标矩阵

| 指标 | qa | text_exam | image_mcq | api_calling | 阶段 |
|------|----|-----------|-----------|-------------|------|
| choice_accuracy | ❌ | ✅ | ✅ | ❌ | 一 |
| exact_match | ✅ | ❌ | ❌ | ❌ | 一 |
| token_f1 | ✅ | ❌ | ❌ | ❌ | 一 |
| BLEU | ✅ | ❌ | ❌ | ❌ | 一 |
| ROUGE-L | ✅ | ❌ | ❌ | ❌ | 一 |
| option_bias | ❌ | ✅ | ✅ | ❌ | 一 |
| win_rate | ✅ | ✅ | ✅ | ✅ | 一 |
| avg_latency_ms | ✅ | ✅ | ✅ | ✅ | 一 |
| avg_tokens | ✅ | ✅ | ✅ | ✅ | 一 |
| total_cost_usd | ✅ | ✅ | ✅ | ✅ | 一 |
| avg_trace_tokens | ✅ | ✅ | ✅ | ✅ | 一 |
| grounding_error_rate | ❌ | ❌ | ✅ | ❌ | 二 |
| retrieval_recall_at_k | ❌ | ✅ | ❌ | ❌ | 二 |
| evidence_hit_rate | ❌ | ✅ | ❌ | ❌ | 二 |
| answer_evidence_alignment | ❌ | ✅ | ❌ | ❌ | 二 |
| hallucination_rate | ❌ | ✅ | ❌ | ❌ | 二 |
| tool_selection_accuracy | ❌ | ❌ | ❌ | ✅ | 三 |
| parameter_accuracy | ❌ | ❌ | ❌ | ✅ | 三 |
| end_to_end_success_rate | ❌ | ❌ | ❌ | ✅ | 三 |
| invalid_call_rate | ❌ | ❌ | ❌ | ✅ | 三 |
| avg_tool_calls | ❌ | ❌ | ❌ | ✅ | 三 |
| avg_reasoning_steps | ✅ | ✅ | ✅ | ✅ | 三 |
| judge_score | ✅ | ❌ | ❌ | ✅ | 三 |

---

## 四、分组统计维度

所有维度均通过 `group_stats.multi_group_stats()` 统一处理，任意 `metadata` 子字段均可作为分组维度，无需修改代码。

| 维度 | 字段来源 | 适用任务 | 说明 |
|------|----------|----------|------|
| `by_difficulty` | `difficulty` | 全部 | easy / medium / hard |
| `by_topic` | `metadata.topic` | qa, text_exam | 知识点主题 |
| `by_strategy` | 实验配置 | 全部 | 跨实验对比时使用 |
| `by_category` | `metadata.category` | api_calling | 设备大类 |
| `by_subcategory` | `metadata.subcategory` | api_calling | 业务小类 |
| `by_call_type` | `metadata.call_type` | api_calling | single / multi_tool / multi_step 等 |
| `by_question_type` | `metadata.question_type` | text_exam, image_mcq | 题型分类 |

每个分组条目输出字段：`accuracy`（或适用指标）、`count`、`avg_tokens`、`avg_latency_ms`。
