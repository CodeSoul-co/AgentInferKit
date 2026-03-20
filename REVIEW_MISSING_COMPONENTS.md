# zyf_code 分支缺失组件清单

## 一、五层工具抽象（文档第5节）

### 层缺失内容

**接口层**
- ❌ 权限要求
- ❌ 前置/后置条件声明
- ❌ 工具版本信息

**状态层**
- ❌ relations/resources/policies 有字段但无工具实际使用

**执行层**
- ❌ timeout
- ❌ retry
- ❌ partial completion
- ❌ async completion
- ❌ 幂等语义

**环境层**
- ❌ 全部缺失

**观测层**
- ❌ 全部缺失

---

## 二、演示域（文档第8节）

- ✅ **File-Search 域**（已完成）
- ❌ **Calendar 域**（create/search/update/delete event，冲突检测）
- ❌ **Issue-Tracker 域**（create/assign/comment/close/reopen，状态转移规则）

---

## 三、后端系统（文档第9节）

- ❌ `backends/` 目录整体缺失
- ❌ MockBackend（有状态版，区别于现有 stateless mock）
- ❌ SandboxBackend（SQLite/临时文件系统）
- ❌ LiveBackend（真实 API 对接）
- ❌ 三类后端统一 schema/trace/evaluator 接口

---

## 四、扰动与鲁棒性（文档第10节）

- ❌ `faults/` 目录整体缺失
- ❌ schema_drift.py（字段名变化、枚举值变化）
- ❌ latency.py（网络抖动、延迟分布）
- ❌ partial_failure.py（transient failure、partial completion）
- ❌ stale_state.py（延迟物化、stale result）
- ❌ observation_noise.py（模糊错误、部分屏蔽日志）

---

## 五、观测模块（文档第5.5节 + 第12节）

- ❌ `observation/` 目录整体缺失
- ❌ formatter.py
- ❌ masking.py
- ❌ diagnostics.py

---

## 六、WorldState 扩展（文档第6节）

- ❌ SideEffectScheduler（异步副作用调度，如 file.write 后延迟进入索引）
- ❌ PolicyEngine（ACL、角色权限、业务规则）
- ❌ clock（模拟时间）

---

## 七、评测指标（文档第11节）

当前 evaluator 缺少以下指标：

- ❌ pass^k
- ❌ invalid call rate
- ❌ recovery rate
- ❌ state corruption rate
- ❌ token cost
- ❌ latency

---

**最后更新：2026-03-20**
