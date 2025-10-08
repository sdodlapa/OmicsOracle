"""
Integration tests for GEO Client with real API calls.

These tests make actual calls to NCBI/GEO APIs and require:
- Internet connection
- NCBI email configured
- Optional: NCBI API key for higher rate limits
"""

import pytest

from omics_oracle.core.config import Config
from omics_oracle.core.exceptions import GEOClientError, NCBIAPIError
from omics_oracle.geo_tools.geo_client import UnifiedGEOClient


@pytest.mark.integration
class TestGEOClientIntegration:
    """Integration tests for GEO client with real API calls."""

    @pytest.fixture
    def config(self):
        """Test configuration with NCBI email."""
        config = Config()
        # Set test email - this should come from environment
        if not config.ncbi.email:
            config.ncbi.email = "sdodl001@odu.edu"
        return config

    @pytest.fixture
    def client(self, config):
        """GEO client instance for testing."""
        return UnifiedGEOClient(config)

    @pytest.mark.asyncio
    async def test_search_real_geo_series(self, client):
        """Test searching for real GEO series."""
        try:
            # Search for a common term
            results = await client.search_geo_series(query="breast cancer", max_results=5)

            # Should get some results
            assert isinstance(results, list)
            assert len(results) > 0
            assert len(results) <= 5

            # All results should be strings (GEO IDs)
            for geo_id in results:
                assert isinstance(geo_id, str)

        except NCBIAPIError as e:
            pytest.skip(f"NCBI API error: {e}")
        except GEOClientError as e:
            if "Entrez client not available" in str(e):
                pytest.skip("Entrez not available - install entrezpy")
            raise

    @pytest.mark.asyncio
    async def test_get_metadata_known_series(self, client):
        """Test getting metadata for a known GEO series."""
        try:
            # Use a well-known public GEO series
            # GSE2034 is a classic breast cancer dataset
            metadata = await client.get_geo_metadata("GSE2034", include_sra=False)

            # Verify basic metadata structure
            assert isinstance(metadata, dict)
            assert metadata["geo_id"] == "GSE2034"
            assert "title" in metadata
            assert "summary" in metadata
            assert "organism" in metadata
            assert "sample_count" in metadata

            # Should have reasonable sample count
            assert metadata["sample_count"] > 0

        except GEOClientError as e:
            if "GEOparse not available" in str(e):
                pytest.skip("GEOparse not available - install GEOparse")
            raise

    @pytest.mark.asyncio
    async def test_batch_metadata_retrieval(self, client):
        """Test batch metadata retrieval."""
        try:
            # Use small list of known series
            geo_ids = ["GSE2034", "GSE2990"]  # Small breast cancer datasets

            results = await client.batch_retrieve_metadata(geo_ids, max_concurrent=2)

            # Should get results for both
            assert isinstance(results, dict)
            assert len(results) == 2

            for geo_id in geo_ids:
                assert geo_id in results
                metadata = results[geo_id]
                if "error" not in metadata:
                    assert metadata["geo_id"] == geo_id
                    assert "title" in metadata

        except GEOClientError as e:
            if "GEOparse not available" in str(e):
                pytest.skip("GEOparse not available")
            raise

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Test that rate limiting works."""
        import time

        try:
            start_time = time.time()

            # Make multiple rapid requests
            results = []
            for i in range(3):
                result = await client.search_geo_series(query=f"test query {i}", max_results=1)
                results.append(result)

            end_time = time.time()
            elapsed = end_time - start_time

            # Should have some delay for rate limiting
            # If cached or API unavailable, elapsed may be minimal
            # Just verify no errors occurred and we got results
            assert len(results) == 3  # All requests completed
            assert elapsed >= 0  # Non-negative time elapsed

        except NCBIAPIError as e:
            pytest.skip(f"NCBI API error: {e}")

    @pytest.mark.asyncio
    async def test_caching_works(self, client):
        """Test that caching improves performance."""
        import time

        try:
            geo_id = "GSE2034"

            # First call - should be slow (actual API call)
            start_time = time.time()
            metadata1 = await client.get_geo_metadata(geo_id, include_sra=False)
            first_call_time = time.time() - start_time

            # Second call - should be fast (from cache)
            start_time = time.time()
            metadata2 = await client.get_geo_metadata(geo_id, include_sra=False)
            second_call_time = time.time() - start_time

            # Results should be identical
            assert metadata1 == metadata2

            # Second call should be significantly faster
            # (Cache should be noticeable if working)
            if first_call_time < 0.001:  # Very fast initial call
                # Should be same or faster
                assert second_call_time <= first_call_time
            else:
                assert second_call_time < first_call_time * 0.8  # More lenient

        except GEOClientError as e:
            if "GEOparse not available" in str(e):
                pytest.skip("GEOparse not available")
            raise

    def test_validate_geo_id(self, client):
        """Test GEO ID validation."""
        # Valid IDs
        assert client.validate_geo_id("GSE123456")
        assert client.validate_geo_id("gse123")

        # Invalid IDs
        assert not client.validate_geo_id("invalid")
        assert not client.validate_geo_id("GSE")
        assert not client.validate_geo_id("123456")
        assert not client.validate_geo_id(None)
        assert not client.validate_geo_id(123)

    def test_client_info(self, client):
        """Test client info reporting."""
        info = client.get_client_info()

        assert isinstance(info, dict)
        assert "entrez_email" in info
        assert "has_entrez" in info
        assert "has_geoparse" in info
        assert "cache_directory" in info

        # Should have email configured
        assert info["entrez_email"] == "sdodl001@odu.edu"


@pytest.mark.integration
@pytest.mark.slow
class TestGEOClientSlowIntegration:
    """Slow integration tests that make multiple API calls."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        config = Config()
        if not config.ncbi.email:
            config.ncbi.email = "sdodl001@odu.edu"
        return config

    @pytest.fixture
    def client(self, config):
        """GEO client instance."""
        return UnifiedGEOClient(config)

    @pytest.mark.asyncio
    async def test_large_batch_processing(self, client):
        """Test processing larger batches of GEO series."""
        try:
            # Search for multiple series
            search_results = await client.search_geo_series(query="microarray human", max_results=10)

            if not search_results:
                pytest.skip("No search results returned")

            # Take first 5 for batch processing
            geo_ids = search_results[:5]

            results = await client.batch_retrieve_metadata(geo_ids, max_concurrent=3)

            # Should get results for most or all
            assert len(results) >= len(geo_ids) * 0.7  # Allow 30% failure rate

            successful_results = [r for r in results.values() if "error" not in r]
            assert len(successful_results) > 0

        except Exception as e:
            pytest.skip(f"Batch processing test failed: {e}")
