# AgentInferKit WebUI 重设计方案

> **文档类型**：前端视觉重设计规范 · v1.0  
> **项目**：AgentInferKit / AIODS · D 岗平台层  
> **状态**：待 Claude Code 实现

---

## 一、现状问题诊断

通过阅读 `webui/templates/base.html`、`index.html` 及 `static/css/main.css`，现有 UI 存在以下四类问题：

### 1.1 视觉层

- 配色单调：白 / 灰 / 蓝三色，stat-card 无图标无视觉重量
- 侧边栏用 emoji 代替图标（📁、🧪 等），显得廉价且无法控制尺寸
- 字体使用系统默认字体栈，无专业感
- 卡片无阴影层次，整体像未完成的后台模板

### 1.2 交互层

- Dashboard 4 个数字卡无趋势信息，仅显示空数字
- 实验创建表单所有字段挤在一张 card，层级混乱
- 策略选择用下拉框，用户无法理解 Direct / CoT / ToT 的区别

### 1.3 数据上传

- drop-zone 拖拽区域视觉反馈弱
- `#upload-status` 区域无样式定义，上传进度完全不可见
- 文件选中后无任何预览或格式验证反馈

### 1.4 结果可视化

- `#charts-container` 是空白占位，用户进入 Results 页面看到的是一片空白
- 图表区域靠 JS 动态注入，无骨架屏，加载体验差

---

## 二、视觉设计语言

### 2.1 配色方案

从纯白底升级为**深色侧边栏 + 浅色主区域**的双色调布局，视觉层次感明显提升。

#### 主色

| Token | 色值 | 用途 |
|---|---|---|
| Primary | `#6366F1` | 主操作、高亮、激活状态 |
| Primary Dark | `#4F46E5` | hover 状态 |
| Info | `#3B82F6` | 信息提示、进度条 |
| Success | `#22C55E` | 成功状态、上传完成 |
| Warning | `#F59E0B` | 警告、进行中 |
| Error | `#EF4444` | 错误、失败 |

#### 中性色

| Token | 色值 | 用途 |
|---|---|---|
| Sidebar BG | `#0F172A` | 侧边栏背景 |
| Text Primary | `#1E293B` | 主要文字 |
| Text Secondary | `#64748B` | 辅助文字 |
| Text Muted | `#94A3B8` | 占位符、弱文字 |
| Border | `#E2E8F0` | 边框、分割线 |
| BG Secondary | `#F8FAFC` | 页面背景 |
| BG Primary | `#FFFFFF` | 卡片背景 |

---

### 2.2 字体

引入 **Inter**（Google Fonts CDN）替代系统默认字体栈。

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

| 层级 | 大小 | 字重 | 颜色 |
|---|---|---|---|
| 页面标题 | 24px | 600 | `#1E293B` |
| 章节标题 H2 | 18px | 600 | `#1E293B` |
| 卡片标题 | 14px | 600 | `#1E293B` |
| 正文 | 14px | 400 | `#1E293B` |
| 辅助文字 | 13px | 400 | `#64748B` |
| 标签/角标 | 12px | 500 | `#94A3B8` |

---

### 2.3 图标

全部 emoji 替换为 **Lucide Icons**（CDN），通过 `lucide.createIcons()` 初始化。

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
```

用法：`<i data-lucide="database"></i>`，在 `base.html` 底部 + `switchTab()` 后各调用一次 `lucide.createIcons()`。

| 位置 | 原 emoji | 替换图标 |
|---|---|---|
| Dashboard | 🏠 | `home` |
| 数据集管理 | 📁 | `database` |
| 实验配置 | 🧪 | `flask-conical` |
| 结果分析 | 📈 | `bar-chart-2` |
| 知识库管理 | 🔍 | `book-open` |
| 对话调试 | 💬 | `message-square` |
| 上传按钮 | 📤 | `upload-cloud` |
| 新建实验 | ➕ | `plus` |
| 刷新 | 🔄 | `refresh-cw` |
| 删除 | — | `trash-2` |

---

### 2.4 阴影层次

| 层级 | CSS 变量 | 使用场景 |
|---|---|---|
| Level 1 | `--shadow-sm` | 普通 card |
| Level 2 | `--shadow-md` | 悬浮 card、下拉框 |
| Level 3 | `--shadow-lg` | Modal、通知 |
| Level 4 | `--shadow-xl` | Sidebar |

---

## 三、整体布局调整

### 3.1 侧边栏

深色背景 `#0F172A`，active 状态改为**左侧 3px 亮色竖条 + 文字变白**（而非整块蓝底）：

```css
.nav-item.active {
  border-left: 3px solid var(--sidebar-active-bar);
  color: #FFFFFF;
  background: rgba(255,255,255,0.08);
}
```

- **Logo 区**：`AgentInferKit`（Inter 粗体，`#6366F1`）+ 版本号（小字，`#94A3B8`）
- **底部状态栏**：圆形状态灯（绿/黄/红）+ "Milvus: connected"，字号 12px

### 3.2 主区域 page-header

- 左：页面标题（24px / 600）
- 右：主操作按钮 + 「上次刷新 HH:MM:SS」灰色小字

### 3.3 CSS 变量完整参考

```css
:root {
  /* 字体 */
  --font-family: 'Inter', system-ui, -apple-system, sans-serif;

  /* 侧边栏 */
  --sidebar-bg: #0F172A;
  --sidebar-border: #1E293B;
  --sidebar-text: #94A3B8;
  --sidebar-text-hover: #E2E8F0;
  --sidebar-text-active: #FFFFFF;
  --sidebar-active-bar: #6366F1;
  --sidebar-hover-bg: rgba(255,255,255,0.05);

  /* 主色 */
  --primary-color: #6366F1;
  --primary-hover: #4F46E5;
  --primary-light: rgba(99,102,241,0.1);

  /* 状态色 */
  --success-color: #22C55E;
  --warning-color: #F59E0B;
  --error-color:   #EF4444;
  --info-color:    #3B82F6;

  /* 背景 */
  --bg-primary:   #FFFFFF;
  --bg-secondary: #F8FAFC;
  --bg-tertiary:  #F1F5F9;

  /* 文字 */
  --text-primary:   #1E293B;
  --text-secondary: #64748B;
  --text-muted:     #94A3B8;

  /* 边框 */
  --border-color:     #E2E8F0;
  --border-radius:    8px;
  --border-radius-lg: 12px;

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.1), 0 8px 10px rgba(0,0,0,0.04);

  /* 过渡 */
  --transition-fast:   150ms cubic-bezier(0.4,0,0.2,1);
  --transition-normal: 250ms cubic-bezier(0.4,0,0.2,1);
}
```

