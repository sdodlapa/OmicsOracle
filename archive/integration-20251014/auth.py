"""
Authentication client for OmicsOracle integration layer.

Handles:
- User registration
- Login/logout
- Token management
- Auto-refresh
- Token storage
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TokenResponse(BaseModel):
    """Authentication token response"""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Token lifetime in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token for obtaining new access token")


class UserResponse(BaseModel):
    """User response model."""

    id: str  # UUID string
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    is_verified: bool = False
    tier: str = "free"
    request_count: int = 0
    last_request_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login_at: Optional[str] = None


class AuthClient:
    """
    Authentication client for integration layer.

    Features:
    - User registration and login
    - Automatic token refresh
    - Token expiration tracking
    - Secure token management

    Usage:
        # Register and login
        async with AuthClient() as auth:
            await auth.register("user@example.com", "password", "User Name")
            token = await auth.login("user@example.com", "password")

        # Use token with other clients
        client = AnalysisClient(api_key=token.access_token)
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize authentication client.

        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._token: Optional[TokenResponse] = None
        self._token_expires_at: Optional[datetime] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def register(self, email: str, password: str, full_name: str) -> UserResponse:
        """
        Register a new user.

        Args:
            email: User email address
            password: User password (min 8 characters)
            full_name: User's full name

        Returns:
            UserResponse with user info

        Raises:
            httpx.HTTPStatusError: If registration fails
        """
        logger.info(f"Registering user: {email}")

        response = await self._client.post(
            f"{self.base_url}/api/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )

        response.raise_for_status()
        data = response.json()

        logger.info(f"User registered successfully: {email}")
        return UserResponse(**data)

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Login and get access token.

        Args:
            email: User's email
            password: User's password

        Returns:
            TokenResponse with access token
        """
        # Use JSON body (not OAuth2 form data)
        login_data = {
            "email": email,
            "password": password,
        }

        response = await self._client.post(
            f"{self.base_url}/api/auth/login",
            json=login_data,  # Backend expects JSON
        )
        response.raise_for_status()

        token_data = response.json()
        self._token = TokenResponse(**token_data)

        # Calculate expiration time
        self._token_expires_at = datetime.now() + timedelta(seconds=self._token.expires_in)

        logger.info(f"Login successful, token expires at {self._token_expires_at}")
        return self._token

    async def logout(self) -> None:
        """
        Logout and invalidate token.

        Raises:
            ValueError: If not logged in
        """
        if not self._token:
            raise ValueError("Not logged in")

        logger.info("Logging out")

        try:
            await self._client.post(
                f"{self.base_url}/api/auth/logout",
                headers={"Authorization": f"Bearer {self._token.access_token}"},
            )
        except httpx.HTTPStatusError as e:
            logger.warning(f"Logout failed: {e}")

        self._token = None
        self._token_expires_at = None

        logger.info("Logged out successfully")

    async def refresh_token(self) -> TokenResponse:
        """
        Refresh access token using current token.

        The backend generates a new JWT token using the current token
        (passed in Authorization header), not a separate refresh token.

        Returns:
            New TokenResponse

        Raises:
            ValueError: If not logged in
            httpx.HTTPStatusError: If refresh fails
        """
        if not self._token:
            raise ValueError("Not logged in - no token to refresh")

        logger.info("Refreshing access token")

        response = await self._client.post(
            f"{self.base_url}/api/auth/refresh",
            headers={"Authorization": f"Bearer {self._token.access_token}"},
        )

        response.raise_for_status()
        data = response.json()

        self._token = TokenResponse(**data)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=self._token.expires_in)

        logger.info("Token refreshed successfully")
        logger.debug("New token expires at: %s", self._token_expires_at)

        return self._token

    def get_token(self) -> Optional[str]:
        """
        Get current access token.

        Returns:
            Access token string or None if not logged in
        """
        return self._token.access_token if self._token else None

    def is_token_expired(self) -> bool:
        """
        Check if token is expired or about to expire.

        Returns:
            True if token is expired or will expire within 5 minutes
        """
        if not self._token_expires_at:
            return True

        # Consider expired if less than 5 minutes remaining
        buffer = timedelta(minutes=5)
        is_expired = datetime.utcnow() + buffer >= self._token_expires_at

        if is_expired:
            logger.debug("Token is expired or about to expire")

        return is_expired

    async def ensure_valid_token(self) -> str:
        """
        Ensure we have a valid token, refreshing if needed.

        Returns:
            Valid access token

        Raises:
            ValueError: If not logged in
        """
        if not self._token:
            raise ValueError("Not logged in - please call login() first")

        if self.is_token_expired():
            logger.info("Token expired, refreshing...")
            await self.refresh_token()

        return self._token.access_token


# Convenience functions


async def create_test_user(
    email: str = "test@example.com",
    password: str = "TestPassword123!",  # Updated to meet password requirements
    full_name: str = "Test User",
) -> str:
    """
    Create a test user and return access token.

    This is a convenience function for testing that combines
    registration and login in one call.

    Args:
        email: User email (default: test@example.com)
        password: User password (default: TestPassword123!)
        full_name: User's full name (default: Test User)

    Returns:
        Access token string

    Example:
        token = await create_test_user()
        client = AnalysisClient(api_key=token)
    """
    async with AuthClient() as auth:
        try:
            # Try to register
            await auth.register(email, password, full_name)
            logger.info(f"Test user created: {email}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                # User already exists, that's fine
                logger.info(f"Test user already exists: {email}")
            else:
                raise

        # Login and get token
        token_response = await auth.login(email, password)
        return token_response.access_token


async def login_and_get_token(email: str = "test@example.com", password: str = "TestPassword123!") -> str:
    """
    Convenience function to login and get token.

    Args:
        email: User's email
        password: User's password

    Returns:
        Access token string
    """
    async with AuthClient() as auth:
        token_response = await auth.login(email, password)
        return token_response.access_token
