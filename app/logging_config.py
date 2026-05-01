"""Shared logging configuration for the Discord bot."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import (
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_FILE_PATH,
    DEFAULT_LOG_MAX_BYTES,
    DEFAULT_LOG_TIMEZONE,
    get_log_level,
    get_log_timezone,
)


LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CONSOLE_LOG_LEVEL = logging.INFO
FILE_LOG_LEVEL = logging.WARNING
_MANAGED_HANDLER_ATTRIBUTE = "_mapleland_managed_handler"


def configure_logging(
    log_file_path: str = DEFAULT_LOG_FILE_PATH,
    max_bytes: int = DEFAULT_LOG_MAX_BYTES,
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT,
    level_name: str | None = None,
    timezone_name: str | None = None,
) -> None:
    """Configure console and rotating file logging once for the whole app."""
    console_level = _get_logging_level(level_name or get_log_level())
    formatter = _create_formatter(timezone_name or get_log_timezone())

    root_logger = logging.getLogger()
    root_logger.setLevel(min(console_level, FILE_LOG_LEVEL))
    _remove_managed_handlers(root_logger)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    setattr(console_handler, _MANAGED_HANDLER_ATTRIBUTE, True)
    root_logger.addHandler(console_handler)

    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(FILE_LOG_LEVEL)
    file_handler.setFormatter(formatter)
    setattr(file_handler, _MANAGED_HANDLER_ATTRIBUTE, True)
    root_logger.addHandler(file_handler)


def _remove_managed_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if getattr(handler, _MANAGED_HANDLER_ATTRIBUTE, False):
            logger.removeHandler(handler)
            handler.close()


def _get_logging_level(level_name: str) -> int:
    level = getattr(logging, level_name.upper(), None)
    if isinstance(level, int):
        return level
    return CONSOLE_LOG_LEVEL


def _create_formatter(timezone_name: str) -> logging.Formatter:
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    formatter.converter = _get_time_converter(timezone_name)
    return formatter


def _get_time_converter(timezone_name: str):
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        timezone = ZoneInfo(DEFAULT_LOG_TIMEZONE)

    def converter(timestamp: float) -> time.struct_time:
        return datetime.fromtimestamp(timestamp, timezone).timetuple()

    return converter
