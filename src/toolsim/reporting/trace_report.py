"""Markdown trace reports for stateful tool runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from toolsim.execution.stateful_executor import ExecutionRecord
from toolsim.runners.experiment_runner import ExperimentResult


def render_stateful_trace_markdown(
    result_or_records: ExperimentResult | Sequence[ExecutionRecord],
    *,
    title: str = "Stateful Tool Trace Report",
) -> str:
    """Render a human-readable Markdown trace report.

    The report focuses on the signals that matter for stateful-tool evaluation:
    execution status, state hash transitions, delayed effects, backend identity,
    and compact observations.
    """
    records, final_state = _normalize_input(result_or_records)
    lines = [
        f"# {title}",
        "",
        "## Summary",
        f"- Total calls: {len(records)}",
        f"- Successful calls: {sum(1 for record in records if record.success)}",
        f"- Failed calls: {sum(1 for record in records if not record.success)}",
        f"- State-changing calls: {sum(1 for record in records if record.state_changed)}",
        f"- Pending/async calls: {sum(1 for record in records if record.async_pending)}",
        "",
        "## Calls",
        "",
        "| Step | Tool | Status | State hash | Effects | Backend |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for idx, record in enumerate(records, start=1):
        state_hash = f"{_short_hash(record.pre_state_hash)} -> {_short_hash(record.post_state_hash)}"
        effects = _format_effects(record)
        lines.append(
            f"| {idx} | `{record.tool_name}` | {record.status} | `{state_hash}` | {effects} | {record.backend_name} |"
        )

    lines.extend(["", "## Observations", ""])
    for idx, record in enumerate(records, start=1):
        lines.extend([
            f"### Step {idx}: `{record.tool_name}`",
            "",
            f"- Success: {record.success}",
            f"- Error: {record.error or ''}",
            f"- State changed: {record.state_changed}",
            f"- Duration ms: {record.duration_ms:.2f}",
            "",
            "State diff:",
            "",
            *_render_record_state_diff(record),
            "",
            "```json",
            _compact_json(record.observation),
            "```",
            "",
        ])

    if final_state is not None:
        lines.extend(["## Final Trace State", ""])
        lines.extend(_render_final_state(final_state))

    return "\n".join(lines)


def write_stateful_trace_markdown(
    result_or_records: ExperimentResult | Sequence[ExecutionRecord],
    path: str | Path,
    *,
    title: str = "Stateful Tool Trace Report",
) -> Path:
    """Write a Markdown trace report and return the output path."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_stateful_trace_markdown(result_or_records, title=title),
        encoding="utf-8",
    )
    return output_path


def _normalize_input(
    result_or_records: ExperimentResult | Sequence[ExecutionRecord],
) -> tuple[list[ExecutionRecord], Any | None]:
    if isinstance(result_or_records, ExperimentResult):
        return list(result_or_records.trace), result_or_records.final_state
    return list(result_or_records), None


def _short_hash(value: str) -> str:
    return value[:10] if value else ""


def _format_effects(record: ExecutionRecord) -> str:
    parts: list[str] = []
    if record.scheduled_effect_ids:
        parts.append("scheduled=" + ",".join(record.scheduled_effect_ids))
    if record.applied_effect_ids:
        parts.append("applied=" + ",".join(record.applied_effect_ids))
    if record.applied_effect_count and not record.applied_effect_ids:
        parts.append(f"applied_count={record.applied_effect_count}")
    return "; ".join(parts) if parts else "-"


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _render_record_state_diff(record: ExecutionRecord) -> list[str]:
    if not record.pre_state_snapshot or not record.post_state_snapshot:
        return ["- State snapshots unavailable"]

    changes: list[str] = []
    changes.extend(_diff_entity_buckets(
        record.pre_state_snapshot.get("entities", {}),
        record.post_state_snapshot.get("entities", {}),
    ))
    changes.extend(_diff_mapping(
        "resources",
        record.pre_state_snapshot.get("resources", {}),
        record.post_state_snapshot.get("resources", {}),
    ))
    changes.extend(_diff_mapping(
        "policies",
        record.pre_state_snapshot.get("policies", {}),
        record.post_state_snapshot.get("policies", {}),
    ))
    changes.extend(_diff_pending_effects(
        record.pre_state_snapshot.get("pending_effects", []),
        record.post_state_snapshot.get("pending_effects", []),
    ))
    return changes if changes else ["- No state diff"]


