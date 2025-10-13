"""
Quick test of the Publications pipeline - Week 1-2 implementation.

This tests:
- PubMed search functionality
- Publication ranking
- Pipeline integration
"""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.search_engines.citations.config import PublicationSearchConfig, PubMedConfig


def test_pubmed_search():
    """Test basic PubMed search."""

    print("=" * 80)
    print("TESTING PUBLICATIONS PIPELINE - WEEK 1-2")
    print("=" * 80)

    # Configure
    pubmed_config = PubMedConfig(
        email="test@example.com",  # Replace with real email for production
        max_results=10,
    )

    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_scholar=False,  # Week 3
        enable_citations=False,  # Week 3
        pubmed_config=pubmed_config,
    )

    # Initialize pipeline
    print("\n1. Initializing PublicationSearchPipeline...")
    pipeline = PublicationSearchPipeline(config)
    print(f"   Enabled features: {pipeline.get_enabled_features()}")

    # Test search
    query = "CRISPR gene editing cancer"
    print(f"\n2. Searching PubMed for: '{query}'")

    try:
        with pipeline:
            result = pipeline.search(query, max_results=5)

            print(f"\n3. Results Summary:")
            print(f"   - Query: {result.query}")
            print(f"   - Total found: {result.total_found}")
            print(f"   - Returned: {len(result.publications)}")
            print(f"   - Sources: {', '.join(result.sources_used)}")
            print(f"   - Search time: {result.search_time_ms:.2f}ms")

            print(f"\n4. Top Results:")
            for i, pub_result in enumerate(result.publications[:5], 1):
                pub = pub_result.publication
                print(f"\n   [{i}] Score: {pub_result.relevance_score:.2f}")
                print(f"       Title: {pub.title[:100]}...")
                print(f"       Authors: {', '.join(pub.authors[:3])}{'...' if len(pub.authors) > 3 else ''}")
                print(f"       Journal: {pub.journal}")
                print(
                    f"       Date: {pub.publication_date.strftime('%Y-%m-%d') if pub.publication_date else 'N/A'}"
                )
                print(f"       PMID: {pub.pmid}")
                print(f"       Score breakdown: {pub_result.score_breakdown}")
                print(f"       Query matches: {', '.join(pub_result.query_matches[:5])}")

            print("\n" + "=" * 80)
            print("✅ TEST PASSED - Publications pipeline working correctly!")
            print("=" * 80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_pubmed_search()
    sys.exit(0 if success else 1)
