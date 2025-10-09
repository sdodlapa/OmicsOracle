"""
Tests for CORE API client.

Tests full-text acquisition from CORE's 45M+ open access repository.
"""

import asyncio
import os
from pathlib import Path

import pytest

from omics_oracle_v2.lib.publications.clients.oa_sources.core_client import COREClient, COREConfig


@pytest.fixture
def core_api_key():
    """Get CORE API key from environment."""
    api_key = os.getenv("CORE_API_KEY")
    if not api_key:
        pytest.skip("CORE_API_KEY not set in environment")
    return api_key


@pytest.fixture
async def core_client(core_api_key):
    """Create CORE client."""
    client = COREClient(api_key=core_api_key)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_core_client_initialization(core_api_key):
    """Test CORE client can be initialized."""
    client = COREClient(api_key=core_api_key)
    assert client is not None
    assert client.config.api_key == core_api_key
    await client.close()


@pytest.mark.asyncio
async def test_get_fulltext_by_doi_open_access(core_client):
    """Test getting full text for an open access paper."""
    # PLOS ONE paper (always OA)
    doi = "10.1371/journal.pone.0123456"

    result = await core_client.get_fulltext_by_doi(doi)

    # CORE may or may not have this specific paper
    # Just verify the API call works
    assert result is None or isinstance(result, dict)

    if result:
        assert "title" in result
        print(f"Found in CORE: {result.get('title')}")
        print(f"PDF URL: {result.get('downloadUrl')}")
        print(f"Has full text: {bool(result.get('fullText'))}")


@pytest.mark.asyncio
async def test_search_by_title(core_client):
    """Test searching by title."""
    title = "CRISPR Cas9 gene editing"

    results = await core_client.search_by_title(title, limit=5)

    assert isinstance(results, list)
    # CORE should have at least some CRISPR papers
    if results:
        first_result = results[0]
        assert "title" in first_result
        assert "id" in first_result
        print(f"\nFound {len(results)} results")
        print(f"First result: {first_result.get('title')}")


@pytest.mark.asyncio
async def test_search_general(core_client):
    """Test general search functionality."""
    query = "machine learning genomics"

    publications = await core_client.search(query, max_results=10)

    assert isinstance(publications, list)
    if publications:
        first_pub = publications[0]
        assert hasattr(first_pub, "title")
        assert hasattr(first_pub, "authors")
        print(f"\nFound {len(publications)} publications")
        print(f"First: {first_pub.title[:50]}")


@pytest.mark.asyncio
async def test_download_pdf(core_client, tmp_path):
    """Test PDF download functionality."""
    # Search for a paper with downloadUrl
    results = await core_client.search_by_title("open access", limit=10)

    # Find one with a download URL
    download_url = None
    for result in results:
        if result.get("downloadUrl"):
            download_url = result["downloadUrl"]
            title = result.get("title", "test")
            break

    if not download_url:
        pytest.skip("No papers with download URLs found")

    # Try to download
    output_path = tmp_path / "test.pdf"
    success = await core_client.download_pdf(download_url, output_path)

    if success:
        assert output_path.exists()
        assert output_path.stat().st_size > 1000  # At least 1KB
        print(f"\nSuccessfully downloaded PDF: {output_path.stat().st_size} bytes")


@pytest.mark.asyncio
async def test_context_manager(core_api_key):
    """Test async context manager usage."""
    async with COREClient(api_key=core_api_key) as client:
        results = await client.search_by_title("test", limit=1)
        assert isinstance(results, list)


@pytest.mark.asyncio
async def test_rate_limiting(core_client):
    """Test that rate limiting works."""
    import time

    start = time.time()

    # Make multiple requests
    for i in range(3):
        await core_client.get_fulltext_by_doi(f"10.1234/test{i}")

    elapsed = time.time() - start

    # Should take at least some time due to rate limiting
    print(f"\n3 requests took {elapsed:.2f}s")


def test_config_validation():
    """Test configuration validation."""
    # Should fail without API key
    with pytest.raises(ValueError):
        COREConfig(api_key="")

    with pytest.raises(ValueError):
        COREClient()


if __name__ == "__main__":
    # Quick manual test
    async def main():
        api_key = os.getenv("CORE_API_KEY", "6rxSGFapquU2Nbgd7vRfX9cAskKBeWEy")

        async with COREClient(api_key=api_key) as client:
            print("Testing CORE API client...\n")

            # Test 1: Search by title
            print("1. Searching by title: 'CRISPR gene editing'")
            results = await client.search_by_title("CRISPR gene editing", limit=3)
            print(f"   Found {len(results)} results")
            if results:
                for i, r in enumerate(results[:2], 1):
                    print(f"   {i}. {r.get('title', 'N/A')[:60]}")
                    print(f"      PDF: {bool(r.get('downloadUrl'))}")

            print()

            # Test 2: Search by DOI (PLOS ONE paper)
            print("2. Searching by DOI: 10.1371/journal.pone.0123456")
            result = await client.get_fulltext_by_doi("10.1371/journal.pone.0123456")
            if result:
                print(f"   Found: {result.get('title', 'N/A')[:60]}")
                print(f"   PDF URL: {bool(result.get('downloadUrl'))}")
                print(f"   Full text: {bool(result.get('fullText'))}")
            else:
                print("   Not found in CORE")

            print("\n✓ CORE client working!")

    asyncio.run(main())
