"""
User management API routes.

This module provides endpoints for managing user profiles,
API keys, and usage statistics.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from omics_oracle_v2.auth import crud
from omics_oracle_v2.auth.dependencies import get_current_active_user, get_current_admin_user
from omics_oracle_v2.auth.models import User
from omics_oracle_v2.auth.schemas import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithSecret,
    QuotaInfo,
    UsageStats,
    UserResponse,
    UserUpdate,
)
from omics_oracle_v2.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


# User Profile Management


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current authenticated user's information.

    Returns complete user profile including email, tier, and account status.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return current_user


@router.get("/me/profile", response_model=UsageStats)
async def get_my_usage_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get current user's usage statistics.

    Returns request counts, API key information, and tier details.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Usage statistics
    """
    # Get API keys count
    api_keys = await crud.get_user_api_keys(db, current_user.id)
    active_keys = [k for k in api_keys if k.is_active]

    return {
        "request_count": current_user.request_count,
        "last_request_at": current_user.last_request_at,
        "tier": current_user.tier,
        "api_keys_count": len(api_keys),
        "active_api_keys_count": len(active_keys),
    }


@router.patch("/me/profile")
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Update current user's profile.

    Args:
        update_data: Profile update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    # Update user fields
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name

    if update_data.email is not None:
        # Check if email is already taken
        existing_user = await crud.get_user_by_email(db, update_data.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = update_data.email
        # Mark email as unverified
        current_user.is_verified = False

    await db.commit()
    await db.refresh(current_user)

    return {"message": "Profile updated successfully"}


# API Key Management


@router.get("/me/api-keys", response_model=list[APIKeyResponse])
async def list_my_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """
    List all API keys for current user.

    Returns both active and revoked keys.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of API keys (without secrets)
    """
    return await crud.get_user_api_keys(db, current_user.id)


@router.post("/me/api-keys", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new API key.

    The full API key is only returned once during creation.
    Store it securely - you won't be able to see it again!

    Args:
        key_data: API key creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created API key with secret (only shown once)
    """
    # Create API key
    api_key, plain_key = await crud.create_user_api_key(
        db,
        user_id=current_user.id,
        name=key_data.name,
    )

    # Return API key with secret
    return {
        **APIKeyResponse.model_validate(api_key).model_dump(),
        "key": plain_key,
    }


@router.delete("/me/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke an API key.

    Revoked keys can no longer be used for authentication.

    Args:
        key_id: API key ID to revoke
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException 404: If key not found or doesn't belong to user
    """
    # Get all user's API keys
    api_keys = await crud.get_user_api_keys(db, current_user.id)

    # Find the key
    api_key = next((k for k in api_keys if k.id == key_id), None)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Revoke the key
    await crud.revoke_api_key(db, api_key)


# Admin Endpoints


@router.get("/admin/quota", response_model=QuotaInfo)
async def get_user_quota(
    user_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get quota information for a user (admin only).

    Args:
        user_id: User ID to check
        admin: Current admin user
        db: Database session

    Returns:
        Quota information

    Raises:
        HTTPException 404: If user not found
    """
    user = await crud.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Calculate quota based on tier
    quota_limits = {
        "free": 1000,  # 1K requests per day
        "pro": 10000,  # 10K requests per day
        "enterprise": 1000000,  # 1M requests per day
    }

    limit = quota_limits.get(user.tier, 1000)

    # For now, use simple request count
    # TODO: Implement proper daily quota tracking
    from datetime import datetime, timedelta

    return {
        "tier": user.tier,
        "requests_used": user.request_count,
        "requests_limit": limit,
        "requests_remaining": max(0, limit - user.request_count),
        "reset_at": datetime.utcnow() + timedelta(days=1),
    }


@router.put("/admin/quota")
async def update_user_quota(
    user_id: UUID,
    tier: str,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Update user's subscription tier (admin only).

    Args:
        user_id: User ID to update
        tier: New tier (free, pro, enterprise)
        admin: Current admin user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If invalid tier
    """
    valid_tiers = ["free", "pro", "enterprise"]

    if tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
        )

    user = await crud.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await crud.update_user_tier(db, user, tier)

    return {"message": f"User tier updated to {tier}"}


@router.post("/admin/deactivate/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Deactivate a user account (admin only).

    Args:
        user_id: User ID to deactivate
        admin: Current admin user
        db: Database session

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If trying to deactivate an admin
    """
    user = await crud.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate admin users",
        )

    await crud.deactivate_user(db, user)


@router.post("/admin/activate/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def activate_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Activate a user account (admin only).

    Args:
        user_id: User ID to activate
        admin: Current admin user
        db: Database session

    Raises:
        HTTPException 404: If user not found
    """
    user = await crud.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await crud.activate_user(db, user)
