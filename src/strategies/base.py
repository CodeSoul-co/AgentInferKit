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
      2. Resolves prompt_id from src/prompts/registry.yaml
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
        # Common generation parameters (runtime > YAML > sensible defaults)
        defaults = self._yaml_cfg.get("generation", {})
        self._temperature: Optional[float] = self._runtime_cfg.get(
            "temperature", defaults.get("temperature")
        )
        self._max_tokens: Optional[int] = self._runtime_cfg.get(
            "max_tokens", defaults.get("max_tokens")
        )

    # ------------------------------------------------------------------
    # Model-config overrides (temperature, max_tokens, etc.)
    # ------------------------------------------------------------------

    def get_model_overrides(self) -> Dict[str, Any]:
        """Return model_config overrides from strategy-level generation params.

        The runner should merge these into model_config before creating the
        LLM so that strategy-specific temperature / max_tokens take effect.
        Only includes keys that are explicitly set (not None).
        """
        overrides: Dict[str, Any] = {}
        if self._temperature is not None:
            overrides["temperature"] = self._temperature
        if self._max_tokens is not None:
            overrides["max_tokens"] = self._max_tokens
        return overrides

    @property
    def temperature(self) -> Optional[float]:
        return self._temperature

    @property
    def max_tokens(self) -> Optional[int]:
        return self._max_tokens

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
        """Build Message list from a prompt_id in src/prompts/.

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

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Strip common markdown formatting that interferes with parsing."""
        # Remove bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        # Remove italic: *text* or _text_ (single)
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', text)
        # Remove backtick code: `text`
        text = re.sub(r'`([^`]+?)`', r'\1', text)
        return text.strip()

    def _extract_answer(self, raw_output: str, task_type: str) -> str:
        """Extract answer using patterns from YAML parse config.

        Priority order:
        1. GSM8K #### pattern (most reliable for math QA)
        2. Answer: pattern (explicit CoT final answer)
        3. Fallback: choice letter / last number / last line
        """
        answer_pattern = self._parse_cfg.get("answer_pattern", r"[Aa]nswer\s*[：:]\s*(.+)")
        choice_pattern = self._parse_cfg.get("choice_pattern", r"\b([A-D])\b")

        # Pre-process: strip markdown from the raw output for parsing
        cleaned = self._strip_markdown(raw_output)

        # Priority 1: GSM8K #### pattern (most unambiguous)
        if task_type in ("qa", "text_qa"):
            hash_match = re.search(r"####\s*(.+)", cleaned)
            if hash_match:
                num = self._extract_final_number(hash_match.group(1))
                if num is not None:
                    return num

        # Priority 2: Explicit "Answer:" line (search from end for last occurrence)
        matches = list(re.finditer(answer_pattern, cleaned))
        if matches:
            parsed = matches[-1].group(1).strip()
            # Strip any remaining markdown from the captured answer
            parsed = self._strip_markdown(parsed)
            if task_type in ("text_exam", "image_mcq"):
                letter = re.search(choice_pattern, parsed)
                if letter:
                    return letter.group(1)
            if task_type in ("qa", "text_qa"):
                num = self._extract_final_number(parsed)
                if num is not None:
                    return num
            return parsed

        # Fallback for choice tasks: scan entire output for a letter
        if task_type in ("text_exam", "image_mcq"):
            letter = re.search(choice_pattern, cleaned)
            if letter:
                return letter.group(1)

        # Fallback for QA: try last line number
        if task_type in ("qa", "text_qa"):
            lines = cleaned.strip().split("\n")
            last_line = lines[-1].strip() if lines else ""
            num = self._extract_final_number(last_line)
            if num is not None:
                return num

        # Ultimate fallback: last non-empty line
        lines = cleaned.strip().split("\n")
        return lines[-1].strip() if lines else cleaned.strip()

    @staticmethod
    def _extract_final_number(text: str) -> Optional[str]:
        """Extract the last number from text, handling currency, commas, markdown."""
        # Strip markdown bold/italic wrapping first
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'`([^`]+?)`', r'\1', text)
        # Match integers or decimals, possibly preceded by $ or other currency symbols
        numbers = re.findall(r'[-+]?\$?\s*[\d,]+\.?\d*', text)
        if numbers:
            num_str = numbers[-1].strip().replace('$', '').replace(',', '').strip()
            try:
                val = float(num_str)
                if val == int(val):
                    return str(int(val))
                return str(val)
            except ValueError:
                pass
        return None

    # ------------------------------------------------------------------
    # Step-splitting patterns for structured trace extraction
    # ------------------------------------------------------------------
    _STEP_PATTERNS = [
        # "Step 1:", "Step 1.", "Step 1)"
        re.compile(r'^(?:Step\s+\d+[.:)]\s*)', re.IGNORECASE | re.MULTILINE),
        # "1. ", "1) ", "1: " at line start (numbered list)
        re.compile(r'^(\d+)[.:)]\s+', re.MULTILINE),
        # "Thought:" / "Thought 1:" (ReAct style)
        re.compile(r'^Thought(?:\s+\d+)?\s*[.:]\s*', re.IGNORECASE | re.MULTILINE),
        # "First," / "Second," / "Third," etc.
        re.compile(r'^(?:First|Second|Third|Fourth|Fifth|Sixth|Next|Then|Finally)[,.:]\s*', re.IGNORECASE | re.MULTILINE),
    ]

    def _extract_trace(self, raw_output: str) -> List[Dict[str, Any]]:
        """Extract reasoning trace as a structured list of steps.

        Splits on recognized step boundaries (Step N:, numbered lists, etc.)
        and returns a list of {step, type, content} dicts.
        Falls back to paragraph splitting if no explicit step markers found.
        """
        answer_pattern = self._parse_cfg.get("answer_pattern", r"[Aa]nswer\s*[：:]\s*(.+)")

        # Remove the final Answer: line(s) from the trace
        lines = raw_output.strip().split("\n")
        trace_lines = [l for l in lines if not re.search(answer_pattern, l)]
        # Also remove GSM8K #### lines
        trace_lines = [l for l in trace_lines if not re.match(r'\s*####\s', l)]
        trace_text = "\n".join(trace_lines).strip()
        if not trace_text:
            return []

        # Try each step pattern to find split points
        for pattern in self._STEP_PATTERNS:
            split_positions = [m.start() for m in pattern.finditer(trace_text)]
            if len(split_positions) >= 2:
                # Found multiple step markers -> split into steps
                steps = []
                for i, pos in enumerate(split_positions):
                    end = split_positions[i + 1] if i + 1 < len(split_positions) else len(trace_text)
                    step_text = trace_text[pos:end].strip()
                    if step_text:
                        steps.append({
                            "step": i + 1,
                            "type": "thought",
                            "content": step_text,
                        })
                return steps

        # Fallback: split by double-newline (paragraph boundaries)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', trace_text) if p.strip()]
        if len(paragraphs) >= 2:
            return [
                {"step": i + 1, "type": "thought", "content": p}
                for i, p in enumerate(paragraphs)
            ]

        # Last resort: single step containing all the reasoning
        return [{"step": 1, "type": "thought", "content": trace_text}]

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
        Returns:
            dict with 'parsed_answer' (str) and 'reasoning_trace' (List[Dict]).
        """
        task_type = sample.get("task_type", "text_qa")
        return {
            "parsed_answer": self._extract_answer(raw_output, task_type),
            "reasoning_trace": self._extract_trace(raw_output),
        }
