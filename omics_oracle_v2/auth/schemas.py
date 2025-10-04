"""
Pydantic schemas for authentication and authorization.

This module defines request/response models for API endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

# User Schemas


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserInDB(UserBase):
    """Schema for user data from database."""

    id: UUID
    is_active: bool
    is_admin: bool
    is_verified: bool
    tier: str
    request_count: int
    last_request_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserResponse(UserInDB):
    """Schema for user response (public data)."""

    pass


# Authentication Schemas


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Schema for data stored in JWT token."""

    user_id: Optional[UUID] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    """Schema for password change request."""

    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordReset(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# API Key Schemas


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: Optional[str] = Field(None, max_length=255)


class APIKeyInDB(BaseModel):
    """Schema for API key data from database."""

    id: UUID
    user_id: UUID
    key_prefix: str
    name: Optional[str] = None
    last_used_at: Optional[datetime] = None
    request_count: int
    created_at: datetime
    revoked_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @property
    def is_active(self) -> bool:
        """Check if API key is active."""
        return self.revoked_at is None


class APIKeyResponse(APIKeyInDB):
    """Schema for API key response (without key itself)."""

    pass


class APIKeyWithSecret(APIKeyResponse):
    """Schema for API key response with the actual key (only returned on creation)."""

    key: str  # Only returned once on creation


# Usage and Statistics Schemas


class UsageStats(BaseModel):
    """Schema for user usage statistics."""

    request_count: int
    last_request_at: Optional[datetime] = None
    tier: str
    api_keys_count: int
    active_api_keys_count: int


class QuotaInfo(BaseModel):
    """Schema for user quota information."""

    tier: str
    requests_used: int
    requests_limit: int
    requests_remaining: int
    reset_at: datetime
