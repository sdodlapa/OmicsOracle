"""
Unit tests for GEO library.

Tests GEO client functionality, caching, rate limiting, and data models.
"""

import tempfile
import time
from pathlib import Path

import pytest

from omics_oracle_v2.core.config import GEOSettings
from omics_oracle_v2.core.exceptions import GEOError
from omics_oracle_v2.lib.geo import (
    ClientInfo,
    GEOClient,
    GEOSeriesMetadata,
    RateLimiter,
    SearchResult,
    SimpleCache,
    SRAInfo,
    retry_with_backoff,
)

# ============================================================================
# Cache Tests
# ============================================================================


class TestSimpleCache:
    """Tests for file-based caching."""

    def setup_method(self):
        """Set up test fixtures with temp directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = SimpleCache(cache_dir=Path(self.temp_dir.name), default_ttl=10)

    def teardown_method(self):
        """Clean up temp directory."""
        self.temp_dir.cleanup()

    def test_cache_init(self):
        """Test cache initialization."""
        assert self.cache.cache_dir.exists()
        assert self.cache.default_ttl == 10

    def test_cache_set_and_get(self):
        """Test basic cache operations."""
        data = {"key1": "value1", "key2": 123}
        self.cache.set("test_key", data)

        retrieved = self.cache.get("test_key")
        assert retrieved == data

    def test_cache_miss(self):
        """Test cache miss returns None."""
        result = self.cache.get("nonexistent_key")
        assert result is None

    def test_cache_expiration(self):
        """Test cache expiration with TTL."""
        data = {"data": "test"}
        self.cache.set("expiring_key", data)

        # Should be cached
        result = self.cache.get("expiring_key", ttl=2)
        assert result == data

        # Wait for expiration
        time.sleep(3)

        # Should be expired
        result = self.cache.get("expiring_key", ttl=2)
        assert result is None

    def test_cache_delete(self):
        """Test cache deletion."""
        self.cache.set("delete_me", {"data": "test"})
        assert self.cache.get("delete_me") is not None

        deleted = self.cache.delete("delete_me")
        assert deleted is True
        assert self.cache.get("delete_me") is None

    def test_cache_clear(self):
        """Test clearing all cache."""
        self.cache.set("key1", {"data": "1"})
        self.cache.set("key2", {"data": "2"})
        self.cache.set("key3", {"data": "3"})

        count = self.cache.clear()
        assert count == 3
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        self.cache.set("key1", {"data": "test data here"})
        self.cache.set("key2", {"more": "data"})

        stats = self.cache.get_stats()
        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["default_ttl"] == 10


# ============================================================================
# Rate Limiter Tests
# ============================================================================


class TestRateLimiter:
    """Tests for rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_calls=3, time_window=1.0)
        assert limiter.max_calls == 3
        assert limiter.time_window == 1.0

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting enforces limits."""
        limiter = RateLimiter(max_calls=2, time_window=1.0)

        start = time.time()

        # First two calls should be immediate
        await limiter.acquire()
        await limiter.acquire()

        # Third call should wait
        await limiter.acquire()

        elapsed = time.time() - start
        # Should have waited approximately 1 second
        assert elapsed >= 0.9  # Allow for timing variance

    @pytest.mark.asyncio
    async def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter(max_calls=2, time_window=1.0)

        await limiter.acquire()
        await limiter.acquire()
        assert len(limiter.calls) == 2

        limiter.reset()
        assert len(limiter.calls) == 0


# ============================================================================
# Retry Tests
# ============================================================================


class TestRetryLogic:
    """Tests for retry with backoff."""

    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test successful call on first attempt."""
        call_count = 0

        async def succeeds():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_with_backoff(succeeds, max_retries=3)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_eventual_success(self):
        """Test success after retries."""
        call_count = 0

        async def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry_with_backoff(fails_twice, max_retries=3, initial_delay=0.1)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_all_fail(self):
        """Test failure after all retries."""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await retry_with_backoff(always_fails, max_retries=2, initial_delay=0.1)

        assert call_count == 3  # Initial + 2 retries


# ============================================================================
# Model Tests
# ============================================================================


