# utils/logger.py
# ─────────────────────────────────────────────────────────────────
# Structured logger using Rich for coloured terminal output.
# Every module gets its own named logger via get_logger().
# ─────────────────────────────────────────────────────────────────
import logging
import sys
from functools import lru_cache

from rich.console import Console
from rich.logging import RichHandler

from config import get_settings

_console = Console(stderr=True)


def _build_handler() -> RichHandler:
    return RichHandler(
        console=_console,
        show_time=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
        markup=True,
    )


@lru_cache(maxsize=None)
def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  Call once per module:

        log = get_logger(__name__)
        log.info("Planning graph started")
    """
    settings = get_settings()
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.addHandler(_build_handler())
        logger.setLevel(getattr(logging, settings.log_level))
        logger.propagate = False

    return logger