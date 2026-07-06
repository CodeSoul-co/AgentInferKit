"""Tests for ToolSandbox data-format adapter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsandbox_fixture_utils import TOOLSANDBOX_CSV_PATH, TOOLSANDBOX_JSON_PATH
from toolsim.adapters.toolsandbox_adapter import (
    convert_toolsandbox_file,
    convert_toolsandbox_scenario,
    load_toolsandbox_scenarios,
    write_converted_cases_jsonl,
)
from toolsim.runners.experiment_runner import ExperimentRunner


def test_load_toolsandbox_json_and_csv():
    json_scenarios = load_toolsandbox_scenarios(TOOLSANDBOX_JSON_PATH, limit=2)
    csv_scenarios = load_toolsandbox_scenarios(TOOLSANDBOX_CSV_PATH, limit=2)

    assert len(json_scenarios) == 2
    assert len(csv_scenarios) == 2
    assert json_scenarios[0].scenario_name == "fixture_add_contact"
    assert csv_scenarios[0].required_tools == ["add_contact", "end_conversation"]


def test_convert_contact_scenario_to_runner_inputs():
    scenario = load_toolsandbox_scenarios(TOOLSANDBOX_JSON_PATH, limit=1)[0]
    case = convert_toolsandbox_scenario(scenario)

    assert case.scenario_name == "fixture_add_contact"
    assert case.domain == "contacts"
    assert case.oracle_tool_calls[0]["tool_name"] == "add_contact"
    assert case.oracle_tool_calls[-1]["tool_name"] == "end_conversation"
    assert any(goal["type"] == "toolsandbox_record_exists" and goal["entity_type"] == "contact" for goal in case.goals)


def test_converted_contact_case_runs_and_passes_goals():
    case = convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH, limit=1)[0]

    result = ExperimentRunner().run(
        tool_calls=case.oracle_tool_calls,
        initial_state=case.initial_state,
        goals=case.goals,
    )

    assert result.state_metrics is not None
    assert result.state_metrics.all_passed is True
    assert result.final_state.get_entity("contact", next(iter(result.final_state.entities["contact"]))) is not None


def test_convert_reminder_and_external_search_cases_are_runnable():
    scenarios = load_toolsandbox_scenarios(TOOLSANDBOX_JSON_PATH)
    selected = [
        next(s for s in scenarios if s.domain == "reminders"),
        next(s for s in scenarios if s.domain == "external_search"),
    ]

    for scenario in selected:
        case = convert_toolsandbox_scenario(scenario)
        result = ExperimentRunner().run(
            tool_calls=case.oracle_tool_calls,
            initial_state=case.initial_state,
            goals=case.goals,
        )
        assert result.state_metrics is not None
        assert result.state_metrics.all_passed is True


def test_multi_turn_update_keeps_latest_final_state_goal():
    scenarios = load_toolsandbox_scenarios(TOOLSANDBOX_JSON_PATH)
    scenario = next(s for s in scenarios if s.scenario_name == "fixture_update_contact_twice")
    case = convert_toolsandbox_scenario(scenario)

    assert any(call["args"].get("relationship") == "enemy" for call in case.oracle_tool_calls)
    assert any(call["args"].get("relationship") == "friend" for call in case.oracle_tool_calls)
    assert not any(goal.get("fields", {}).get("relationship") == "enemy" for goal in case.goals)
    assert any(goal.get("fields", {}).get("relationship") == "friend" for goal in case.goals)

    result = ExperimentRunner().run(
        tool_calls=case.oracle_tool_calls,
        initial_state=case.initial_state,
        goals=case.goals,
    )
    assert result.state_metrics is not None
    assert result.state_metrics.all_passed is True


def test_write_converted_cases_jsonl(tmp_path):
    cases = convert_toolsandbox_file(TOOLSANDBOX_JSON_PATH, limit=3)
    path = write_converted_cases_jsonl(cases, tmp_path / "converted.jsonl")

    assert path.exists()
    assert len(path.read_text(encoding="utf-8").splitlines()) == 3
