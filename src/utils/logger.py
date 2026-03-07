import sys
from pathlib import Path

from loguru import logger

from src.config import OUTPUTS_LOGS_DIR


def setup_logger(level: str = "INFO") -> None:
    """Configure loguru logger with console and file sinks."""
    logger.remove()

    # Console sink
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
    )

    # File sink
    log_path = OUTPUTS_LOGS_DIR / "app.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_path),
        level=level,
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
               "{name}:{function}:{line} | {message}",
    )