---

## 四、各页面详细设计

### 4.1 Dashboard

#### Stat Cards

4 个 stat-card 改为 **2×2 网格**，每张卡片结构：

```
┌─────────────────────────────────┐
│  [Icon 40px]    数字（28px/700）│
│  圆角正方形      标签（12px）   │
│  主色10%背景                    │
│  ─────────────────────────────  │
│  较上周 +2 ↑（绿色 12px）      │
└─────────────────────────────────┘
```

| 卡片 | 图标 | 图标背景 |
|---|---|---|
| 数据集数量 | `database` | `rgba(99,102,241,0.1)` |
| 实验数量 | `flask-conical` | `rgba(34,197,94,0.1)` |
| 知识库数量 | `book-open` | `rgba(249,115,22,0.1)` |
| 可用模型 | `cpu` | `rgba(59,130,246,0.1)` |

#### 快捷操作栏

Dashboard 顶部新增一行按钮：「上传数据集」「新建实验」「查看最新结果」，分别跳转对应 tab。

#### 最近实验表格

增加「进度」列，`running` 状态显示动态蓝色进度条：

```css
@keyframes progress-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.progress-fill.running {
  animation: progress-pulse 1.5s ease-in-out infinite;
}
```

---

### 4.2 数据集上传（重点）

#### 状态 1：初始（空）

高度 160px，虚线圆角边框，中心对齐内容：

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│                                    │
│       [upload-cloud 48px]          │
│      拖拽 JSONL 文件至此处          │
│   或  点击选择文件  （#6366F1）    │
│                                    │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
  border: 2px dashed #E2E8F0
  border-radius: 12px
```

#### 状态 2：拖拽悬停

```css
.drop-zone.drag-over {
  border: 2px solid var(--primary-color);
  background: rgba(99,102,241,0.04);
}
.drop-zone.drag-over .drop-zone-icon { color: var(--primary-color); }
```

#### 状态 3：文件已选择

drop-zone 替换为文件信息卡片：

```
┌─────────────────────────────────────┐
│  📄 demo_qa_v1.jsonl           [×]  │
│     128 KB                          │
│  ✓ JSONL 格式正确 · 预检 120 条     │  ← 绿色
└─────────────────────────────────────┘
```

在 `upload.js` 中补充预验证逻辑（读取前 50KB，检查 JSON 格式）：

```js
async function prevalidateJsonl(file) {
  const text = await file.slice(0, 50000).text();
  const lines = text.split('\n').filter(l => l.trim());
  let errors = 0, firstError = null;
  lines.forEach((line, i) => {
    try { JSON.parse(line); }
    catch { errors++; if (!firstError) firstError = i + 1; }
  });
  return { total: lines.length, errors, firstError };
}
```

#### 状态 4：上传中 / 完成

```
上传中：
[████████████░░░░░░░░] 65%
已处理 78 / 120 条 · 0 个错误

上传成功（左侧绿色 4px 边框）：
✅ demo_qa_v1.jsonl · 120 条 · task_type: text_qa · v1
                                              [查看数据集 →]

上传失败（左侧红色 4px 边框）：
✗ 第 23 行 JSON 解析失败：缺少闭合括号
```

---

### 4.3 实验配置

#### 3 步引导式创建表单（Stepper）

```
● Step 1 ──────── ○ Step 2 ──────── ○ Step 3
  选择数据集         模型与策略         高级配置
```

| 步骤 | 标题 | 字段 |
|---|---|---|
| Step 1 | 选择数据集 | `dataset_path`、`split`、`max_samples` |
| Step 2 | 选择模型与策略 | `model`（provider + model_id）、`strategy` |
| Step 3 | 高级配置（默认折叠） | `concurrency`、`retry_times`、`evaluators`、`group_by` |

#### 策略选择卡片（Strategy Cards）

4 种推理策略改为 **2×2 卡片网格**：

```
┌──────────────────┐  ┌──────────────────┐
│  ⚡ Direct       │  │  🌿 CoT          │
│  直接生成答案     │  │  逐步推理后给出   │
│  速度最快         │  │  适合需要过程分析 │
└──────────────────┘  └──────────────────┘
┌──────────────────┐  ┌──────────────────┐
│  📋 Long CoT     │  │  🕸 ToT          │
│  深度分解子问题   │  │  树状搜索多路径   │
│  适合复杂推理     │  │  适合开放性问题   │
└──────────────────┘  └──────────────────┘
```

选中状态：边框 `2px solid #6366F1`，背景 `rgba(99,102,241,0.04)`。

---

### 4.4 结果分析

#### 骨架屏

```css
@keyframes skeleton-shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
.skeleton {
  background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 6px;
}
```

#### 指标卡片

| 指标 | 图标 | 颜色 |
|---|---|---|
| Accuracy | `target` | `#22C55E` 绿 |
| F1 Score | `activity` | `#3B82F6` 蓝 |
| Avg Latency | `clock` | `#F59E0B` 橙 |
| Avg Tokens | `file-text` | `#6366F1` 紫 |

#### 图表布局

- **左图**（50%）：准确率按 `difficulty` 分组的水平条形图
- **右图**（50%）：P50 / P95 延迟对比柱状图
- 响应式：`<900px` 时堆叠为单列

---

### 4.5 对话调试（Chat）

