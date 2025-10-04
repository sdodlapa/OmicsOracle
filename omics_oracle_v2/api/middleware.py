"""
API Middleware

Custom middleware for logging, error handling, and request processing.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Log request
        start_time = time.time()
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Response: {response.status_code} ({process_time:.3f}s)",
                extra={
                    "status_code": response.status_code,
                    "process_time_seconds": process_time,
                },
            )

            # Add custom headers
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {str(e)} ({process_time:.3f}s)",
                extra={
                    "error": str(e),
                    "process_time_seconds": process_time,
                },
                exc_info=True,
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors consistently."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors."""
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

            # Return JSON error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": "An internal server error occurred",
                    "detail": str(e) if logger.level <= logging.DEBUG else None,
                },
            )
