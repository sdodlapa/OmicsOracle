"""
Authentication and Authorization Module.

This module provides comprehensive authentication and authorization functionality
including JWT tokens, API keys, password hashing, and user management.
"""

from omics_oracle_v2.auth.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
    require_api_key,
)
from omics_oracle_v2.auth.models import APIKey, User
from omics_oracle_v2.auth.security import create_access_token, create_api_key, verify_api_key, verify_password

__all__ = [
    # Models
    "User",
    "APIKey",
    # Security functions
    "create_access_token",
    "create_api_key",
    "verify_password",
    "verify_api_key",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "require_api_key",
]
