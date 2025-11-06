"""
Global error handler middleware for the FastAPI application.

This module provides centralized error handling to ensure consistent
error responses across all API endpoints.
"""

import logging
import traceback
from typing import Callable, Union

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.errors import (
    ChatbotAPIError,
    DatabaseError,
    OpenAIAPIUnavailableError,
    OpenAIRateLimitError,
    OpenAIServiceError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and handle all exceptions in a consistent manner.
    
    This middleware intercepts exceptions raised during request processing
    and converts them into appropriate JSON error responses.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Union[Response, JSONResponse]:
        """
        Process the request and handle any exceptions.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            The response from the route handler or an error response
        """
        try:
            response = await call_next(request)
            return response

        except ChatbotAPIError as exc:
            # Handle our custom application errors
            return await self._handle_chatbot_error(request, exc)

        except PydanticValidationError as exc:
            # Handle Pydantic validation errors
            return await self._handle_validation_error(request, exc)

        except (
            RateLimitError,
            APIConnectionError,
            AuthenticationError,
            BadRequestError,
            ConflictError,
            InternalServerError,
            NotFoundError,
            PermissionDeniedError,
            UnprocessableEntityError,
            APIError,
        ) as exc:
            # Handle OpenAI API errors
            return await self._handle_openai_error(request, exc)

        except SQLAlchemyError as exc:
            # Handle database errors
            return await self._handle_database_error(request, exc)

        except Exception as exc:
            # Handle unexpected errors
            return await self._handle_unexpected_error(request, exc)

    async def _handle_chatbot_error(
        self, request: Request, exc: ChatbotAPIError
    ) -> JSONResponse:
        """
        Handle custom ChatbotAPIError exceptions.

        Args:
            request: The incoming HTTP request
            exc: The chatbot API error

        Returns:
            JSON error response
        """
        logger.error(
            f"ChatbotAPIError: {exc.message}",
            extra={
                "error_type": type(exc).__name__,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": type(exc).__name__,
                    "message": exc.message,
                    "details": exc.details,
                },
                "path": str(request.url.path),
                "method": request.method,
            },
        )

    async def _handle_validation_error(
        self, request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors.

        Args:
            request: The incoming HTTP request
            exc: The Pydantic validation error

        Returns:
            JSON error response with validation details
        """
        errors = exc.errors()
        logger.warning(
            f"Validation error: {len(errors)} validation errors",
            extra={
                "errors": errors,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "ValidationError",
                    "message": "Request validation failed",
                    "details": {"validation_errors": errors},
                },
                "path": str(request.url.path),
                "method": request.method,
            },
        )

    async def _handle_openai_error(
        self, request: Request, exc: APIError
    ) -> JSONResponse:
        """
        Handle OpenAI API errors.

        Args:
            request: The incoming HTTP request
            exc: The OpenAI API error

        Returns:
            JSON error response
        """
        # Determine status code and error message
        if isinstance(exc, RateLimitError):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
            message = "OpenAI API rate limit exceeded. Please try again later."
            error_type = "OpenAIRateLimitError"
        elif isinstance(exc, APIConnectionError):
            status_code = status.HTTP_502_BAD_GATEWAY
            message = "Failed to connect to OpenAI API. Please try again later."
            error_type = "OpenAIConnectionError"
        elif isinstance(exc, AuthenticationError):
            status_code = status.HTTP_502_BAD_GATEWAY
            message = "OpenAI API authentication failed. Please contact support."
            error_type = "OpenAIAuthenticationError"
        elif isinstance(exc, BadRequestError):
            status_code = status.HTTP_400_BAD_REQUEST
            message = f"Invalid request to OpenAI API: {str(exc)}"
            error_type = "OpenAIBadRequestError"
        else:
            status_code = status.HTTP_502_BAD_GATEWAY
            message = f"OpenAI API error: {str(exc)}"
            error_type = "OpenAIServiceError"

        logger.error(
            f"OpenAI API error: {message}",
            extra={
                "error_type": error_type,
                "status_code": status_code,
                "original_error": str(exc),
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "type": error_type,
                    "message": message,
                    "details": {"original_error": str(exc)},
                },
                "path": str(request.url.path),
                "method": request.method,
            },
        )

    async def _handle_database_error(
        self, request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """
        Handle SQLAlchemy database errors.

        Args:
            request: The incoming HTTP request
            exc: The SQLAlchemy error

        Returns:
            JSON error response
        """
        logger.error(
            f"Database error: {str(exc)}",
            extra={
                "error_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc(),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "DatabaseError",
                    "message": "A database error occurred. Please try again later.",
                    "details": {"error_type": type(exc).__name__},
                },
                "path": str(request.url.path),
                "method": request.method,
            },
        )

    async def _handle_unexpected_error(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle unexpected errors.

        Args:
            request: The incoming HTTP request
            exc: The unexpected exception

        Returns:
            JSON error response
        """
        logger.critical(
            f"Unexpected error: {str(exc)}",
            extra={
                "error_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc(),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": "An unexpected error occurred. Please try again later.",
                    "details": {"error_type": type(exc).__name__},
                },
                "path": str(request.url.path),
                "method": request.method,
            },
        )


def setup_error_handlers(app) -> None:
    """
    Set up error handlers for the FastAPI application.
    
    This function can be used to register additional exception handlers
    if needed beyond the middleware.

    Args:
        app: The FastAPI application instance
    """
    # Add the error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)
    
    logger.info("Error handler middleware configured")
