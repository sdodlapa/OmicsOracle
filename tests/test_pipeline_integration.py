"""Test pipeline integration with FullTextManager."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline


def test_pipeline_integration():
    """Test that FullTextManager is properly integrated into pipeline."""
    print("Testing Pipeline Integration with FullTextManager...")
    print()

    # Create config with full-text retrieval enabled
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_openalex=False,  # Disable to speed up test
        enable_scholar=False,
        enable_citations=False,
        enable_pdf_download=False,
        enable_fulltext=False,
        enable_fulltext_retrieval=True,  # Enable OA full-text retrieval
        enable_institutional_access=False,
        enable_cache=False,
    )

    # Initialize pipeline
    print("1. Initializing pipeline with FullTextManager...")
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()

    # Check FullTextManager is initialized
    if pipeline.fulltext_manager:
        print("   [SUCCESS] FullTextManager initialized")
    else:
        print("   [FAILED] FullTextManager not initialized")
        return
    print()

    # Run a simple search
    print("2. Running search for 'CRISPR gene editing'...")
    result = pipeline.search("CRISPR gene editing", max_results=5)

    print(f"   Found {len(result.publications)} publications")
    print()

    # Check if full-text URLs were added
    print("3. Checking full-text URL enrichment...")
    publications_with_fulltext = [
        p for p in result.publications if p.publication.metadata.get("fulltext_url")
    ]

    print(f"   {len(publications_with_fulltext)}/{len(result.publications)} publications have full-text URLs")

    if publications_with_fulltext:
        print()
        print("   Sample publications with full-text:")
        for i, pub_result in enumerate(publications_with_fulltext[:3], 1):
            pub = pub_result.publication
            print(f"   [{i}] {pub.title[:60]}...")
            print(f"       URL: {pub.metadata.get('fulltext_url')}")
            print(f"       Source: {pub.metadata.get('fulltext_source')}")
            print()

    # Show FullTextManager statistics
    print("4. FullTextManager Statistics:")
    stats = pipeline.fulltext_manager.get_statistics()
    print(f"   Total attempts: {stats['total_attempts']}")
    print(f"   Successes: {stats['successes']}")
    print(f"   Failures: {stats['failures']}")
    print(f"   Success rate: {stats['success_rate']}")
    print(f"   By source: {stats['by_source']}")
    print()

    # Cleanup
    print("5. Cleaning up...")
    pipeline.cleanup()
    print("   [SUCCESS] Pipeline cleaned up")
    print()

    print("Pipeline integration test complete!")


if __name__ == "__main__":
    test_pipeline_integration()
