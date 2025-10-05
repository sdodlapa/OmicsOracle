"""
Tests for authentication endpoints.

Based on successful manual tests from manual_api_test.py (91% pass rate)
Tests cover: registration, login, token auth, user management
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUserRegistration:
    """Test user registration."""

    async def test_register_new_user(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v2/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "username": "newuser",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Should never expose password

    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data):
        """Test registration with duplicate email fails."""
        # Register first user
        await client.post("/api/v2/auth/register", json=test_user_data)

        # Try to register again with same email
        response = await client.post("/api/v2/auth/register", json=test_user_data)
        assert response.status_code in [400, 409]  # Either is acceptable for duplicate
        error_detail = str(response.json().get("detail", "")).lower()
        assert "already" in error_detail or "exists" in error_detail or "duplicate" in error_detail

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v2/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "username": "testuser",
            },
        )
        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        response = await client.post(
            "/api/v2/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "username": "testuser",
            },
        )
        assert response.status_code == 422

    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields fails."""
        response = await client.post(
            "/api/v2/auth/register",
            json={
                "email": "test@example.com",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestUserLogin:
    """Test user login."""

    async def test_login_success(self, client: AsyncClient, test_user_data):
        """Test successful login."""
        # Register user first
        await client.post("/api/v2/auth/register", json=test_user_data)

        # Login
        response = await client.post(
            "/api/v2/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    async def test_login_wrong_password(self, client: AsyncClient, test_user_data):
        """Test login with wrong password fails."""
        # Register user first
        await client.post("/api/v2/auth/register", json=test_user_data)

        # Try to login with wrong password
        response = await client.post(
            "/api/v2/auth/login",
            json={
                "email": test_user_data["email"],
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/api/v2/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!",
            },
        )
        assert response.status_code == 401

    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login without credentials fails."""
        response = await client.post("/api/v2/auth/login", json={})
        assert response.status_code == 422


@pytest.mark.asyncio
class TestTokenAuthentication:
    """Test JWT token authentication."""

    async def test_access_protected_route_with_token(self, authenticated_client):
        """Test accessing protected route with valid token."""
        client, _ = authenticated_client
        response = await client.get("/api/v2/users/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data

    async def test_access_protected_route_without_token(self, client: AsyncClient):
        """Test accessing protected route without token fails."""
        response = await client.get("/api/v2/users/me")
        assert response.status_code == 401

    async def test_access_protected_route_invalid_token(self, client: AsyncClient):
        """Test accessing protected route with invalid token fails."""
        client.headers["Authorization"] = "Bearer invalid_token_12345"
        response = await client.get("/api/v2/users/me")
        assert response.status_code == 401

    async def test_access_protected_route_malformed_header(self, client: AsyncClient):
        """Test accessing protected route with malformed auth header fails."""
        client.headers["Authorization"] = "InvalidFormat token123"
        response = await client.get("/api/v2/users/me")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUserManagement:
    """Test user management endpoints."""

    async def test_get_current_user(self, authenticated_client, test_user_data):
        """Test getting current user information."""
        client, _ = authenticated_client
        response = await client.get("/api/v2/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "tier" in data
        assert "is_active" in data
        assert "created_at" in data
