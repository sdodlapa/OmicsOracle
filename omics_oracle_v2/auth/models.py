"""
Database models for authentication and authorization.

This module defines SQLAlchemy models for users and API keys.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from omics_oracle_v2.database.base import Base


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Subscription tier
    tier = Column(String(50), default="free", nullable=False)  # free, pro, enterprise

    # Usage tracking
    request_count = Column(Integer, default=0, nullable=False)
    last_request_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(email='{self.email}', tier='{self.tier}')>"

    @property
    def is_free_tier(self) -> bool:
        """Check if user is on free tier."""
        return self.tier == "free"

    @property
    def is_pro_tier(self) -> bool:
        """Check if user is on pro tier."""
        return self.tier == "pro"

    @property
    def is_enterprise_tier(self) -> bool:
        """Check if user is on enterprise tier."""
        return self.tier == "enterprise"


class APIKey(Base):
    """API key model for programmatic access."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # API key data
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(10), nullable=False, index=True)
    name = Column(String(255), nullable=True)

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    request_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        """String representation."""
        status = "revoked" if self.revoked_at else "active"
        return f"<APIKey(prefix='{self.key_prefix}', status='{status}')>"

    @property
    def is_active(self) -> bool:
        """Check if API key is active (not revoked)."""
        return self.revoked_at is None

    def revoke(self) -> None:
        """Revoke the API key."""
        self.revoked_at = datetime.utcnow()
