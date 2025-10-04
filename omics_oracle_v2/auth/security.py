"""
Security utilities for authentication and authorization.

This module provides functions for password hashing, JWT token generation,
and API key management.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from omics_oracle_v2.core.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_api_key() -> tuple[str, str, str]:
    """
    Create a new API key.

    Returns:
        Tuple of (full_key, key_hash, key_prefix)
        - full_key: The complete API key to return to user (only once)
        - key_hash: Hashed version to store in database
        - key_prefix: First 8 characters for identification
    """
    # Generate a secure random key (32 bytes = 64 hex characters)
    key = f"omics_{secrets.token_urlsafe(32)}"

    # Create prefix for identification (first 12 chars)
    key_prefix = key[:12]

    # Hash the key for storage
    key_hash = get_password_hash(key)

    return key, key_hash, key_prefix


def verify_api_key(key: str, key_hash: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        key: Plain text API key
        key_hash: Hashed API key from database

    Returns:
        True if key matches, False otherwise
    """
    return pwd_context.verify(key, key_hash)


def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token.

    Args:
        email: User email address

    Returns:
        Password reset token
    """
    expires_delta = timedelta(hours=settings.password_reset_token_expire_hours)
    data = {"sub": email, "type": "password_reset"}
    return create_access_token(data, expires_delta=expires_delta)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and extract email.

    Args:
        token: Password reset token

    Returns:
        Email if token is valid, None otherwise
    """
    payload = decode_access_token(token)

    if not payload:
        return None

    if payload.get("type") != "password_reset":
        return None

    return payload.get("sub")


def create_email_verification_token(email: str) -> str:
    """
    Create an email verification token.

    Args:
        email: User email address

    Returns:
        Email verification token
    """
    expires_delta = timedelta(hours=settings.email_verification_token_expire_hours)
    data = {"sub": email, "type": "email_verification"}
    return create_access_token(data, expires_delta=expires_delta)


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify an email verification token and extract email.

    Args:
        token: Email verification token

    Returns:
        Email if token is valid, None otherwise
    """
    payload = decode_access_token(token)

    if not payload:
        return None

    if payload.get("type") != "email_verification":
        return None

    return payload.get("sub")
