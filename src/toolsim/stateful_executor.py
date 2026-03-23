from __future__ import annotations

import inspect
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from toolsim.backends.base import BaseBackend
from toolsim.backends.mock_backend import MockBackend
from toolsim.calendar_tools import CALENDAR_TOOLS
from toolsim.environment import ToolEnvironment
from toolsim.file_tools import FILE_TOOLS
from toolsim.search_tools import SEARCH_TOOLS
from toolsim.tool_spec import ConditionCheckResult, ExecutionContext, PostconditionSpec, PreconditionSpec, ToolExecutionResult, ToolSpec
from toolsim.world_state import PendingEffect, WorldState


@dataclass
class ExecutorConfig:
    default_timeout_ms: Optional[int] = None
    default_max_attempts: int = 1
    strict_preconditions: bool = True
    strict_postconditions: bool = False
    enforce_permissions: bool = True
    auto_advance_clock: float = 0.0
    auto_apply_ready_effects: bool = True


@dataclass
class ExecutionRecord:
    call_id: str
    tool_name: str
    tool_version: str = "0.1"
    args: Dict[str, Any] = field(default_factory=dict)
    status: str = "failed"
    success: bool = False
    observation: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    state_changed: bool = False
    partial: bool = False
    async_pending: bool = False
    pre_state_hash: str = ""
    post_state_hash: str = ""
    hash_changed: bool = False
    precondition_results: list[ConditionCheckResult] = field(default_factory=list)
    postcondition_results: list[ConditionCheckResult] = field(default_factory=list)
    permission_results: list[ConditionCheckResult] = field(default_factory=list)
    attempt_count: int = 1
    duration_ms: float = 0.0
    timeout_ms: Optional[int] = None
    scheduled_effect_ids: list[str] = field(default_factory=list)
    applied_effect_ids: list[str] = field(default_factory=list)
    applied_effect_count: int = 0
    consistency_warning: Optional[str] = None
    backend_name: str = "mock"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "args": self.args,
            "status": self.status,
            "success": self.success,
            "observation": self.observation,
            "error": self.error,
            "state_changed": self.state_changed,
            "partial": self.partial,
            "async_pending": self.async_pending,
            "pre_state_hash": self.pre_state_hash,
            "post_state_hash": self.post_state_hash,
            "hash_changed": self.hash_changed,
            "precondition_results": [result.to_dict() for result in self.precondition_results],
            "postcondition_results": [result.to_dict() for result in self.postcondition_results],
            "permission_results": [result.to_dict() for result in self.permission_results],
            "attempt_count": self.attempt_count,
            "duration_ms": self.duration_ms,
            "timeout_ms": self.timeout_ms,
            "scheduled_effect_ids": self.scheduled_effect_ids,
            "applied_effect_ids": self.applied_effect_ids,
            "applied_effect_count": self.applied_effect_count,
            "consistency_warning": self.consistency_warning,
            "backend_name": self.backend_name,
        }


