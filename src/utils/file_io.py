import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import orjson
import yaml


def read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    """Read a JSONL file and return a list of dicts."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(orjson.loads(line))
    return records


def write_jsonl(
    path: str | Path, records: List[Dict[str, Any]], mode: str = "w"
) -> None:
    """Write a list of dicts to a JSONL file.

    Args:
        path: Target file path.
        records: List of dicts to write.
        mode: 'w' to overwrite, 'a' to append.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode, encoding="utf-8") as f:
        for record in records:
            f.write(orjson.dumps(record).decode("utf-8") + "\n")


def read_yaml(path: str | Path) -> Dict[str, Any]:
    """Read a YAML file and return a dict."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _resolve_env_vars(value: str) -> str:
    """Replace ${ENV_VAR} placeholders with environment variable values."""
    pattern = re.compile(r"\$\{(\w+)\}")

    def _replace(match: re.Match) -> str:
        env_key = match.group(1)
        env_val = os.environ.get(env_key, "")
        return env_val

    return pattern.sub(_replace, value)


def _walk_and_resolve(obj: Any) -> Any:
    """Recursively resolve environment variable placeholders in a dict."""
    if isinstance(obj, dict):
        return {k: _walk_and_resolve(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_resolve(item) for item in obj]
    if isinstance(obj, str):
        return _resolve_env_vars(obj)
    return obj


def load_config_yaml(path: str | Path) -> Dict[str, Any]:
    """Read a YAML config file with ${ENV_VAR} placeholder support."""
    raw = read_yaml(path)
    return _walk_and_resolve(raw)
