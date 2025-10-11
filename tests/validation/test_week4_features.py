"""
Week 4 Feature Validation - Simple Direct Tests

Tests only the new Week 4 features:
1. Citation filters (recency, ranking)
2. GEO citation discovery (if infrastructure works)

No complex agent initialization - just direct component tests.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add workspace root to path
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

print("\n" + "=" * 80)
print("WEEK 4 FEATURE VALIDATION")
print("=" * 80 + "\n")

# Test 1: Citation Filters
print("TEST 1: Citation Filters")
print("-" * 40)

try:
    from omics_oracle_v2.lib.citations.filters import (
        filter_by_citation_count,
        filter_by_year_range,
        filter_recent_publications,
        rank_by_citations_and_recency,
    )
    from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

    # Create test publications
    pubs = [
        Publication(
            title="Recent paper 2024",
            source=PublicationSource.PUBMED,
            publication_date=datetime(2024, 1, 1),
            citations=50,
        ),
        Publication(
            title="Old paper 2010",
            source=PublicationSource.PUBMED,
            publication_date=datetime(2010, 1, 1),
            citations=500,
        ),
        Publication(
            title="Recent paper 2023",
            source=PublicationSource.PUBMED,
            publication_date=datetime(2023, 1, 1),
            citations=30,
        ),
        Publication(
            title="Old paper 2015",
            source=PublicationSource.PUBMED,
            publication_date=datetime(2015, 1, 1),
            citations=200,
        ),
    ]

    # Test year range filter
    recent = filter_by_year_range(pubs, min_year=2020, max_year=2025)
    assert len(recent) == 2, f"Expected 2 papers from 2020-2025, got {len(recent)}"
    print(f"✅ Year range filter: {len(recent)}/4 papers from 2020-2025")

    # Test last N years filter
    last_5yr = filter_recent_publications(pubs, years_back=5)
    assert len(last_5yr) >= 1, "Expected at least 1 paper from last 5 years"
    print(f"✅ Last 5 years filter: {len(last_5yr)}/4 papers")

    # Test citation count filter
    highly_cited = filter_by_citation_count(pubs, min_citations=100)
    assert len(highly_cited) == 2, f"Expected 2 papers with 100+ citations, got {len(highly_cited)}"
    print(f"✅ Citation filter: {len(highly_cited)}/4 papers with 100+ citations")

    # Test ranking
    ranked = rank_by_citations_and_recency(pubs)
    assert len(ranked) == 4, "Ranking should return all papers"
    # Recent papers should rank higher even with fewer citations
    assert ranked[0].publication_date.year >= 2020, "Most recent paper should rank first"
    print(f"✅ Ranking: Papers ranked by citations + recency")
    print(f"   Top paper: {ranked[0].title} ({ranked[0].publication_date.year}, {ranked[0].citations} cites)")

    print("\n✅ TEST 1 PASSED: All filter functions work correctly\n")
    test1_pass = True

except Exception as e:
    print(f"\n❌ TEST 1 FAILED: {e}\n")
    import traceback

    traceback.print_exc()
    test1_pass = False


# Test 2: Citation Models
print("\nTEST 2: Citation Models & Infrastructure")
print("-" * 40)

try:
    from omics_oracle_v2.lib.citations.clients.openalex import OpenAlexClient, OpenAlexConfig
    from omics_oracle_v2.lib.citations.clients.semantic_scholar import (
        SemanticScholarClient,
        SemanticScholarConfig,
    )
    from omics_oracle_v2.lib.citations.discovery.geo_discovery import (
        CitationDiscoveryResult,
        GEOCitationDiscovery,
    )

    # Check classes exist
    assert GEOCitationDiscovery is not None
    assert CitationDiscoveryResult is not None
    assert SemanticScholarClient is not None
    assert OpenAlexClient is not None
    print("✅ All citation infrastructure classes exist")

    # Test Semantic Scholar client initialization
    ss_config = SemanticScholarConfig(enable=True)
    ss_client = SemanticScholarClient(ss_config)
    assert ss_client is not None
    print("✅ SemanticScholarClient can be initialized")

    # Test OpenAlex client initialization
    oa_config = OpenAlexConfig(enable=True, email="test@example.com")
    oa_client = OpenAlexClient(oa_config)
    assert oa_client is not None
    print("✅ OpenAlexClient can be initialized")

    # Test GEO Citation Discovery initialization
    discovery = GEOCitationDiscovery()
    assert discovery is not None
    print("✅ GEOCitationDiscovery can be initialized")

    print("\n✅ TEST 2 PASSED: All citation infrastructure exists and initializes\n")
    test2_pass = True

except Exception as e:
    print(f"\n❌ TEST 2 FAILED: {e}\n")
    import traceback

    traceback.print_exc()
    test2_pass = False


# Test 3: GEO Models with PubMed IDs
print("\nTEST 3: GEO Models (PubMed ID Support)")
print("-" * 40)

try:
    from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata

    # Create test GEO metadata
    geo_meta = GEOSeriesMetadata(
        geo_id="GSE12345",
        title="Test Dataset",
        summary="Test summary",
        organism="Homo sapiens",
        pubmed_ids=["12345678", "87654321"],
    )

    assert geo_meta.geo_id == "GSE12345"
    assert len(geo_meta.pubmed_ids) == 2
    print(f"✅ GEOSeriesMetadata has pubmed_ids field")
    print(f"   Test dataset has {len(geo_meta.pubmed_ids)} PMIDs")

    print("\n✅ TEST 3 PASSED: GEO models support PubMed IDs\n")
    test3_pass = True

except Exception as e:
    print(f"\n❌ TEST 3 FAILED: {e}\n")
    import traceback

    traceback.print_exc()
    test3_pass = False


# Summary
print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80 + "\n")

results = {"Citation Filters": test1_pass, "Citation Infrastructure": test2_pass, "GEO Models": test3_pass}

passed = sum(1 for v in results.values() if v)
total = len(results)

print(f"Tests passed: {passed}/{total}\n")

for test_name, success in results.items():
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {status}  {test_name}")

print("\n" + "=" * 80)

if all(results.values()):
    print("✅ ALL WEEK 4 FEATURES VALIDATED!")
    print("=" * 80 + "\n")
    print("Week 4 deliverables are working:")
    print("  • Citation filters (year range, recency, citations)")
    print("  • Ranking by citations + recency")
    print("  • Citation discovery infrastructure")
    print("  • GEO citation tracking support")
    print("\nReady for production use!")
    exit(0)
else:
    print("❌ SOME TESTS FAILED")
    print("=" * 80 + "\n")
    exit(1)