- **用户气泡**：右对齐，`#6366F1` 背景白字，`border-radius: 12px 12px 2px 12px`
- **AI 气泡**：左对齐，白底深色字，左侧 AI 头像圆圈，`border-radius: 12px 12px 12px 2px`
- **输入区**：`position: sticky; bottom: 0`，不随消息滚动
- **Placeholder**：`输入消息... (Ctrl+Enter 发送)`
- **流式光标**：`▌` 闪烁动画

---

## 五、文件改动清单

### 5.1 需要修改的文件

| 文件 | 改动类型 | 改动内容 |
|---|---|---|
| `webui/static/css/main.css` | **完整重写** | 新 CSS 变量、Inter 字体、深色侧边栏、阴影系统、skeleton 动画、strategy card 样式 |
| `webui/templates/base.html` | 局部修改 | 引入 Inter + Lucide CDN，emoji 替换为 `<i data-lucide="">` |
| `webui/templates/index.html` | 局部修改 | Stat card 结构、快捷操作、Strategy card、骨架屏、上传 4 状态 HTML |
| `webui/static/js/upload.js` | 局部修改 | 文件预验证逻辑、进度条更新函数、成功/失败 card 渲染 |

### 5.2 不需要修改的文件

| 文件 | 原因 |
|---|---|
| `webui/static/js/api.js` | API 调用逻辑不动，只改展示层 |
| `webui/static/js/experiment.js` | 实验管理逻辑完整，不动 |
| `webui/static/js/results.js` | 结果可视化 JS 不动，只改 HTML 骨架 |
| `src/` 下所有 Python 文件 | 后端不变 |

---

## 六、给 Claude Code 的约束与注意事项

### 6.1 不能破坏的功能点

| 约束项 | 具体要求 |
|---|---|
| **upload.js 变量名** | `#drop-zone`、`#file-input`、`#upload-status`、`datasetUploader` **不能改**，只改样式和包裹结构 |
| **tab 切换机制** | `switchTab()` 函数、`.tab-content.active` CSS 控制逻辑**保持不变** |
| **API 调用链路** | `API.xxx()` 所有调用不动，只改展示层 |
| **Lucide 初始化** | `base.html` 底部调用 `lucide.createIcons()`；`switchTab()` 后也重新调用一次 |
| **CSS 变量作用域** | 所有颜色值写在 `:root` 变量里，不允许 hardcode 颜色 |

### 6.2 实现顺序

1. 更新 `main.css` — CSS 变量、字体、深色侧边栏
2. 更新 `base.html` — 引入 Inter + Lucide，替换 emoji
3. 更新 Dashboard section — Stat card + 快捷操作
4. 更新 Datasets section — 上传 4 状态结构
5. 更新 `upload.js` — 预验证 + 进度条逻辑
6. 更新 Experiments section — Strategy card 结构
7. 更新 Results section — 骨架屏 + 图表占位
8. 更新 Chat section — 气泡样式 + 固定输入区

### 6.3 验收标准

- ✅ **上传数据集**：文件选择 → 预览 → 上传进度条 → 成功/失败反馈
- ✅ **新建实验**：3 步 Stepper → 策略卡片选择 → 提交
- ✅ **查看结果**：骨架屏 → 真实数据 → 图表渲染
- ✅ **侧边栏状态**：Milvus 状态灯正常显示
- ✅ **整体感观**：无 emoji、Inter 字体、深色侧边栏、主色 `#6366F1`

---

*AgentInferKit · WebUI 重设计规范 · v1.0 · D 岗交付物*

# 结果分析页重设计方案

> **范围**：`webui/templates/index.html`（Results tab）+ `webui/static/js/results.js`  
> **后端不变**：`src/api/results.py` 接口保持原样，只改前端渲染逻辑  
> **参考文档**：`FORMAT_AND_METRICS.md` v2.0

---

## 一、现状问题（基于截图 + 代码分析）

### 问题 1：指标卡分类错误

`renderMetrics()` 直接遍历 `metrics.overall` 的所有字段平铺成卡片，导致 **Valid Samples / Total Samples 这类元信息**和 **Exact Match / F1 等性能指标**混在同一排。元信息不是"评测结果"，不应出现在指标卡区域。

### 问题 2：图表 Y 轴量纲混乱（核心问题）

`createMetricsBarChart()` 把 `精确匹配(0.5)`、`F1(0.5)`、`平均延迟(1749ms)`、`Valid Samples(6)`、`Total Samples(6)` 全部放在同一个 Y 轴。1749ms 撑满整图，0.5 的准确率柱子接近于零，图表**完全没有信息价值**。

### 问题 3：无任务类型感知

`results.js` 对所有任务类型展示同一套指标卡 + 同一套图表，但 FORMAT_AND_METRICS.md 明确规定了四类任务（qa / text_exam / image_mcq / api_calling）对应完全不同的指标矩阵。

### 问题 4：分组统计没有 UI 入口

后端 `_load_metrics()` 已返回 `by_difficulty` / `by_topic` / `by_category` 等分组数据，但 `renderCharts()` 只处理了 `by_difficulty` 和 `by_topic`，其他分组维度（`by_call_type`、`by_question_type`）直接丢弃，且没有切换维度的 UI。

### 问题 5：样本级浏览入口缺失

后端 `GET /results/{experiment_id}/predictions` 已支持分页 + 过滤（correct / difficulty），但 UI 没有任何入口触达这个接口，用户无法查看单条预测结果。

### 问题 6：多实验对比功能无入口

`compareExperiments()` 函数已经写好，但 HTML 里没有触发它的 UI，该功能等于死代码。

---

## 二、重设计后的页面结构

