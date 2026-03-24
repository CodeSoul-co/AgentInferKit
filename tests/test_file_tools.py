"""
Unit tests for toolsim.file_tools (FileWriteTool / FileReadTool).

Run with: python -m pytest tests/test_file_tools.py -v
Or directly: python tests/test_file_tools.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.core.world_state import WorldState
from toolsim.tools.file_tools import FileWriteTool, FileReadTool, FILE_TOOLS
from toolsim.core.tool_spec import ToolExecutionResult


# ------------------------------------------------------------------
# 场景 1：file.write 正确写入 WorldState
# ------------------------------------------------------------------

def test_file_write_creates_entity():
    """Test file.write creates a file entity in WorldState."""
    ws = WorldState()
    tool = FileWriteTool()

    result = tool.execute(ws, {"file_id": "doc1", "content": "Hello World"})

    assert result.success is True
    assert result.state_changed is True
    assert result.error is None

    # 实体确实写入了 entities["file"]["doc1"]
    entity = ws.get_entity("file", "doc1")
    assert entity is not None
    assert entity["content"] == "Hello World"
    assert entity["revision"] == 1
    assert entity["created_at"] == ws.clock
    assert entity["updated_at"] == ws.clock

    print("✓ test_file_write_creates_entity passed")


def test_file_write_observation_fields():
    """Test file.write observation contains required fields."""
    ws = WorldState()
    result = FileWriteTool().execute(ws, {"file_id": "f1", "content": "data"})

    obs = result.observation
    assert obs["tool_name"] == "file.write"
    assert obs["file_id"] == "f1"
    assert obs["action"] == "created"
    assert obs["revision"] == 1

    print("✓ test_file_write_observation_fields passed")


def test_file_write_with_metadata():
    """Test file.write persists optional metadata."""
    ws = WorldState()
    meta = {"author": "Alice", "tags": ["draft"]}
    FileWriteTool().execute(ws, {"file_id": "readme", "content": "# README", "metadata": meta})

    entity = ws.get_entity("file", "readme")
    assert entity["metadata"]["author"] == "Alice"
    assert entity["metadata"]["tags"] == ["draft"]

    print("✓ test_file_write_with_metadata passed")


# ------------------------------------------------------------------
# 场景 2：file.read 正确读取已写入文件
# ------------------------------------------------------------------

def test_file_read_returns_written_content():
    """Test file.read retrieves content previously written by file.write."""
    ws = WorldState()
    FileWriteTool().execute(ws, {"file_id": "note", "content": "remember this"})

    result = FileReadTool().execute(ws, {"file_id": "note"})

    assert result.success is True
    assert result.state_changed is False
    assert result.observation["content"] == "remember this"
    assert result.observation["file_id"] == "note"
    assert result.observation["tool_name"] == "file.read"

    print("✓ test_file_read_returns_written_content passed")


def test_file_read_observation_has_all_fields():
    """Test file.read observation includes revision, created_at, updated_at."""
    ws = WorldState(clock=5.0)
    FileWriteTool().execute(ws, {"file_id": "x", "content": "v1"})

    result = FileReadTool().execute(ws, {"file_id": "x"})
    obs = result.observation

    assert obs["revision"] == 1
    assert obs["created_at"] == 5.0
    assert obs["updated_at"] == 5.0
    assert obs["metadata"] == {}

    print("✓ test_file_read_observation_has_all_fields passed")


# ------------------------------------------------------------------
# 场景 3：读取不存在文件时返回失败
# ------------------------------------------------------------------

def test_file_read_missing_file_returns_failure():
    """Test file.read returns success=False when file does not exist."""
    ws = WorldState()
    result = FileReadTool().execute(ws, {"file_id": "ghost"})

    assert result.success is False
    assert result.state_changed is False
    assert result.error is not None
    assert "ghost" in result.error

    print("✓ test_file_read_missing_file_returns_failure passed")


def test_file_read_empty_file_id_returns_failure():
    """Test file.read returns error when file_id is missing."""
    ws = WorldState()
    result = FileReadTool().execute(ws, {})

    assert result.success is False
    assert "file_id" in result.error

    print("✓ test_file_read_empty_file_id_returns_failure passed")


# ------------------------------------------------------------------
# 场景 4：重复 write 同一 file_id 时能覆盖内容
# ------------------------------------------------------------------

def test_file_write_overwrite_updates_content():
    """Test file.write overwrites content when file already exists."""
    ws = WorldState(clock=1.0)
    write = FileWriteTool()

    write.execute(ws, {"file_id": "log", "content": "v1"})

    ws.clock = 2.0
    result = write.execute(ws, {"file_id": "log", "content": "v2"})

    assert result.success is True
    assert result.observation["action"] == "overwritten"
    assert result.observation["revision"] == 2

    entity = ws.get_entity("file", "log")
    assert entity["content"] == "v2"
    assert entity["revision"] == 2
    assert entity["created_at"] == 1.0   # 保留原始创建时间
    assert entity["updated_at"] == 2.0   # 更新时间变化

    print("✓ test_file_write_overwrite_updates_content passed")


def test_file_write_overwrite_preserves_metadata_if_not_provided():
    """Test that re-writing without metadata keeps the original metadata."""
    ws = WorldState()
    write = FileWriteTool()
    write.execute(ws, {"file_id": "cfg", "content": "old", "metadata": {"env": "prod"}})

    # 再次写入，不携带 metadata
    write.execute(ws, {"file_id": "cfg", "content": "new"})
    entity = ws.get_entity("file", "cfg")

    assert entity["content"] == "new"
    assert entity["metadata"]["env"] == "prod"   # 元数据应被保留

    print("✓ test_file_write_overwrite_preserves_metadata_if_not_provided passed")


# ------------------------------------------------------------------
# 场景 5：write 导致 version/hash 变化，read 不导致状态变化
# ------------------------------------------------------------------

def test_file_write_changes_version_and_hash():
    """Test file.write increments version and changes state hash."""
    ws = WorldState()
    version_before = ws.version
    hash_before = ws.compute_hash()

    FileWriteTool().execute(ws, {"file_id": "a", "content": "content"})

    assert ws.version == version_before + 1
    assert ws.compute_hash() != hash_before

    print("✓ test_file_write_changes_version_and_hash passed")


def test_file_read_does_not_change_version_or_hash():
    """Test file.read leaves version and hash unchanged."""
    ws = WorldState()
    FileWriteTool().execute(ws, {"file_id": "b", "content": "data"})

    version_after_write = ws.version
    hash_after_write = ws.compute_hash()

    FileReadTool().execute(ws, {"file_id": "b"})

    assert ws.version == version_after_write
    assert ws.compute_hash() == hash_after_write

    print("✓ test_file_read_does_not_change_version_or_hash passed")


def test_multiple_writes_increment_version_each_time():
    """Test each write call increments version by exactly 1."""
    ws = WorldState()
    write = FileWriteTool()

    for i in range(5):
        write.execute(ws, {"file_id": f"f{i}", "content": f"content_{i}"})

    assert ws.version == 5

    print("✓ test_multiple_writes_increment_version_each_time passed")


# ------------------------------------------------------------------
# FILE_TOOLS 注册表
# ------------------------------------------------------------------

def test_file_tools_registry():
    """Test FILE_TOOLS contains both tools by name."""
    assert "file.write" in FILE_TOOLS
    assert "file.read" in FILE_TOOLS
    assert isinstance(FILE_TOOLS["file.write"], FileWriteTool)
    assert isinstance(FILE_TOOLS["file.read"], FileReadTool)

    print("✓ test_file_tools_registry passed")


# ------------------------------------------------------------------
# 参数缺失的错误处理
# ------------------------------------------------------------------

def test_file_write_missing_file_id_returns_failure():
    """Test file.write returns error when file_id is missing."""
    ws = WorldState()
    result = FileWriteTool().execute(ws, {"content": "text"})

    assert result.success is False
    assert result.state_changed is False
    assert "file_id" in result.error

    print("✓ test_file_write_missing_file_id_returns_failure passed")


def test_file_write_missing_content_returns_failure():
    """Test file.write returns error when content is missing."""
    ws = WorldState()
    result = FileWriteTool().execute(ws, {"file_id": "f1"})

    assert result.success is False
    assert result.state_changed is False
    assert "content" in result.error

    print("✓ test_file_write_missing_content_returns_failure passed")


# ------------------------------------------------------------------
# 入口
# ------------------------------------------------------------------

def run_all_tests() -> None:
    """Run all file_tools tests."""
    print("=" * 60)
    print("Running file_tools tests...")
    print("=" * 60)

    test_file_write_creates_entity()
    test_file_write_observation_fields()
    test_file_write_with_metadata()
    test_file_read_returns_written_content()
    test_file_read_observation_has_all_fields()
    test_file_read_missing_file_returns_failure()
    test_file_read_empty_file_id_returns_failure()
    test_file_write_overwrite_updates_content()
    test_file_write_overwrite_preserves_metadata_if_not_provided()
    test_file_write_changes_version_and_hash()
    test_file_read_does_not_change_version_or_hash()
    test_multiple_writes_increment_version_each_time()
    test_file_tools_registry()
    test_file_write_missing_file_id_returns_failure()
    test_file_write_missing_content_returns_failure()

    print("=" * 60)
    print("All file_tools tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
