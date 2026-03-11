"""
LLM-as-Judge evaluation interface.

Provides an extensible framework for using LLMs as evaluators:
- Configurable judge model (any ModelAdapter)
- Customizable judge prompt templates
- Scoring rubrics (1-5 scale, binary, custom)
- Batch judging with concurrent API calls

Usage:
    from src.evaluators.llm_judge import llm_judge_evaluate

    results = await llm_judge_evaluate(
        predictions=predictions,
        judge_config={
            "provider": "deepseek",
            "model": "deepseek-chat",
            "template": "default",
            "rubric": "accuracy",
        }
    )
"""

import asyncio
import re
from typing import Any, Dict, List, Optional

from loguru import logger


# Built-in judge prompt templates
_JUDGE_TEMPLATES: Dict[str, str] = {
    "accuracy": (
        "You are an expert evaluator. Given a question, a reference answer, "
        "and a model's response, rate the model's response on a scale of 1-5:\n"
        "1 = Completely wrong\n"
        "2 = Mostly wrong with minor correct elements\n"
        "3 = Partially correct\n"
        "4 = Mostly correct with minor errors\n"
        "5 = Completely correct\n\n"
        "Question: {question}\n"
        "Reference Answer: {reference}\n"
        "Model Response: {prediction}\n\n"
        "Respond with ONLY a JSON object: {{\"score\": <1-5>, \"reason\": \"<brief explanation>\"}}"
    ),
    "relevance": (
        "You are an expert evaluator. Given a question and a model's response, "
        "rate how relevant the response is to the question on a scale of 1-5:\n"
        "1 = Completely irrelevant\n"
        "2 = Slightly relevant\n"
        "3 = Moderately relevant\n"
        "4 = Highly relevant\n"
        "5 = Perfectly relevant and on-topic\n\n"
        "Question: {question}\n"
        "Model Response: {prediction}\n\n"
        "Respond with ONLY a JSON object: {{\"score\": <1-5>, \"reason\": \"<brief explanation>\"}}"
    ),
    "faithfulness": (
        "You are an expert evaluator. Given retrieved evidence and a model's answer, "
        "rate how faithful the answer is to the evidence (i.e., not hallucinated):\n"
        "1 = Completely hallucinated, no basis in evidence\n"
        "2 = Mostly hallucinated\n"
        "3 = Mixed — some parts grounded, some not\n"
        "4 = Mostly faithful with minor unsupported claims\n"
        "5 = Completely faithful to the evidence\n\n"
        "Evidence:\n{evidence}\n\n"
        "Model Answer: {prediction}\n\n"
        "Respond with ONLY a JSON object: {{\"score\": <1-5>, \"reason\": \"<brief explanation>\"}}"
    ),
    "custom": "{custom_prompt}",
}


def register_judge_template(name: str, template: str) -> None:
    """Register a custom judge prompt template.

    Args:
        name: Template name for later reference.
        template: Prompt string with placeholders like {question}, {prediction}, {reference}.
    """
    _JUDGE_TEMPLATES[name] = template
    logger.info(f"Registered judge template: {name}")


def list_judge_templates() -> List[str]:
    """Return all available judge template names."""
    return sorted(_JUDGE_TEMPLATES.keys())


def _build_judge_prompt(
    template_name: str,
    prediction: Dict[str, Any],
    custom_prompt: Optional[str] = None,
) -> str:
    """Build a judge prompt from a template and prediction dict."""
    template = _JUDGE_TEMPLATES.get(template_name, _JUDGE_TEMPLATES["accuracy"])

    rag_ctx = prediction.get("rag_context", {})
    chunks = rag_ctx.get("retrieved_chunks", [])
    evidence = "\n".join(c.get("text", "") for c in chunks) if chunks else "(no evidence)"

    return template.format(
        question=prediction.get("input_prompt", ""),
        reference=prediction.get("answer", prediction.get("reference_answer", "")),
        prediction=prediction.get("parsed_answer", prediction.get("raw_output", "")),
        evidence=evidence,
        custom_prompt=custom_prompt or "",
    )


