#!/usr/bin/env python
"""
Test Enhanced Google Scholar Client

This script tests the new features:
- Citation enrichment
- Cited-by paper access
- Author profile information
- Retry logic
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.publications.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.publications.config import GoogleScholarConfig
from omics_oracle_v2.lib.publications.models import Publication


def test_search_with_citations():
    """Test basic search with citation counts."""
    print("\n" + "=" * 60)
    print("TEST 1: Search with Citation Counts")
    print("=" * 60)

    config = GoogleScholarConfig(
        enable=True,
        rate_limit_seconds=5.0,  # Be gentle with Google
    )
    client = GoogleScholarClient(config)

    query = "CRISPR-Cas9"
    print(f"\nSearching for: '{query}'")

    try:
        results = client.search(query, max_results=3)

        print(f"\n✅ Found {len(results)} publications:")
        for i, pub in enumerate(results, 1):
            print(f"\n{i}. {pub.title}")
            print(f"   Citations: {pub.citations}")
            print(f"   Year: {pub.publication_date.year if pub.publication_date else 'N/A'}")
            print(f"   Authors: {', '.join(pub.authors[:3]) if pub.authors else 'N/A'}")
            print(f"   Has citedby_url: {'citedby_url' in pub.metadata}")

        return results[0] if results else None

    except Exception as e:
        print(f"\n❌ Search failed: {e}")
        return None


def test_citation_enrichment():
    """Test enriching a publication with citations."""
    print("\n" + "=" * 60)
    print("TEST 2: Citation Enrichment")
    print("=" * 60)

    # Create a sample publication without citations
    pub = Publication(
        title="CRISPR-Cas9 genome editing",
        abstract="A revolutionary genome editing technology",
        authors=["Jennifer Doudna", "Emmanuelle Charpentier"],
        journal="Science",
        citations=0,  # No citations initially
    )

    print(f"\nOriginal publication:")
    print(f"  Title: {pub.title}")
    print(f"  Citations: {pub.citations}")

    config = GoogleScholarConfig(enable=True, rate_limit_seconds=5.0)
    client = GoogleScholarClient(config)

    try:
        enriched = client.enrich_with_citations(pub)

        print(f"\nAfter enrichment:")
        print(f"  Title: {enriched.title}")
        print(f"  Citations: {enriched.citations}")
        print(f"  Scholar ID: {enriched.metadata.get('scholar_id', 'N/A')}")
        print(f"  Scholar URL: {enriched.metadata.get('scholar_url', 'N/A')}")

        if enriched.citations > 0:
            print("\n✅ Citation enrichment successful!")
        else:
            print("\n⚠️  No citations found (may not match exactly)")

    except Exception as e:
        print(f"\n❌ Enrichment failed: {e}")


def test_cited_by_papers(publication):
    """Test getting papers that cite a given work."""
    if not publication:
        print("\n⚠️  Skipping cited-by test (no publication provided)")
        return

    print("\n" + "=" * 60)
    print("TEST 3: Cited-By Papers")
    print("=" * 60)

    print(f"\nGetting papers that cite:")
    print(f"  '{publication.title}'")
    print(f"  (has {publication.citations} citations)")

    config = GoogleScholarConfig(enable=True, rate_limit_seconds=5.0)
    client = GoogleScholarClient(config)

    try:
        citing_papers = client.get_cited_by_papers(publication, max_papers=5)

        print(f"\n✅ Found {len(citing_papers)} citing papers:")
        for i, citing_pub in enumerate(citing_papers, 1):
            print(f"\n{i}. {citing_pub.title}")
            print(f"   Year: {citing_pub.publication_date.year if citing_pub.publication_date else 'N/A'}")
            print(f"   Citations: {citing_pub.citations}")

    except Exception as e:
        print(f"\n❌ Cited-by retrieval failed: {e}")


def test_author_info():
    """Test getting author profile information."""
    print("\n" + "=" * 60)
    print("TEST 4: Author Profile Information")
    print("=" * 60)

    author_name = "Jennifer Doudna"
    print(f"\nGetting profile for: {author_name}")

    config = GoogleScholarConfig(enable=True, rate_limit_seconds=5.0)
    client = GoogleScholarClient(config)

    try:
        info = client.get_author_info(author_name)

        if info:
            print(f"\n✅ Author profile found:")
            print(f"  Name: {info.get('name', 'N/A')}")
            print(f"  Affiliation: {info.get('affiliation', 'N/A')}")
            print(f"  H-index: {info.get('hindex', 'N/A')}")
            print(f"  Total Citations: {info.get('citedby', 'N/A')}")
            print(f"  i10-index: {info.get('i10index', 'N/A')}")
            interests = info.get("interests", [])
            if interests:
                print(f"  Interests: {', '.join(interests[:5])}")
        else:
            print("\n⚠️  No author profile found")

    except Exception as e:
        print(f"\n❌ Author info retrieval failed: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ENHANCED GOOGLE SCHOLAR CLIENT - TEST SUITE")
    print("=" * 60)
    print("\n⚠️  Note: These tests make real API calls to Google Scholar")
    print("⏱️  Tests may take 30-60 seconds due to rate limiting")
    print("🚫 May be blocked if run too frequently")

    # Test 1: Search with citations
    top_publication = test_search_with_citations()

    # Test 2: Citation enrichment
    test_citation_enrichment()

    # Test 3: Cited-by papers (uses result from Test 1)
    if top_publication:
        test_cited_by_papers(top_publication)

    # Test 4: Author information
    test_author_info()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
    print("\nℹ️  If tests failed, Google Scholar may have blocked requests.")
    print("   Wait 30-60 minutes and try again, or use a proxy.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
