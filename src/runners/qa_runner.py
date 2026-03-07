import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from src.adapters.base import BaseModelAdapter
from src.api.schemas import Message
from src.runners.base import BaseRunner
from src.strategies.base import BaseStrategy
from src.rag.retriever import retrieve as rag_retrieve


class QARunner(BaseRunner):
    """Runner for text_qa tasks.

    Handles: build prompt -> (optional RAG) -> call model -> parse output -> prediction dict.
    """

    def __init__(
        self,
        adapter: BaseModelAdapter,
        strategy: BaseStrategy,
        rag_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._adapter = adapter
        self._strategy = strategy
        self._rag_config = rag_config or {}

    async def run_single(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Run inference on a single QA sample."""
        start = time.perf_counter()

        # Build prompt via strategy
        messages = self._strategy.build_prompt(sample)

        # Optional RAG context injection
        rag_context = {"mode": None, "retrieved_chunks": []}
        if self._rag_config.get("enabled"):
            query = sample.get("question", "")
            kb_name = self._rag_config.get("kb_name", "")
            top_k = self._rag_config.get("top_k", 3)
            chunks = rag_retrieve(query, kb_name, top_k=top_k)
            rag_context = {
                "mode": self._rag_config.get("mode", "retrieved"),
                "retrieved_chunks": [
                    {"chunk_id": c["chunk_id"], "score": c["score"], "text": c["text"]}
                    for c in chunks
                ],
            }
            # Inject retrieved context into the last user message
            context_text = "\n\n".join(c["text"] for c in chunks)
            if messages and messages[-1].role == "user":
                messages[-1] = Message(
                    role="user",
                    content=f"Reference:\n{context_text}\n\n{messages[-1].content}",
                )

        # Call model
        result = await self._adapter.generate(messages)

        # Parse output
        parsed = self._strategy.parse_output(result.content, sample)

        # Build prediction dict (SCHEMA.md section 5)
        prediction = {
            "sample_id": sample.get("sample_id", ""),
            "experiment_id": "",
            "model": "",
            "strategy": "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_prompt": "\n".join(f"[{m.role}] {m.content}" for m in messages),
            "raw_output": result.content,
            "parsed_answer": parsed["parsed_answer"],
            "reasoning_trace": parsed.get("reasoning_trace"),
            "rag_context": rag_context,
            "usage": {
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.prompt_tokens + result.completion_tokens,
                "latency_ms": result.latency_ms,
            },
            "error": result.error,
        }
        return prediction

    async def run_batch(
        self,
        samples: List[Dict[str, Any]],
        experiment_id: str,
        on_progress: Optional[Callable[[int, int, int], None]] = None,
    ) -> str:
        """Delegate to BatchRunner for batch execution."""
        raise NotImplementedError(
            "QARunner.run_batch() should be called via BatchRunner."
        )
