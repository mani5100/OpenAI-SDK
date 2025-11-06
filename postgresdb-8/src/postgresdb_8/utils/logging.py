"""
Structured logging configuration with request ID tracking.

This module sets up structured logging for the application with JSON formatting,
request ID tracking, and contextual information for better observability.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

# Context variable to store request ID across async contexts
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class RequestIDFilter(logging.Filter):
    """
    Logging filter that adds request ID to log records.
    
    This filter retrieves the request ID from the context variable
    and adds it to each log record for request tracing.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request ID to the log record.

        Args:
            record: The log record to filter

        Returns:
            Always True to allow the record to pass
        """
        record.request_id = request_id_var.get()
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON with consistent fields including
    timestamp, level, message, request ID, and any additional context.
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """
        Add custom fields to the log record.

        Args:
            log_record: The dictionary to be logged as JSON
            record: The original log record
            message_dict: Additional fields from the message
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add log level
        log_record["level"] = record.levelname
        
        # Add logger name
        log_record["logger"] = record.name
        
        # Add request ID if available
        if hasattr(record, "request_id") and record.request_id:
            log_record["request_id"] = record.request_id
        
        # Add source location
        log_record["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add any extra fields from the record
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        The current request ID or None if not set
    """
    return request_id_var.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set the request ID in the context.

    Args:
        request_id: Optional request ID to set. If not provided, generates a new UUID.

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def clear_request_id() -> None:
    """Clear the request ID from the context."""
    request_id_var.set(None)


def setup_logging(
    log_level: str = "INFO",
    json_logs: bool = True,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to use JSON formatting (True) or plain text (False)
        log_file: Optional file path to write logs to (in addition to stdout)
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Set up formatter
    if json_logs:
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    console_handler.setFormatter(formatter)
    
    # Add request ID filter
    console_handler.addFilter(RequestIDFilter())
    
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RequestIDFilter())
        root_logger.addHandler(file_handler)
    
    # Set log level for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    
    root_logger.info(
        "Logging configured",
        extra={
            "extra_fields": {
                "log_level": log_level,
                "json_logs": json_logs,
                "log_file": log_file,
            }
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: The name for the logger (typically __name__)

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to log records.
    
    This adapter can be used to add extra fields to all log messages
    from a specific context (e.g., a service or handler).
    """

    def process(
        self, msg: str, kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Process the log message and kwargs.

        Args:
            msg: The log message
            kwargs: Additional keyword arguments

        Returns:
            Tuple of (message, kwargs) with extra fields added
        """
        # Add extra fields to the record
        extra = kwargs.get("extra", {})
        
        # Merge with adapter's extra fields
        if self.extra:
            extra_fields = extra.get("extra_fields", {})
            extra_fields.update(self.extra)
            extra["extra_fields"] = extra_fields
            kwargs["extra"] = extra
        
        return msg, kwargs


def create_logger_with_context(name: str, **context: Any) -> LoggerAdapter:
    """
    Create a logger with contextual information.

    Args:
        name: The name for the logger
        **context: Additional context to include in all log messages

    Returns:
        A LoggerAdapter with the specified context
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)
