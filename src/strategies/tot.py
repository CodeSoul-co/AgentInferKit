from typing import Any, Dict, List, Optional

from src.api.schemas import Message
from src.strategies.base import BaseStrategy


class ToTStrategy(BaseStrategy):
    """Tree-of-Thought strategy backed by langchain-experimental.

    Reads config from configs/strategies/tot.yaml.
    Uses ToTChain from langchain-experimental for tree search.
    The build_prompt() and build_checker_prompt() methods provide the
    generation and evaluation prompts; the runner drives the search loop.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("tot", config)
        tot_cfg = self._yaml_cfg.get("tot_config", {})
        self._k = self._runtime_cfg.get("k", tot_cfg.get("k", 3))
        self._depth = self._runtime_cfg.get("depth", tot_cfg.get("depth", 3))

    @property
    def k(self) -> int:
        return self._k

    @property
    def depth(self) -> int:
        return self._depth

    def build_prompt(self, sample: Dict[str, Any], **kwargs: Any) -> List[Message]:
        """Build the thought-generation prompt for a single branch."""
        task_type = sample.get("task_type", "text_qa")

        prompt_id = self.resolve_prompt(task_type)
        if prompt_id:
            self._resolved_prompt_id = prompt_id
            return self.build_messages_from_prompt_id(prompt_id, **self.build_template_vars(sample))

        # Fallback to legacy strategy YAML
        question = sample.get("question", "")
        system = self._prompts.get("system", "")
        messages: List[Message] = []
        if system and system.strip():
            messages.append(Message(role="system", content=system.strip()))

        if task_type in ("text_exam", "image_mcq"):
            options = sample.get("options", {})
            options_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))
            user_content = self.render_prompt("user_exam", question=question, options_text=options_text)
        else:
            user_content = self.render_prompt("user_qa", question=question)

        messages.append(Message(role="user", content=user_content.strip()))
        return messages

    def build_checker_prompt(self, thoughts: str, sample: Dict[str, Any]) -> List[Message]:
        """Build the checker/evaluation prompt for candidate thoughts.

        Uses the checker_template from YAML config, compatible with
        langchain-experimental ToTChain's checker interface.
        """
        question = sample.get("question", "")
        checker_text = self.render_prompt("checker_template", question=question, thoughts=thoughts)
        return [Message(role="user", content=checker_text.strip())]

    def get_tot_chain_kwargs(self) -> Dict[str, Any]:
        """Return kwargs for constructing a langchain-experimental ToTChain."""
        return {"k": self._k, "c": self._depth}
