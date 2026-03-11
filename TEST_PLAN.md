# AgentInferKit 完整测试方案

> 所有命令在项目根目录 `/Users/lixin/Downloads/AgentInferKit` 下运行
> 需要先激活 conda 环境: `conda activate benchmark`

---

## 0. 前置检查

```bash
# 确认服务运行中
curl -s http://localhost:8000/api/v1/system/health | python3 -m json.tool

# 如果没运行，启动服务
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 &

# 确认 DeepSeek API Key 已设置
echo $DEEPSEEK_API_KEY
# 如果没设置: export DEEPSEEK_API_KEY="sk-xxx"
```

---

## 第一阶段: 策略推理对比 (text_exam)

目标：逐一验证 direct / cot / tot / long_cot / self_refine / self_consistency 六种策略的推理过程

### 1.1 Direct 策略 (基线)

```bash
python scripts/run_experiment.py --config configs/experiments/test_exam_direct.yaml
```

**检查点:**
- [ ] 输出文件: `outputs/predictions/test_exam_direct_001.jsonl`
- [ ] 指标文件: `outputs/metrics/test_exam_direct_001.json`
- [ ] 查看推理结果 (无思维链):

```bash
head -1 outputs/predictions/test_exam_direct_001.jsonl | python3 -m json.tool
```

- [ ] 确认 `reasoning_trace` 为 null 或很短
- [ ] 确认 `parsed_answer` 是 A/B/C/D

### 1.2 CoT 策略 (Chain of Thought)

```bash
python scripts/run_experiment.py --config configs/experiments/test_exam_cot.yaml
```

**检查点:**
- [ ] 查看思维链:

```bash
python3 -c "
import json
with open('outputs/predictions/test_exam_cot_001.jsonl') as f:
    p = json.loads(f.readline())
print('=== Sample:', p['sample_id'], '===')
print('Parsed Answer:', p['parsed_answer'])
print('--- Reasoning Trace ---')
trace = p.get('reasoning_trace')
if isinstance(trace, list):
    for step in trace:
        print(f\"  Step {step.get('step',0)}: {step.get('thought','')[:100]}...\")
else:
    print(trace[:300] if trace else 'None')
print('--- RAG Context ---')
print(json.dumps(p.get('rag_context', {}), ensure_ascii=False, indent=2))
"
```

- [ ] 确认有多步推理过程
- [ ] 确认 `rag_context.mode` 为 null (无RAG)
- [ ] 对比 Direct vs CoT 准确率: `cat outputs/metrics/test_exam_cot_001.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('Accuracy:', d['overall'].get('accuracy'))"` 

### 1.3 ToT 策略 (Tree of Thought)

```bash
python scripts/run_experiment.py --config configs/experiments/test_exam_tot.yaml
```

**检查点:**
- [ ] 查看 ToT 多分支推理:

```bash
python3 -c "
import json
with open('outputs/predictions/test_exam_tot_001.jsonl') as f:
    p = json.loads(f.readline())
print('=== Sample:', p['sample_id'], '===')
print('Raw Output (前500字):')
print(p.get('raw_output', '')[:500])
print('---')
print('Reasoning Trace:')
trace = p.get('reasoning_trace')
print(json.dumps(trace, ensure_ascii=False, indent=2) if trace else 'None')
"
```

- [ ] 确认 reasoning_trace 里有多个 thought 分支
- [ ] 确认 token 消耗 > CoT (更深的思考)

### 1.4 Long CoT 策略

```bash
python scripts/run_experiment.py --config configs/experiments/test_exam_long_cot.yaml
```

**检查点:**
- [ ] `reasoning_trace` 应该比普通 CoT 更长
- [ ] 查看 token 消耗:

```bash
python3 -c "
import json
with open('outputs/predictions/test_exam_long_cot_001.jsonl') as f:
    p = json.loads(f.readline())
usage = p.get('usage', {})
print(f\"Tokens: {usage.get('total_tokens')} | Latency: {usage.get('latency_ms')}ms\")
print(f\"Trace length: {len(str(p.get('reasoning_trace','')))}\")
"
```

### 1.5 Self-Refine 策略

```bash
python scripts/run_experiment.py --config configs/experiments/test_exam_self_refine.yaml
```

**检查点:**
- [ ] 查看 refine 过程:

```bash
python3 -c "
import json
with open('outputs/predictions/test_exam_self_refine_001.jsonl') as f:
    p = json.loads(f.readline())
print('=== Sample:', p['sample_id'], '===')
trace = p.get('reasoning_trace')
if isinstance(trace, list):
    for i, step in enumerate(trace):
        print(f'--- Round {i+1} ---')
        print(f\"  Thought: {str(step.get('thought',''))[:150]}...\")
        print(f\"  Action: {step.get('action','')}\")
else:
    print(str(trace)[:500])
"
```

