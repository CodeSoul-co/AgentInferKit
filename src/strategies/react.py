"""
ReAct strategy — calls vendor/ReAct Thought->Action->Observation loop.

Reference implementation: https://github.com/ysymyth/ReAct
The core loop is adapted from ``vendor/ReAct/hotpotqa.ipynb`` (``webthink()``).
LLM calls go through our LangChain ChatOpenAI; tool execution goes through
our ``MockExecutor``.
"""

import json
import re
from typing import Any, Dict, List, Optional

from loguru import logger

from src.api.schemas import Message
from src.langchain_bridge import TokenUsageTracker, make_langchain_llm
from src.strategies.base import BaseStrategy


# ---------------------------------------------------------------------------
# Instruction prompt from vendor/ReAct/hotpotqa.ipynb
# ---------------------------------------------------------------------------
_REACT_INSTRUCTION = (
    "Solve a question answering task with interleaving Thought, Action, "
    "Observation steps. Thought can reason about the current situation, "
    "and Action can be one of the following types:\n"
    "{tool_desc}\n"
    "({n_tools}) Finish[answer], which returns the answer and finishes the task.\n\n"
    "Use EXACTLY this format:\n"
    "Thought 1: <reasoning>\n"
    "Action 1: <ToolName>[<input>]\n"
    "Observation 1: <result from tool>\n"
    "... (repeat until done)\n"
    "Thought N: I now know the answer\n"
    "Action N: Finish[<answer>]\n\n"
)