```
┌──────────────────────────────────────────────────────────────────┐
│  结果分析                              [对比模式 ⇄] [导出 ↓]    │
│  查看实验评测指标与可视化图表                                      │
├──────────────────────────────────────────────────────────────────┤
│  🔍 选择实验...（带搜索的下拉，显示实验名 + task_type badge）     │
├────────────────┬─────────────────────────────────────────────────┤
│                │  ── 区域 A：实验元信息卡 ──────────────────────  │
│                │  实验ID / 数据集 / 模型 / 策略 / 样本数 / 耗时   │
│                │                                                  │
│                │  ── 区域 B：性能指标卡（按 task_type 动态渲染） ─ │
│  （隐藏，      │  [大卡片 × 3~4，只展示核心性能指标]              │
│   对比模式     │                                                  │
│   时展开为     │  ── 区域 C：效率指标卡（通用，小卡片） ──────────  │
│   实验列表）   │  Avg Latency | Avg Tokens | Total Cost | Trace   │
│                │                                                  │
│                │  ── 区域 D：图表区（按 task_type 动态渲染） ─────  │
│                │  [左图 50%] [右图 50%]                           │
│                │                                                  │
│                │  ── 区域 E：分组统计表（维度切换标签页） ─────────  │
│                │  [难度] [主题/类别] [调用类型] ...               │
│                │                                                  │
│                │  ── 区域 F：样本级浏览（折叠，默认收起） ─────────  │
│                │  分页表格 + 筛选（correct/difficulty）           │
└────────────────┴─────────────────────────────────────────────────┘
```

---

## 三、区域 A：实验元信息卡

从 `metrics.overall` 中**只提取元信息字段**，以横向 key-value pill 样式渲染，不作为"指标卡"：

```
┌──────────────────────────────────────────────────────────────┐
│  test_qa_cot_001                              [text_qa] [cot] │
│  数据集: demo_qa_v1 · test split   模型: deepseek-chat        │
│  样本: 6 有效 / 6 总计             完成时间: 2026-03-10 14:32  │
└──────────────────────────────────────────────────────────────┘
```

**JS 实现要点：**

```js
// 从 overall 中分离元信息字段，不渲染为指标卡
const META_FIELDS = new Set([
  'experiment_id', 'model', 'strategy', 'dataset',
  'total_samples', 'valid_samples', 'evaluated_at'
]);

// 渲染指标卡时过滤掉这些字段
const performanceEntries = Object.entries(overall)
  .filter(([k]) => !META_FIELDS.has(k));
```

---

## 四、区域 B：性能指标卡（task_type 感知）

根据 `metrics.task_type`（或从 `experiment_id` 对应实验的 `dataset_id` 推断）动态渲染不同指标卡。

### 指标卡配置表

```js
const METRIC_CARDS_BY_TASK = {
  qa: [
    { key: 'exact_match',  label: '精确匹配',  icon: 'target',    color: 'green',  fmt: 'pct' },
    { key: 'f1',           label: 'F1 分数',   icon: 'activity',  color: 'blue',   fmt: 'pct' },
    { key: 'rouge_l',      label: 'ROUGE-L',   icon: 'align-left',color: 'purple', fmt: 'pct' },
    { key: 'bleu',         label: 'BLEU',      icon: 'hash',      color: 'orange', fmt: 'pct' },
  ],
  text_exam: [
    { key: 'choice_accuracy', label: '选择题准确率', icon: 'check-circle', color: 'green',  fmt: 'pct' },
    { key: 'win_rate',        label: 'Win Rate',    icon: 'trophy',       color: 'yellow', fmt: 'pct' },
  ],
  image_mcq: [
    { key: 'choice_accuracy',      label: '选择题准确率',  icon: 'check-circle',  color: 'green',  fmt: 'pct' },
    { key: 'grounding_error_rate', label: 'Grounding 错误率', icon: 'eye-off',   color: 'red',    fmt: 'pct' },
    { key: 'win_rate',             label: 'Win Rate',     icon: 'trophy',       color: 'yellow', fmt: 'pct' },
  ],
  api_calling: [
    { key: 'tool_selection_accuracy',  label: '工具选择准确率',  icon: 'wrench',    color: 'blue',   fmt: 'pct' },
    { key: 'parameter_accuracy',       label: '参数准确率',      icon: 'sliders',   color: 'green',  fmt: 'pct' },
    { key: 'end_to_end_success_rate',  label: '端到端成功率',    icon: 'check-circle', color: 'purple', fmt: 'pct' },
    { key: 'invalid_call_rate',        label: '无效调用率',      icon: 'x-circle',  color: 'red',    fmt: 'pct' },
  ],
};
```

### 指标卡样式

每张大卡片结构（参考整体 UI 方案的 stat-card）：

```
┌─────────────────────────────────┐
│  [icon 20px]  精确匹配          │
│  绿色图标区   ────────────────   │
│               50.0%  ← 大字     │
│               (3/6 correct)     │← 小字辅助信息
└─────────────────────────────────┘
```

---

## 五、区域 C：效率指标卡（通用）

所有任务类型统一显示，以**小卡片 + 灰色调**区别于性能指标区：

| 指标 | 图标 | 格式 |
|---|---|---|
| `avg_latency_ms` | `clock` | `1749 ms` |
| `avg_tokens` | `file-text` | `284 tok` |
| `total_cost_usd` | `dollar-sign` | `$0.0023` |
| `avg_trace_tokens` | `git-branch` | `0 tok`（direct 为 0） |

> **关键修复**：这 4 个效率指标单独一排，绝不与性能指标共用图表 Y 轴。

---

## 六、区域 D：图表区（按 task_type 动态渲染）

### 图表选型原则

- **性能指标** → 百分比，用**水平条形图**（横向更易读，标签不遮挡）
- **分布数据** → 用**柱状图**
- **延迟数据** → 单独图表，Y 轴单位为 ms
- **绝不混用量纲不同的指标在同一 Y 轴**

---

### qa 任务：2 图

**左图：文本指标对比**（水平条形图）

```
精确匹配  ████████░░  50.0%
F1 分数   ████████░░  50.0%
ROUGE-L   █████░░░░░  38.2%
BLEU      ████░░░░░░  31.5%

Y 轴：指标名  X 轴：0~100%
```

