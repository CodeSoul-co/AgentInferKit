import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.api.schemas import Message
from src.prompts.loader import (
    get_instruction_template,
    get_prompt_version,
    get_system_prompt,
    load_prompt,
    render_instruction,
    resolve_prompt_id,
)

_CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "configs" / "strategies"


def load_strategy_config(strategy_name: str) -> Dict[str, Any]:
    """Load a strategy's YAML config from configs/strategies/{name}.yaml."""
    path = _CONFIGS_DIR / f"{strategy_name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Strategy config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class BaseStrategy(ABC):
    """Abstract base class for all inference strategies.

    Each concrete strategy:
      1. Reads its YAML config from configs/strategies/
      2. Resolves prompt_id from configs/prompts/registry.yaml
      3. Exposes build_prompt() + parse_output() for the runner

    Prompt loading priority:
      - If runtime config contains 'prompt_id', use it directly.
      - Otherwise, resolve from task_type + strategy_name via registry.
      - Fall back to configs/strategies/{name}.yaml prompts as last resort.
    """

    def __init__(self, strategy_name: str, config: Optional[Dict[str, Any]] = None) -> None:
        self._strategy_name = strategy_name
        self._yaml_cfg = load_strategy_config(strategy_name)
        self._runtime_cfg = config or {}
        self._prompts = self._yaml_cfg.get("prompts", {})
        self._parse_cfg = self._yaml_cfg.get("parse", {})
        # Explicit prompt_id from experiment config overrides auto-resolve
        self._explicit_prompt_id: Optional[str] = self._runtime_cfg.get("prompt_id")

    # ------------------------------------------------------------------
    # Prompt helpers (new: prompt_id based)
    # ------------------------------------------------------------------

    def resolve_prompt(self, task_type: str) -> str:
        """Resolve the prompt_id for this strategy + task_type.

        Returns:
            A prompt_id string like 'text_exam.cot'.
        """
        if self._explicit_prompt_id:
            return self._explicit_prompt_id
        try:
            return resolve_prompt_id(task_type, self._strategy_name)
        except KeyError:
            return ""

    def build_messages_from_prompt_id(
        self, prompt_id: str, **template_vars: Any
    ) -> List[Message]:
        """Build Message list from a prompt_id in configs/prompts/.

        Args:
            prompt_id: e.g. 'text_exam.cot'
            **template_vars: Variables for the instruction_template.

        Returns:
            List[Message] with system (if present) + user messages.
        """
        messages: List[Message] = []
        sys_prompt = get_system_prompt(prompt_id)
        if sys_prompt:
            messages.append(Message(role="system", content=sys_prompt))
        user_content = render_instruction(prompt_id, **template_vars)
        messages.append(Message(role="user", content=user_content.strip()))
        return messages

    @property
    def prompt_id(self) -> Optional[str]:
        """The currently resolved prompt_id, if any."""
        return self._explicit_prompt_id

    @property
    def prompt_version(self) -> Optional[str]:
        """The version of the currently resolved prompt."""
        pid = self._explicit_prompt_id
        if pid:
            try:
                return get_prompt_version(pid)
            except (KeyError, FileNotFoundError):
                return None
        return None

    # ------------------------------------------------------------------
    # Common template variable builder
    # ------------------------------------------------------------------

    @staticmethod
    def build_template_vars(sample: Dict[str, Any]) -> Dict[str, str]:
        """Build template variables from sample fields for prompt rendering."""
        task_type = sample.get("task_type", "text_qa")
        question = sample.get("question", "")
        vs: Dict[str, str] = {"question": question}
        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            vs["options_text"] = "\n".join(
                f"{k}. {v}" for k, v in sorted(options.items())
            )
        if task_type == "api_calling":
            vs["user_goal"] = sample.get("user_goal", question)
            tools = sample.get("available_tools", [])
            vs["tools_text"] = "\n".join(
                f"- {t.get('name', t.get('tool_id', ''))}: "
                f"{t.get('description', t.get('core_description', ''))}"
                if isinstance(t, dict) else f"- {t}"
                for t in tools
            )
        return vs

    # ------------------------------------------------------------------
    # Legacy prompt helpers (fallback to configs/strategies/*.yaml)
    # ------------------------------------------------------------------

    def get_prompt_template(self, key: str) -> str:
        """Get a raw prompt template string by key from strategy YAML."""
        tpl = self._prompts.get(key)
        if tpl is None:
            raise KeyError(
                f"Prompt key '{key}' not found in {self._strategy_name}.yaml. "
                f"Available: {list(self._prompts.keys())}"
            )
        return tpl

    def render_prompt(self, key: str, **kwargs: Any) -> str:
        """Render a prompt template with variable substitution."""
        return self.get_prompt_template(key).format(**kwargs)

    # ------------------------------------------------------------------
    # Common parse logic (subclasses can override)
    # ------------------------------------------------------------------

    def _extract_answer(self, raw_output: str, task_type: str) -> str:
        """Extract answer using patterns from YAML parse config."""
        answer_pattern = self._parse_cfg.get("answer_pattern", r"[Aa]nswer\s*[：:]\s*(.+)")
        choice_pattern = self._parse_cfg.get("choice_pattern", r"\b([A-D])\b")

        match = re.search(answer_pattern, raw_output)
        if match:
            parsed = match.group(1).strip()
            if task_type in ("text_exam", "image_mcq"):
                letter = re.search(choice_pattern, parsed)
                if letter:
                    return letter.group(1)
            return parsed

        # Fallback for choice tasks
        if task_type in ("text_exam", "image_mcq"):
            letter = re.search(choice_pattern, raw_output)
            if letter:
                return letter.group(1)

        # Fallback: last line
        lines = raw_output.strip().split("\n")
        return lines[-1].strip() if lines else raw_output.strip()

    def _extract_trace(self, raw_output: str) -> Optional[str]:
        """Extract reasoning trace (everything except the Answer line)."""
        answer_pattern = self._parse_cfg.get("answer_pattern", r"[Aa]nswer\s*[：:]\s*(.+)")
        lines = raw_output.strip().split("\n")
        trace_lines = [l for l in lines if not re.search(answer_pattern, l)]
        trace = "\n".join(trace_lines).strip()
        return trace if trace else None

    # ------------------------------------------------------------------
    # Abstract interface for subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def build_prompt(self, sample: Dict[str, Any], **kwargs: Any) -> List[Message]:
        """Build the prompt messages for a given sample."""
        ...

    def parse_output(self, raw_output: str, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the model's raw output into a structured result.

        Default implementation uses YAML parse config. Subclasses can override.
        """
        task_type = sample.get("task_type", "text_qa")
        return {
            "parsed_answer": self._extract_answer(raw_output, task_type),
            "reasoning_trace": self._extract_trace(raw_output),
        }
