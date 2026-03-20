"""
world_state.py — WorldState 原型

为 toolsim 模块提供一个最小可运行的"世界状态"基础对象，
供后续 executor、tool spec、snapshot、evaluator 等组件使用。

设计原则：
  - 可读 / 可写 / 可快照 / 可哈希
  - 仅依赖标准库，不引入外部依赖
  - 状态变更时自动递增 version，以便追踪变更历史
"""

import copy
import hashlib
import json
from typing import Any, Dict, Optional


class WorldState:
    """有状态世界的最小原型对象。

    维护实体（entities）、关系（relations）、资源（resources）、
    策略（policies）四类数据，以及模拟时钟（clock）和版本号（version）。

    每次调用 set_entity / delete_entity 后 version 自动 +1，
    保证调用方可通过版本号感知状态是否发生变化。
    """

    # ------------------------------------------------------------------
    # 构造
    # ------------------------------------------------------------------

    def __init__(
        self,
        entities: Optional[Dict[str, Dict[str, Any]]] = None,
        relations: Optional[Dict[str, Any]] = None,
        resources: Optional[Dict[str, Any]] = None,
        policies: Optional[Dict[str, Any]] = None,
        clock: float = 0.0,
        version: int = 0,
    ) -> None:
        self.entities: Dict[str, Dict[str, Any]] = entities if entities is not None else {}
        self.relations: Dict[str, Any] = relations if relations is not None else {}
        self.resources: Dict[str, Any] = resources if resources is not None else {}
        self.policies: Dict[str, Any] = policies if policies is not None else {}
        self.clock: float = clock
        self.version: int = version

    # ------------------------------------------------------------------
    # 序列化 / 反序列化
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """将当前状态导出为普通字典（浅拷贝字段，适合日志/传输）。"""
        return {
            "entities": copy.deepcopy(self.entities),
            "relations": copy.deepcopy(self.relations),
            "resources": copy.deepcopy(self.resources),
            "policies": copy.deepcopy(self.policies),
            "clock": self.clock,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldState":
        """从字典构造 WorldState 实例。

        Args:
            data: 由 to_dict() 或 snapshot() 产生的字典。

        Returns:
            新的 WorldState 实例。
        """
        return cls(
            entities=copy.deepcopy(data.get("entities", {})),
            relations=copy.deepcopy(data.get("relations", {})),
            resources=copy.deepcopy(data.get("resources", {})),
            policies=copy.deepcopy(data.get("policies", {})),
            clock=float(data.get("clock", 0.0)),
            version=int(data.get("version", 0)),
        )

    # ------------------------------------------------------------------
    # 实体 CRUD
    # ------------------------------------------------------------------

    def get_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """读取指定实体。

        Args:
            entity_type: 实体类型，例如 "user"、"file"。
            entity_id:   实体唯一标识符。

        Returns:
            实体数据字典，若不存在则返回 None。
        """
        return self.entities.get(entity_type, {}).get(entity_id)

    def set_entity(self, entity_type: str, entity_id: str, value: Dict[str, Any]) -> None:
        """写入或覆盖一个实体，并令 version +1。

        Args:
            entity_type: 实体类型。
            entity_id:   实体唯一标识符。
            value:       实体数据字典（会被深拷贝存储，避免外部引用污染）。
        """
        if entity_type not in self.entities:
            self.entities[entity_type] = {}
        self.entities[entity_type][entity_id] = copy.deepcopy(value)
        self.version += 1

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """删除指定实体，若实体存在则令 version +1。

        Args:
            entity_type: 实体类型。
            entity_id:   实体唯一标识符。

        Returns:
            True 表示删除成功，False 表示实体不存在。
        """
        bucket = self.entities.get(entity_type, {})
        if entity_id not in bucket:
            return False
        del bucket[entity_id]
        # 清理空桶，保持结构整洁
        if not bucket:
            del self.entities[entity_type]
        self.version += 1
        return True

    # ------------------------------------------------------------------
    # 快照 / 恢复
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """返回当前状态的完整深拷贝快照，可用于 restore()。

        Returns:
            可完整恢复状态的字典。
        """
        return self.to_dict()

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """从快照完整恢复状态（原地替换所有字段）。

        Args:
            snapshot: 由 snapshot() 产生的字典。
        """
        restored = WorldState.from_dict(snapshot)
        self.entities = restored.entities
        self.relations = restored.relations
        self.resources = restored.resources
        self.policies = restored.policies
        self.clock = restored.clock
        self.version = restored.version

    # ------------------------------------------------------------------
    # 状态哈希
    # ------------------------------------------------------------------

    def compute_hash(self) -> str:
        """计算当前状态的稳定 SHA-256 哈希值。

        使用 sort_keys=True 确保字典键排序一致，
        避免因 Python dict 插入顺序不同导致哈希不稳定。

        Returns:
            64 位十六进制字符串。
        """
        payload = self._stable_serialize()
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # 私有辅助
    # ------------------------------------------------------------------

    def _stable_serialize(self) -> str:
        """将状态序列化为键有序的 JSON 字符串，供哈希计算使用。"""
        data = {
            "entities": self.entities,
            "relations": self.relations,
            "resources": self.resources,
            "policies": self.policies,
            "clock": self.clock,
            "version": self.version,
        }
        return json.dumps(data, sort_keys=True, ensure_ascii=False)

    def __repr__(self) -> str:
        entity_count = sum(len(v) for v in self.entities.values())
        return (
            f"WorldState(version={self.version}, clock={self.clock}, "
            f"entities={entity_count}, relations={len(self.relations)}, "
            f"resources={len(self.resources)}, policies={len(self.policies)})"
        )
