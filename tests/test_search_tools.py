"""
Unit tests for toolsim.search_tools.

Run with: python -m pytest tests/test_search_tools.py -v
Or directly: python tests/test_search_tools.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toolsim.tools.file_tools import FileWriteTool
from toolsim.tools.search_tools import SEARCH_TOOLS, SearchIndexTool, SearchQueryTool
from toolsim.core.world_state import WorldState


def test_search_query_cannot_find_unindexed_file():
    """file.write alone should not make content searchable."""
    ws = WorldState()
    FileWriteTool().execute(ws, {"file_id": "doc1", "content": "alpha beta"})

    result = SearchQueryTool().execute(ws, {"query": "alpha"})

    assert result.success is True
    assert result.state_changed is False
    assert result.observation["hits"] == []


def test_search_query_finds_file_after_index():
    """search.index should make the current file snapshot searchable."""
    ws = WorldState(clock=10.0)
    FileWriteTool().execute(
        ws,
        {"file_id": "doc1", "content": "alpha beta", "metadata": {"topic": "demo"}},
    )

    index_result = SearchIndexTool().execute(ws, {"file_id": "doc1"})
    query_result = SearchQueryTool().execute(ws, {"query": "alpha"})

    assert index_result.success is True
    assert index_result.state_changed is True
    assert index_result.observation["tool_name"] == "search.index"
    assert index_result.observation["file_id"] == "doc1"
    assert index_result.observation["action"] == "indexed"

    assert query_result.success is True
    assert query_result.state_changed is False
    assert len(query_result.observation["hits"]) == 1
    assert query_result.observation["hits"][0]["file_id"] == "doc1"
    assert query_result.observation["hits"][0]["content"] == "alpha beta"
    assert query_result.observation["hits"][0]["metadata"]["topic"] == "demo"


def test_search_query_returns_empty_hits_when_no_match():
    """Non-matching substrings should return an empty hit list."""
    ws = WorldState()
    FileWriteTool().execute(ws, {"file_id": "doc1", "content": "alpha beta"})
    SearchIndexTool().execute(ws, {"file_id": "doc1"})

    result = SearchQueryTool().execute(ws, {"query": "gamma"})

    assert result.success is True
    assert result.observation["hits"] == []


def test_search_index_missing_file_returns_failure():
    """Indexing a missing file should fail without mutating state."""
    ws = WorldState()
    version_before = ws.version
    hash_before = ws.compute_hash()

    result = SearchIndexTool().execute(ws, {"file_id": "ghost"})

    assert result.success is False
    assert result.state_changed is False
    assert "ghost" in result.error
    assert ws.version == version_before
    assert ws.compute_hash() == hash_before


def test_search_query_uses_stale_snapshot_until_reindexed():
    """After overwrite, query should still reflect the old indexed snapshot."""
    ws = WorldState(clock=1.0)
    write_tool = FileWriteTool()
    index_tool = SearchIndexTool()
    query_tool = SearchQueryTool()

    write_tool.execute(ws, {"file_id": "doc1", "content": "alpha beta"})
    index_tool.execute(ws, {"file_id": "doc1"})

    ws.clock = 2.0
    write_tool.execute(ws, {"file_id": "doc1", "content": "gamma delta"})

    stale_old = query_tool.execute(ws, {"query": "alpha"})
    stale_new = query_tool.execute(ws, {"query": "gamma"})

    assert len(stale_old.observation["hits"]) == 1
    assert stale_old.observation["hits"][0]["content"] == "alpha beta"
    assert stale_new.observation["hits"] == []


def test_search_query_reflects_latest_content_after_reindex():
    """Re-indexing should replace the stale snapshot with the latest file content."""
    ws = WorldState(clock=1.0)
    write_tool = FileWriteTool()
    index_tool = SearchIndexTool()
    query_tool = SearchQueryTool()

    write_tool.execute(ws, {"file_id": "doc1", "content": "alpha beta"})
    index_tool.execute(ws, {"file_id": "doc1"})

    ws.clock = 2.0
    write_tool.execute(ws, {"file_id": "doc1", "content": "gamma delta"})
    reindex_result = index_tool.execute(ws, {"file_id": "doc1"})

    old_query = query_tool.execute(ws, {"query": "alpha"})
    new_query = query_tool.execute(ws, {"query": "gamma"})

    assert reindex_result.success is True
    assert reindex_result.observation["source_revision"] == 2
    assert old_query.observation["hits"] == []
    assert len(new_query.observation["hits"]) == 1
    assert new_query.observation["hits"][0]["content"] == "gamma delta"


def test_search_query_does_not_change_version_or_hash():
    """search.query should be a pure read against indexed snapshots."""
    ws = WorldState()
    FileWriteTool().execute(ws, {"file_id": "doc1", "content": "alpha beta"})
    SearchIndexTool().execute(ws, {"file_id": "doc1"})

    version_before = ws.version
    hash_before = ws.compute_hash()

    result = SearchQueryTool().execute(ws, {"query": "alpha"})

    assert result.success is True
    assert ws.version == version_before
    assert ws.compute_hash() == hash_before


def test_search_tools_registry():
    """SEARCH_TOOLS should expose both search tools by tool_name."""
    assert "search.index" in SEARCH_TOOLS
    assert "search.query" in SEARCH_TOOLS
    assert isinstance(SEARCH_TOOLS["search.index"], SearchIndexTool)
    assert isinstance(SEARCH_TOOLS["search.query"], SearchQueryTool)


def run_all_tests() -> None:
    """Run all search_tools tests."""
    test_search_query_cannot_find_unindexed_file()
    test_search_query_finds_file_after_index()
    test_search_query_returns_empty_hits_when_no_match()
    test_search_index_missing_file_returns_failure()
    test_search_query_uses_stale_snapshot_until_reindexed()
    test_search_query_reflects_latest_content_after_reindex()
    test_search_query_does_not_change_version_or_hash()
    test_search_tools_registry()
    print("All search_tools tests passed!")


if __name__ == "__main__":
    run_all_tests()