**右图：延迟分布**（柱状图，Y 轴单位 ms）

```
P50延迟  ████  1200ms
P95延迟  ██████████ 3100ms
平均延迟 █████  1749ms

Y 轴：ms（独立轴，不与准确率混用）
```

---

### text_exam 任务：3 图

**左图：按难度分组准确率**（水平条形图）

```
easy   ██████████  80.0%
medium ████████░░  60.0%
hard   ████░░░░░░  30.0%
```

**中图：选项偏置分布**（饼图 / 柱状图）

```
A  █████  30%
B  ████   25%
C  ████   25%
D  ███    20%
```

> 选项偏置来自 `_wrap_option_bias()` 返回的 `distribution` 字段，已在 registry.py 中实现。

**右图：按主题分组准确率**（水平条形图，若有 by_topic 数据）

---

### image_mcq 任务：3 图

**左图：按题型分组准确率**（水平条形图）

```
object_recognition  ████████  70%
attribute           ██████░░  55%
relation            ████░░░░  40%
ocr                 ███░░░░░  30%
```

> 来自 `by_question_type` 分组，`metadata.question_type` 字段。

**中图：难度分组准确率**（条形图）

**右图：选项偏置**（柱状图）

---

### api_calling 任务：3 图

**左图：4 个 Agent 指标对比**（水平条形图，统一 0~100% 轴）

```
工具选择准确率  ████████  75%
参数准确率      ██████░░  60%
端到端成功率    █████░░░  50%
无效调用率      ██░░░░░░  20%  ← 越低越好（红色）
```

> 注意：`invalid_call_rate` 语义相反，条形用红色且标注"越低越好"。

**中图：按调用类型分组成功率**（水平条形图）

```
single_tool   ████████  80%
multi_tool    █████░░░  50%
multi_step    ████░░░░  40%
param_sensitive ███░░░  30%
```

> 来自 `by_call_type` 分组。

**右图：平均工具调用次数 vs 端到端成功率**（散点图，按策略着色）

---

## 七、区域 E：分组统计表（标签页切换）

在图表区下方，将所有分组维度以**标签页（Tab）**形式组织，用户点击切换：

```
[按难度] [按主题] [按调用类型] [按题型]
         ↑ 根据 task_type 动态显示可用标签
```

每个标签页内为一张统计表：

| 分组 | 样本数 | 准确率 | Avg Latency | Avg Tokens |
|---|---|---|---|---|
| easy | 20 | 80.0% | 1200ms | 210 |
| medium | 30 | 60.0% | 1800ms | 285 |
| hard | 10 | 30.0% | 2400ms | 360 |

**JS 实现：**

```js
// 分组维度配置（根据 task_type 过滤显示）
const GROUP_DIMS = {
  by_difficulty:   { label: '按难度',    tasks: ['qa','text_exam','image_mcq','api_calling'] },
  by_topic:        { label: '按主题',    tasks: ['qa','text_exam'] },
  by_question_type:{ label: '按题型',    tasks: ['text_exam','image_mcq'] },
  by_category:     { label: '按设备类别', tasks: ['api_calling'] },
  by_call_type:    { label: '按调用类型', tasks: ['api_calling'] },
};

function renderGroupTabs(metrics, taskType) {
  const available = Object.entries(GROUP_DIMS)
    .filter(([key, cfg]) => cfg.tasks.includes(taskType) && metrics[key]?.length > 0);
  // 渲染标签页...
}
```

---

## 八、区域 F：样本级浏览（折叠面板）

默认折叠，点击「查看样本详情 ▼」展开。

**筛选栏：**

```
[全部 ▼] [正确 ✓] [错误 ✗]     难度: [全部 ▼]     🔍 搜索 sample_id
```

**表格列（根据 task_type）：**

| sample_id | 预测答案 | 正确答案 | 是否正确 | 延迟 | Token |
|---|---|---|---|---|---|
| qa_001 | 巴黎 | 巴黎 | ✅ | 1.2s | 210 |
| qa_002 | 柏林 | 巴黎 | ❌ | 2.1s | 285 |

- api_calling 任务额外显示「工具调用链」列，点击展开 tool_trace
- 点击行 → 右侧弹出 Drawer，显示完整 `reasoning_trace` 和 `input_prompt`

**分页：** 20 条/页，支持上一页/下一页。调用 `GET /results/{experiment_id}/predictions?offset=X&limit=20&correct=true`。

---

## 九、对比模式

点击「对比模式 ⇄」按钮后，页面切换为对比视图：

```
┌────────────────────────────────────────────────────────────────┐
│  实验对比                               [退出对比模式 ×]       │
├────────────────────────────────────────────────────────────────┤
│  + 添加实验（最多 4 个）                                        │
│  [test_qa_direct ×]  [test_qa_cot ×]  [test_qa_tot ×]          │
├────────────────────────────────────────────────────────────────┤
│  对比指标选择：[✓ 精确匹配] [✓ F1] [□ ROUGE-L] [✓ Avg Latency] │
├────────────────────────────────────────────────────────────────┤
│  对比图表（分组柱状图，每个指标一组，按实验着色）               │
│                                                                 │
│  对比汇总表                                                     │
│  指标 | direct | cot | tot | △ best vs direct                  │
└────────────────────────────────────────────────────────────────┘
```

调用已有的 `API.Results.compare(experimentIds, metrics)` 接口，不需要修改后端。

---

## 十、文件改动清单

### 10.1 需要修改的文件

| 文件 | 改动类型 | 核心改动内容 |
|---|---|---|
| `webui/static/js/results.js` | **重构** | `renderMetrics()` 增加 task_type 感知；`renderCharts()` 按任务类型分路渲染；新增 `renderGroupTabs()`、`renderSampleBrowser()`、`renderCompareMode()` |
| `webui/templates/index.html` | 局部修改 | Results tab 新增骨架 HTML：元信息区、性能/效率指标分区、分组统计标签页容器、样本浏览折叠面板、对比模式按钮 |

