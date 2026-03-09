"""Data ingestion module — validation, schema filling, version management."""

from src.ingest.validator import validate_sample, validate_dataset
from src.ingest.schema_filler import fill_defaults, fill_dataset
from src.ingest.version_manager import get_next_version, write_changelog, lock_to_benchmark

__all__ = [
    "validate_sample",
    "validate_dataset",
    "fill_defaults",
    "fill_dataset",
    "get_next_version",
    "write_changelog",
    "lock_to_benchmark",
]
