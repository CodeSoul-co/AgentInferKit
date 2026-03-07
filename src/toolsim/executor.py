from typing import Any, Dict, List, Optional

from loguru import logger

from src.toolsim.registry import ToolRegistry
from src.toolsim.tracer import ToolCallTracer


class MockExecutor:
    """Execute mock tool calls based on tool schema mock_responses.

    For each call, matches the parameters against conditions defined in the
    tool schema's mock_responses list, returns the corresponding mock response,
    and records the call via the tracer.
    """

    def __init__(self, registry: ToolRegistry, tracer: Optional[ToolCallTracer] = None) -> None:
        self._registry = registry
        self._tracer = tracer

    def execute(self, tool_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mock tool call.

        Args:
            tool_id: The tool to invoke.
            parameters: Parameters to pass to the tool.

        Returns:
            A dict with keys: tool_id, response, matched_condition.
        """
        try:
            schema = self._registry.get_tool(tool_id)
        except KeyError as e:
            result = {"tool_id": tool_id, "response": {}, "matched_condition": None}
            if self._tracer:
                self._tracer.record(tool_id, parameters, {}, "error_not_found")
            logger.error(str(e))
            return result

        mock_responses = schema.get("mock_responses", [])
        response, matched_condition = self._match_response(mock_responses, parameters)

        if self._tracer:
            self._tracer.record(tool_id, parameters, response, "success")

        return {
            "tool_id": tool_id,
            "response": response,
            "matched_condition": matched_condition,
        }

    def _match_response(
        self,
        mock_responses: List[Dict[str, Any]],
        parameters: Dict[str, Any],
    ) -> tuple:
        """Find the first matching mock response for the given parameters.

        Returns:
            A tuple of (response_dict, condition_name).
        """
        default_response = {}
        default_condition = None

        for entry in mock_responses:
            condition = entry.get("condition", "default")
            if condition == "default":
                default_response = entry.get("response", {})
                default_condition = condition
                continue

            # Condition matching: condition can be a dict of param_key -> expected_value
            if isinstance(condition, dict):
                if all(parameters.get(k) == v for k, v in condition.items()):
                    return entry.get("response", {}), str(condition)

        return default_response, default_condition