### 10.2 不需要修改的文件

| 文件 | 原因 |
|---|---|
| `src/api/results.py` | 已提供所需的全部接口 |
| `src/evaluators/` | 评测逻辑完整，不动 |
| `webui/static/js/api.js` | API 调用层不动 |

---

## 十一、results.js 核心重构思路

### 11.1 主入口 `loadMetrics()` 改造

```js
async loadMetrics(experimentId) {
  this.currentExperimentId = experimentId;
  this.showSkeleton();  // 显示骨架屏

  const [metrics, expInfo] = await Promise.all([
    API.getMetrics(experimentId),
    API.fetchExperiment(experimentId).catch(() => null),
  ]);

  const taskType = expInfo?.dataset_id
    ? this.inferTaskType(expInfo.dataset_id)
    : metrics.task_type || 'qa';  // fallback

  this.renderExperimentMeta(metrics, expInfo);       // 区域 A
  this.renderPerformanceCards(metrics, taskType);    // 区域 B
  this.renderEfficiencyCards(metrics);               // 区域 C
  this.renderTaskCharts(metrics, taskType);          // 区域 D
  this.renderGroupTabs(metrics, taskType);           // 区域 E
  this.initSampleBrowser(experimentId);              // 区域 F（懒加载）
}
```

### 11.2 图表量纲分离原则

```js
renderTaskCharts(metrics, taskType) {
  // 性能图表（0~100% 轴）
  this.createHorizontalBar('perf-chart', {
    data: this.getPerformanceData(metrics, taskType),
    xMax: 100,
    unit: '%',
  });

  // 延迟图表（独立 ms 轴，绝不与性能混用）
  this.createLatencyChart('latency-chart', {
    p50: metrics.overall?.latency_p50_ms,
    p95: metrics.overall?.latency_p95_ms,
    avg: metrics.overall?.avg_latency_ms,
  });

  // 任务特定图表
  if (taskType === 'text_exam' || taskType === 'image_mcq') {
    this.createOptionBiasChart('bias-chart', metrics.option_bias);
  }
  if (taskType === 'api_calling') {
    this.createCallTypeChart('calltype-chart', metrics.by_call_type);
  }
}
```

### 11.3 选项偏置图（已有数据，需新增渲染）

```js
// option_bias 字段来自 _wrap_option_bias()，结构：
// { distribution: { A: 0.30, B: 0.25, C: 0.25, D: 0.20 }, total: 120 }

createOptionBiasChart(id, optionBias) {
  if (!optionBias?.distribution) return;
  const dist = optionBias.distribution;
  // 饼图（分布接近 25% 为理想）
  // 可视化哪个选项被过度选择
}
```

---

## 十二、验收标准

- ✅ **量纲分离**：性能指标（%）和延迟（ms）不出现在同一图表的同一 Y 轴
- ✅ **元信息不作为指标卡**：Valid Samples / Total Samples 只在元信息区显示
- ✅ **task_type 感知**：qa / text_exam / image_mcq / api_calling 四种任务展示不同指标卡和图表
- ✅ **选项偏置可视化**：text_exam 和 image_mcq 任务展示 A/B/C/D 选项分布图
- ✅ **分组统计可切换**：by_difficulty / by_topic / by_call_type 等维度可通过标签页切换
- ✅ **样本级浏览**：可分页查看单条预测，支持 correct/difficulty 过滤
- ✅ **对比模式可用**：调用已有 compare API，支持最多 4 个实验对比

---

*AgentInferKit · 结果分析页重设计方案 · v1.0 · D 岗交付物*


# 实验配置页重设计方案

> **核心方向**：推理（Inference）与评估（Evaluation）彻底分离  
> **覆盖范围**：`experiment.js` + `index.html` Experiments tab + `src/api/schemas.py`（微调）  
> **对齐需求**：实验组 A（QA/RAG）、实验组 B（image_mcq）、实验组 C（api_calling + CoT/ToT）

---

## 一、现状 Gap 分析

### Gap 1：推理与评估耦合（最核心问题）

当前 `ExperimentCreateRequest` 把 `eval: EvalConfig`（评估指标 + 分组维度）和推理参数（model、strategy、rag）打包在一起，**一次创建 = 推理 + 评估同时配置**，违背老板「推理和评估分开」的要求。

正确架构应当是：
- **推理配置（Inference Config）**：选数据、选模型、选策略、选 RAG 模式 → 生成 `predictions.jsonl`
- **评估配置（Evaluation Config）**：选 predictions 文件、选指标、选分组维度 → 生成 `metrics.json`

### Gap 2：截图中「模型与策略」是 Step 2，但 Step 1 已包含模型

截图里 Step 1（基本信息）里已经有了「模型」下拉框，Step 2 又是「模型与策略」，**字段重复**，说明 Stepper 步骤分配混乱，用户完全不知道每步在做什么。

### Gap 3：RAG 配置完全缺失

后端 `RAGConfig` 已定义三种模式（`closed` / `oracle` / `retrieved`），实验组 A 的核心就是 wo RAG / Oracle RAG / Retrieved RAG 三种对比实验，但**当前表单没有任何 RAG 相关字段**，导致实验组 A 根本无法在 UI 上配置。

### Gap 4：评估指标配置无感知

当前「评估指标」字段是一个**纯文本输入框**（`value="accuracy"`），用户需要手动输入逗号分隔的指标名。但 FORMAT_AND_METRICS.md 规定了四种 task_type 各有不同的指标集，用户根本不知道该填什么。

### Gap 5：api_calling 无工具配置入口

实验组 C 的核心是工具调用评测，需要指定 `available_tools` / `tool_index`，但表单没有任何工具相关字段。

### Gap 6：没有「保存推理结果 + 单独评估」的操作路径

当前只有「创建实验」一个按钮，没有「仅运行推理」和「对已有 predictions 运行评估」两个独立入口。

---

## 二、重设计：推理与评估彻底分离

### 2.1 页面整体结构

