"""Centralized logging for the Avatar API."""
import sys
import os
from loguru import logger


def setup_logger(level: str = "INFO", log_file: str = None):
    """Configure loguru with consistent formatting."""
    logger.remove()  # Remove default handler

    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(sys.stderr, format=fmt, level=level, colorize=True)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logger.add(log_file, format=fmt, level=level, rotation="50 MB", retention="7 days")

    return logger
