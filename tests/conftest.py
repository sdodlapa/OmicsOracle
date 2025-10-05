"""
Test Configuration and Fixtures for OmicsOracle.

This module provides shared fixtures and test configuration for all test suites,
including database sessions, HTTP clients, and authentication helpers.

Fixtures:
    - temp_dir: Temporary directory for test files
    - sample_data_dir: Path to test data files
    - mock_geo_response: Mock GEO API response
    - sample_fasta_content: Sample FASTA sequences
    - sample_metadata: Sample metadata structure
    - test_config: Test configuration with safe defaults
    - mock_nlp_service: Mocked NLP service for testing
    - mock_cache: Mocked cache service for testing
    - db_session: Database session for API tests
    - client: HTTP client for API tests
    - authenticated_client: Authenticated HTTP client for API tests

Usage:
    def test_something(temp_dir, mock_geo_response):
        # temp_dir and mock_geo_response are automatically provided
        pass
"""

import asyncio
import os  # noqa: F401 - used by fixture functions
import tempfile
import uuid  # noqa: F401 - used by fixture functions
from pathlib import Path
from typing import Any, AsyncGenerator, Dict  # noqa: F401 - used by fixture functions
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from faker import Faker  # noqa: F401 - used by fixture functions
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (  # noqa: F401 - used by fixture functions
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """
    Configure custom pytest markers.

    Registers markers for:
    - unit: Unit tests (fast, no external dependencies)
    - integration: Integration tests (may require services)
    - e2e: End-to-end tests (full system)
    - slow: Slow-running tests
    - requires_api_key: Tests requiring API keys
    - requires_network: Tests requiring network access

    Args:
        config: pytest config object
    """
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full system)")
    config.addinivalue_line("markers", "requires_api_key: Tests requiring API keys")
    config.addinivalue_line("markers", "requires_network: Tests requiring network access")


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for tests.

    The directory is automatically cleaned up after the test.

    Returns:
        Path: Path object pointing to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_data_dir():
    """
    Path to sample data directory.

    Returns:
        Path: Path to tests/data directory
    """
    return Path(__file__).parent / "data"


@pytest.fixture
def test_data_dir(temp_dir: Path) -> Path:
    """
    Create a test data directory with sample files.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Path to test data directory
    """
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    return data_dir


# ============================================================================
# Mock Data Fixtures
# ============================================================================


@pytest.fixture
def mock_geo_response() -> Dict[str, Any]:
    """
    Mock GEO API response for testing.

    Returns:
        dict: Sample GEO series metadata
    """
    return {
        "accession": "GSE12345",
        "title": "Test Dataset",
        "summary": "This is a test genomics dataset",
        "organism": "Homo sapiens",
        "samples": 24,
        "platform": "GPL1234",
        "type": "Expression profiling by array",
        "pubmed_id": "12345678",
    }


@pytest.fixture
def sample_fasta_content() -> str:
    """
    Sample FASTA content for testing.

    Returns:
        str: Multi-sequence FASTA format data
    """
    return """>seq1
ATCGATCGATCGATCG
>seq2
GCTAGCTAGCTAGCTA
>seq3
TTTTAAAACCCCGGGG
"""