- [ ] 确认有"初始回答 → 自我批评 → 修正"的多轮过程

### 1.6 Self-Consistency 策略

```bash
python scripts/run_experiment.py --config configs/experiments/test_exam_self_consistency.yaml
```

**检查点:**
- [ ] 查看多次采样+投票:

```bash
python3 -c "
import json
with open('outputs/predictions/test_exam_self_consistency_001.jsonl') as f:
    p = json.loads(f.readline())
print('=== Sample:', p['sample_id'], '===')
print('Final Answer:', p['parsed_answer'])
trace = p.get('reasoning_trace')
if isinstance(trace, list):
    print(f'Sampled {len(trace)} paths')
    for i, step in enumerate(trace):
        print(f\"  Path {i+1}: {str(step.get('thought',''))[:80]}...\")
else:
    print(str(trace)[:500])
"
```

- [ ] 确认有多条推理路径
- [ ] 最终答案是多次投票的结果

### 1.7 策略横向对比

等以上6个实验都跑完后:

```bash
python3 -c "
import json, os, glob

metrics = {}
for f in sorted(glob.glob('outputs/metrics/test_exam_*.json')):
    name = os.path.basename(f).replace('.json','')
    with open(f) as fh:
        d = json.load(fh)
    overall = d.get('overall', {})
    metrics[name] = {
        'accuracy': overall.get('accuracy', '-'),
        'avg_tokens': overall.get('avg_tokens', '-'),
        'avg_latency_ms': overall.get('avg_latency_ms', '-'),
    }

print(f\"{'实验':<40} {'准确率':<10} {'平均Token':<12} {'平均延迟ms':<12}\")
print('=' * 74)
for name, m in metrics.items():
    print(f\"{name:<40} {str(m['accuracy']):<10} {str(m['avg_tokens']):<12} {str(m['avg_latency_ms']):<12}\")
"
```

---

## 第二阶段: RAG 实验 (实验A — RAG vs No-RAG on text_exam)

目标：验证 RAG oracle / retrieved 模式对准确率的影响

### 2.1 对照组: 无RAG + Direct

```bash
python scripts/run_experiment.py --config configs/experiments/expA_exam_norag_direct.yaml
```

### 2.2 对照组: 无RAG + CoT

```bash
python scripts/run_experiment.py --config configs/experiments/expA_exam_norag_cot.yaml
```

### 2.3 实验组: RAG Oracle + Direct

```bash
python scripts/run_experiment.py --config configs/experiments/expA_exam_rag_oracle_direct.yaml
```

**检查点 (重点看 RAG trace):**

```bash
python3 -c "
import json
with open('outputs/predictions/expA_exam_rag_oracle_direct.jsonl') as f:
    p = json.loads(f.readline())
print('=== Sample:', p['sample_id'], '===')
print('Answer:', p['parsed_answer'])
rc = p.get('rag_context', {})
print(f\"RAG Mode: {rc.get('mode')}\")
print(f\"Query: {rc.get('query_text')}\")
print(f\"Latency: {rc.get('retrieval_latency_ms')}ms\")
print(f\"Chunks: {len(rc.get('retrieved_chunks', []))}\")
for c in rc.get('retrieved_chunks', []):
    print(f\"  [{c.get('chunk_id')}] score={c.get('score')} text={c.get('text','')[:80]}...\")
print()
print('--- Input Prompt (前300字) ---')
print(p.get('input_prompt', '')[:300])
"
```

- [ ] 确认 `rag_context.mode = "oracle"`
- [ ] 确认 `retrieved_chunks` 包含正确的参考知识
- [ ] 确认 `input_prompt` 中注入了 "Reference: ..." 内容

### 2.4 实验组: RAG Oracle + CoT

```bash
python scripts/run_experiment.py --config configs/experiments/expA_exam_rag_oracle_cot.yaml
```

**检查点:**
- [ ] 同时有 reasoning_trace (思维链) 和 rag_context (RAG轨迹)

```bash
python3 -c "
import json
with open('outputs/predictions/expA_exam_rag_oracle_cot.jsonl') as f:
    p = json.loads(f.readline())
print('Has reasoning_trace:', p.get('reasoning_trace') is not None)
print('Has rag_context:', p.get('rag_context',{}).get('mode') is not None)
print('RAG mode:', p.get('rag_context',{}).get('mode'))
print('Chunks:', len(p.get('rag_context',{}).get('retrieved_chunks',[])))
"
```

### 2.5 实验组: RAG Retrieved + CoT (需要 Milvus)

> ⚠️ 此实验需要 Milvus 服务运行中，且知识库 `qa_chunks_v1` 已构建

