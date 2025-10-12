"""
Quota management API endpoints.

Provides endpoints for users to view their quota usage and
for admins to manage user quotas.
"""

import logging
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from omics_oracle_v2.auth import crud
from omics_oracle_v2.auth.dependencies import get_current_active_user, get_current_admin_user
from omics_oracle_v2.auth.quota import check_rate_limit
from omics_oracle_v2.auth.schemas import UserResponse
from omics_oracle_v2.cache import memory_delete, redis_delete
from omics_oracle_v2.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quotas", tags=["Quotas"])


# Pydantic schemas
class QuotaUsageResponse(BaseModel):
    """Current quota usage information."""

    user_id: UUID
    tier: str

    # Hourly quota
    hourly_limit: int
    hourly_used: int
    hourly_remaining: int
    hourly_reset_at: int

    # Daily quota
    daily_limit: int
    daily_used: int
    daily_remaining: int
    daily_reset_at: int

    # Status
    quota_exceeded: bool

    # Metadata
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class QuotaUpdateRequest(BaseModel):
    """Request to update user quota (admin only)."""

    tier: str = Field(..., description="New tier (free, pro, enterprise)")


class QuotaResetRequest(BaseModel):
    """Request to reset user quota counters (admin only)."""

    window: str = Field(default="hour", description="Window to reset (hour, day, or all)")


class UsageHistoryItem(BaseModel):
    """Historical usage data point."""

    date: datetime
    requests: int
    tier: str


class UsageHistoryResponse(BaseModel):
    """Usage history over time."""

    user_id: UUID
    period_start: datetime
    period_end: datetime
    total_requests: int
    average_daily_requests: float
    peak_daily_requests: int
    current_tier: str
    history: List[UsageHistoryItem] = []


# User quota endpoints
@router.get("/me", response_model=QuotaUsageResponse)
async def get_my_quota(
    current_user: UserResponse = Depends(get_current_active_user),
) -> QuotaUsageResponse:
    """
    Get current user's quota usage.

    Returns quota limits, current usage, and reset times for both
    hourly and daily windows.
    """
    # Check hourly usage
    hourly_info = await check_rate_limit(
        user_id=current_user.id,
        ip_address=None,
        tier=current_user.tier,
        window="hour",
    )

    # Check daily usage
    daily_info = await check_rate_limit(
        user_id=current_user.id,
        ip_address=None,
        tier=current_user.tier,
        window="day",
    )

    return QuotaUsageResponse(
        user_id=current_user.id,
        tier=current_user.tier,
        hourly_limit=hourly_info.limit,
        hourly_used=hourly_info.limit - hourly_info.remaining,
        hourly_remaining=hourly_info.remaining,
        hourly_reset_at=hourly_info.reset_at,
        daily_limit=daily_info.limit,
        daily_used=daily_info.limit - daily_info.remaining,
        daily_remaining=daily_info.remaining,
        daily_reset_at=daily_info.reset_at,
        quota_exceeded=hourly_info.quota_exceeded or daily_info.quota_exceeded,
    )


@router.get("/me/history", response_model=UsageHistoryResponse)
async def get_my_usage_history(
    days: int = 30,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UsageHistoryResponse:
    """
    Get usage history for current user.

    Args:
        days: Number of days of history to retrieve (default: 30, max: 90)

    Returns:
        Usage history with daily breakdowns
    """
    # Validate days parameter
    if days < 1 or days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 90",
        )

    # Get user from database for request_count
    user = await crud.get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Calculate period
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    # Note: This is a simplified implementation
    # In production, you'd want to store daily request counts in the database
    # For now, we'll use the total request_count as a proxy
    total_requests = user.request_count
    average_daily = total_requests / max(days, 1)

    # Build history (placeholder - would come from DB in production)
    history = []
    # In a real implementation, you'd query a usage_history table

    return UsageHistoryResponse(
        user_id=current_user.id,
        period_start=period_start,
        period_end=period_end,
        total_requests=total_requests,
        average_daily_requests=round(average_daily, 2),
        peak_daily_requests=int(average_daily * 1.5),  # Estimated
        current_tier=current_user.tier,
        history=history,
    )