```
实验配置（Experiments Tab）
│
├── 子 Tab 1：推理任务（Inference）← 主功能
│     ├── 创建推理任务表单（Stepper，3 步）
│     └── 推理任务列表
│
└── 子 Tab 2：评估任务（Evaluation）← 结果分析的入口
      ├── 对已有 predictions 运行评估
      └── 评估历史（跳转结果分析页）
```

> **注**：评估任务完成后，跳转到「结果分析」页面展示。结果分析页本身就是「评估结果的持久化视图」，满足「保存结果」的需求（metrics.json 已写到 `outputs/metrics/`）。

---

### 2.2 推理任务：重新设计的 3 步 Stepper

#### Step 1：数据选择

| 字段 | 控件类型 | 说明 |
|---|---|---|
| 实验名称 * | 文本输入 | 推荐格式：`{数据集}_{模型}_{策略}` |
| 描述 | 文本域 | 可选 |
| 数据集 * | 卡片式选择 | 显示数据集名 + task_type badge + 样本数 |
| 数据分割 | 下拉 | train / dev / test |
| 最大样本数 | 数字输入 | 留空 = 全部 |

**task_type 自动识别**：选择数据集后，从数据集元信息中读取 `task_type`，后续步骤根据 task_type 动态显示不同字段。

---

#### Step 2：推理配置（根据 task_type 动态渲染）

**通用字段（所有任务）：**

| 字段 | 控件类型 | 说明 |
|---|---|---|
| 模型 * | 下拉 | 显示 provider + model_id |
| 推理策略 * | 卡片式选择（4选1） | Direct / CoT / Long CoT / ToT |

**text_exam 任务（实验组 A）额外显示：RAG 配置区**

```
RAG 模式
  ○ Closed-book（不使用外部知识，直接作答）    ← wo RAG
  ○ Oracle RAG（使用标注好的正确知识块）        ← Oracle RAG  
  ● Retrieved RAG（从知识库自动检索）           ← Retrieved RAG

[仅 Retrieved RAG 显示以下字段]
知识库        [选择知识库...  ▼]
Top-K 召回数  [3            ±]
```

> 这三种模式直接对应实验组 A 的三种协议，让研究员在 UI 上选择后直接生成对应配置。

**api_calling 任务（实验组 C）额外显示：工具配置区**

```
工具集
  ☑ search_api    ☑ tool_elec_0001    □ tool_elec_0002    □ ...
  （从 data/schemas/tool_schemas/ 读取可用工具列表）

Mock 模式      ● 使用 mock responses    ○ 真实调用
```

**image_mcq 任务（实验组 B）额外显示：视觉模型提示**

```
ℹ  图像任务需要支持多模态的模型（VLM）
   当前选择的 deepseek-chat 不支持图像输入，请选择支持视觉的模型。
```

---

#### Step 3：运行参数

| 字段 | 控件类型 | 默认值 | 说明 |
|---|---|---|---|
| 并发数 | 数字输入 | 5 | 1~50 |
| 重试次数 | 数字输入 | 3 | 0~10 |
| 随机种子 | 数字输入 | 留空 | 用于复现 |
| 断点续跑 | Toggle | 开 | 中断后可恢复 |

**底部按钮：**

```
[取消]                    [保存配置]  [▶ 开始推理]
```

- **保存配置**：保存为 YAML 配置文件但不执行，供 Claude Code CLI 复用
- **开始推理**：创建实验 + 立即运行

---

### 2.3 评估任务：独立入口

在「评估任务」子 Tab 中：

```
┌─────────────────────────────────────────────────────┐
│  对已有推理结果运行评估                               │
├─────────────────────────────────────────────────────┤
│  推理结果文件 *                                      │
│  [选择 predictions 文件...  ▼]                       │
│  （列出 outputs/predictions/ 下所有 .jsonl 文件）    │
│                                                      │
│  评估指标（自动根据 task_type 预填，可调整）          │
│  ┌────────────────────────────────────────────────┐ │
│  │ ☑ exact_match  ☑ f1_score  ☑ rouge_l  □ bleu  │ │  ← qa 任务
│  │ ☑ choice_accuracy  ☑ option_bias  ☑ win_rate   │ │  ← text_exam
│  │ ☑ tool_selection_accuracy  ☑ parameter_accuracy│ │  ← api_calling
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  分组统计维度（可多选）                               │
│  ☑ 按难度  ☑ 按主题  □ 按调用类型  □ 按题型         │
│                                                      │
│  Baseline 对比（用于计算 win_rate，可选）             │
│  [选择基线实验...  ▼]                                │
│                                                      │
│  [▶ 运行评估]                                        │
└─────────────────────────────────────────────────────┘
```

评估完成后：
1. 写入 `outputs/metrics/{experiment_id}.json`
2. 自动跳转至「结果分析」页展示结果
3. 在「结果分析」页提供「导出报告」按钮（JSON / CSV）

---

## 三、三种实验流程的完整 UI 路径

### 实验组 A：QA / text_exam + RAG 对比

**要跑的三个实验：**

```
实验 1：text_exam_direct_closed
  数据集: demo_exam_cs  模型: deepseek-chat  策略: Direct  RAG: Closed-book

实验 2：text_exam_cot_oracle  
  数据集: demo_exam_cs  模型: deepseek-chat  策略: CoT  RAG: Oracle RAG

实验 3：text_exam_cot_retrieved
  数据集: demo_exam_cs  模型: deepseek-chat  策略: CoT  RAG: Retrieved RAG  知识库: qa_chunks  Top-K: 3
```

**UI 操作路径：**

```
Step 1: 选 demo_exam_cs → 自动识别 task_type=text_exam
Step 2: 选 deepseek-chat + 选 CoT + RAG 模式选「Retrieved RAG」
        → 出现知识库选择 + top_k 配置
Step 3: 默认参数 → 开始推理
→ 推理完成后，进入「评估任务」Tab
→ 选刚生成的 predictions 文件
→ 指标自动预填：choice_accuracy ✓ option_bias ✓ win_rate ✓
→ 分组：按难度 ✓ 按主题 ✓
→ 运行评估 → 跳转结果分析
```