def _parse_judge_response(text: str) -> Dict[str, Any]:
    """Parse the judge model's JSON response into score + reason."""
    import json

    # Try direct JSON parse
    try:
        obj = json.loads(text.strip())
        return {
            "score": int(obj.get("score", 0)),
            "reason": str(obj.get("reason", "")),
        }
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: extract score via regex
    m = re.search(r'"score"\s*:\s*(\d)', text)
    score = int(m.group(1)) if m else 0
    m2 = re.search(r'"reason"\s*:\s*"([^"]*)"', text)
    reason = m2.group(1) if m2 else text[:200]
    return {"score": score, "reason": reason}


async def llm_judge_evaluate(
    predictions: List[Dict[str, Any]],
    judge_config: Optional[Dict[str, Any]] = None,
    concurrency: int = 3,
) -> Dict[str, Any]:
    """Run LLM-as-Judge evaluation on predictions.

    Args:
        predictions: List of prediction dicts.
        judge_config: Configuration dict with keys:
            - provider (str): Model provider, e.g. "deepseek"
            - model (str): Model name, e.g. "deepseek-chat"
            - template (str): Judge template name (default: "accuracy")
            - custom_prompt (str, optional): Custom prompt for "custom" template
        concurrency: Max concurrent judge calls.

    Returns:
        Dict with avg_score, scores, total, details.
    """
    judge_config = judge_config or {}
    template_name = judge_config.get("template", "accuracy")
    custom_prompt = judge_config.get("custom_prompt")

    # Load the judge model adapter
    from src.adapters.registry import load_adapter
    from src.api.schemas import Message

    adapter_config = {
        "provider": judge_config.get("provider", "deepseek"),
        "model": judge_config.get("model", "deepseek-chat"),
    }

    try:
        adapter = load_adapter(adapter_config)
    except Exception as e:
        logger.error(f"Failed to load judge adapter: {e}")
        return {
            "metric": "llm_judge",
            "error": str(e),
            "avg_score": 0.0,
            "total": len(predictions),
            "details": [],
        }

    semaphore = asyncio.Semaphore(concurrency)
    results: List[Dict[str, Any]] = [None] * len(predictions)  # type: ignore

    async def _judge_one(idx: int, pred: Dict[str, Any]) -> None:
        async with semaphore:
            prompt_text = _build_judge_prompt(template_name, pred, custom_prompt)
            messages = [Message(role="user", content=prompt_text)]
            try:
                resp = await adapter.generate(messages)
                parsed = _parse_judge_response(resp.content)
                results[idx] = {
                    "sample_id": pred.get("sample_id", ""),
                    "score": parsed["score"],
                    "reason": parsed["reason"],
                    "judge_tokens": resp.prompt_tokens + resp.completion_tokens,
                }
            except Exception as e:
                logger.warning(f"Judge failed for sample {pred.get('sample_id', '?')}: {e}")
                results[idx] = {
                    "sample_id": pred.get("sample_id", ""),
                    "score": 0,
                    "reason": f"Judge error: {e}",
                    "judge_tokens": 0,
                }

    tasks = [_judge_one(i, p) for i, p in enumerate(predictions)]
    await asyncio.gather(*tasks)

    scores = [r["score"] for r in results if r]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    total_tokens = sum(r.get("judge_tokens", 0) for r in results if r)

    return {
        "metric": "llm_judge",
        "template": template_name,
        "judge_model": adapter_config.get("model", ""),
        "avg_score": round(avg_score, 4),
        "max_score": 5,
        "total": len(predictions),
        "judged": len(scores),
        "total_judge_tokens": total_tokens,
        "details": [r for r in results if r],
    }


def llm_judge_sync(predictions: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
    """Synchronous wrapper for llm_judge_evaluate (for registry compatibility)."""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, llm_judge_evaluate(predictions, **kwargs))
            return future.result()
    except RuntimeError:
        return asyncio.run(llm_judge_evaluate(predictions, **kwargs))
