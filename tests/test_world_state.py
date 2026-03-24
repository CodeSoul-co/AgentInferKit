"""
Unit tests for toolsim.world_state.WorldState.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.core.world_state import PendingEffect, WorldState


def test_set_and_get_entity():
    ws = WorldState()
    ws.set_entity("user", "u1", {"name": "Alice", "age": 30})

    result = ws.get_entity("user", "u1")
    assert result is not None
    assert result["name"] == "Alice"
    assert result["age"] == 30


def test_get_entity_not_found():
    ws = WorldState()
    assert ws.get_entity("user", "nonexistent") is None
    assert ws.get_entity("missing_type", "any") is None


def test_set_entity_increments_version():
    ws = WorldState()
    assert ws.version == 0
    ws.set_entity("file", "f1", {"path": "/tmp/a.txt"})
    assert ws.version == 1
    ws.set_entity("file", "f2", {"path": "/tmp/b.txt"})
    assert ws.version == 2


def test_delete_entity():
    ws = WorldState()
    ws.set_entity("user", "u1", {"name": "Bob"})
    version_before = ws.version

    deleted = ws.delete_entity("user", "u1")
    assert deleted is True
    assert ws.get_entity("user", "u1") is None
    assert ws.version == version_before + 1


def test_delete_entity_cleans_empty_bucket():
    ws = WorldState()
    ws.set_entity("item", "i1", {"val": 1})
    ws.delete_entity("item", "i1")
    assert "item" not in ws.entities


def test_delete_entity_not_found():
    ws = WorldState()
    version_before = ws.version
    deleted = ws.delete_entity("ghost", "g999")
    assert deleted is False
    assert ws.version == version_before


def test_set_entity_deep_copies_value():
    ws = WorldState()
    data = {"x": [1, 2, 3]}
    ws.set_entity("obj", "o1", data)
    data["x"].append(99)
    stored = ws.get_entity("obj", "o1")
    assert stored["x"] == [1, 2, 3]


def test_snapshot_returns_deep_copy():
    ws = WorldState()
    ws.set_entity("user", "u1", {"name": "Carol"})
    snap = ws.snapshot()
    ws.set_entity("user", "u1", {"name": "Changed"})
    assert snap["entities"]["user"]["u1"]["name"] == "Carol"


def test_restore_from_snapshot():
    ws = WorldState()
    ws.set_entity("user", "u1", {"name": "Dave"})
    ws.resources["gold"] = 100
    ws.clock = 42.0

    snap = ws.snapshot()

    ws.set_entity("user", "u2", {"name": "Eve"})
    ws.resources["gold"] = 0
    ws.clock = 999.0

    ws.restore(snap)

    assert ws.get_entity("user", "u1") == {"name": "Dave"}
    assert ws.get_entity("user", "u2") is None
    assert ws.resources["gold"] == 100
    assert ws.clock == 42.0


def test_restore_preserves_version():
    ws = WorldState()
    ws.set_entity("x", "1", {})
    snap = ws.snapshot()
    ws.set_entity("x", "2", {})
    ws.restore(snap)
    assert ws.version == 1


def test_named_snapshot_and_rollback_restore_previous_state():
    ws = WorldState()
    ws.set_entity("doc", "d1", {"value": 1})
    snapshot_id = ws.create_snapshot("before-change")
    ws.set_entity("doc", "d1", {"value": 2})

    rolled_back = ws.rollback_to(snapshot_id)

    assert rolled_back is True
    assert ws.get_entity("doc", "d1") == {"value": 1}
    assert any(snapshot.snapshot_id == snapshot_id for snapshot in ws.list_snapshots())


def test_clock_helpers_increment_state_version():
    ws = WorldState()
    ws.set_clock(10)
    version_after_set = ws.version
    ws.advance_clock(2.5)

    assert ws.now() == 12.5
    assert ws.version == version_after_set + 1


def test_pending_effects_roundtrip_and_affect_hash():
    ws = WorldState()
    before_hash = ws.compute_hash()
    effect = PendingEffect(effect_id="eff1", kind="delayed.write", scheduled_at=0.0, execute_after=3.0, payload={"x": 1})
    ws.schedule_effect(effect)
    after_hash = ws.compute_hash()
    clone = WorldState.from_dict(ws.to_dict())

    assert before_hash != after_hash
    assert len(ws.list_pending_effects()) == 1
    assert clone.pending_effects[0].effect_id == "eff1"


def test_policy_check_uses_blocked_actions_and_required_permissions():
    ws = WorldState(
        policies={
            "blocked_actions": ["file.delete"],
            "required_permissions": {"file.write": ["file.write"]},
        }
    )

    blocked = ws.check_policy("file.delete", {}, permissions={"file.delete"})
    missing = ws.check_policy("file.write", {}, permissions=set())
    allowed = ws.check_policy("file.write", {}, permissions={"file.write"})

    assert blocked.allowed is False
    assert missing.allowed is False
    assert allowed.allowed is True


def test_hash_changes_after_mutation():
    ws = WorldState()
    h1 = ws.compute_hash()
    ws.set_entity("node", "n1", {"active": True})
    h2 = ws.compute_hash()
    assert h1 != h2


def test_hash_consistent_for_same_state():
    ws1 = WorldState()
    ws1.set_entity("role", "admin", {"level": 9})
    ws1.clock = 10.0

    ws2 = WorldState()
    ws2.set_entity("role", "admin", {"level": 9})
    ws2.clock = 10.0

    assert ws1.compute_hash() == ws2.compute_hash()


def test_hash_after_restore_equals_snapshot_hash():
    ws = WorldState()
    ws.set_entity("item", "sword", {"damage": 50})
    snap = ws.snapshot()
    hash_before = ws.compute_hash()
    ws.set_entity("item", "shield", {"defense": 20})
    ws.restore(snap)
    assert ws.compute_hash() == hash_before


def test_to_dict_and_from_dict_roundtrip():
    ws = WorldState()
    ws.set_entity("agent", "a1", {"goal": "explore"})
    ws.relations["a1->a2"] = "ally"
    ws.resources["energy"] = 75
    ws.policies["max_steps"] = 100
    ws.clock = 3.14

    data = ws.to_dict()
    ws2 = WorldState.from_dict(data)

    assert ws2.get_entity("agent", "a1") == {"goal": "explore"}
    assert ws2.relations["a1->a2"] == "ally"
    assert ws2.resources["energy"] == 75
    assert ws2.policies["max_steps"] == 100
    assert ws2.clock == 3.14
    assert ws2.version == ws.version


def run_all_tests() -> None:
    test_set_and_get_entity()
    test_get_entity_not_found()
    test_set_entity_increments_version()
    test_delete_entity()
    test_delete_entity_cleans_empty_bucket()
    test_delete_entity_not_found()
    test_set_entity_deep_copies_value()
    test_snapshot_returns_deep_copy()
    test_restore_from_snapshot()
    test_restore_preserves_version()
    test_named_snapshot_and_rollback_restore_previous_state()
    test_clock_helpers_increment_state_version()
    test_pending_effects_roundtrip_and_affect_hash()
    test_policy_check_uses_blocked_actions_and_required_permissions()
    test_hash_changes_after_mutation()
    test_hash_consistent_for_same_state()
    test_hash_after_restore_equals_snapshot_hash()
    test_to_dict_and_from_dict_roundtrip()
    print("All WorldState tests passed!")


if __name__ == "__main__":
    run_all_tests()
