"""
Rate limiting middleware for FastAPI.

Enforces tier-based rate limits and adds X-RateLimit-* headers to responses.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from omics_oracle_v2.auth.dependencies import get_optional_user
from omics_oracle_v2.auth.quota import check_rate_limit, get_endpoint_cost
from omics_oracle_v2.core.config import Settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for enforcing rate limits.

    Checks rate limits before processing requests and adds
    X-RateLimit-* headers to all responses.
    """

    def __init__(self, app, settings: Settings | None = None):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            settings: Application settings (optional)
        """
        super().__init__(app)
        self.settings = settings or Settings()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with rate limit headers
        """
        # Skip rate limiting if disabled
        if not self.settings.rate_limit.enabled:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else None

        # Try to get authenticated user
        try:
            user = await get_optional_user(request)
            user_id = user.id if user else None
            tier = user.tier if user else "anonymous"
        except Exception as e:
            # If we can't determine user, treat as anonymous
            logger.debug(f"Could not determine user from request: {e}")
            user_id = None
            tier = "anonymous"

        # Get endpoint cost multiplier
        cost = get_endpoint_cost(request.url.path, request.method)

        # Free endpoints bypass rate limiting
        if cost == 0:
            response = await call_next(request)
            return response

        # Check rate limit (hourly)
        rate_info = await check_rate_limit(
            user_id=user_id,
            ip_address=client_ip,
            tier=tier,
            window="hour",
        )

        # If quota exceeded, return 429
        if rate_info.quota_exceeded:
            logger.warning(
                f"Rate limit exceeded for {'user ' + str(user_id) if user_id else 'IP ' + str(client_ip)}"
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"You have exceeded your quota of {rate_info.limit} requests per hour. "
                    f"Please try again in {rate_info.retry_after} seconds.",
                    "limit": rate_info.limit,
                    "retry_after": rate_info.retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info.reset_at),
                    "Retry-After": str(rate_info.retry_after),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_info.limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_info.remaining - 1)  # -1 for current request
        response.headers["X-RateLimit-Reset"] = str(rate_info.reset_at)

        # Add tier info for debugging (optional)
        if self.settings.debug:
            response.headers["X-RateLimit-Tier"] = tier

        return response


def create_rate_limit_middleware(settings: Settings | None = None) -> RateLimitMiddleware:
    """
    Factory function to create rate limit middleware.

    Args:
        settings: Application settings (optional)

    Returns:
        RateLimitMiddleware instance

    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(RateLimitMiddleware)
    """
    return lambda app: RateLimitMiddleware(app, settings)


# Export public API
__all__ = [
    "RateLimitMiddleware",
    "create_rate_limit_middleware",
]