```bash
# 先检查 Milvus 连接 & KB 状态
curl -s http://localhost:8000/api/v1/rag/qa_chunks_v1/status | python3 -m json.tool

# 如果 KB 不存在，先构建:
# curl -X POST http://localhost:8000/api/v1/rag/build \
#   -H "Content-Type: application/json" \
#   -d '{"kb_name":"qa_chunks_v1","source_file":"data/rag/qa_chunks_v1_source.jsonl"}'

# 运行实验
python scripts/run_experiment.py --config configs/experiments/expA_exam_rag_retrieved_cot.yaml
```

**检查点:**
- [ ] `rag_context.mode = "retrieved"`
- [ ] 检索延迟 `retrieval_latency_ms` 合理 (几十~几百ms)
- [ ] `retrieved_chunks` 的 `score` 是向量相似度分

```bash
python3 -c "
import json
with open('outputs/predictions/expA_exam_rag_retrieved_cot.jsonl') as f:
    for line in f:
        p = json.loads(line)
        rc = p.get('rag_context', {})
        if rc.get('mode') == 'retrieved':
            print(f\"[{p['sample_id']}] latency={rc.get('retrieval_latency_ms')}ms chunks={len(rc.get('retrieved_chunks',[]))}\")
            for c in rc.get('retrieved_chunks', []):
                print(f\"    {c['chunk_id']} score={c['score']:.4f} text={c['text'][:60]}...\")
            break
"
```

### 2.6 实验A 横向对比

```bash
python3 -c "
import json, os, glob

experiments = [
    'expA_exam_norag_direct',
    'expA_exam_norag_cot', 
    'expA_exam_rag_oracle_direct',
    'expA_exam_rag_oracle_cot',
    'expA_exam_rag_retrieved_cot',
]
print(f\"{'实验':<35} {'准确率':<10} {'Token':<10} {'延迟ms':<10} {'RAG':<10}\")
print('=' * 75)
for name in experiments:
    path = f'outputs/metrics/{name}.json'
    if not os.path.exists(path):
        print(f\"{name:<35} (未运行)\")
        continue
    with open(path) as f:
        d = json.load(f)
    o = d.get('overall', {})
    rag = '有' if 'rag' in name else '无'
    print(f\"{name:<35} {str(o.get('accuracy','-')):<10} {str(o.get('avg_tokens','-')):<10} {str(o.get('avg_latency_ms','-')):<10} {rag:<10}\")
"
```

**预期结论:** RAG oracle > RAG retrieved > No-RAG (准确率递增)

---

## 第三阶段: 实验B — Image MCQ (图像理解)

> 注意: deepseek-chat 是纯文本模型，无法真正处理图像。
> 这里测试的是框架流程是否正确，模型会基于题目文字猜答案。
> 真正测试需要 VLM 模型 (如 gpt-4o)。

### 3.1 Image MCQ + Direct

```bash
python scripts/run_experiment.py --config configs/experiments/expB_image_mcq_direct.yaml
```

### 3.2 Image MCQ + CoT

```bash
python scripts/run_experiment.py --config configs/experiments/expB_image_mcq_cot.yaml
```

**检查点:**

```bash
python3 -c "
import json
with open('outputs/predictions/expB_image_mcq_direct.jsonl') as f:
    for line in f:
        p = json.loads(line)
        print(f\"[{p['sample_id']}] answer={p['parsed_answer']} question={p.get('input_prompt','')[:80]}...\")
"
```

- [ ] 确认 image_mcq 样本能正常走完推理流程
- [ ] 确认评估指标正常输出

---

## 第四阶段: API Calling / Agent 实验

### 4.1 Agent + Direct

```bash
python scripts/run_experiment.py --config configs/experiments/test_agent_direct.yaml
```

### 4.2 Agent + CoT

```bash
python scripts/run_experiment.py --config configs/experiments/test_agent_cot.yaml
```

### 4.3 Agent + ReAct

```bash
python scripts/run_experiment.py --config configs/experiments/test_agent_react.yaml
```

**检查点 (重点看 tool_trace):**

```bash
python3 -c "
import json
for name in ['test_agent_direct_001', 'test_agent_cot_001', 'test_agent_react_001']:
    path = f'outputs/predictions/{name}.jsonl'
    try:
        with open(path) as f:
            p = json.loads(f.readline())
        print(f'=== {name} ===')
        print(f\"  Answer: {p.get('parsed_answer','')[:80]}\")
        print(f\"  Tool Trace: {json.dumps(p.get('tool_trace',[]), ensure_ascii=False)[:200]}\")
        print(f\"  Reasoning: {str(p.get('reasoning_trace',''))[:150]}\")
        print()
    except FileNotFoundError:
        print(f'{name}: 未运行')
"
```

- [ ] ReAct 策略有 Thought → Action → Observation 循环
- [ ] tool_trace 记录了调用的工具名称和参数

---

## 第五阶段: WebUI 验证

