"""
Tests for parsed content cache.

Tests the ParsedCache class for caching parsed full-text content
(tables, figures, sections, etc.) to avoid expensive re-parsing.
"""

import asyncio
import gzip
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from omics_oracle_v2.lib.pipelines.text_enrichment.parsed_cache import ParsedCache


class TestParsedCacheInit:
    """Test ParsedCache initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        cache = ParsedCache()

        assert cache.cache_dir.exists()
        assert cache.ttl_days == 90
        assert cache.use_compression is True

    def test_custom_directory(self, tmp_path):
        """Test initialization with custom directory."""
        custom_dir = tmp_path / "custom_cache"
        cache = ParsedCache(cache_dir=custom_dir)

        assert cache.cache_dir == custom_dir
        assert custom_dir.exists()

    def test_custom_ttl(self):
        """Test initialization with custom TTL."""
        cache = ParsedCache(ttl_days=30)
        assert cache.ttl_days == 30

    def test_no_compression(self):
        """Test initialization without compression."""
        cache = ParsedCache(use_compression=False)
        assert cache.use_compression is False


class TestParsedCacheSaveAndGet:
    """Test saving and retrieving cached content."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a ParsedCache with temp directory."""
        return ParsedCache(cache_dir=tmp_path / "parsed_cache")

    @pytest.fixture
    def sample_content(self):
        """Sample parsed content."""
        return {
            "title": "Test Paper",
            "abstract": "This is a test abstract.",
            "sections": [
                {"heading": "Introduction", "text": "Intro text..."},
                {"heading": "Methods", "text": "Methods text..."},
            ],
            "tables": [{"caption": "Table 1", "data": [["A", "B"], ["1", "2"]]}],
            "figures": [{"caption": "Figure 1", "url": "http://example.com/fig1.png"}],
            "references": [{"title": "Reference 1", "doi": "10.1234/ref1"}],
        }

    @pytest.mark.asyncio
    async def test_save_compressed(self, cache, sample_content):
        """Test saving content with compression."""
        cache.use_compression = True

        saved_path = await cache.save(
            publication_id="PMC123456",
            content=sample_content,
            source_file="/path/to/file.pdf",
            source_type="pdf",
            parse_duration_ms=2000,
            quality_score=0.95,
        )

        assert saved_path.exists()
        assert saved_path.suffix == ".gz"
        assert saved_path.name == "PMC123456.json.gz"

        # Verify content
        with gzip.open(saved_path, "rt", encoding="utf-8") as f:
            data = json.load(f)

        assert data["publication_id"] == "PMC123456"
        assert data["source_type"] == "pdf"
        assert data["parse_duration_ms"] == 2000
        assert data["quality_score"] == 0.95
        assert data["content"] == sample_content

    @pytest.mark.asyncio
    async def test_save_uncompressed(self, cache, sample_content):
        """Test saving content without compression."""
        cache.use_compression = False

        saved_path = await cache.save(publication_id="PMC123456", content=sample_content)

        assert saved_path.exists()
        assert saved_path.suffix == ".json"

        # Verify content
        data = json.loads(saved_path.read_text(encoding="utf-8"))
        assert data["publication_id"] == "PMC123456"
        assert data["content"] == sample_content

    @pytest.mark.asyncio
    async def test_get_compressed(self, cache, sample_content):
        """Test retrieving compressed cached content."""
        cache.use_compression = True

        # Save first
        await cache.save("PMC123456", sample_content)

        # Retrieve
        cached = await cache.get("PMC123456")

        assert cached is not None
        assert cached["publication_id"] == "PMC123456"
        assert cached["content"] == sample_content

    @pytest.mark.asyncio
    async def test_get_uncompressed(self, cache, sample_content):
        """Test retrieving uncompressed cached content."""
        cache.use_compression = False

        # Save first
        await cache.save("PMC123456", sample_content)

        # Retrieve
        cached = await cache.get("PMC123456")

        assert cached is not None
        assert cached["content"] == sample_content

    @pytest.mark.asyncio
    async def test_get_missing(self, cache):
        """Test retrieving non-existent content."""
        cached = await cache.get("PMC999999")
        assert cached is None

    @pytest.mark.asyncio
    async def test_get_prefers_compressed(self, cache, sample_content):
        """Test that get() prefers compressed over uncompressed."""
        # Save both compressed and uncompressed
        compressed_path = cache._get_cache_path("PMC123456", compressed=True)
        uncompressed_path = cache._get_cache_path("PMC123456", compressed=False)

        # Create uncompressed with different content
        old_content = {"title": "Old content"}
        uncompressed_path.write_text(
            json.dumps(
                {
                    "publication_id": "PMC123456",
                    "cached_at": datetime.now().isoformat(),
                    "content": old_content,
                }
            ),
            encoding="utf-8",
        )

        # Create compressed with new content
        with gzip.open(compressed_path, "wt", encoding="utf-8") as f:
            json.dump(
                {
                    "publication_id": "PMC123456",
                    "cached_at": datetime.now().isoformat(),
                    "content": sample_content,
                },
                f,
            )

        # Should get compressed version
        cached = await cache.get("PMC123456")
        assert cached["content"] == sample_content  # Not old_content