class TestGEOModels:
    """Tests for Pydantic data models."""

    def test_geo_series_metadata_creation(self):
        """Test GEOSeriesMetadata model creation."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE123456",
            title="Test Study",
            summary="Test summary",
            organism="Homo sapiens",
            sample_count=10,
        )
        assert metadata.geo_id == "GSE123456"
        assert metadata.title == "Test Study"
        assert metadata.sample_count == 10

    def test_geo_series_has_sra_data(self):
        """Test SRA data detection."""
        # Without SRA
        metadata = GEOSeriesMetadata(geo_id="GSE123456")
        assert metadata.has_sra_data() is False

        # With SRA
        sra_info = SRAInfo(srp_ids=["SRP123456"], run_count=5)
        metadata.sra_info = sra_info
        assert metadata.has_sra_data() is True

    def test_search_result_creation(self):
        """Test SearchResult model creation."""
        result = SearchResult(
            query="breast cancer",
            total_found=100,
            geo_ids=["GSE1", "GSE2", "GSE3"],
            search_time=1.5,
        )
        assert result.query == "breast cancer"
        assert len(result.geo_ids) == 3
        assert result.search_time == 1.5

    def test_client_info_creation(self):
        """Test ClientInfo model creation."""
        info = ClientInfo(
            entrez_email="test@example.com",
            has_api_key=True,
            cache_enabled=True,
            cache_directory="/tmp/cache",
            rate_limit=3,
            ssl_verify=True,
            has_geoparse=True,
            has_pysradb=False,
        )
        assert info.entrez_email == "test@example.com"
        assert info.has_api_key is True
        assert info.has_geoparse is True

    def test_sra_info_defaults(self):
        """Test SRAInfo with defaults."""
        sra = SRAInfo()
        assert sra.run_count == 0
        assert sra.experiment_count == 0
        assert len(sra.srp_ids) == 0


# ============================================================================
# GEO Client Tests (Unit - No API calls)
# ============================================================================


class TestGEOClientBasic:
    """Basic tests for GEO client without API calls."""

    def test_geo_client_init_no_email(self):
        """Test GEO client initialization without email."""
        settings = GEOSettings(ncbi_email=None)
        client = GEOClient(settings)
        assert client.ncbi_client is None

    def test_geo_client_init_with_email(self):
        """Test GEO client initialization with email."""
        settings = GEOSettings(ncbi_email="test@example.com")
        client = GEOClient(settings)
        assert client.ncbi_client is not None

    def test_validate_geo_id_valid(self):
        """Test GEO ID validation with valid IDs."""
        settings = GEOSettings(ncbi_email="test@example.com")
        client = GEOClient(settings)

        assert client.validate_geo_id("GSE123456") is True
        assert client.validate_geo_id("GSE1") is True
        assert client.validate_geo_id("gse999") is True  # Case insensitive

    def test_validate_geo_id_invalid(self):
        """Test GEO ID validation with invalid IDs."""
        settings = GEOSettings(ncbi_email="test@example.com")
        client = GEOClient(settings)

        assert client.validate_geo_id("INVALID") is False
        assert client.validate_geo_id("GSE") is False
        assert client.validate_geo_id("GSE123ABC") is False
        assert client.validate_geo_id(123) is False

    def test_convert_ncbi_id_to_gse(self):
        """Test NCBI ID to GSE conversion."""
        settings = GEOSettings(ncbi_email="test@example.com")
        client = GEOClient(settings)

        # Standard conversion
        assert client._convert_ncbi_id_to_gse("200096615") == "GSE96615"
        assert client._convert_ncbi_id_to_gse("200000001") == "GSE1"

        # Already in GSE format
        assert client._convert_ncbi_id_to_gse("GSE123456") == "GSE123456"

    def test_get_info(self):
        """Test client info retrieval."""
        settings = GEOSettings(
            ncbi_email="test@example.com",
            ncbi_api_key="test_key",
            cache_dir=Path("/tmp/cache"),
            rate_limit=5,
        )
        client = GEOClient(settings)
        info = client.get_info()

        assert info.entrez_email == "test@example.com"
        assert info.has_api_key is True
        assert info.rate_limit == 5
        assert "/tmp/cache" in info.cache_directory


# ============================================================================
# Integration Tests (Require API Access)
# ============================================================================


@pytest.mark.integration
class TestGEOClientIntegration:
    """
    Integration tests requiring actual NCBI API access.

    These tests require:
    - Internet connection
    - Valid email in OMICS_GEO_NCBI_EMAIL environment variable
    - Optional: NCBI API key in OMICS_GEO_NCBI_API_KEY

    Run with: pytest -m integration
    """

    @pytest.fixture
    async def geo_client(self):
        """Create GEO client for testing."""
        settings = GEOSettings(
            ncbi_email="test@example.com",  # Replace with actual email
            verify_ssl=False,  # For testing
        )
        client = GEOClient(settings)
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_search_geo_series(self, geo_client):
        """Test GEO series search."""
        try:
            result = await geo_client.search("breast cancer[Title]", max_results=5)
            assert isinstance(result, SearchResult)
            assert len(result.geo_ids) > 0
            assert all(gid.startswith("GSE") for gid in result.geo_ids)
        except GEOError:
            pytest.skip("NCBI API not available or email not configured")

    @pytest.mark.asyncio
    async def test_get_metadata(self, geo_client):
        """Test metadata retrieval."""
        try:
            # Use a well-known public dataset
            metadata = await geo_client.get_metadata("GSE2109", include_sra=False)
            assert isinstance(metadata, GEOSeriesMetadata)
            assert metadata.geo_id == "GSE2109"
            assert len(metadata.title) > 0
            assert metadata.sample_count > 0
        except GEOError as e:
            if "GEOparse" in str(e):
                pytest.skip("GEOparse not available")
            raise


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.performance
class TestGEOPerformance:
    """Performance tests for GEO client."""

    def test_cache_performance(self):
        """Test cache read/write performance."""
        temp_dir = tempfile.TemporaryDirectory()
        cache = SimpleCache(Path(temp_dir.name), default_ttl=3600)

        data = {"key": "value" * 100}  # Moderate size data

        start = time.time()
        for i in range(100):
            cache.set(f"key_{i}", data)
        write_time = time.time() - start

        start = time.time()
        for i in range(100):
            cache.get(f"key_{i}")
        read_time = time.time() - start

        # Should be fast (< 1 second for 100 operations each)
        assert write_time < 1.0
        assert read_time < 1.0

        temp_dir.cleanup()
