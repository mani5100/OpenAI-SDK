"""Structured logging setup for the FastAPI application."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi_9.config import get_config


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation ID if available
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_data["correlation_id"] = record.correlation_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Add custom fields
        if hasattr(record, "custom_fields"):
            log_data.update(record.custom_fields)

        return json.dumps(log_data)


class PlainFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as plain text."""
        correlation_id = getattr(record, "correlation_id", None)
        correlation_str = f"[{correlation_id}] " if correlation_id else ""

        # Basic format
        fmt = f"{correlation_str}%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Add exception traceback if present
        if record.exc_info:
            fmt += "\n%(exc_info)s"

        self._style._fmt = fmt
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    use_json: bool = False,
    correlation_id: Optional[str] = None,
) -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Use JSON formatter if True, plain text if False
        correlation_id: Optional correlation ID for logs

    Returns:
        Configured logger instance
    """
    config = get_config()

    # Create logger
    logger = logging.getLogger("fastapi_9")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Set formatter based on use_json flag
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = PlainFormatter()

    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Store correlation ID in logger for use in log records
    if correlation_id:
        logger.correlation_id = correlation_id

    return logger


def get_logger(name: str, correlation_id: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name
        correlation_id: Optional correlation ID to attach to logs

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    if correlation_id:
        logger.correlation_id = correlation_id

    return logger


class CorrelationIDFilter(logging.Filter):
    """Filter to inject correlation ID into log records."""

    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id or str(uuid.uuid4())

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        record.correlation_id = self.correlation_id
        return True


def generate_correlation_id() -> str:
    """Generate a unique correlation ID."""
    return str(uuid.uuid4())


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    correlation_id: Optional[str] = None,
    **custom_fields,
) -> None:
    """
    Log a message with optional context and custom fields.

    Args:
        logger: Logger instance
        level: Log level (e.g., logging.INFO)
        message: Log message
        correlation_id: Optional correlation ID
        **custom_fields: Additional fields to include in structured logs
    """
    # Create a log record with custom attributes
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        message,
        (),
        None,
    )

    # Add correlation ID
    if correlation_id:
        record.correlation_id = correlation_id

    # Add custom fields
    if custom_fields:
        record.custom_fields = custom_fields

    # Handle the record through all handlers
    logger.handle(record)