class TestParsedCacheTTL:
    """Test time-to-live (TTL) functionality."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a ParsedCache with 7-day TTL."""
        return ParsedCache(
            cache_dir=tmp_path / "parsed_cache", ttl_days=7, use_compression=False  # Easier to manipulate
        )

    @pytest.mark.asyncio
    async def test_fresh_content(self, cache):
        """Test that fresh content is returned."""
        # Save content
        content = {"title": "Test"}
        await cache.save("PMC123456", content)

        # Should be able to retrieve immediately
        cached = await cache.get("PMC123456")
        assert cached is not None
        assert cached["content"] == content

    @pytest.mark.asyncio
    async def test_stale_content(self, cache):
        """Test that stale content is not returned."""
        # Save content
        content = {"title": "Test"}
        cache_path = await cache.save("PMC123456", content)

        # Manually modify cached_at to be 8 days ago (beyond 7-day TTL)
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        data["cached_at"] = (datetime.now() - timedelta(days=8)).isoformat()
        cache_path.write_text(json.dumps(data), encoding="utf-8")

        # Should not retrieve stale content
        cached = await cache.get("PMC123456")
        assert cached is None

    @pytest.mark.asyncio
    async def test_almost_stale_content(self, cache):
        """Test that content just under TTL is still returned."""
        # Save content
        content = {"title": "Test"}
        cache_path = await cache.save("PMC123456", content)

        # Manually modify cached_at to be 6 days ago (within 7-day TTL)
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        data["cached_at"] = (datetime.now() - timedelta(days=6)).isoformat()
        cache_path.write_text(json.dumps(data), encoding="utf-8")

        # Should still retrieve
        cached = await cache.get("PMC123456")
        assert cached is not None


class TestParsedCacheDelete:
    """Test deletion functionality."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a ParsedCache."""
        return ParsedCache(cache_dir=tmp_path / "parsed_cache")

    @pytest.mark.asyncio
    async def test_delete_existing(self, cache):
        """Test deleting existing cache entry."""
        # Save content
        content = {"title": "Test"}
        await cache.save("PMC123456", content)

        # Verify it exists
        assert await cache.get("PMC123456") is not None

        # Delete
        deleted = cache.delete("PMC123456")
        assert deleted is True

        # Verify it's gone
        assert await cache.get("PMC123456") is None

    def test_delete_nonexistent(self, cache):
        """Test deleting non-existent cache entry."""
        deleted = cache.delete("PMC999999")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_delete_both_versions(self, cache):
        """Test that delete removes both compressed and uncompressed."""
        # Save both versions
        content = {"title": "Test"}

        compressed_path = cache._get_cache_path("PMC123456", compressed=True)
        uncompressed_path = cache._get_cache_path("PMC123456", compressed=False)

        # Create both
        with gzip.open(compressed_path, "wt", encoding="utf-8") as f:
            json.dump(
                {"publication_id": "PMC123456", "cached_at": datetime.now().isoformat(), "content": content},
                f,
            )

        uncompressed_path.write_text(
            json.dumps(
                {"publication_id": "PMC123456", "cached_at": datetime.now().isoformat(), "content": content}
            ),
            encoding="utf-8",
        )

        # Both should exist
        assert compressed_path.exists()
        assert uncompressed_path.exists()

        # Delete
        cache.delete("PMC123456")

        # Both should be gone
        assert not compressed_path.exists()
        assert not uncompressed_path.exists()


class TestParsedCacheClearStale:
    """Test clearing stale entries."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a ParsedCache with 7-day TTL."""
        return ParsedCache(cache_dir=tmp_path / "parsed_cache", ttl_days=7, use_compression=False)

    @pytest.mark.asyncio
    async def test_clear_stale_entries(self, cache):
        """Test clearing stale cache entries."""
        # Save fresh content
        await cache.save("PMC_FRESH", {"title": "Fresh"})

        # Save stale content
        stale_path = await cache.save("PMC_STALE", {"title": "Stale"})
        data = json.loads(stale_path.read_text(encoding="utf-8"))
        data["cached_at"] = (datetime.now() - timedelta(days=10)).isoformat()
        stale_path.write_text(json.dumps(data), encoding="utf-8")

        # Clear stale
        deleted_count = cache.clear_stale()

        assert deleted_count == 1

        # Fresh should still exist
        assert await cache.get("PMC_FRESH") is not None

        # Stale should be gone
        assert await cache.get("PMC_STALE") is None

    @pytest.mark.asyncio
    async def test_clear_corrupted_files(self, cache):
        """Test that clear_stale removes corrupted files."""
        # Create corrupted file
        corrupted_path = cache.cache_dir / "corrupted.json"
        corrupted_path.write_text("INVALID JSON{{{", encoding="utf-8")

        # Clear stale (should also remove corrupted)
        deleted_count = cache.clear_stale()

        assert deleted_count == 1
        assert not corrupted_path.exists()


