"""
Structured logging configuration.

Configures Python's standard logging with either JSON (structured) or
human-readable text format. JSON logs are optimised for ingestion by
log aggregators (Loki, ELK, Datadog, CloudWatch, etc.).

Usage::

    from app.utils.logging import setup_logging, get_logger

    setup_logging(level="INFO", log_format="json")
    logger = get_logger(__name__)
    logger.info("Request received", extra={"request_id": "abc123"})
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from typing import Any

from pythonjsonlogger.json import JsonFormatter


class _JsonFormatter(JsonFormatter):  # type: ignore[misc]
    """
    Structured log formatter that serialises log records as JSON using python-json-logger.
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Build custom structured fields
        log_record["timestamp"] = datetime.now(UTC).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["message"] = record.getMessage()
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Extract extra fields
        standard_fields = {
            "timestamp",
            "level",
            "logger",
            "message",
            "module",
            "function",
            "line",
            "exception",
        }
        extra_keys = {key: value for key, value in log_record.items() if key not in standard_fields}

        # Clear extra keys from the root log_record
        for key in list(extra_keys.keys()):
            del log_record[key]

        # Put them under "extra" nested key
        if extra_keys:
            log_record["extra"] = extra_keys

        # Format exception if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


class _TextFormatter(logging.Formatter):
    """Human-readable log formatter for local development."""

    _COLOURS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        colour = self._COLOURS.get(record.levelname, "")
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        level = f"{colour}{record.levelname:<8}{self._RESET}"
        return f"{timestamp} | {level} | {record.name} | {record.getMessage()}"


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_file: str | None = None,
) -> None:
    """
    Configure the root logger for the application.

    Should be called exactly once during application startup (see events.py).

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — "json" for structured logs, "text" for human-readable.
        log_file: Optional file path to also write logs to disk.
    """
    formatter: logging.Formatter = _JsonFormatter() if log_format == "json" else _TextFormatter()

    handlers: list[logging.Handler] = [
        _build_stream_handler(formatter, stream=sys.stdout),
    ]

    if log_file:
        handlers.append(_build_file_handler(formatter, log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=handlers,
        force=True,  # Override any previously configured handlers
    )

    # Silence noisy third-party loggers
    for noisy_logger in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def _build_stream_handler(
    formatter: logging.Formatter,
    stream: Any = sys.stdout,
) -> logging.StreamHandler:  # type: ignore[type-arg]
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    return handler


def _build_file_handler(
    formatter: logging.Formatter,
    log_file: str,
) -> logging.FileHandler:
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(formatter)
    return handler


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger instance.

    Convenience wrapper around ``logging.getLogger`` so that callers
    don't need to import the ``logging`` module directly.

    Args:
        name: Logger name (typically ``__name__``).

    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)