# Admin quota endpoints
@router.get("/{user_id}", response_model=QuotaUsageResponse)
async def get_user_quota(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> QuotaUsageResponse:
    """
    Get quota usage for any user (admin only).

    Args:
        user_id: User ID to check

    Returns:
        User's quota usage information
    """
    # Get user from database
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Check hourly usage
    hourly_info = await check_rate_limit(
        user_id=user.id,
        ip_address=None,
        tier=user.tier,
        window="hour",
    )

    # Check daily usage
    daily_info = await check_rate_limit(
        user_id=user.id,
        ip_address=None,
        tier=user.tier,
        window="day",
    )

    return QuotaUsageResponse(
        user_id=user.id,
        tier=user.tier,
        hourly_limit=hourly_info.limit,
        hourly_used=hourly_info.limit - hourly_info.remaining,
        hourly_remaining=hourly_info.remaining,
        hourly_reset_at=hourly_info.reset_at,
        daily_limit=daily_info.limit,
        daily_used=daily_info.limit - daily_info.remaining,
        daily_remaining=daily_info.remaining,
        daily_reset_at=daily_info.reset_at,
        quota_exceeded=hourly_info.quota_exceeded or daily_info.quota_exceeded,
    )


@router.put("/{user_id}/tier", response_model=UserResponse)
async def update_user_tier(
    user_id: UUID,
    request: QuotaUpdateRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update user's tier (admin only).

    Changes the user's subscription tier, which affects their rate limits.

    Args:
        user_id: User ID to update
        request: New tier information

    Returns:
        Updated user information
    """
    # Validate tier
    valid_tiers = ["free", "pro", "enterprise"]
    if request.tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
        )

    # Get user from database
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Update tier
    old_tier = user.tier
    updated_user = await crud.update_user_tier(db, user_id, request.tier)

    logger.info(f"Admin {current_user.id} updated user {user_id} tier from {old_tier} to {request.tier}")

    return UserResponse.model_validate(updated_user)


@router.post("/{user_id}/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_user_quota(
    user_id: UUID,
    request: QuotaResetRequest = QuotaResetRequest(),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Reset user's quota counters (admin only).

    Clears the rate limit counters for a user, effectively giving them
    a fresh quota. Use with caution.

    Args:
        user_id: User ID to reset
        request: Which window to reset (hour, day, or all)
    """
    # Verify user exists
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Delete rate limit keys from cache
    windows_to_reset = ["hour", "day"] if request.window == "all" else [request.window]

    for window in windows_to_reset:
        key = f"ratelimit:user:{user_id}:{window}"

        # Try Redis first
        redis_deleted = await redis_delete(key)
        if not redis_deleted:
            # Fallback to memory
            await memory_delete(key)

    logger.info(f"Admin {current_user.id} reset quota for user {user_id} (window: {request.window})")


@router.get("/stats/overview")
async def get_quota_stats_overview(
    current_user: UserResponse = Depends(get_current_admin_user),
) -> dict:
    """
    Get system-wide quota usage statistics (admin only).

    Returns aggregate statistics across all users and tiers.
    """
    # Note: This is a simplified implementation
    # In production, you'd aggregate from a metrics database

    return {
        "total_users": 0,  # Would query database
        "active_users_hour": 0,  # Users who made requests in last hour
        "active_users_day": 0,  # Users who made requests in last day
        "requests_hour": 0,  # Total requests in last hour
        "requests_day": 0,  # Total requests in last day
        "tier_distribution": {
            "free": 0,
            "pro": 0,
            "enterprise": 0,
        },
        "quota_exceeded_users": 0,  # Users currently over quota
        "message": "Placeholder - full metrics coming in Task 5 (Monitoring)",
    }


# Export router
__all__ = ["router"]
