"""Professional logging configuration for the agent pipeline."""

import logging
import sys
from typing import Any, Dict

from loguru import logger


def setup_logging(level: str = "INFO", json_format: bool = False):
    """
    Configures logging using loguru.
    If json_format is True, it will output logs as JSON for production parsing.
    """
    # Remove default handler
    logger.remove()

    # Configure console format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    if json_format:
        logger.add(sys.stdout, format="{message}", serialize=True, level=level)
    else:
        logger.add(sys.stdout, format=log_format, level=level, colorize=True)

    # Intercept standard logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Silence chatty libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.ERROR)


def get_logger(name: str):
    """Helper to get a named logger (compatible with loguru)."""
    return logger.bind(name=name)
