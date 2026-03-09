import json
import re
from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class ReActStrategy(BaseStrategy):
    """ReAct (Reasoning + Acting) strategy backed by LangChain AgentExecutor.

    Reads config from configs/strategies/react.yaml.
    Interleaves Thought / Action / Observation steps.
    The runner drives the agent loop; this class provides prompt building
    and output parsing compatible with LangChain's ReAct agent format.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("react", config)
        react_cfg = self._yaml_cfg.get("react_config", {})
        self._max_steps = self._runtime_cfg.get("max_steps", react_cfg.get("max_steps", 10))
        self._handle_parsing_errors = react_cfg.get("handle_parsing_errors", True)

    @property
    def max_steps(self) -> int:
        return self._max_steps

    def build_prompt(
        self, sample: Dict[str, Any], history: Optional[List[Dict]] = None, **kwargs: Any
    ) -> List[Message]:
        """Build the prompt including previous Thought/Action/Observation history."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", sample.get("user_goal", ""))
        available_tools = sample.get("available_tools", [])

        # Build tool description string (used by both prompt_id and legacy)
        tool_desc = ""
        if available_tools:
            tool_desc = "\n\nAvailable tools:\n"
            for t in available_tools:
                if isinstance(t, dict):
                    tool_desc += f"- {t.get('name', t.get('tool_id', ''))}: {t.get('description', t.get('core_description', ''))}\n"
                else:
                    tool_desc += f"- {t}\n"

        # Try prompt_id from registry (primarily for api_calling tasks)
        prompt_id = self.resolve_prompt(task_type)
        if prompt_id:
            self._resolved_prompt_id = prompt_id
            tpl_vars = self.build_template_vars(sample)
            tpl_vars["tool_desc"] = tool_desc
            messages = self.build_messages_from_prompt_id(prompt_id, **tpl_vars)
        else:
            # Fallback to legacy strategy YAML
            system = self._prompts.get("system", "")
            messages = []
            if system and system.strip():
                messages.append(Message(role="system", content=system.strip()))
            user_content = self.render_prompt("user", question=question, tool_desc=tool_desc)
            messages.append(Message(role="user", content=user_content.strip()))

        # Append history turns (Thought/Action/Observation loop)
        if history:
            for turn in history:
                role = turn.get("role", "assistant")
                content = turn.get("content", "")
                messages.append(Message(role=role, content=content))

        return messages

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the model output to detect Thought, Action, or Answer.

        Compatible with LangChain AgentExecutor's ReAct output format.
        """
        text = raw_output.strip()
        task_type = sample.get("task_type", "text_qa")

        # Check for final Answer
        answer_match = re.search(
            self._parse_cfg.get("answer_pattern", r"[Aa]nswer\s*[：:]\s*(.+)"), text
        )
        if answer_match:
            parsed = answer_match.group(1).strip()
            if task_type in ("text_exam", "image_mcq"):
                letter = re.search(self._parse_cfg.get("choice_pattern", r"\b([A-D])\b"), parsed)
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

    def get_agent_executor_kwargs(self) -> Dict[str, Any]:
        """Return kwargs for constructing a LangChain AgentExecutor."""
        return {
            "max_iterations": self._max_steps,
            "handle_parsing_errors": self._handle_parsing_errors,
        }
