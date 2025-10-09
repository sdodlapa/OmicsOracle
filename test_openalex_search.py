#!/usr/bin/env python3
"""
Test OpenAlex search integration in pipeline.

This verifies that OpenAlex is now being used for publication search,
not just for citation analysis.
"""

import logging

from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_openalex_search_integration():
    """Test that OpenAlex is used in search workflow."""

    print("=" * 80)
    print("TEST: OpenAlex Search Integration")
    print("=" * 80)

    # Create config with OpenAlex enabled
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_openalex=True,  # Enable for search
        enable_scholar=False,  # Disabled (blocked)
        enable_citations=False,  # Not testing citations now
        enable_pdf_download=False,
        enable_fulltext=False,
        enable_cache=False,  # Disable cache for fresh results
    )

    print("\nConfiguration:")
    print(f"  PubMed: {config.enable_pubmed}")
    print(f"  OpenAlex: {config.enable_openalex}")
    print(f"  Scholar: {config.enable_scholar}")

    # Create pipeline
    print("\nInitializing pipeline...")
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()

    print("\nComponents initialized:")
    print(f"  PubMed client: {pipeline.pubmed_client is not None}")
    print(f"  OpenAlex client: {pipeline.openalex_client is not None}")
    print(f"  Scholar client: {pipeline.scholar_client is not None}")

    # Test search
    query = "CRISPR gene editing"
    print(f"\n{'='*80}")
    print(f"Searching: '{query}'")
    print(f"{'='*80}")

    result = pipeline.search(query, max_results=10)

    print("\nResults:")
    print(f"  Total found: {result.total_found}")
    print(f"  Publications returned: {len(result.publications)}")
    print(f"  Sources used: {', '.join(result.sources_used)}")
    print(f"  Search time: {result.search_time_ms:.1f}ms")

    # Check sources
    print("\nSource breakdown:")
    source_counts = {}
    for ranked_pub in result.publications:
        source = ranked_pub.publication.source.value
        source_counts[source] = source_counts.get(source, 0) + 1

    for source, count in source_counts.items():
        print(f"  {source}: {count} publications")

    # Verify OpenAlex was used
    if "openalex" in result.sources_used:
        print("\n✅ SUCCESS: OpenAlex is being used for search!")
    else:
        print("\n❌ FAILURE: OpenAlex was NOT used for search")
        return False

    # Show sample results
    print("\nSample results:")
    for i, ranked_pub in enumerate(result.publications[:3], 1):
        pub = ranked_pub.publication
        print(f"\n{i}. {pub.title}")
        print(f"   Source: {pub.source.value}")
        print(f"   Relevance Score: {ranked_pub.relevance_score:.3f}")
        if pub.authors:
            print(f"   Authors: {', '.join(pub.authors[:2])} et al.")
        if pub.citations:
            print(f"   Citations: {pub.citations}")

    # Check metadata
    print("\nMetadata:")
    print(f"  OpenAlex enabled in config: {result.metadata['config']['openalex_enabled']}")

    pipeline.cleanup()

    print("\n" + "=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = test_openalex_search_integration()
        exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        exit(1)