class TestParsedCacheStats:
    """Test statistics functionality."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a ParsedCache."""
        return ParsedCache(cache_dir=tmp_path / "parsed_cache", use_compression=True)

    @pytest.mark.asyncio
    async def test_empty_stats(self, cache):
        """Test statistics for empty cache."""
        stats = cache.get_stats()

        assert stats["total_entries"] == 0
        assert stats["total_size_mb"] == 0
        assert stats["by_source_type"] == {}
        assert stats["ttl_days"] == 90
        assert stats["compression_enabled"] is True

    @pytest.mark.asyncio
    async def test_stats_with_content(self, cache):
        """Test statistics with cached content."""
        # Add some content
        await cache.save("PMC1", {"title": "Test 1"}, source_type="pdf")
        await cache.save("PMC2", {"title": "Test 2"}, source_type="pdf")
        await cache.save("PMC3", {"title": "Test 3"}, source_type="xml")

        stats = cache.get_stats()

        assert stats["total_entries"] == 3
        assert stats["total_size_mb"] > 0
        assert stats["by_source_type"] == {"pdf": 2, "xml": 1}

    @pytest.mark.asyncio
    async def test_age_distribution(self, cache):
        """Test age distribution in statistics."""
        cache.use_compression = False  # Easier to manipulate

        # Add fresh content (<7 days)
        await cache.save("PMC_FRESH", {"title": "Fresh"})

        # Add older content (7-30 days)
        old_path = await cache.save("PMC_OLD", {"title": "Old"})
        data = json.loads(old_path.read_text(encoding="utf-8"))
        data["cached_at"] = (datetime.now() - timedelta(days=15)).isoformat()
        old_path.write_text(json.dumps(data), encoding="utf-8")

        stats = cache.get_stats()

        assert stats["age_distribution"]["<7d"] == 1
        assert stats["age_distribution"]["7-30d"] == 1


class TestParsedCacheCorruptedData:
    """Test handling of corrupted cache data."""

    @pytest.fixture
    def cache(self, tmp_path):
        """Create a ParsedCache."""
        return ParsedCache(cache_dir=tmp_path / "parsed_cache", use_compression=False)

    @pytest.mark.asyncio
    async def test_corrupted_json(self, cache):
        """Test handling of corrupted JSON file."""
        # Create corrupted file
        cache_path = cache._get_cache_path("PMC123456", compressed=False)
        cache_path.write_text("INVALID JSON{{{", encoding="utf-8")

        # Should return None and delete corrupted file
        cached = await cache.get("PMC123456")
        assert cached is None
        assert not cache_path.exists()  # Should be deleted

    @pytest.mark.asyncio
    async def test_missing_cached_at(self, cache):
        """Test handling of cache entry without cached_at field."""
        # Create entry without cached_at
        cache_path = cache._get_cache_path("PMC123456", compressed=False)
        cache_path.write_text(
            json.dumps({"publication_id": "PMC123456", "content": {"title": "Test"}}), encoding="utf-8"
        )

        # Should be considered stale
        cached = await cache.get("PMC123456")
        assert cached is None


class TestParsedCachePerformance:
    """Test cache performance."""

    @pytest.mark.asyncio
    async def test_large_content(self, tmp_path):
        """Test caching large content."""
        cache = ParsedCache(cache_dir=tmp_path / "parsed_cache")

        # Create large content (simulate paper with many tables)
        large_content = {
            "title": "Large Paper",
            "tables": [
                {
                    "caption": f"Table {i}",
                    "data": [[f"Cell-{i}-{j}-{k}" for k in range(50)] for j in range(100)],
                }
                for i in range(20)  # 20 tables with 100 rows and 50 columns each
            ],
        }

        # Should be able to save and retrieve
        await cache.save("PMC_LARGE", large_content)
        cached = await cache.get("PMC_LARGE")

        assert cached is not None
        assert len(cached["content"]["tables"]) == 20

    @pytest.mark.asyncio
    async def test_many_entries(self, tmp_path):
        """Test cache with many entries."""
        cache = ParsedCache(cache_dir=tmp_path / "parsed_cache")

        # Save 100 entries
        for i in range(100):
            await cache.save(f"PMC_{i}", {"title": f"Paper {i}"})

        # All should be retrievable
        for i in range(100):
            cached = await cache.get(f"PMC_{i}")
            assert cached is not None
            assert cached["content"]["title"] == f"Paper {i}"

        # Stats should show 100 entries
        stats = cache.get_stats()
        assert stats["total_entries"] == 100


class TestParsedCacheConvenienceFunction:
    """Test the convenience function."""

    def test_get_parsed_cache(self):
        """Test get_parsed_cache() convenience function."""
        from omics_oracle_v2.lib.pipelines.text_enrichment.parsed_cache import get_parsed_cache

        cache = get_parsed_cache()
        assert isinstance(cache, ParsedCache)
        assert cache.cache_dir.exists()
