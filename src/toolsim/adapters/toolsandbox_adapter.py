"""Adapter for ToolSandbox scenario files.

The adapter preserves the original ToolSandbox metadata while translating a
scenario into AgentInferKit's stateful ``ExperimentRunner`` inputs:

- initial ``WorldState``
- oracle tool-call sequence inferred from milestone targets
- state-level goals inferred from milestone constraints
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from toolsim.core.world_state import WorldState


_NAMESPACE_TO_ENTITY = {
    "CONTACT": "contact",
    "REMINDER": "reminder",
    "MESSAGING": "messaging",
    "SETTING": "setting",
    "SANDBOX": "sandbox",
}


@dataclass
class ToolSandboxScenario:
    scenario_name: str
    canonical_task_key: str
    user_request: str
    domain: str
    required_tools: list[str]
    categories: list[str]
    milestones: list[dict[str, Any]]
    minefields: list[dict[str, Any]]
    initial_settings: dict[str, Any] = field(default_factory=dict)
    initial_contact_names: list[str] = field(default_factory=list)
    initial_contact_count: int = 0
    initial_message_count: int = 0
    initial_reminder_count: int = 0
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "ToolSandboxScenario":
        return cls(
            scenario_name=str(raw.get("scenario_name", "")),
            canonical_task_key=str(raw.get("canonical_task_key", "")),
            user_request=str(raw.get("user_request", "")),
            domain=str(raw.get("domain", "")),
            required_tools=list(raw.get("required_tools", []) or []),
            categories=list(raw.get("categories", []) or []),
            milestones=list(raw.get("milestones", []) or []),
            minefields=list(raw.get("minefields", []) or []),
            initial_settings=dict(raw.get("initial_settings", {}) or {}),
            initial_contact_names=list(raw.get("initial_contact_names", []) or []),
            initial_contact_count=int(raw.get("initial_contact_count", 0) or 0),
            initial_message_count=int(raw.get("initial_message_count", 0) or 0),
            initial_reminder_count=int(raw.get("initial_reminder_count", 0) or 0),
            raw=raw,
        )


@dataclass
class ToolSandboxConvertedCase:
    scenario_name: str
    user_request: str
    domain: str
    required_tools: list[str]
    categories: list[str]
    initial_state: WorldState
    oracle_tool_calls: list[dict[str, Any]]
    goals: list[dict[str, Any]]
    minefield_goals: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "user_request": self.user_request,
            "domain": self.domain,
            "required_tools": self.required_tools,
            "categories": self.categories,
            "initial_state": self.initial_state.to_dict(),
            "oracle_tool_calls": self.oracle_tool_calls,
            "goals": self.goals,
            "minefield_goals": self.minefield_goals,
            "metadata": self.metadata,
        }


def load_toolsandbox_scenarios(path: str | Path, limit: int | None = None) -> list[ToolSandboxScenario]:
    """Load ToolSandbox scenarios from JSON or CSV."""
    input_path = Path(path)
    if input_path.suffix.lower() == ".csv":
        rows = _load_csv(input_path)
    else:
        rows = json.loads(input_path.read_text(encoding="utf-8"))
    scenarios = [ToolSandboxScenario.from_raw(row) for row in rows]
    return scenarios[:limit] if limit is not None else scenarios


def convert_toolsandbox_scenario(scenario: ToolSandboxScenario) -> ToolSandboxConvertedCase:
    """Convert one ToolSandbox scenario into ExperimentRunner inputs."""
    initial_state = build_initial_state(scenario)
    goals = milestones_to_goals(scenario.milestones)
    minefield_goals = milestones_to_goals(scenario.minefields)
    oracle_tool_calls = milestones_to_oracle_tool_calls(scenario.milestones)
    return ToolSandboxConvertedCase(
        scenario_name=scenario.scenario_name,
        user_request=scenario.user_request,
        domain=scenario.domain,
        required_tools=scenario.required_tools,
        categories=scenario.categories,
        initial_state=initial_state,
        oracle_tool_calls=oracle_tool_calls,
        goals=goals,
        minefield_goals=minefield_goals,
        metadata={
            "canonical_task_key": scenario.canonical_task_key,
            "milestone_count": len(scenario.milestones),
            "minefield_count": len(scenario.minefields),
        },
    )


def convert_toolsandbox_file(path: str | Path, limit: int | None = None) -> list[ToolSandboxConvertedCase]:
    """Load and convert a ToolSandbox scenario file."""
    return [convert_toolsandbox_scenario(scenario) for scenario in load_toolsandbox_scenarios(path, limit=limit)]


def select_toolsandbox_subset_cases(
    cases: list[ToolSandboxConvertedCase],
    *,
    group_by: str = "domain",
    per_group: int = 8,
    include_minefields: bool = True,
) -> list[ToolSandboxConvertedCase]:
    """Select a deterministic benchmark subset with 5-10 cases per group.

    Args:
        cases: Converted ToolSandbox cases.
        group_by: ``"domain"`` for mutually exclusive task domains, or
            ``"category"`` for ToolSandbox category labels.
        per_group: Number of cases to target per group. Must be between 5 and 10.
        include_minefields: Whether to reserve a small number of cases per group
            for minefield / insufficient-information scenarios when available.

    Returns:
        A de-duplicated list of converted cases, preserving deterministic order.
    """
    if not 5 <= per_group <= 10:
        raise ValueError("per_group must be between 5 and 10")
    if group_by not in {"domain", "category"}:
        raise ValueError("group_by must be either 'domain' or 'category'")

    grouped: dict[str, list[ToolSandboxConvertedCase]] = {}
    for case in cases:
        group_names = [case.domain or "unknown"] if group_by == "domain" else case.categories or ["uncategorized"]
        for group_name in group_names:
            grouped.setdefault(group_name, []).append(case)

    selected: list[ToolSandboxConvertedCase] = []
    seen_names: set[str] = set()
    for group_name in sorted(grouped):
        group_selection = _select_group_cases(
            grouped[group_name],
            per_group=per_group,
            include_minefields=include_minefields,
        )
        for case in group_selection:
            if case.scenario_name in seen_names:
                continue
            case.metadata = {**case.metadata, "subset_group_by": group_by, "subset_group": group_name}
            selected.append(case)
            seen_names.add(case.scenario_name)
    return selected


def write_converted_cases_jsonl(cases: Iterable[ToolSandboxConvertedCase], path: str | Path) -> Path:
    """Write converted cases as JSONL for inspection or downstream use."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case.to_dict(), ensure_ascii=False) + "\n")
    return output_path


