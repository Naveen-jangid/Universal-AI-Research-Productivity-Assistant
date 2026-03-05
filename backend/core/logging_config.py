"""Structured logging configuration using Python's standard logging module."""

import logging
import logging.handlers
import sys
from pathlib import Path

from backend.core.config import settings


def setup_logging() -> None:
    """Configure root logger with console + rotating file handlers."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Ensure log directory exists
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(log_level)

    # Rotating file handler (10 MB, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_path), maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Quieten noisy third-party loggers
    for noisy in ("httpx", "httpcore", "openai", "faiss"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
