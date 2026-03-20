"""
tool_spec.py — 最小工具抽象

定义 toolsim 中有状态工具的核心接口：
  - ToolExecutionResult  执行结果数据容器（dataclass）
  - ToolSpec             工具规范抽象基类（ABC）

设计原则：
  - 最小接口：不预设 backend、权限、副作用调度等复杂机制
  - 每个工具是一个独立的 ToolSpec 子类，持有自己的元数据
  - execute() 接收 WorldState（可能被原地修改）和参数字典，返回结果对象
  - 调用方通过 state_changed 标志感知状态是否真的发生了改变
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from toolsim.world_state import WorldState


# ------------------------------------------------------------------
# 执行结果
# ------------------------------------------------------------------

@dataclass
class ToolExecutionResult:
    """单次工具调用的执行结果。

    Attributes:
        success:       是否执行成功。
        observation:   调用方可观察到的结构化输出（不含敏感内部字段）。
        error:         失败时的错误描述；成功时为 None。
        state_changed: 此次调用是否真正修改了 WorldState。
    """

    success: bool
    observation: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    state_changed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """序列化为普通字典，方便日志和传输。"""
        return {
            "success": self.success,
            "observation": self.observation,
            "error": self.error,
            "state_changed": self.state_changed,
        }


# ------------------------------------------------------------------
# 工具规范基类
# ------------------------------------------------------------------

class ToolSpec(ABC):
    """有状态工具规范的抽象基类。

    子类只需要：
      1. 声明 tool_name / description / input_schema 三个类属性
      2. 实现 execute() 方法

    input_schema 遵循简化的 JSON Schema 风格（dict），
    仅作文档和 prompt 注入用，当前阶段不做运行时校验。
    """

    #: 工具唯一名称，建议用 "domain.action" 格式，例如 "file.write"
    tool_name: str
    #: 工具的自然语言说明，用于 prompt 注入
    description: str
    #: 输入参数的 JSON Schema 风格描述
    input_schema: Dict[str, Any]

    @abstractmethod
    def execute(self, state: WorldState, args: Dict[str, Any]) -> ToolExecutionResult:
        """执行工具，允许原地修改 state。

        Args:
            state: 当前世界状态，工具可读取或修改。
            args:  工具输入参数字典，结构由 input_schema 描述。

        Returns:
            ToolExecutionResult 实例。
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tool_name={self.tool_name!r})"