class ReActStrategy(BaseStrategy):
    """ReAct (Reasoning + Acting) strategy using the vendor loop.

    Adapted from ``vendor/ReAct/hotpotqa.ipynb`` ``webthink()`` function.
    The loop:
      for i in 1..max_steps:
        1. LLM generates "Thought i: ... \\nAction i: ..."
        2. Parse the action, execute via MockExecutor
        3. Append "Observation i: ..." to the prompt
        4. If action is Finish[answer], stop

    Reads config from configs/strategies/react.yaml.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("react", config)
        react_cfg = self._yaml_cfg.get("react_config", {})
        self._max_steps = self._runtime_cfg.get(
            "max_steps", react_cfg.get("max_steps", 7)
        )

    @property
    def max_steps(self) -> int:
        return self._max_steps

    # ------------------------------------------------------------------
    # Core: vendor ReAct loop (adapted from webthink())
    # ------------------------------------------------------------------

    def run_react_loop(
        self,
        sample: Dict[str, Any],
        model_config: Dict[str, Any],
        tool_schemas: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run the Thought->Action->Observation loop from vendor/ReAct.

        Adapted from vendor/ReAct/hotpotqa.ipynb ``webthink()`` function.

        Args:
            sample: The input sample dict.
            model_config: Model config for make_langchain_llm.
            tool_schemas: List of tool schema dicts from ToolRegistry.

        Returns:
            Dict with raw_output, parsed_answer, reasoning_trace, tool_trace, usage.
        """
        from langchain_core.messages import HumanMessage

        from src.toolsim.executor import MockExecutor
        from src.toolsim.registry import ToolRegistry

        llm = make_langchain_llm(model_config)
        tracker = TokenUsageTracker()

        registry = ToolRegistry()
        executor = MockExecutor(registry)

        # Build tool description for the instruction
        tool_desc_parts = []
        for idx, ts in enumerate(tool_schemas, 1):
            name = ts.get("tool_id", ts.get("name", "unknown"))
            desc = ts.get("description", ts.get("core_description", ""))
            tool_desc_parts.append(f"({idx}) {name}[input], {desc}")
        tool_desc_str = "\n".join(tool_desc_parts)

        instruction = _REACT_INSTRUCTION.format(
            tool_desc=tool_desc_str, n_tools=len(tool_schemas) + 1
        )

        # Build initial prompt: instruction + question
        question = sample.get("user_goal", sample.get("question", ""))
        prompt = instruction + f"Question: {question}\n"

        reasoning_trace = []
        tool_trace = []
        n_calls = 0
        final_answer = ""

        for i in range(1, self._max_steps + 1):
            n_calls += 1

            # Ask LLM for Thought + Action
            thought_action_prompt = prompt + f"Thought {i}:"
            resp = llm.invoke(
                [HumanMessage(content=thought_action_prompt)],
                config={"callbacks": [tracker]},
                stop=[f"\nObservation {i}:"],
            )
            thought_action = resp.content if hasattr(resp, "content") else str(resp)

            # Parse thought and action (vendor pattern)
            # LLM may or may not include the "Thought i:" prefix
            ta_text = thought_action.strip()
            # Try splitting on "Action i: " with various patterns
            action = ""
            thought = ta_text
            for sep in [f"\nAction {i}: ", f"\nAction {i}:", "\nAction: "]:
                if sep in ta_text:
                    thought, action = ta_text.split(sep, 1)
                    break
            if not action:
                # Fallback: ask LLM for action separately
                thought = ta_text.split("\n")[0]
                n_calls += 1
                action_resp = llm.invoke(
                    [HumanMessage(
                        content=prompt + f"Thought {i}: {thought}\nAction {i}:"
                    )],
                    config={"callbacks": [tracker]},
                    stop=["\n"],
                )
                action = (
                    action_resp.content
                    if hasattr(action_resp, "content")
                    else str(action_resp)
                ).strip()
            action = action.strip()

            reasoning_trace.append({
                "step": i,
                "type": "thought_action",
                "content": f"Thought: {thought.strip()}\nAction: {action.strip()}",
                "thought": thought.strip(),
                "action": action.strip(),
            })

            # Check for Finish action
            finish_match = re.match(r"[Ff]inish\[(.+)\]", action.strip())
            if finish_match:
                final_answer = finish_match.group(1)
                prompt += f"Thought {i}: {thought}\nAction {i}: {action}\n"
                break

            # Execute tool action
            tool_match = re.match(r"(\w+)\[(.+)\]", action.strip())
            if tool_match:
                tool_name = tool_match.group(1).lower()
                tool_input = tool_match.group(2)
                result = executor.execute(tool_name, {"input": tool_input})
                obs = json.dumps(
                    result.get("response", result), ensure_ascii=False
                )
                tool_trace.append({
                    "tool_id": tool_name,
                    "parameters": {"input": tool_input},
                    "response": obs,
                    "status": "success" if "error" not in result else "error",
                })
            else:
                obs = f"Invalid action format: {action}"
                logger.warning(f"ReAct step {i}: invalid action: {action}")

            step_str = (
                f"Thought {i}: {thought}\n"
                f"Action {i}: {action}\n"
                f"Observation {i}: {obs}\n"
            )
            prompt += step_str

        # If loop exhausted without Finish
        if not final_answer:
            final_answer = thought_action.strip() if thought_action else ""

        parsed = self.parse_output(final_answer, sample)
        return {
            "raw_output": prompt,
            "parsed_answer": parsed["parsed_answer"] or final_answer.strip(),
            "reasoning_trace": reasoning_trace,
            "tool_trace": tool_trace,
            "usage": tracker.to_usage_dict(),
        }

    # ------------------------------------------------------------------
    # Prompt building (fallback for non-loop paths)
    # ------------------------------------------------------------------

    def build_prompt(
        self, sample: Dict[str, Any], history: Optional[List[Dict]] = None, **kwargs: Any
    ) -> List[Message]:
        """Build prompt messages for manual (non-loop) usage."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", sample.get("user_goal", ""))
        available_tools = sample.get("available_tools", [])

        tool_desc = ""
        if available_tools:
            tool_desc = "\n\nAvailable tools:\n"
            for t in available_tools:
                if isinstance(t, dict):
                    tool_desc += (
                        f"- {t.get('name', t.get('tool_id', ''))}: "
                        f"{t.get('description', t.get('core_description', ''))}\n"
                    )
                else:
                    tool_desc += f"- {t}\n"

        prompt_id = self.resolve_prompt(task_type)
        if prompt_id:
            self._resolved_prompt_id = prompt_id
            tpl_vars = self.build_template_vars(sample)
            tpl_vars["tool_desc"] = tool_desc
            messages = self.build_messages_from_prompt_id(prompt_id, **tpl_vars)
        else:
            system = self._prompts.get("system", "")
            messages = []
            if system and system.strip():
                messages.append(Message(role="system", content=system.strip()))
            user_content = self.render_prompt("user", question=question, tool_desc=tool_desc)
            messages.append(Message(role="user", content=user_content.strip()))

        if history:
            for turn in history:
                role = turn.get("role", "assistant")
                content = turn.get("content", "")
                messages.append(Message(role=role, content=content))

        return messages

    # ------------------------------------------------------------------
    # Output parsing
    # ------------------------------------------------------------------

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Parse model output to detect Thought, Action, or Answer."""
        text = raw_output.strip()
        task_type = sample.get("task_type", "text_qa")

        answer_match = re.search(
            self._parse_cfg.get("answer_pattern", r"[Aa]nswer\s*[：:]\s*(.+)"), text
        )
        if answer_match:
            parsed = answer_match.group(1).strip()
            if task_type in ("text_exam", "image_mcq"):
                letter = re.search(
                    self._parse_cfg.get("choice_pattern", r"\b([A-D])\b"), parsed
                )
                if letter:
                    parsed = letter.group(1)
            return {
                "parsed_answer": parsed,
                "reasoning_trace": text,
                "action": None,
                "step_type": "answer",
            }

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

        return {
            "parsed_answer": text,
            "reasoning_trace": text,
            "action": None,
            "step_type": "thought",
        }
