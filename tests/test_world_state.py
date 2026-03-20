"""
Unit tests for toolsim.world_state.WorldState.

Run with: python -m pytest tests/test_world_state.py -v
Or directly: python tests/test_world_state.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.world_state import WorldState


# ------------------------------------------------------------------
# 实体 CRUD
# ------------------------------------------------------------------

def test_set_and_get_entity():
    """Test basic set / get entity operations."""
    ws = WorldState()
    ws.set_entity("user", "u1", {"name": "Alice", "age": 30})

    result = ws.get_entity("user", "u1")
    assert result is not None
    assert result["name"] == "Alice"
    assert result["age"] == 30

    print("✓ test_set_and_get_entity passed")


def test_get_entity_not_found():
    """Test get_entity returns None for missing entities."""
    ws = WorldState()
    assert ws.get_entity("user", "nonexistent") is None
    assert ws.get_entity("missing_type", "any") is None

    print("✓ test_get_entity_not_found passed")


def test_set_entity_increments_version():
    """Test that set_entity increments version each time."""
    ws = WorldState()
    assert ws.version == 0

    ws.set_entity("file", "f1", {"path": "/tmp/a.txt"})
    assert ws.version == 1

    ws.set_entity("file", "f2", {"path": "/tmp/b.txt"})
    assert ws.version == 2

    print("✓ test_set_entity_increments_version passed")


def test_delete_entity():
    """Test delete_entity removes entity and increments version."""
    ws = WorldState()
    ws.set_entity("user", "u1", {"name": "Bob"})
    version_before = ws.version

    deleted = ws.delete_entity("user", "u1")
    assert deleted is True
    assert ws.get_entity("user", "u1") is None
    assert ws.version == version_before + 1

    print("✓ test_delete_entity passed")


def test_delete_entity_cleans_empty_bucket():
    """Test that deleting the last entity of a type removes the type bucket."""
    ws = WorldState()
    ws.set_entity("item", "i1", {"val": 1})
    ws.delete_entity("item", "i1")

    # 空桶应当被清理
    assert "item" not in ws.entities

    print("✓ test_delete_entity_cleans_empty_bucket passed")


def test_delete_entity_not_found():
    """Test delete_entity returns False when entity does not exist."""
    ws = WorldState()
    version_before = ws.version

    deleted = ws.delete_entity("ghost", "g999")
    assert deleted is False
    assert ws.version == version_before  # version 不应变化

    print("✓ test_delete_entity_not_found passed")


def test_set_entity_deep_copies_value():
    """Test that set_entity stores a deep copy, not a reference."""
    ws = WorldState()
    data = {"x": [1, 2, 3]}
    ws.set_entity("obj", "o1", data)

    # 修改原始 dict，不应影响存储值
    data["x"].append(99)
    stored = ws.get_entity("obj", "o1")
    assert stored["x"] == [1, 2, 3]

    print("✓ test_set_entity_deep_copies_value passed")


# ------------------------------------------------------------------
# 快照 / 恢复
# ------------------------------------------------------------------

def test_snapshot_returns_deep_copy():
    """Test that snapshot returns a deep copy independent of live state."""
    ws = WorldState()
    ws.set_entity("user", "u1", {"name": "Carol"})
    snap = ws.snapshot()

    # 修改 live 状态不影响快照
    ws.set_entity("user", "u1", {"name": "Changed"})
    assert snap["entities"]["user"]["u1"]["name"] == "Carol"

    print("✓ test_snapshot_returns_deep_copy passed")


def test_restore_from_snapshot():
    """Test that restore fully recovers state from a snapshot."""
    ws = WorldState()
    ws.set_entity("user", "u1", {"name": "Dave"})
    ws.resources["gold"] = 100
    ws.clock = 42.0

    snap = ws.snapshot()

    # 大幅修改状态
    ws.set_entity("user", "u2", {"name": "Eve"})
    ws.resources["gold"] = 0
    ws.clock = 999.0

    ws.restore(snap)

    assert ws.get_entity("user", "u1") == {"name": "Dave"}
    assert ws.get_entity("user", "u2") is None
    assert ws.resources["gold"] == 100
    assert ws.clock == 42.0

    print("✓ test_restore_from_snapshot passed")


def test_restore_preserves_version():
    """Test that restore also restores the version number."""
    ws = WorldState()
    ws.set_entity("x", "1", {})          # version -> 1
    snap = ws.snapshot()                  # 快照 version=1

    ws.set_entity("x", "2", {})          # version -> 2
    ws.restore(snap)
    assert ws.version == 1

    print("✓ test_restore_preserves_version passed")


# ------------------------------------------------------------------
# 哈希
# ------------------------------------------------------------------

def test_hash_changes_after_mutation():
    """Test that compute_hash changes after state mutation."""
    ws = WorldState()
    h1 = ws.compute_hash()

    ws.set_entity("node", "n1", {"active": True})
    h2 = ws.compute_hash()

    assert h1 != h2

    print("✓ test_hash_changes_after_mutation passed")


def test_hash_consistent_for_same_state():
    """Test that compute_hash returns the same value for identical states."""
    ws1 = WorldState()
    ws1.set_entity("role", "admin", {"level": 9})
    ws1.clock = 10.0

    ws2 = WorldState()
    ws2.set_entity("role", "admin", {"level": 9})
    ws2.clock = 10.0

    assert ws1.compute_hash() == ws2.compute_hash()

    print("✓ test_hash_consistent_for_same_state passed")


def test_hash_after_restore_equals_snapshot_hash():
    """Test that hash after restore equals the hash at snapshot time."""
    ws = WorldState()
    ws.set_entity("item", "sword", {"damage": 50})
    snap = ws.snapshot()
    hash_before = ws.compute_hash()

    ws.set_entity("item", "shield", {"defense": 20})
    ws.restore(snap)

    assert ws.compute_hash() == hash_before

    print("✓ test_hash_after_restore_equals_snapshot_hash passed")


# ------------------------------------------------------------------
# 序列化往返
# ------------------------------------------------------------------

def test_to_dict_and_from_dict_roundtrip():
    """Test to_dict / from_dict round-trip preserves all fields."""
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

    print("✓ test_to_dict_and_from_dict_roundtrip passed")


# ------------------------------------------------------------------
# 入口
# ------------------------------------------------------------------

def run_all_tests() -> None:
    """Run all WorldState tests."""
    print("=" * 55)
    print("Running WorldState tests...")
    print("=" * 55)

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
    test_hash_changes_after_mutation()
    test_hash_consistent_for_same_state()
    test_hash_after_restore_equals_snapshot_hash()
    test_to_dict_and_from_dict_roundtrip()

    print("=" * 55)
    print("All WorldState tests passed!")
    print("=" * 55)


if __name__ == "__main__":
    run_all_tests()
