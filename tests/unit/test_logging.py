"""
Unit tests for structured logging and custom formatters.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from app.utils.logging import _JsonFormatter, _TextFormatter, get_logger, setup_logging


def test_json_formatter() -> None:
    """_JsonFormatter must format LogRecord to valid JSON with correct fields."""
    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Test message with %s",
        args=("arg1",),
        exc_info=None,
    )
    # Mock some extra attributes
    record.__dict__["custom_field"] = "custom_value"

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Test message with arg1"
    assert parsed["line"] == 42
    assert parsed["extra"]["custom_field"] == "custom_value"

    # Verify that unicode characters are formatted directly in UTF-8 instead of being escaped
    record_unicode = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="← Test arrow →",
        args=(),
        exc_info=None,
    )
    formatted_unicode = formatter.format(record_unicode)
    assert "←" in formatted_unicode
    assert "→" in formatted_unicode
    assert "\\u2190" not in formatted_unicode
    assert "\\u2192" not in formatted_unicode


def test_json_formatter_exception() -> None:
    """_JsonFormatter must include exception trace when present."""
    formatter = _JsonFormatter()
    try:
        raise ValueError("test exception")
    except ValueError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test_file.py",
        lineno=50,
        msg="Error occurred",
        args=(),
        exc_info=exc_info,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert "exception" in parsed
    assert "ValueError: test exception" in parsed["exception"]


def test_text_formatter() -> None:
    """_TextFormatter must output correct human-readable format."""
    formatter = _TextFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Hello info",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "INFO" in formatted
    assert "test_logger" in formatted
    assert "Hello info" in formatted


def test_setup_logging(tmp_path: Path) -> None:
    """setup_logging must configure standard logging successfully."""
    # JSON format to console
    setup_logging(level="DEBUG", log_format="json")

    # Text format to file
    log_file = tmp_path / "test.log"
    setup_logging(level="WARNING", log_format="text", log_file=str(log_file))
    assert log_file.exists()


def test_get_logger() -> None:
    """get_logger must return a logger instance."""
    logger = get_logger("my_named_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "my_named_logger"
