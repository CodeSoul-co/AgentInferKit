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
