"""
Test Configuration and Fixtures for OmicsOracle

This module provides shared fixtures and test configuration for all test suites.

Fixtures:
    - temp_dir: Temporary directory for test files
    - sample_data_dir: Path to test data files
    - mock_geo_response: Mock GEO API response
    - sample_fasta_content: Sample FASTA sequences
    - sample_metadata: Sample metadata structure
    - test_config: Test configuration with safe defaults
    - mock_nlp_service: Mocked NLP service for testing
    - mock_cache: Mocked cache service for testing

Usage:
    def test_something(temp_dir, mock_geo_response):
        # temp_dir and mock_geo_response are automatically provided
        pass
"""

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

# ============================================================================
# Directory and Path Fixtures
# ============================================================================


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
# Test Markers Configuration
# ============================================================================


def pytest_configure(config):
    """
    Configure custom pytest markers.

    Args:
        config: pytest config object
    """
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (may require services)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full system)")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "requires_api_key: Tests requiring API keys")
    config.addinivalue_line("markers", "requires_network: Tests requiring network access")


# ============================================================================
# Database Fixtures (for v2 API tests)
# ============================================================================


@pytest.fixture
async def db_session():
    """
    Create an async database session for testing.

    Uses SQLite in-memory database for fast, isolated tests.

    Returns:
        AsyncSession: Database session
    """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from omics_oracle_v2.database import Base

    # Create in-memory database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # Cleanup
    await engine.dispose()


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