def _select_group_cases(
    cases: list[ToolSandboxConvertedCase],
    *,
    per_group: int,
    include_minefields: bool,
) -> list[ToolSandboxConvertedCase]:
    ordered = sorted(cases, key=_case_sort_key)
    minefield_cases = [case for case in ordered if case.minefield_goals and not case.goals]
    goal_cases = [case for case in ordered if case.goals]

    selected: list[ToolSandboxConvertedCase] = []
    if include_minefields and minefield_cases:
        minefield_slots = min(len(minefield_cases), max(1, per_group // 4))
        selected.extend(_diverse_prefix(minefield_cases, minefield_slots))

    selected.extend(_diverse_prefix(goal_cases, per_group - len(selected)))
    if len(selected) < per_group:
        selected_names = {case.scenario_name for case in selected}
        selected.extend(case for case in ordered if case.scenario_name not in selected_names)
    return selected[:per_group]


def _diverse_prefix(cases: list[ToolSandboxConvertedCase], limit: int) -> list[ToolSandboxConvertedCase]:
    if limit <= 0:
        return []
    selected: list[ToolSandboxConvertedCase] = []
    seen_keys: set[str] = set()
    for case in cases:
        key = str(case.metadata.get("canonical_task_key") or case.scenario_name)
        if key in seen_keys:
            continue
        selected.append(case)
        seen_keys.add(key)
        if len(selected) >= limit:
            return selected

    selected_names = {case.scenario_name for case in selected}
    for case in cases:
        if case.scenario_name in selected_names:
            continue
        selected.append(case)
        if len(selected) >= limit:
            break
    return selected


def _case_sort_key(case: ToolSandboxConvertedCase) -> tuple[Any, ...]:
    is_minefield = bool(case.minefield_goals and not case.goals)
    return (
        str(case.metadata.get("canonical_task_key") or ""),
        not is_minefield,
        case.scenario_name,
    )


def build_initial_state(scenario: ToolSandboxScenario) -> WorldState:
    """Build a minimal WorldState from ToolSandbox initial metadata."""
    state = WorldState()
    if scenario.initial_settings:
        state.set_entity("setting", "device", dict(scenario.initial_settings))

    for index, name in enumerate(scenario.initial_contact_names):
        person_id = f"initial_contact_{index}"
        state.set_entity("contact", person_id, {
            "person_id": person_id,
            "name": name,
            "phone_number": None,
            "relationship": None,
            "is_self": False,
            "sandbox_message_index": None,
        })

    for index in range(max(0, scenario.initial_message_count)):
        message_id = f"initial_message_{index}"
        state.set_entity("messaging", message_id, {
            "message_id": message_id,
            "content": None,
            "recipient_phone_number": None,
            "sender_phone_number": None,
            "sandbox_message_index": index,
        })

    for index in range(max(0, scenario.initial_reminder_count)):
        reminder_id = f"initial_reminder_{index}"
        state.set_entity("reminder", reminder_id, {
            "reminder_id": reminder_id,
            "content": None,
            "reminder_timestamp": None,
            "sandbox_message_index": index,
        })

    return state


def milestones_to_goals(milestones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translate ToolSandbox milestone constraints to state-level goals."""
    goals: list[dict[str, Any]] = []
    for constraint in _iter_constraints(milestones):
        namespace = constraint.get("database_namespace")
        function = constraint.get("constraint_function")
        entity_type = _NAMESPACE_TO_ENTITY.get(namespace)
        if entity_type is None:
            continue

        for target in constraint.get("target_records") or []:
            if namespace == "SETTING":
                goals.extend(_setting_goals(target))
            elif namespace == "SANDBOX":
                goal = _sandbox_goal(target)
                if goal is not None:
                    goals.append(goal)
            elif function == "removal_similarity":
                goals.append({"type": "toolsandbox_record_absent", "entity_type": entity_type, "fields": _goal_fields(target)})
            else:
                goals.append({"type": "toolsandbox_record_exists", "entity_type": entity_type, "fields": _goal_fields(target)})
    return _collapse_final_goals(_dedupe_dicts(goals))


def milestones_to_oracle_tool_calls(milestones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Infer an oracle tool-call sequence from ToolSandbox milestone targets."""
    calls: list[dict[str, Any]] = []
    for constraint in _iter_constraints(milestones):
        namespace = constraint.get("database_namespace")
        function = constraint.get("constraint_function")
        for target in constraint.get("target_records") or []:
            calls.extend(_target_to_tool_calls(namespace, function, target))
    return _dedupe_tool_calls(calls)


def _load_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(_normalize_csv_row(row))
    return rows


def _normalize_csv_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "scenario_name": row.get("scenario_name", ""),
        "canonical_task_key": row.get("canonical_task_key", ""),
        "is_augmented_variant": row.get("is_augmented_variant") == "True",
        "real_world_scenario": row.get("real_world_scenario", ""),
        "user_request": row.get("user_request", ""),
        "system_instruction_to_user": row.get("system_instruction_to_user", ""),
        "domain": row.get("domain", ""),
        "max_messages": int(row.get("max_messages") or 0),
        "required_tool_count": int(row.get("required_tool_count") or 0),
        "required_tools": _split_pipe(row.get("required_tools", "")),
        "categories": _split_pipe(row.get("categories", "")),
        "distraction_tags": _split_pipe(row.get("distraction_tags", "")),
        "augmentation_tags": _split_pipe(row.get("augmentation_tags", "")),
        "initial_settings": {
            "wifi": row.get("wifi") == "True",
            "cellular": row.get("cellular") == "True",
            "location_service": row.get("location_service") == "True",
            "low_battery_mode": row.get("low_battery_mode") == "True",
            "latitude": _maybe_float(row.get("latitude")),
            "longitude": _maybe_float(row.get("longitude")),
        },
        "initial_contact_count": int(row.get("initial_contact_count") or 0),
        "initial_message_count": int(row.get("initial_message_count") or 0),
        "initial_reminder_count": int(row.get("initial_reminder_count") or 0),
        "initial_contact_names": _split_pipe(row.get("initial_contact_names", "")),
        "milestones": json.loads(row.get("milestones_json") or "[]"),
        "minefields": json.loads(row.get("minefields_json") or "[]"),
    }


def _iter_constraints(milestones: list[dict[str, Any]]):
    for milestone in milestones:
        for constraint in milestone.get("snapshot_constraints", []) or []:
            yield constraint


def _setting_goals(target: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"type": "toolsandbox_setting_equals", "field": field, "expected": value}
        for field, value in target.items()
        if field in {"wifi", "cellular", "location_service", "low_battery_mode", "latitude", "longitude"}
    ]


def _sandbox_goal(target: dict[str, Any]) -> dict[str, Any] | None:
    if target.get("tool_trace"):
        tool_names = _tool_trace_names(target.get("tool_trace"))
        tool_name = tool_names[0] if tool_names else None
        if tool_name:
            return {"type": "toolsandbox_record_exists", "entity_type": "sandbox", "fields": {"openai_function_name": tool_name}}
    fields = _goal_fields(target, allowed={"sender", "recipient", "content"})
    if fields:
        return {"type": "toolsandbox_record_exists", "entity_type": "sandbox", "fields": fields}
    return None


def _goal_fields(target: dict[str, Any], allowed: set[str] | None = None) -> dict[str, Any]:
    fields = {}
    for key, value in target.items():
        if allowed is not None and key not in allowed:
            continue
        if value is not None:
            fields[key] = value
        elif key in {"relationship", "phone_number", "content"}:
            fields[key] = value
    return fields


def _target_to_tool_calls(namespace: str, function: str, target: dict[str, Any]) -> list[dict[str, Any]]:
    if namespace == "CONTACT":
        tool_name = "remove_contact" if function == "removal_similarity" else "modify_contact" if function == "update_similarity" else "add_contact"
        return [{"tool_name": tool_name, "args": _goal_fields(target)}]
    if namespace == "REMINDER":
        tool_name = "remove_reminder" if function == "removal_similarity" else "modify_reminder" if function == "update_similarity" else "add_reminder"
        return [{"tool_name": tool_name, "args": _goal_fields(target)}]
    if namespace == "MESSAGING":
        return [{"tool_name": "send_message_with_phone_number", "args": _goal_fields(target)}]
    if namespace == "SETTING":
        call = _setting_tool_call(target)
        return [call] if call is not None else []
    if namespace == "SANDBOX":
        if target.get("tool_trace"):
            return _tool_trace_calls(target.get("tool_trace"))
        if target.get("content"):
            return [{"tool_name": "end_conversation", "args": {"content": target.get("content")}}]
    return []


def _setting_tool_call(target: dict[str, Any]) -> dict[str, Any] | None:
    mapping = {
        "wifi": "set_wifi_status",
        "cellular": "set_cellular_service_status",
        "location_service": "set_location_service_status",
        "low_battery_mode": "set_low_battery_mode_status",
    }
    for field, tool_name in mapping.items():
        if field in target:
            return {"tool_name": tool_name, "args": {field: target[field]}}
    return None


def _tool_trace_calls(raw_trace: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(raw_trace)
    except (TypeError, json.JSONDecodeError):
        return []
    if isinstance(payload, list):
        return [_tool_trace_payload_to_call(item) for item in payload if _tool_trace_payload_to_call(item) is not None]
    call = _tool_trace_payload_to_call(payload)
    return [call] if call is not None else []


def _tool_trace_payload_to_call(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    tool_name = payload.get("tool_name")
    if not tool_name:
        return None
    return {"tool_name": tool_name, "args": payload.get("arguments") or {}}


def _tool_trace_names(raw_trace: str) -> list[str]:
    return [call["tool_name"] for call in _tool_trace_calls(raw_trace)]


def _split_pipe(value: str) -> list[str]:
    return [item for item in value.split("|") if item]


def _maybe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _dedupe_tool_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _dedupe_dicts(calls)


def _collapse_final_goals(goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the latest final-state assertion for mutable ToolSandbox records."""
    keyed_positions: dict[tuple[Any, ...], int] = {}
    result: list[dict[str, Any]] = []
    for goal in goals:
        key = _goal_identity_key(goal)
        if key is not None and key in keyed_positions:
            result[keyed_positions[key]] = goal
        else:
            if key is not None:
                keyed_positions[key] = len(result)
            result.append(goal)
    return result


def _goal_identity_key(goal: dict[str, Any]) -> tuple[Any, ...] | None:
    goal_type = goal.get("type")
    if goal_type == "toolsandbox_setting_equals":
        return ("setting", goal.get("field"))
    if goal_type not in {"toolsandbox_record_exists", "toolsandbox_record_absent"}:
        return None
    entity_type = goal.get("entity_type")
    if entity_type == "sandbox":
        return None
    fields = goal.get("fields", {})
    for identity_field in ["person_id", "reminder_id", "message_id", "phone_number", "name", "content"]:
        if identity_field in fields:
            return (entity_type, identity_field, fields[identity_field])
    return None
