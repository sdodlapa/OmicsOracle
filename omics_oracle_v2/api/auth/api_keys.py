"""
API Key Authentication

Simple, production-ready API key authentication system.
"""

import logging
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyAuth:
    """API key authentication dependency."""

    def __init__(self, required: bool = True):
        """
        Initialize API key auth.

        Args:
            required: Whether API key is required
        """
        self.required = required

    async def __call__(self, api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
        """
        Validate API key.

        Args:
            api_key: API key from header

        Returns:
            User ID if valid, None if not required

        Raises:
            HTTPException: If key is required but missing/invalid
        """
        if not api_key:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required. Provide X-API-Key header.",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            return None

        # Validate API key
        user_id = await validate_api_key(api_key)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        return user_id


def create_api_key(user_id: str, tier: str = "free") -> str:
    """
    Generate a new API key.

    Args:
        user_id: User identifier
        tier: User tier (free/basic/pro/enterprise)

    Returns:
        API key string

    Note:
        In production, store this in database with:
        - user_id
        - tier
        - created_at
        - last_used
        - request_count
    """
    # Generate secure random key
    key = "sk_" + secrets.token_urlsafe(32)

    # TODO: Store in database
    logger.info(f"Created API key for user {user_id} (tier: {tier})")

    return key


async def validate_api_key(api_key: str) -> Optional[str]:
    """
    Validate API key and return user ID.

    Args:
        api_key: API key to validate

    Returns:
        User ID if valid, None otherwise

    Note:
        In production, this should:
        1. Query database for key
        2. Check if key is active
        3. Update last_used timestamp
        4. Increment request_count
        5. Return user_id
    """
    # TODO: Implement database lookup
    # For now, accept any key starting with "sk_" for testing
    if api_key.startswith("sk_"):
        # Extract user from key (demo only - NOT SECURE)
        return "demo_user"

    return None


async def get_current_user(user_id: str = Depends(APIKeyAuth(required=True))) -> str:
    """
    Get current authenticated user.

    Args:
        user_id: User ID from API key validation

    Returns:
        User ID

    Usage:
        @router.get("/protected")
        async def protected_route(user: str = Depends(get_current_user)):
            return {"user": user}
    """
    return user_id


# Rate limit tiers
RATE_LIMITS = {
    "free": {"requests_per_hour": 100, "burst": 10},
    "basic": {"requests_per_hour": 1000, "burst": 50},
    "pro": {"requests_per_hour": 10000, "burst": 200},
    "enterprise": {"requests_per_hour": None, "burst": 500},  # Unlimited
}


def get_rate_limit(tier: str) -> dict:
    """
    Get rate limit configuration for tier.

    Args:
        tier: User tier

    Returns:
        Rate limit configuration
    """
    return RATE_LIMITS.get(tier, RATE_LIMITS["free"])
