import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo

from app.logging_config import _get_time_converter, configure_logging


def test_configure_logging_writes_warning_logs_to_utf8_rotating_file(tmp_path) -> None:
    log_file = tmp_path / "logs" / "bot.log"

    configure_logging(log_file_path=str(log_file))
    logger = logging.getLogger("tests.logging_config")

    logger.info("정상 흐름")
    logger.warning("주의 필요")
    for handler in logging.getLogger().handlers:
        handler.flush()

    log_text = log_file.read_text(encoding="utf-8")
    assert "주의 필요" in log_text
    assert "정상 흐름" not in log_text
    assert "WARNING [tests.logging_config]" in log_text


def test_configure_logging_uses_rotating_file_handler_settings(tmp_path) -> None:
    log_file = tmp_path / "bot.log"

    configure_logging(
        log_file_path=str(log_file),
        max_bytes=2 * 1024 * 1024,
        backup_count=5,
    )

    file_handlers = [
        handler
        for handler in logging.getLogger().handlers
        if isinstance(handler, RotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    assert file_handlers[0].maxBytes == 2 * 1024 * 1024
    assert file_handlers[0].backupCount == 5


def test_log_time_converter_uses_configured_timezone() -> None:
    timestamp = datetime(2026, 5, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC")).timestamp()

    converted_time = _get_time_converter("Asia/Seoul")(timestamp)

    assert converted_time.tm_year == 2026
    assert converted_time.tm_mon == 5
    assert converted_time.tm_mday == 1
    assert converted_time.tm_hour == 9