def _diff_entity_buckets(pre_entities: dict[str, Any], post_entities: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    entity_types = sorted(set(pre_entities) | set(post_entities))
    for entity_type in entity_types:
        pre_bucket = pre_entities.get(entity_type, {}) or {}
        post_bucket = post_entities.get(entity_type, {}) or {}
        entity_ids = sorted(set(pre_bucket) | set(post_bucket))
        for entity_id in entity_ids:
            pre_entity = pre_bucket.get(entity_id)
            post_entity = post_bucket.get(entity_id)
            label = f"`{entity_type}.{entity_id}`"
            if pre_entity is None and post_entity is not None:
                lines.append(f"- Created {label}")
                for key, value in sorted(post_entity.items()):
                    lines.append(f"  - `{key}` = {_format_value(value)}")
            elif pre_entity is not None and post_entity is None:
                lines.append(f"- Deleted {label}")
            elif pre_entity != post_entity:
                field_lines = _diff_mapping_fields(pre_entity, post_entity)
                if field_lines:
                    lines.append(f"- Updated {label}")
                    lines.extend(field_lines)
    return lines


def _diff_mapping(label: str, pre_map: dict[str, Any], post_map: dict[str, Any]) -> list[str]:
    if pre_map == post_map:
        return []
    lines = [f"- Updated `{label}`"]
    lines.extend(_diff_mapping_fields(pre_map, post_map))
    return lines


def _diff_mapping_fields(pre_map: dict[str, Any], post_map: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key in sorted(set(pre_map) | set(post_map)):
        old_value = pre_map.get(key, "<missing>")
        new_value = post_map.get(key, "<missing>")
        if old_value != new_value:
            lines.append(f"  - `{key}`: {_format_value(old_value)} -> {_format_value(new_value)}")
    return lines


def _diff_pending_effects(pre_effects: list[dict[str, Any]], post_effects: list[dict[str, Any]]) -> list[str]:
    pre_by_id = {item.get("effect_id"): item for item in pre_effects}
    post_by_id = {item.get("effect_id"): item for item in post_effects}
    lines: list[str] = []
    for effect_id in sorted(set(pre_by_id) | set(post_by_id)):
        pre_effect = pre_by_id.get(effect_id)
        post_effect = post_by_id.get(effect_id)
        if pre_effect is None and post_effect is not None:
            lines.append(f"- Scheduled effect `{effect_id}` kind={post_effect.get('kind')} status={post_effect.get('status')}")
        elif pre_effect is not None and post_effect is None:
            lines.append(f"- Removed effect `{effect_id}`")
        elif pre_effect != post_effect:
            lines.append(f"- Updated effect `{effect_id}`")
            lines.extend(_diff_mapping_fields(pre_effect, post_effect))
    return lines


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return repr(value)
    return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"


def _render_final_state(final_state: Any) -> list[str]:
    lines = [
        f"- Clock: {final_state.clock}",
        f"- Version: {final_state.version}",
        f"- Hash: `{final_state.compute_hash()}`",
        "",
        "### Entities",
        "",
    ]
    if not final_state.entities:
        lines.append("- No entities")
    else:
        for entity_type, bucket in sorted(final_state.entities.items()):
            lines.append(f"- `{entity_type}`: {len(bucket)}")
            for entity_id, entity in sorted(bucket.items()):
                status = entity.get("status")
                revision = entity.get("revision")
                suffix = []
                if status is not None:
                    suffix.append(f"status={status}")
                if revision is not None:
                    suffix.append(f"revision={revision}")
                detail = f" ({', '.join(suffix)})" if suffix else ""
                lines.append(f"  - `{entity_id}`{detail}")

    lines.extend(["", "### Pending Effects", ""])
    if not final_state.pending_effects:
        lines.append("- No pending effects")
    else:
        for effect in final_state.pending_effects:
            lines.append(
                f"- `{effect.effect_id}` kind={effect.kind} status={effect.status.value} execute_after={effect.execute_after}"
            )
    return lines
