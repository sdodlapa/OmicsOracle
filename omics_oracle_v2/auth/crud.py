"""
CRUD operations for authentication models.

This module provides database operations for users and API keys.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omics_oracle_v2.auth.models import APIKey, User
from omics_oracle_v2.auth.schemas import UserCreate
from omics_oracle_v2.auth.security import create_api_key, get_password_hash

# User CRUD operations


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User if found, None otherwise
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email.

    Args:
        db: Database session
        email: User email

    Returns:
        User if found, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        user: User creation data

    Returns:
        Created user
    """
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> User:
    """
    Update user password.

    Args:
        db: Database session
        user: User to update
        new_password: New password (plain text)

    Returns:
        Updated user
    """
    user.hashed_password = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_last_login(db: AsyncSession, user: User) -> User:
    """
    Update user's last login timestamp.

    Args:
        db: Database session
        user: User to update

    Returns:
        Updated user
    """
    user.last_login_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def increment_user_request_count(db: AsyncSession, user: User) -> User:
    """
    Increment user's request count and update last request timestamp.

    Args:
        db: Database session
        user: User to update

    Returns:
        Updated user
    """
    user.request_count += 1
    user.last_request_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_tier(db: AsyncSession, user_id: UUID, tier: str) -> User:
    """
    Update user's subscription tier.

    Args:
        db: Database session
        user_id: User ID to update
        tier: New tier (free, pro, enterprise)

    Returns:
        Updated user
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    user.tier = tier
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def verify_user_email(db: AsyncSession, user: User) -> User:
    """
    Mark user's email as verified.

    Args:
        db: Database session
        user: User to verify

    Returns:
        Updated user
    """
    user.is_verified = True
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user: User) -> User:
    """
    Deactivate a user account.

    Args:
        db: Database session
        user: User to deactivate

    Returns:
        Updated user
    """
    user.is_active = False
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


async def activate_user(db: AsyncSession, user: User) -> User:
    """
    Activate a user account.

    Args:
        db: Database session
        user: User to activate

    Returns:
        Updated user
    """
    user.is_active = True
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


# API Key CRUD operations


async def get_api_key_by_prefix(db: AsyncSession, prefix: str) -> Optional[APIKey]:
    """
    Get API key by prefix.

    Args:
        db: Database session
        prefix: API key prefix

    Returns:
        APIKey if found, None otherwise
    """
    result = await db.execute(select(APIKey).where(APIKey.key_prefix == prefix))
    return result.scalar_one_or_none()


async def get_user_api_keys(db: AsyncSession, user_id: UUID) -> list[APIKey]:
    """
    Get all API keys for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of API keys
    """
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == user_id).order_by(APIKey.created_at.desc())
    )
    return list(result.scalars().all())


async def get_active_user_api_keys(db: AsyncSession, user_id: UUID) -> list[APIKey]:
    """
    Get active (non-revoked) API keys for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of active API keys
    """
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == user_id, APIKey.revoked_at.is_(None))
        .order_by(APIKey.created_at.desc())
    )
    return list(result.scalars().all())


async def create_user_api_key(
    db: AsyncSession, user_id: UUID, name: Optional[str] = None
) -> tuple[APIKey, str]:
    """
    Create a new API key for a user.

    Args:
        db: Database session
        user_id: User ID
        name: Optional name for the API key

    Returns:
        Tuple of (APIKey, plain_text_key)
        The plain text key is only returned here and should be shown to user once.
    """
    key, key_hash, key_prefix = create_api_key()

    db_api_key = APIKey(user_id=user_id, key_hash=key_hash, key_prefix=key_prefix, name=name)

    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)

    return db_api_key, key


async def revoke_api_key(db: AsyncSession, api_key: APIKey) -> APIKey:
    """
    Revoke an API key.

    Args:
        db: Database session
        api_key: API key to revoke

    Returns:
        Updated API key
    """
    api_key.revoke()
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def update_api_key_usage(db: AsyncSession, api_key: APIKey) -> APIKey:
    """
    Update API key usage statistics.

    Args:
        db: Database session
        api_key: API key to update

    Returns:
        Updated API key
    """
    api_key.request_count += 1
    api_key.last_used_at = datetime.utcnow()
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def delete_api_key(db: AsyncSession, api_key: APIKey) -> None:
    """
    Permanently delete an API key.

    Args:
        db: Database session
        api_key: API key to delete
    """
    await db.delete(api_key)
    await db.commit()