class StatefulExecutor:
    """Stateful executor with backend-aware environments."""

    def __init__(self, tools: Dict[str, ToolSpec], tracer: Optional[object] = None, config: Optional[ExecutorConfig] = None, backend: Optional[BaseBackend] = None) -> None:
        self._tools = dict(tools)
        self._tracer = tracer
        self._config = config or ExecutorConfig()
        self._backend = backend or MockBackend()

    def execute(self, tool_name: str, state: WorldState, args: Dict[str, Any], permissions: Optional[Set[str]] = None, environment: Optional[ToolEnvironment] = None) -> ExecutionRecord:
        call_id = f"call_{uuid.uuid4().hex[:12]}"
        tool_environment = environment or ToolEnvironment(state=state, backend=self._backend, auto_advance_clock=self._config.auto_advance_clock, auto_apply_ready_effects=self._config.auto_apply_ready_effects)
        backend = tool_environment.backend
        tool_environment.before_call(tool_name, args)
        pre_state_hash = state.compute_hash()
        tool = self._tools.get(tool_name)

        if tool is None:
            record = ExecutionRecord(call_id=call_id, tool_name=tool_name, args=dict(args), status="failed", success=False, observation={}, error=f"Tool not found: {tool_name!r}", state_changed=False, pre_state_hash=pre_state_hash, post_state_hash=pre_state_hash, hash_changed=False, backend_name=backend.get_backend_name())
            self._log_record(record)
            return record

        metadata = tool.get_metadata()
        permission_results = self._check_permissions(metadata.name, metadata.required_permissions, state, args, permissions)
        precondition_results = self._check_preconditions(tool.get_preconditions(), state, args)

        if self._should_short_circuit(permission_results, precondition_results):
            record = ExecutionRecord(call_id=call_id, tool_name=metadata.name, tool_version=metadata.version, args=dict(args), status="failed", success=False, observation={}, error=self._build_failure_message(permission_results, precondition_results), state_changed=False, pre_state_hash=pre_state_hash, post_state_hash=pre_state_hash, hash_changed=False, precondition_results=precondition_results, permission_results=permission_results, timeout_ms=self._config.default_timeout_ms, backend_name=backend.get_backend_name())
            self._log_record(record)
            return record

        start = time.perf_counter()
        context = ExecutionContext(state=state, call_id=call_id, clock=state.now(), permissions=set(permissions or set()), timeout_ms=self._config.default_timeout_ms, attempt=1, max_attempts=self._config.default_max_attempts, environment=tool_environment, backend=backend)

        try:
            result = self._invoke_tool(tool, context, args)
            self._schedule_declared_effects(result.scheduled_effects, state, metadata.name, backend)
            applied_results = tool_environment.after_call(tool_name, args, result)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            post_state_hash = state.compute_hash()
            record = ExecutionRecord(call_id=call_id, tool_name=metadata.name, tool_version=metadata.version, args=dict(args), status="failed", success=False, observation={}, error=f"Tool execution raised an exception: {exc}", state_changed=False, pre_state_hash=pre_state_hash, post_state_hash=post_state_hash, hash_changed=(pre_state_hash != post_state_hash), precondition_results=precondition_results, permission_results=permission_results, attempt_count=1, duration_ms=duration_ms, timeout_ms=self._config.default_timeout_ms, consistency_warning=("Tool raised an exception after mutating state." if pre_state_hash != post_state_hash else None), backend_name=backend.get_backend_name())
            self._log_record(record)
            return record

        duration_ms = (time.perf_counter() - start) * 1000
        post_state_hash = state.compute_hash()
        hash_changed = pre_state_hash != post_state_hash
        postcondition_results = self._check_postconditions(tool.get_postconditions(), state, args, pre_state_hash, post_state_hash)

        if self._config.strict_postconditions and any(not result.passed for result in postcondition_results):
            result.success = False
            result.status = "failed"
            if result.error is None:
                result.error = self._build_failure_message([], postcondition_results)

        record = ExecutionRecord(call_id=call_id, tool_name=metadata.name, tool_version=metadata.version, args=dict(args), status=result.status, success=result.success, observation=result.observation, error=result.error, state_changed=result.state_changed, partial=result.partial, async_pending=result.pending, pre_state_hash=pre_state_hash, post_state_hash=post_state_hash, hash_changed=hash_changed, precondition_results=precondition_results, postcondition_results=postcondition_results, permission_results=permission_results, attempt_count=1, duration_ms=duration_ms, timeout_ms=self._config.default_timeout_ms, scheduled_effect_ids=[effect.get("effect_id", "") for effect in result.scheduled_effects], applied_effect_ids=[item.effect_id for item in applied_results if item.applied], applied_effect_count=sum(1 for item in applied_results if item.applied), consistency_warning=_build_consistency_warning(result.state_changed, hash_changed), backend_name=backend.get_backend_name())
        self._log_record(record)
        return record

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def _schedule_declared_effects(self, scheduled_effects: list[dict[str, Any]], state: WorldState, source_tool: str, backend: BaseBackend) -> None:
        for item in scheduled_effects:
            effect = item if isinstance(item, PendingEffect) else PendingEffect.from_dict({**item, "source_tool": item.get("source_tool", source_tool)})
            if state.get_pending_effect(effect.effect_id) is None:
                backend.schedule_effect(state, effect)

    def _invoke_tool(self, tool: ToolSpec, context: ExecutionContext, args: Dict[str, Any]) -> ToolExecutionResult:
        signature = inspect.signature(tool.execute)
        params = list(signature.parameters.values())
        if len(params) >= 2 and params[0].name in {"state_or_context", "context", "ctx"}:
            return tool.execute(context, args)
        return tool.execute(context.state, args)

    def _check_permissions(self, action: str, required_permissions: list[str], state: WorldState, args: Dict[str, Any], permissions: Optional[Set[str]]) -> list[ConditionCheckResult]:
        if not self._config.enforce_permissions:
            return []
        if permissions is None:
            return []
        results: list[ConditionCheckResult] = []
        for permission in required_permissions:
            passed = permission in permissions
            results.append(ConditionCheckResult(kind="permission", passed=passed, message=(f"Permission granted: {permission}" if passed else f"Missing required permission: {permission}"), details={"permission": permission}))
        policy_decision = state.check_policy(action, args, permissions)
        results.append(ConditionCheckResult(kind="policy_check", passed=policy_decision.allowed, message=policy_decision.reason, details=policy_decision.details))
        return results

    def _check_preconditions(self, specs: list[PreconditionSpec], state: WorldState, args: Dict[str, Any]) -> list[ConditionCheckResult]:
        return [self._evaluate_condition(spec, state, args, None, None) for spec in specs]

    def _check_postconditions(self, specs: list[PostconditionSpec], state: WorldState, args: Dict[str, Any], pre_state_hash: str, post_state_hash: str) -> list[ConditionCheckResult]:
        return [self._evaluate_condition(spec, state, args, pre_state_hash, post_state_hash) for spec in specs]

    def _evaluate_condition(self, spec: PreconditionSpec | PostconditionSpec, state: WorldState, args: Dict[str, Any], pre_state_hash: Optional[str], post_state_hash: Optional[str]) -> ConditionCheckResult:
        config = spec.config
        message = spec.message or spec.kind
        if spec.kind == "entity_exists":
            entity_type = config.get("entity_type")
            entity_id = config.get("entity_id") or args.get(config.get("arg_field", "entity_id"))
            passed = state.get_entity(entity_type, entity_id) is not None
            return ConditionCheckResult(spec.kind, passed, message, {"entity_type": entity_type, "entity_id": entity_id})
        if spec.kind == "entity_absent":
            entity_type = config.get("entity_type")
            entity_id = config.get("entity_id") or args.get(config.get("arg_field", "entity_id"))
            passed = state.get_entity(entity_type, entity_id) is None
            return ConditionCheckResult(spec.kind, passed, message, {"entity_type": entity_type, "entity_id": entity_id})
        if spec.kind == "resource_available":
            resource_key = config.get("resource_key")
            min_value = config.get("min_value", 0)
            actual = state.resources.get(resource_key, 0)
            passed = actual >= min_value
            return ConditionCheckResult(spec.kind, passed, message, {"resource_key": resource_key, "actual": actual, "min_value": min_value})
        if spec.kind == "policy_check":
            action = config.get("policy_action", "unknown")
            decision = state.check_policy(action, args)
            return ConditionCheckResult(spec.kind, decision.allowed, decision.reason or message, decision.details)
        if spec.kind == "state_hash_changed":
            passed = pre_state_hash is not None and post_state_hash is not None and pre_state_hash != post_state_hash
            return ConditionCheckResult(spec.kind, passed, message)
        if spec.kind == "state_hash_unchanged":
            passed = pre_state_hash is not None and post_state_hash is not None and pre_state_hash == post_state_hash
            return ConditionCheckResult(spec.kind, passed, message)
        if spec.kind == "entity_field_equals":
            entity_type = config.get("entity_type")
            entity_id = config.get("entity_id") or args.get(config.get("arg_field", "entity_id"))
            field = config.get("field")
            expected = config.get("expected")
            entity = state.get_entity(entity_type, entity_id)
            actual = entity.get(field) if entity is not None else None
            passed = entity is not None and actual == expected
            return ConditionCheckResult(spec.kind, passed, message, {"entity_type": entity_type, "entity_id": entity_id, "field": field, "expected": expected, "actual": actual})
        if spec.kind == "scheduled_effect_created":
            effect_kind = config.get("kind")
            passed = any(effect.kind == effect_kind for effect in state.pending_effects)
            return ConditionCheckResult(spec.kind, passed, message, {"kind": effect_kind})
        return ConditionCheckResult(spec.kind, False, f"Unsupported condition kind: {spec.kind}")

    def _should_short_circuit(self, permission_results: list[ConditionCheckResult], precondition_results: list[ConditionCheckResult]) -> bool:
        if any(not result.passed for result in permission_results):
            return True
        return self._config.strict_preconditions and any(not result.passed for result in precondition_results)

    def _build_failure_message(self, primary_results: list[ConditionCheckResult], secondary_results: list[ConditionCheckResult]) -> str:
        failures = [result.message for result in [*primary_results, *secondary_results] if not result.passed]
        return failures[0] if failures else "Execution failed"

    def _log_record(self, record: ExecutionRecord) -> None:
        if self._tracer is not None:
            self._tracer.log(record)


def create_default_tool_registry() -> Dict[str, ToolSpec]:
    registry: Dict[str, ToolSpec] = {}
    registry.update(FILE_TOOLS)
    registry.update(SEARCH_TOOLS)
    registry.update(CALENDAR_TOOLS)
    return registry


def _build_consistency_warning(state_changed: bool, hash_changed: bool) -> Optional[str]:
    if not state_changed and hash_changed:
        return "Tool reported state_changed=False, but state hash changed."
    if state_changed and not hash_changed:
        return "Tool reported state_changed=True, but state hash did not change."
    return None
