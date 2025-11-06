"""
Custom exception classes for the chatbot API.

This module defines custom exceptions for domain-specific error handling,
making it easier to distinguish between different types of errors and
provide appropriate HTTP status codes and error messages.
"""

from typing import Any, Dict, Optional


class ChatbotAPIError(Exception):
    """Base exception class for all chatbot API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the base API error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code to return
            details: Additional error details for debugging
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ThreadNotFoundError(ChatbotAPIError):
    """Raised when a requested thread does not exist."""

    def __init__(self, thread_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize thread not found error.

        Args:
            thread_id: The ID of the thread that was not found
            details: Additional error details
        """
        message = f"Thread not found: {thread_id}"
        super().__init__(message, status_code=404, details=details)
        self.thread_id = thread_id


class MessageNotFoundError(ChatbotAPIError):
    """Raised when a requested message does not exist."""

    def __init__(self, message_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize message not found error.

        Args:
            message_id: The ID of the message that was not found
            details: Additional error details
        """
        message = f"Message not found: {message_id}"
        super().__init__(message, status_code=404, details=details)
        self.message_id = message_id


class OpenAIServiceError(ChatbotAPIError):
    """Raised when OpenAI API encounters an error."""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize OpenAI service error.

        Args:
            message: Human-readable error message
            original_error: The original exception from OpenAI SDK
            details: Additional error details
        """
        error_details = details or {}
        if original_error:
            error_details["original_error"] = str(original_error)
            error_details["error_type"] = type(original_error).__name__

        super().__init__(message, status_code=502, details=error_details)
        self.original_error = original_error


class OpenAIRateLimitError(OpenAIServiceError):
    """Raised when OpenAI API rate limit is exceeded."""

    def __init__(
        self,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize rate limit error.

        Args:
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        message = "OpenAI API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"

        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after

        super().__init__(message, details=error_details)
        self.retry_after = retry_after


class OpenAIAPIUnavailableError(OpenAIServiceError):
    """Raised when OpenAI API is unavailable or times out."""

    def __init__(
        self,
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize API unavailable error.

        Args:
            original_error: The original exception
            details: Additional error details
        """
        message = "OpenAI API is currently unavailable. Please try again later."
        super().__init__(message, original_error, details)


class DatabaseError(ChatbotAPIError):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize database error.

        Args:
            message: Human-readable error message
            original_error: The original database exception
            details: Additional error details
        """
        error_details = details or {}
        if original_error:
            error_details["original_error"] = str(original_error)
            error_details["error_type"] = type(original_error).__name__

        super().__init__(message, status_code=500, details=error_details)
        self.original_error = original_error


class ValidationError(ChatbotAPIError):
    """Raised when request validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error.

        Args:
            message: Human-readable error message
            details: Additional validation error details (field errors, etc.)
        """
        super().__init__(message, status_code=422, details=details)


class ConfigurationError(ChatbotAPIError):
    """Raised when application configuration is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration error.

        Args:
            message: Human-readable error message
            details: Additional configuration error details
        """
        super().__init__(message, status_code=500, details=details)
