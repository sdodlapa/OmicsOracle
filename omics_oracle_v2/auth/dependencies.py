"""
FastAPI dependencies for authentication and authorization.

This module provides dependency functions for protecting API endpoints.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from omics_oracle_v2.auth import crud
from omics_oracle_v2.auth.models import User
from omics_oracle_v2.auth.security import decode_access_token, verify_api_key
from omics_oracle_v2.database import get_db

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User if token is valid, None otherwise

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    try:
        from uuid import UUID

        user = await crud.get_user_by_id(db, UUID(user_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_from_api_key(
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user from API key.

    Args:
        api_key: API key from header
        db: Database session

    Returns:
        User if API key is valid, None otherwise

    Raises:
        HTTPException: If API key is invalid or revoked
    """
    if not api_key:
        return None

    # Extract prefix from API key
    if not api_key.startswith("omics_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    prefix = api_key[:12]

    # Get API key from database
    db_api_key = await crud.get_api_key_by_prefix(db, prefix)

    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Check if API key is revoked
    if not db_api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked",
        )

    # Verify API key hash
    if not verify_api_key(api_key, db_api_key.key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Update API key usage
    await crud.update_api_key_usage(db, db_api_key)

    # Get user
    user = await crud.get_user_by_id(db, db_api_key.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_user(
    user_from_token: Optional[User] = Depends(get_current_user_from_token),
    user_from_api_key: Optional[User] = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from either JWT token or API key.

    This dependency tries both authentication methods and returns the user
    if either is valid. Use this for endpoints that support both auth methods.

    Args:
        user_from_token: User from JWT token (if provided)
        user_from_api_key: User from API key (if provided)
        db: Database session

    Returns:
        Authenticated user

    Raises:
        HTTPException: If neither authentication method succeeds

    Example:
        ```python
        @router.get("/protected")
        async def protected_endpoint(
            current_user: User = Depends(get_current_user)
        ):
            return {"user": current_user.email}
        ```
    """
    user = user_from_token or user_from_api_key

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update user request count
    await crud.increment_user_request_count(db, user)

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (account not deactivated).

    Args:
        current_user: Current authenticated user

    Returns:
        Active user

    Raises:
        HTTPException: If user is not active

    Example:
        ```python
        @router.get("/users/me")
        async def read_users_me(
            current_user: User = Depends(get_current_active_user)
        ):
            return current_user
        ```
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current admin user.

    Args:
        current_user: Current active user

    Returns:
        Admin user

    Raises:
        HTTPException: If user is not an admin

    Example:
        ```python
        @router.get("/admin/users")
        async def list_all_users(
            admin: User = Depends(get_current_admin_user)
        ):
            # Only admins can access this
            return {"users": [...]}
        ```
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return current_user


async def require_api_key(
    user: Optional[User] = Depends(get_current_user_from_api_key),
) -> User:
    """
    Require API key authentication (no JWT tokens allowed).

    Use this for endpoints that should only accept API key auth.

    Args:
        user: User from API key

    Returns:
        Authenticated user

    Raises:
        HTTPException: If no valid API key is provided

    Example:
        ```python
        @router.post("/batch/submit")
        async def submit_batch(
            current_user: User = Depends(require_api_key)
        ):
            # Only API key auth allowed
            return {"status": "submitted"}
        ```
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return user


async def get_optional_user(
    user_from_token: Optional[User] = Depends(get_current_user_from_token),
    user_from_api_key: Optional[User] = Depends(get_current_user_from_api_key),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Use this for endpoints that have optional authentication
    (e.g., public endpoints with rate limit benefits for authenticated users).

    Args:
        user_from_token: User from JWT token (if provided)
        user_from_api_key: User from API key (if provided)

    Returns:
        User if authenticated, None otherwise

    Example:
        ```python
        @router.get("/public/data")
        async def get_public_data(
            current_user: Optional[User] = Depends(get_optional_user)
        ):
            # Higher rate limits for authenticated users
            if current_user:
                return {"data": "full", "user": current_user.email}
            return {"data": "limited"}
        ```
    """
    return user_from_token or user_from_api_key
