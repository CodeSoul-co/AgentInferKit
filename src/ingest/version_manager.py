"""Version manager — data versioning, changelog, and benchmark locking."""

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.config import DATA_DIR


def _get_data_dir(stage: str, task_type: str) -> Path:
    """Get the directory for a given data stage and task type."""
    base = DATA_DIR / stage / task_type
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_next_version(dataset_name: str, task_type: str, stage: str = "processed") -> str:
    """Determine the next version number for a dataset.

    Scans existing files in the directory and increments the minor version.

    Returns:
        Version string like "1.0", "1.1", etc.
    """
    directory = _get_data_dir(stage, task_type)
    pattern = re.compile(rf"^{re.escape(dataset_name)}_v(\d+)\.(\d+)\.jsonl$")
    max_major = 1
    max_minor = -1

    for f in directory.iterdir():
        match = pattern.match(f.name)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            if major > max_major or (major == max_major and minor > max_minor):
                max_major = major
                max_minor = minor

    if max_minor < 0:
        return f"{max_major}.0"
    return f"{max_major}.{max_minor + 1}"


def write_changelog(
    dataset_name: str,
    task_type: str,
    version: str,
    message: str,
    stage: str = "processed",
) -> Path:
    """Append an entry to the CHANGELOG.md for a dataset directory.

    Returns:
        Path to the CHANGELOG.md file.
    """
    directory = _get_data_dir(stage, task_type)
    changelog_path = directory / "CHANGELOG.md"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = f"\n## v{version} ({now})\n- {message}\n"

    if changelog_path.exists():
        existing = changelog_path.read_text(encoding="utf-8")
        # Prepend new entry after any existing header
        if existing.strip():
            content = existing.rstrip() + "\n" + entry
        else:
            content = f"# {dataset_name} Changelog\n" + entry
    else:
        content = f"# {dataset_name} Changelog\n" + entry

    changelog_path.write_text(content, encoding="utf-8")
    return changelog_path


def lock_to_benchmark(
    dataset_path: str,
    dataset_name: str,
    task_type: Optional[str] = None,
) -> str:
    """Copy a processed dataset file to data/benchmark/ for experiment locking.

    Args:
        dataset_path: Path to the processed JSONL file.
        dataset_name: Dataset name (used for directory organization).
        task_type: Optional task_type subdirectory.

    Returns:
        Path to the locked benchmark file.
    """
    src = Path(dataset_path)
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {dataset_path}")

    if task_type:
        dest_dir = DATA_DIR / "benchmark" / task_type
    else:
        dest_dir = DATA_DIR / "benchmark"
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / src.name
    shutil.copy2(str(src), str(dest))
    return str(dest)
