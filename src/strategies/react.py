import re
from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class ReActStrategy(BaseStrategy):
    """ReAct (Reasoning + Acting) strategy.

    Interleaves Thought / Action / Observation steps. The strategy builds
    prompts that include previous interaction history so the model can
    decide when to call a tool (Action) and when to give a final answer.
    The actual tool execution loop is driven by the runner.
    """

    SYSTEM_PROMPT = (
        "You are a helpful assistant that solves problems by interleaving "
        "reasoning and actions. At each step, output exactly ONE of:\n"
        "  Thought: <your reasoning>\n"
        "  Action: <tool_name>(<json_params>)\n"
        "  Answer: <final answer>\n"
        "After receiving an Observation from a tool, continue reasoning."
    )

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._max_steps = self._config.get("max_steps", 10)

    def build_prompt(
        self, sample: Dict[str, Any], history: Optional[List[Dict]] = None
    ) -> List[Message]:
        """Build the prompt including previous Thought/Action/Observation history.

        Args:
            sample: The data sample.
            history: Optional list of dicts with keys 'role' and 'content',
                     representing previous interaction turns.

        Returns:
            List of Message objects.
        """
        question = sample.get("question", sample.get("user_goal", ""))
        available_tools = sample.get("available_tools", [])

        messages: List[Message] = [
            Message(role="system", content=self.SYSTEM_PROMPT),
        ]

        # Include tool descriptions if available
        tool_desc = ""
        if available_tools:
            tool_desc = "\n\nAvailable tools:\n"
            for t in available_tools:
                if isinstance(t, dict):
                    tool_desc += f"- {t.get('name', t.get('tool_id', ''))}: {t.get('description', '')}\n"
                else:
                    tool_desc += f"- {t}\n"

        user_content = f"{question}{tool_desc}"
        messages.append(Message(role="user", content=user_content))

        # Append history turns
        if history:
            for turn in history:
                role = turn.get("role", "assistant")
                content = turn.get("content", "")
                messages.append(Message(role=role, content=content))

        return messages

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the model output to detect Thought, Action, or Answer.

        Returns:
            Dict with:
                - parsed_answer: str (non-empty if final answer found)
                - reasoning_trace: str
                - action: dict | None (tool_name, parameters if Action detected)
                - step_type: 'thought' | 'action' | 'answer'
        """
        text = raw_output.strip()

        # Check for final Answer
        answer_match = re.search(r"[Aa]nswer\s*:\s*(.+)", text)
        if answer_match:
            parsed = answer_match.group(1).strip()
            task_type = sample.get("task_type", "text_qa")
            if task_type in ("text_exam", "image_mcq"):
                letter = re.search(r"\b([A-D])\b", parsed)
                if letter:
                    parsed = letter.group(1)
            return {
                "parsed_answer": parsed,
                "reasoning_trace": text,
                "action": None,
                "step_type": "answer",
            }

        # Check for Action
        action_match = re.search(r"[Aa]ction\s*:\s*(\w+)\((.+?)\)", text, re.DOTALL)
        if action_match:
            tool_name = action_match.group(1)
            params_str = action_match.group(2).strip()
            try:
                import json
                params = json.loads(params_str)
            except Exception:
                params = {"raw": params_str}
            return {
                "parsed_answer": "",
                "reasoning_trace": text,
                "action": {"tool_name": tool_name, "parameters": params},
                "step_type": "action",
            }

        # Default: treat as Thought
        return {
            "parsed_answer": "",
            "reasoning_trace": text,
            "action": None,
            "step_type": "thought",
        }