---

### 实验组 B：image_mcq VLM 测试

**UI 操作路径：**

```
Step 1: 选 image_mcq 数据集 → 自动识别 task_type=image_mcq
Step 2: 选 VLM 模型（如 gpt-4o）
        → 若选了纯文本模型，显示 ⚠ 警告
        策略选 Direct（图像任务推荐直接作答）
Step 3: 开始推理
→ 评估：指标自动预填 choice_accuracy + grounding_error_rate + option_bias
→ 分组：按题型 ✓ 按难度 ✓
```

---

### 实验组 C：api_calling + CoT/ToT 对比

**要跑的 4 个实验（对比矩阵）：**

```
demo_agent × Direct
demo_agent × CoT
demo_agent × Long CoT
demo_agent × ToT
```

**UI 操作路径：**

```
Step 1: 选 demo_agent → 自动识别 task_type=api_calling
Step 2: 选模型 + 选策略（4 个实验各跑一次，每次选不同策略）
        → 工具配置区出现：勾选 search_api ✓  Mock 模式: 开
Step 3: 开始推理
→ 评估：指标自动预填 tool_selection_accuracy + parameter_accuracy + end_to_end_success_rate + invalid_call_rate + avg_tool_calls
→ 分组：按调用类型 ✓
```

**对比视图**：4 个实验完成后，在结果分析页进入「对比模式」，选择这 4 个实验，生成策略对比图。

---

## 四、评估指标的自动预填逻辑

根据上传数据集的 `eval_type` 字段（已在数据文件中存在）自动推断并预填：

```js
const DEFAULT_METRICS_BY_TASK = {
  qa: {
    performance: ['exact_match', 'f1_score', 'rouge_l'],
    efficiency:  ['avg_latency_ms', 'avg_tokens', 'total_cost_usd'],
    optional:    ['bleu', 'win_rate', 'avg_trace_tokens'],
  },
  text_exam: {
    performance: ['choice_accuracy', 'option_bias', 'win_rate'],
    efficiency:  ['avg_latency_ms', 'avg_tokens', 'total_cost_usd'],
    optional:    ['avg_trace_tokens'],
    // RAG 额外指标（仅 retrieved 模式）
    rag:         ['retrieval_recall_at_k', 'evidence_hit_rate', 'answer_evidence_alignment'],
  },
  image_mcq: {
    performance: ['choice_accuracy', 'option_bias', 'grounding_error_rate'],
    efficiency:  ['avg_latency_ms', 'avg_tokens', 'total_cost_usd'],
    optional:    ['win_rate'],
  },
  api_calling: {
    performance: ['tool_selection_accuracy', 'parameter_accuracy', 'end_to_end_success_rate', 'invalid_call_rate'],
    efficiency:  ['avg_tool_calls', 'avg_latency_ms', 'avg_tokens', 'total_cost_usd'],
    optional:    ['avg_reasoning_steps', 'avg_trace_tokens'],
  },
};
```

---

## 五、文件改动清单

### 5.1 前端（重构）

| 文件 | 改动 |
|---|---|
| `webui/static/js/experiment.js` | 重构：拆分为 `InferenceManager` + `EvaluationManager` 两个 class；Stepper 增加 task_type 感知；RAG / 工具配置区按 task_type 动态显示 |
| `webui/templates/index.html` | Experiments tab 增加「推理 / 评估」子 Tab；评估表单新增指标 checkbox 组 + 分组多选 + baseline 对比选择 |

### 5.2 后端（微调）

| 文件 | 改动 | 说明 |
|---|---|---|
| `src/api/schemas.py` | `ExperimentCreateRequest` 拆分评估字段 | 推理请求不需要 eval config，或将 eval 设为完全可选 |
| `src/api/experiments.py` | 新增 `POST /experiments/{id}/evaluate` 端点 | 接收 predictions 文件路径 + 指标配置，触发独立评估 |

### 5.3 不需要修改

| 文件 | 原因 |
|---|---|
| `src/evaluators/` | 评测逻辑完整，不动 |
| `src/api/results.py` | 读取 metrics.json 的逻辑不变 |
| `webui/static/js/api.js` | 增加 `API.Experiments.evaluate()` 调用即可 |

---

## 六、给 Claude Code 的实现约束

1. **`experimentManager.getFormData()`** 中的字段名（`name`, `dataset_id`, `model_id`, `strategy`）不能改，只扩展
2. **`experimentManager.runExperiment()`** 逻辑不动，只改触发方式
3. **`experimentManager.renderExperimentList()`** 在列表中增加「评估」按钮（对 finished 状态的实验），点击跳转到评估 Tab 并预填 predictions 路径
4. task_type 识别逻辑：从数据集 API 返回的 `task_type` 字段读取，缓存在 `currentDatasetTaskType` 变量中，Step 2 渲染时读取
5. RAG 配置区默认隐藏，仅 `task_type === 'text_exam'` 时显示
6. 工具配置区默认隐藏，仅 `task_type === 'api_calling'` 时显示

---

## 七、验收标准

- ✅ **推理/评估分离**：可以只跑推理生成 predictions，再单独选择 predictions 文件运行评估
- ✅ **实验组 A 可配置**：text_exam 数据集下，Step 2 出现 RAG 配置区，可选 closed / oracle / retrieved 三种模式
- ✅ **实验组 B 可配置**：image_mcq 数据集下，选择纯文本模型时显示 VLM 警告
- ✅ **实验组 C 可配置**：api_calling 数据集下，Step 2 出现工具选择区
- ✅ **评估指标自动预填**：根据 task_type 自动勾选对应的默认指标 checkbox
- ✅ **结果保存**：评估完成后 metrics.json 写入 outputs/metrics/，结果分析页可展示并导出

---

*AgentInferKit · 实验配置页重设计方案 · v1.0 · D 岗交付物*