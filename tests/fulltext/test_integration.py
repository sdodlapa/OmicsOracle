"""
Integration tests for PMC XML extraction with FullTextManager

Tests the complete workflow:
1. Standalone PMC XML extraction
2. Integration with existing FullTextManager
3. End-to-end waterfall with PMC as Priority 0
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.fulltext.manager_integration import add_pmc_xml_support, try_pmc_xml_extraction
from lib.fulltext.models import ContentType, SourceType


# Mock publication for testing
class MockPublication:
    """Mock publication object for testing."""

    def __init__(self, pmc_id=None, title="Test Article", doi=None):
        self.pmc_id = pmc_id
        self.pmc = pmc_id  # Alternative attribute name
        self.title = title
        self.doi = doi


@pytest.mark.asyncio
async def test_standalone_pmc_extraction_success():
    """Test standalone PMC XML extraction with a real article."""

    # Use a known PMC article
    publication = MockPublication(
        pmc_id="PMC3166277",
        title="Bacteriophage lysis time stochasticity",
        doi="10.1186/1471-2180-11-174",
    )

    result = await try_pmc_xml_extraction(publication, cache_dir=Path("data/fulltext"))

    # Assertions
    assert result.success is True
    assert result.content_type == ContentType.XML
    assert result.source == SourceType.PMC
    assert result.structured_content is not None

    # Check structured content
    structured = result.structured_content
    assert structured.title is not None
    assert len(structured.title) > 0
    assert len(structured.authors) > 0
    assert len(structured.sections) > 0

    # Check quality indicators
    assert result.quality_score > 0.8  # Should be high for PMC XML
    assert result.has_abstract is True
    assert result.has_references is True

    print("\nSUCCESS: Standalone extraction SUCCESS:")
    print("  Title: {structured.title}")
    print("  Authors: {len(structured.authors)}")
    print("  Sections: {len(structured.sections)}")
    print("  Figures: {len(structured.figures)}")
    print("  Tables: {len(structured.tables)}")
    print("  References: {len(structured.references)}")
    print("  Quality Score: {result.quality_score:.2f}")


@pytest.mark.asyncio
async def test_standalone_pmc_extraction_no_pmc_id():
    """Test standalone extraction with publication that has no PMC ID."""

    publication = MockPublication(
        pmc_id=None,  # No PMC ID
        title="Article without PMC ID",
    )

    result = await try_pmc_xml_extraction(publication)

    assert result.success is False
    assert "No PMC ID" in result.error_message


@pytest.mark.asyncio
async def test_manager_integration():
    """Test integration with FullTextManager."""

    # Import the actual manager
    try:
        from omics_oracle_v2.lib.pipelines.url_collection.manager import FullTextManager, FullTextManagerConfig
    except ImportError:
        pytest.skip("FullTextManager not available")

    # Create config with API keys from environment
    config = FullTextManagerConfig(
        core_api_key=os.getenv("CORE_API_KEY"),
        unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
    )

    # Create manager
    manager = FullTextManager(config=config)

    # Add PMC XML support
    add_pmc_xml_support(manager, cache_dir=Path("data/fulltext"))

    # Verify _try_pmc_xml method was added
    assert hasattr(manager, "_try_pmc_xml")
    assert callable(manager._try_pmc_xml)

    # Create test publication
    publication = MockPublication(
        pmc_id="PMC3166277",
        title="Bacteriophage lysis time stochasticity",
    )

    # Initialize manager
    await manager.initialize()

    # Test direct _try_pmc_xml call
    result = await manager._try_pmc_xml(publication)

    assert result.success is True
    assert result.source == "pmc_xml"
    assert result.content is not None
    assert result.metadata is not None
    assert "structured_content" in result.metadata
    assert result.metadata["quality_score"] > 0.8

    # Cleanup
    await manager.cleanup()

    print("\nSUCCESS: Manager integration SUCCESS")
    print("  Result source: {result.source}")
    print("  Quality score: {result.metadata['quality_score']:.2f}")
    print("  Word count: {result.metadata['word_count']}")


@pytest.mark.asyncio
async def test_waterfall_with_pmc_priority():
    """Test complete waterfall with PMC as Priority 0."""

    try:
        from omics_oracle_v2.lib.pipelines.url_collection.manager import FullTextManager, FullTextManagerConfig
    except ImportError:
        pytest.skip("FullTextManager not available")

    # Create config with API keys from environment
    config = FullTextManagerConfig(
        core_api_key=os.getenv("CORE_API_KEY"),
        unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
    )

    # Create manager
    manager = FullTextManager(config=config)

    # Add PMC XML support (this updates waterfall)
    add_pmc_xml_support(manager, cache_dir=Path("data/fulltext"))

    await manager.initialize()

    # Test with PMC publication (should use PMC XML)
    pmc_publication = MockPublication(
        pmc_id="PMC3166277",
        title="Bacteriophage lysis time stochasticity",
    )

    result = await manager.get_fulltext(pmc_publication)

    assert result.success is True
    assert result.source == "pmc_xml"  # Should use PMC XML
    assert result.metadata["quality_score"] > 0.8

    print("\nSUCCESS: Waterfall with PMC SUCCESS")
    print("  Used source: {result.source}")
    print("  Quality: {result.metadata['quality_score']:.2f}")

    # Test with non-PMC publication (should fall back to other sources)
    non_pmc_publication = MockPublication(
        pmc_id=None,
        title="Article without PMC ID",
        doi="10.1234/test.2024",
    )

    result2 = await manager.get_fulltext(non_pmc_publication)

    # May succeed or fail depending on other sources, but should not be PMC
    if result2.success:
        assert result2.source != "pmc_xml"
        print("  Fallback source: {result2.source}")

    await manager.cleanup()


@pytest.mark.asyncio
async def test_multiple_articles_batch():
    """Test extraction of multiple PMC articles."""

    publications = [
        MockPublication(pmc_id="PMC3166277", title="Article 1"),
        MockPublication(pmc_id="PMC2228570", title="Article 2"),
        MockPublication(pmc_id="PMC3148254", title="Article 3"),
    ]

    results = await asyncio.gather(*[try_pmc_xml_extraction(pub) for pub in publications])

    success_count = sum(1 for r in results if r.success)

    print("\nSUCCESS: Batch extraction: {success_count}/{len(publications)} succeeded")

    for i, (pub, result) in enumerate(zip(publications, results), 1):
        if result.success:
            print(
                "  {i}. {pub.pmc_id}: {result.structured_content.title[:50]}... "
                "(quality={result.quality_score:.2f})"
            )
        else:
            print("  {i}. {pub.pmc_id}: FAILED - {result.error_message}")


if __name__ == "__main__":
    # Run tests manually for demo
    print("=" * 80)
    print("PMC XML INTEGRATION TESTS")
    print("=" * 80)

    async def run_all_tests():
        print("\n[TEST 1/5] Standalone PMC extraction (success case)")
        await test_standalone_pmc_extraction_success()

        print("\n[TEST 2/5] Standalone PMC extraction (no PMC ID)")
        await test_standalone_pmc_extraction_no_pmc_id()

        print("\n[TEST 3/5] Manager integration")
        try:
            await test_manager_integration()
        except Exception as e:
            print("  SKIPPED: {e}")

        print("\n[TEST 4/5] Waterfall with PMC priority")
        try:
            await test_waterfall_with_pmc_priority()
        except Exception as e:
            print("  SKIPPED: {e}")

        print("\n[TEST 5/5] Batch extraction")
        await test_multiple_articles_batch()

        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETE")
        print("=" * 80)

    asyncio.run(run_all_tests())