确保服务在运行中，打开浏览器 http://localhost:8000

### 5.1 数据集上传

```bash
# 上传 image_mcq 数据集 (通过API)
curl -X POST http://localhost:8000/api/v1/datasets/upload \
  -F "file=@data/benchmark/image_mcq/demo_image_mcq_v1.jsonl" \
  -F "dataset_name=demo_image_mcq" \
  -F "task_type=image_mcq" \
  -F "version=1.0.0" | python3 -m json.tool
```

### 5.2 在 WebUI 上验证

- [ ] **数据集 Tab**: 能看到上传的数据集，点击预览能看到样本
- [ ] **实验配置 Tab**: 创建新实验，选择数据集，选择策略
- [ ] **实验列表**: 已完成的实验显示「评估」「结果」「详情」按钮
- [ ] **详情按钮**: 点击能看到每个样本的:
  - 模型/策略参数
  - 预测 vs 正确答案
  - 思维链 (可展开)
  - 原始输出 (可展开)
  - RAG 轨迹 (可展开，含 chunks/scores)
- [ ] **结果分析 Tab**: 选择实验后显示指标卡片和图表
- [ ] **Sample Browser**: 思维链列有「查看」/「详情」按钮
- [ ] **对话调试 Tab**: 选择 cot 策略聊天，回复下方有思维链折叠

---

## 第六阶段: 查看所有结果文件

```bash
# 列出所有 prediction 文件
ls -la outputs/predictions/*.jsonl

# 列出所有 metrics 文件
ls -la outputs/metrics/*.json

# 快速查看某个实验的完整 metrics
cat outputs/metrics/test_exam_cot_001.json | python3 -m json.tool

# 导出所有实验对比 CSV (通过 export_figures 脚本)
python scripts/export_figures.py --metrics-dir outputs/metrics --output-dir outputs/figures
```

---

## 实验配置文件清单

| 文件 | 任务类型 | 策略 | RAG | 说明 |
|------|----------|------|-----|------|
| `test_exam_direct.yaml` | text_exam | direct | 无 | 基线 |
| `test_exam_cot.yaml` | text_exam | cot | 无 | CoT推理 |
| `test_exam_tot.yaml` | text_exam | tot | 无 | ToT推理 |
| `test_exam_long_cot.yaml` | text_exam | long_cot | 无 | 深度思考 |
| `test_exam_self_refine.yaml` | text_exam | self_refine | 无 | 自我修正 |
| `test_exam_self_consistency.yaml` | text_exam | self_consistency | 无 | 多路投票 |
| `expA_exam_norag_direct.yaml` | text_exam | direct | 无 | 实验A对照 |
| `expA_exam_norag_cot.yaml` | text_exam | cot | 无 | 实验A对照 |
| `expA_exam_rag_oracle_direct.yaml` | text_exam | direct | oracle | 实验A实验组 |
| `expA_exam_rag_oracle_cot.yaml` | text_exam | cot | oracle | 实验A实验组 |
| `expA_exam_rag_retrieved_cot.yaml` | text_exam | cot | retrieved | 实验A (需Milvus) |
| `expB_image_mcq_direct.yaml` | image_mcq | direct | 无 | 实验B |
| `expB_image_mcq_cot.yaml` | image_mcq | cot | 无 | 实验B |
| `test_agent_direct.yaml` | api_calling | direct | 无 | Agent基线 |
| `test_agent_cot.yaml` | api_calling | cot | 无 | Agent+CoT |
| `test_agent_react.yaml` | api_calling | react | 无 | Agent+ReAct |
| `test_qa_cot.yaml` | qa | cot | 无 | QA问答 |

---

## 快速全部运行 (可选)

```bash
# 按顺序运行所有实验 (约需30分钟，取决于API速度)
for config in \
  configs/experiments/test_exam_direct.yaml \
  configs/experiments/test_exam_cot.yaml \
  configs/experiments/test_exam_tot.yaml \
  configs/experiments/test_exam_long_cot.yaml \
  configs/experiments/test_exam_self_refine.yaml \
  configs/experiments/test_exam_self_consistency.yaml \
  configs/experiments/expA_exam_norag_direct.yaml \
  configs/experiments/expA_exam_norag_cot.yaml \
  configs/experiments/expA_exam_rag_oracle_direct.yaml \
  configs/experiments/expA_exam_rag_oracle_cot.yaml \
  configs/experiments/expB_image_mcq_direct.yaml \
  configs/experiments/expB_image_mcq_cot.yaml \
  configs/experiments/test_agent_direct.yaml \
  configs/experiments/test_agent_cot.yaml \
  configs/experiments/test_agent_react.yaml \
  configs/experiments/test_qa_cot.yaml; do
  echo "===== Running: $config ====="
  python scripts/run_experiment.py --config "$config"
  echo ""
done
```
