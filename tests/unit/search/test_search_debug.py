#!/usr/bin/env python
"""
Quick test script to debug search issues.
"""

import sys

sys.path.insert(0, "/Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle")

from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline


def test_search(query: str):
    """Test search with given query."""
    print(f"\n{'='*60}")
    print(f"Testing search: '{query}'")
    print(f"{'='*60}\n")

    # Create config
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_scholar=True,
        enable_citations=False,
        max_total_results=10,
    )

    print(f"Config:")
    print(f"  - PubMed: {config.enable_pubmed}")
    print(f"  - Scholar: {config.enable_scholar}")
    print(f"  - Max results: {config.max_total_results}")
    print()

    # Create pipeline
    pipeline = PublicationSearchPipeline(config)

    # Execute search
    print("Executing search...")
    result = pipeline.search(query=query, max_results=10)

    # Display results
    print(f"\nResults:")
    print(f"  - Query: {result.query}")
    print(f"  - Publications found: {len(result.publications)}")
    print(f"  - Total found (before ranking): {result.total_found}")
    print(f"  - Sources used: {result.sources_used}")
    print(f"  - Search time: {result.search_time_ms:.2f}ms")
    print()

    if result.publications:
        print(f"First 3 results:")
        for i, pub in enumerate(result.publications[:3], 1):
            print(f"\n  {i}. {pub.title}")
            print(f"     Score: {pub.relevance_score}")
            print(f"     Source: {pub.source}")
    else:
        print("⚠️ No publications returned!")
        print(f"\nMetadata: {result.metadata}")

    print(f"\n{'='*60}\n")

    return result


if __name__ == "__main__":
    # Test with the user's query
    test_search("JOint profiling of HiC and DNA methylation")

    # Test with a simpler query
    test_search("cancer")
