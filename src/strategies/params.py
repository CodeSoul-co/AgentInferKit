"""
Per-strategy configurable parameter definitions.

Used by the GET /strategies API endpoint to tell the frontend which
parameters are available for each strategy, their types, defaults,
constraints, and human-readable descriptions.
"""

from typing import Any, Dict, List

# Each param is a dict with:
#   name, type (float|int|str|bool), default, description,
#   and optional: min, max, options (for enum/select)

STRATEGY_PARAMS: Dict[str, List[Dict[str, Any]]] = {
    "direct": [
        {
            "name": "temperature",
            "type": "float",
            "default": 0.0,
            "min": 0.0,
            "max": 2.0,
            "description": "Sampling temperature. 0 = deterministic.",
        },
        {
            "name": "max_tokens",
            "type": "int",
            "default": 1024,
            "min": 64,
            "max": 16384,
            "description": "Maximum output tokens.",
        },
    ],
    "cot": [
        {
            "name": "reasoning_depth",
            "type": "str",
            "default": "normal",
            "options": ["normal", "deep"],
            "description": "Reasoning depth. 'normal' = standard CoT, 'deep' = extended reasoning (formerly long_cot).",
        },
        {
            "name": "temperature",
            "type": "float",
            "default": 0.0,
            "min": 0.0,
            "max": 2.0,
            "description": "Sampling temperature. 0 = deterministic.",
        },
        {
            "name": "max_tokens",
            "type": "int",
            "default": 2048,
            "min": 64,
            "max": 16384,
            "description": "Maximum output tokens.",
        },
    ],
    "long_cot": [
        {
            "name": "temperature",
            "type": "float",
            "default": 0.0,
            "min": 0.0,
            "max": 2.0,
            "description": "Sampling temperature. 0 = deterministic.",
        },
        {
            "name": "max_tokens",
            "type": "int",
            "default": 2048,
            "min": 64,
            "max": 16384,
            "description": "Maximum output tokens.",
        },
    ],
    "self_consistency": [
        {
            "name": "num_samples",
            "type": "int",
            "default": 5,
            "min": 2,
            "max": 30,
            "description": "Number of diverse CoT paths to sample for majority voting.",
        },
        {
            "name": "temperature",
            "type": "float",
            "default": 0.7,
            "min": 0.0,
            "max": 2.0,
            "description": "Sampling temperature. Higher = more diverse paths.",
        },
        {
            "name": "max_tokens",
            "type": "int",
            "default": 2048,
            "min": 64,
            "max": 16384,
            "description": "Maximum output tokens per path.",
        },
    ],
    "self_refine": [
        {
            "name": "max_rounds",
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 10,
            "description": "Maximum critique-and-refine iterations.",
        },
        {
            "name": "temperature",
            "type": "float",
            "default": 0.0,
            "min": 0.0,
            "max": 2.0,
            "description": "Sampling temperature.",
        },
        {
            "name": "max_tokens",
            "type": "int",
            "default": 2048,
            "min": 64,
            "max": 16384,
            "description": "Maximum output tokens per round.",
        },
    ],
    "tot": [
        {
            "name": "search_method",
            "type": "str",
            "default": "bfs",
            "options": ["bfs", "dfs"],
            "description": "Tree search method. BFS = breadth-first (good for MCQ), DFS = depth-first (good for open QA).",
        },
        {
            "name": "k",
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 10,
            "description": "Candidates generated per step (BFS width / DFS branching factor).",
        },
        {
            "name": "depth",
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 10,
            "description": "Maximum search depth (BFS layers / DFS recursion limit).",
        },
        {
            "name": "n_evaluate_sample",
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 10,
            "description": "Number of LLM calls per evaluation (higher = more reliable scoring).",
        },
        {
            "name": "max_dfs_nodes",
            "type": "int",
            "default": 20,
            "min": 5,
            "max": 100,
            "description": "Maximum nodes visited in DFS before stopping (prevents runaway). Only used when search_method=dfs.",
        },
        {
            "name": "temperature",
            "type": "float",
            "default": 0.7,
            "min": 0.0,
            "max": 2.0,
            "description": "Sampling temperature for candidate generation.",
        },
        {
            "name": "max_tokens",
            "type": "int",
            "default": 2048,
            "min": 64,
            "max": 16384,
            "description": "Maximum output tokens per LLM call.",
        },
    ],
    "react": [
        {
            "name": "max_steps",
            "type": "int",
            "default": 10,
            "min": 1,
            "max": 30,
            "description": "Maximum Thought-Action-Observation loop iterations.",
        },
        {
            "name": "temperature",
            "type": "float",
            "default": 0.0,
            "min": 0.0,
            "max": 2.0,
            "description": "Sampling temperature.",
        },
        {
            "name": "max_tokens",
            "type": "int",
            "default": 2048,
            "min": 64,
            "max": 16384,
            "description": "Maximum output tokens per step.",
        },
    ],
}


def get_strategy_params(strategy_name: str) -> List[Dict[str, Any]]:
    """Return configurable parameters for a given strategy."""
    return STRATEGY_PARAMS.get(strategy_name, [])


def get_all_strategy_params() -> Dict[str, List[Dict[str, Any]]]:
    """Return configurable parameters for all strategies."""
    return STRATEGY_PARAMS
