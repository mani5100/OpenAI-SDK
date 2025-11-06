"""
Request ID middleware for tracking requests across the application.

This middleware adds a unique request ID to each incoming request
and makes it available in the logging context.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.logging import clear_request_id, set_request_id

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request.
    
    The request ID can be provided in the X-Request-ID header,
    or a new UUID will be generated. The request ID is stored in
    the logging context for tracking across the request lifecycle.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and add request ID.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            The response with X-Request-ID header
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        request_id = set_request_id(request_id)
        
        # Store request ID in request state for access in route handlers
        request.state.request_id = request_id
        
        # Log the incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_host": request.client.host if request.client else None,
                }
            },
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log the response
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                    }
                },
            )
            
            return response
            
        finally:
            # Clear request ID from context
            clear_request_id()
