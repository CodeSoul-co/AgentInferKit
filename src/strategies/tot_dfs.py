"""
DFS (Depth-First Search) solver for Tree-of-Thought.

Algorithm from Yao et al. (2023) "Tree of Thoughts" paper:
  - Generate candidates at each node
  - Evaluate each candidate (sure/likely/impossible)
  - Prune "impossible" branches
  - Recurse deeper on promising candidates
  - Backtrack when a branch is exhausted
  - Return the best complete path found

This module mirrors the interface of ``tot.methods.bfs.solve()`` so
ToTStrategy can dispatch to either search method seamlessly.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple


# Threshold: value_outputs_unwrap returns sum of
# {'impossible': 0.001, 'likely': 1, 'sure': 20} * counts
# With n_evaluate_sample=3, "impossible" ~ 0.003, "likely" ~ 3, "sure" ~ 60
_PRUNE_THRESHOLD = 0.1


def _get_samples(task: Any, x: str, y: str, n: int, prompt_sample: str,
                 stop: Optional[str], gpt_fn: Callable) -> List[str]:
    if prompt_sample == "standard":
        prompt = task.standard_prompt_wrap(x, y)
    elif prompt_sample == "cot":
        prompt = task.cot_prompt_wrap(x, y)
    else:
        raise ValueError(f"prompt_sample {prompt_sample} not recognized")
    samples = gpt_fn(prompt, n=n, stop=stop)
    return [y + s for s in samples]


def _get_value(task: Any, x: str, y: str, n_eval: int,
               gpt_fn: Callable, cache: bool = True) -> float:
    value_prompt = task.value_prompt_wrap(x, y)
    if cache and value_prompt in task.value_cache:
        return task.value_cache[value_prompt]
    value_outputs = gpt_fn(value_prompt, n=n_eval, stop=None)
    value = task.value_outputs_unwrap(x, y, value_outputs)
    if cache:
        task.value_cache[value_prompt] = value
    return value


def solve(args: Any, task: Any, idx: int, to_print: bool = True,
          gpt_fn: Optional[Callable] = None) -> Tuple[List[str], Dict]:
    """DFS solver for Tree-of-Thought.

    Args:
        args: Namespace with backend, temperature, n_generate_sample,
              n_evaluate_sample, prompt_sample, max_dfs_nodes (optional).
        task: A Task instance with prompt_wrap and value methods.
        idx: Index into task data (0 for BenchmarkTask).
        to_print: Whether to print debug info.
        gpt_fn: The (already-patched) gpt callable.  When *None* the
                 function falls back to ``tot.models.gpt`` for
                 compatibility, but callers should always pass it.

    Returns:
        (ys, info) — ys is a list of complete candidate paths (best first),
        info contains step-level details and nodes_visited count.
    """
    if gpt_fn is None:
        from functools import partial as _partial
        import tot.models as _m
        gpt_fn = _partial(_m.gpt, model=args.backend, temperature=args.temperature)

    x = task.get_input(idx)
    max_depth = task.steps
    max_nodes = getattr(args, "max_dfs_nodes", 20)

    completed: List[Tuple[float, str]] = []
    infos: List[Dict] = []
    nodes_visited = [0]

    def _dfs(y: str, depth: int) -> None:
        if nodes_visited[0] >= max_nodes:
            return
        nodes_visited[0] += 1

        if depth >= max_depth:
            v = _get_value(task, x, y, args.n_evaluate_sample, gpt_fn)
            completed.append((v, y))
            infos.append({
                "step": depth,
                "type": "leaf",
                "x": x,
                "y": y,
                "value": v,
            })
            return

        candidates = _get_samples(
            task, x, y,
            args.n_generate_sample,
            args.prompt_sample,
            stop=task.stops[depth] if depth < len(task.stops) else None,
            gpt_fn=gpt_fn,
        )

        scored = []
        for c in candidates:
            v = _get_value(task, x, c, args.n_evaluate_sample, gpt_fn)
            scored.append((v, c))
        scored.sort(key=lambda t: t[0], reverse=True)

        infos.append({
            "step": depth,
            "type": "branch",
            "x": x,
            "ys": [c for _, c in scored],
            "values": [v for v, _ in scored],
            "n_pruned": sum(1 for v, _ in scored if v < _PRUNE_THRESHOLD),
        })

        for v, c in scored:
            if nodes_visited[0] >= max_nodes:
                break
            if v < _PRUNE_THRESHOLD:
                continue
            _dfs(c, depth + 1)

    _dfs("", 0)

    completed.sort(key=lambda t: t[0], reverse=True)
    ys = [path for _, path in completed]

    # Fallback: if no complete path, return best partial
    if not ys:
        best_partial = ""
        best_val = -1.0
        for info in infos:
            if info["type"] == "branch":
                for v, c in zip(info["values"], info["ys"]):
                    if v > best_val:
                        best_val = v
                        best_partial = c
        if best_partial:
            ys = [best_partial]

    return ys, {"steps": infos, "nodes_visited": nodes_visited[0]}
