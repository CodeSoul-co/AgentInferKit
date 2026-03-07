import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from src.config import TOOL_SCHEMAS_DIR


class ToolRegistry:
    """Registry that loads tool schemas from data/schemas/tool_schemas/ and provides lookup."""

    def __init__(self, schemas_dir: Optional[str] = None) -> None:
        self._schemas_dir = Path(schemas_dir) if schemas_dir else TOOL_SCHEMAS_DIR
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Scan the schemas directory and load all tool JSON files."""
        if not self._schemas_dir.exists():
            logger.warning(f"Tool schemas directory not found: {self._schemas_dir}")
            return
        for json_file in sorted(self._schemas_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                tool_id = schema.get("tool_id", json_file.stem)
                self._tools[tool_id] = schema
                logger.debug(f"Loaded tool schema: {tool_id}")
            except Exception as e:
                logger.error(f"Failed to load tool schema {json_file}: {e}")

    def get_tool(self, tool_id: str) -> Dict[str, Any]:
        """Get a tool schema by tool_id.

        Args:
            tool_id: The unique identifier of the tool.

        Returns:
            The full tool schema dict.

        Raises:
            KeyError: If the tool_id is not found.
        """
        if tool_id not in self._tools:
            raise KeyError(f"Tool '{tool_id}' not found. Available: {list(self._tools.keys())}")
        return self._tools[tool_id]

    def get_tools_for_sample(self, available_tools: List[str]) -> List[Dict[str, Any]]:
        """Return formatted tool descriptions for a list of tool_ids, suitable for prompt injection.

        Args:
            available_tools: List of tool_id strings referenced by a sample.

        Returns:
            A list of tool schema dicts (each containing name, description, parameters).
        """
        result = []
        for tool_id in available_tools:
            try:
                schema = self.get_tool(tool_id)
                result.append({
                    "tool_id": schema.get("tool_id", tool_id),
                    "name": schema.get("name", tool_id),
                    "description": schema.get("description", ""),
                    "parameters": schema.get("parameters", {}),
                })
            except KeyError:
                logger.warning(f"Tool '{tool_id}' not found in registry, skipping.")
        return result

    def list_tools(self) -> List[str]:
        """Return all registered tool_ids."""
        return list(self._tools.keys())

    def reload(self) -> None:
        """Re-scan the schemas directory."""
        self._tools.clear()
        self._load_all()