@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """
    Sample metadata for testing.

    Returns:
        dict: Sample genomics dataset metadata
    """
    return {
        "dataset_id": "TEST001",
        "title": "Sample Genomics Dataset",
        "description": "A sample dataset for testing purposes",
        "organism": "Homo sapiens",
        "tissue": "brain",
        "condition": "control",
        "replicate_count": 3,
        "platform": "Illumina HiSeq",
        "date_created": "2024-01-01",
    }


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """
    Test configuration with safe defaults.

    Provides configuration that doesn't require external services
    or API keys. Safe for CI/CD environments.

    Returns:
        dict: Test configuration settings
    """
    return {
        "environment": "testing",
        "debug": True,
        "ncbi": {
            "api_key": "test_api_key",
            "email": "test@example.com",
            "tool": "omics_oracle_test",
        },
        "cache": {
            "enabled": False,  # Disable cache for tests
            "ttl": 300,
        },
        "database": {
            "url": "sqlite:///:memory:",  # In-memory database for tests
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8000,
            "workers": 1,
        },
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Set up mock environment variables for testing.

    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    env_vars = {
        "OMICS_ORACLE_ENV": "testing",
        "NCBI_API_KEY": "test_api_key",
        "NCBI_EMAIL": "test@example.com",
        "OPENAI_API_KEY": "test_openai_key",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


# ============================================================================
# Service Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_nlp_service():
    """
    Mocked NLP service for testing.

    Returns:
        MagicMock: Mock NLP service with common methods
    """
    mock = MagicMock()
    mock.process_query = AsyncMock(
        return_value={
            "entities": ["BRCA1", "breast cancer"],
            "intent": "search",
            "normalized_query": "BRCA1 breast cancer expression",
        }
    )
    mock.extract_terms = MagicMock(return_value=["BRCA1", "breast cancer"])
    return mock


@pytest.fixture
def mock_cache():
    """
    Mocked cache service for testing.

    Returns:
        MagicMock: Mock cache with get/set methods
    """
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.clear = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def mock_geo_client():
    """
    Mocked GEO client for testing.

    Returns:
        MagicMock: Mock GEO client with search methods
    """
    client = MagicMock()
    client.search = AsyncMock(
        return_value={
            "count": 1,
            "results": [
                {
                    "accession": "GSE12345",
                    "title": "Test Dataset",
                    "organism": "Homo sapiens",
                }
            ],
        }
    )
    client.fetch = AsyncMock(
        return_value={
            "accession": "GSE12345",
            "title": "Test Dataset",
            "summary": "Test summary",
        }
    )
    return client


# ============================================================================
# Database Fixtures (for v2 API tests)
# ============================================================================


@pytest.fixture
async def db_session():
    """
    Create an async database session for testing.

    Function-scoped to ensure test isolation.

    Returns:
        Tuple[engine, session_factory]: Database engine and session factory
    """
    import sqlalchemy  # noqa: F401 - used in Base.metadata
    from sqlalchemy.orm import sessionmaker  # noqa: F401 - used for session factory
    from sqlalchemy.pool import NullPool  # noqa: F401 - used for test isolation

    from omics_oracle_v2.auth.models import APIKey, User  # noqa: F401 - needed for create_all
    from omics_oracle_v2.database import Base  # noqa: F401 - used for create_all


@pytest.fixture
async def client(db_session):
    """
    Create test HTTP client with database override and rate limiting disabled.

    Function-scoped to ensure test isolation.

    Args:
        db_session: Tuple of (engine, session_factory)

    Returns:
        AsyncClient: HTTP client for testing
    """
    from omics_oracle_v2.api.main import app
    from omics_oracle_v2.auth.quota import RateLimitInfo
    from omics_oracle_v2.database import get_db

    # Unpack the tuple
    engine, session_factory = db_session

    # Override get_db dependency to use test database
    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Mock rate limit check to always allow requests (for testing)
    async def mock_check_rate_limit(*args, **kwargs):
        return RateLimitInfo(
            limit=1000000,
            remaining=1000000,
            reset_at=int(asyncio.get_event_loop().time() + 3600),
            quota_exceeded=False,
        )

    app.dependency_overrides[get_db] = override_get_db

    # Patch the rate limit check function
    with patch("omics_oracle_v2.middleware.rate_limit.check_rate_limit", side_effect=mock_check_rate_limit):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "username": "testuser",
    }


@pytest.fixture
async def authenticated_client(client, test_user_data):
    """
    Create authenticated HTTP client with token.

    Args:
        client: HTTP client
        test_user_data: User registration data

    Returns:
        tuple: (client, user_data)
    """
    # Register user
    response = await client.post("/api/v2/auth/register", json=test_user_data)
    assert response.status_code in [201, 409]  # 409 if user exists

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
    token = data["access_token"]

    # Set auth header
    client.headers["Authorization"] = f"Bearer {token}"

    yield client, data

    # Cleanup
    client.headers.pop("Authorization", None)


@pytest.fixture
async def create_test_user():
    """
    Factory fixture for creating test users.

    Returns:
        Callable: Function to create users with custom attributes
    """
    from omics_oracle_v2.auth.models import User
    from omics_oracle_v2.auth.security import get_password_hash

    async def _create_user(
        db_session,
        email: str,
        password: str,
        tier: str = "free",
        is_admin: bool = False,
        is_active: bool = True,
        is_verified: bool = True,
        full_name: str = None,
    ) -> User:
        """
        Create a test user.

        Args:
            db_session: Database session
            email: User email
            password: Plain text password
            tier: Subscription tier
            is_admin: Admin status
            is_active: Active status
            is_verified: Verified status
            full_name: User's full name

        Returns:
            User: Created user
        """
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            tier=tier,
            is_admin=is_admin,
            is_active=is_active,
            is_verified=is_verified,
            full_name=full_name or email.split("@")[0],
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Store password for later use (e.g., login tests)
        user._test_password = password
        return user

    return _create_user


@pytest.fixture
async def get_auth_headers():
    """
    Get authentication headers for a user.

    Returns:
        Callable: Function that returns auth headers for a user
    """
    from omics_oracle_v2.auth.security import create_access_token

    async def _get_headers(user):
        """
        Get auth headers for user.

        Args:
            user: User object

        Returns:
            dict: Headers with JWT token
        """
        token = create_access_token({"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    return _get_headers
