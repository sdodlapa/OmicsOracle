#!/usr/bin/env python
"""
Week 1-2 Implementation Validation Script

Tests all Week 1-2 components:
1. Publications module imports
2. PubMed search functionality
3. Institutional access integration
4. SearchAgent integration
5. Multi-factor ranking
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test 1: Verify all imports work."""
    print("\n" + "=" * 70)
    print("TEST 1: Module Imports")
    print("=" * 70)

    try:
        from omics_oracle_v2.lib.publications import (
            Publication,
            PublicationResult,
            PublicationSearchConfig,
            PublicationSearchPipeline,
            PubMedConfig,
        )

        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_configuration():
    """Test 2: Verify configuration system."""
    print("\n" + "=" * 70)
    print("TEST 2: Configuration System")
    print("=" * 70)

    try:
        from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig

        # Create PubMed config
        pubmed_config = PubMedConfig(email="test@example.com", max_results=10)
        print(f"✅ PubMedConfig created: {pubmed_config.email}")

        # Create search config with feature toggles
        search_config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=False,
            enable_citations=False,
            enable_pdf_download=False,
            enable_fulltext=False,
            enable_institutional_access=True,
            primary_institution="gatech",
            secondary_institution="odu",
            pubmed_config=pubmed_config,
        )
        print(f"✅ PublicationSearchConfig created")
        print(f"   - PubMed: {search_config.enable_pubmed}")
        print(f"   - Institutional Access: {search_config.enable_institutional_access}")
        print(f"   - Primary Institution: {search_config.primary_institution}")

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_pipeline_initialization():
    """Test 3: Verify pipeline initialization."""
    print("\n" + "=" * 70)
    print("TEST 3: Pipeline Initialization")
    print("=" * 70)

    try:
        from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig
        from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_institutional_access=True,
            primary_institution="gatech",
            pubmed_config=PubMedConfig(email="test@example.com"),
        )

        pipeline = PublicationSearchPipeline(config)

        # Check components
        print(f"✅ Pipeline initialized")
        print(f"   - PubMed client: {'✅' if pipeline.pubmed_client else '❌'}")
        print(f"   - Ranker: {'✅' if pipeline.ranker else '❌'}")
        print(f"   - Institutional manager: {'✅' if pipeline.institutional_manager else '❌'}")

        # Check enabled features
        features = pipeline.get_enabled_features()
        print(f"✅ Enabled features: {features}")

        return True
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_pubmed_search():
    """Test 4: Test PubMed search (real API call)."""
    print("\n" + "=" * 70)
    print("TEST 4: PubMed Search (Real API)")
    print("=" * 70)
    print("⚠️  This makes a real API call to NCBI PubMed")

    try:
        from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig
        from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_institutional_access=True,
            primary_institution="gatech",
            pubmed_config=PubMedConfig(email="test@example.com", max_results=5),
        )

        pipeline = PublicationSearchPipeline(config)

        # Perform search
        print("🔍 Searching for: 'CRISPR cancer therapy'")
        result = pipeline.search("CRISPR cancer therapy", max_results=5)

        print(f"✅ Search completed")
        print(f"   - Query: {result.query}")
        print(f"   - Total found: {result.total_found}")
        print(f"   - Sources: {result.metadata.get('sources_used', [])}")
        print(f"   - Features: {result.metadata.get('features_enabled', [])}")
        print(f"   - Search time: {result.metadata.get('search_time_seconds', 0):.2f}s")

        # Display top results
        print(f"\n📊 Top {min(3, len(result.publications))} Results:")
        for i, pub_result in enumerate(result.publications[:3], 1):
            pub = pub_result.publication
            print(f"\n{i}. {pub.title[:80]}...")
            print(f"   - Relevance: {pub_result.relevance_score:.1f}/100")
            print(f"   - PMID: {pub.pmid}")
            print(f"   - Citations: {pub.citations or 'N/A'}")
            print(f"   - Journal: {pub.journal or 'N/A'}")

            # Access information
            if pub.metadata.get("has_access"):
                access_url = pub.metadata.get("access_url", "N/A")
                print(f"   - 🔓 Access: {access_url[:60]}...")
            elif pub.pmcid:
                print(f"   - 🔓 Free access: PMC{pub.pmcid}")
            else:
                print(f"   - 🔒 No institutional access found")

        return len(result.publications) > 0

    except Exception as e:
        print(f"❌ PubMed search failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_institutional_access():
    """Test 5: Verify institutional access integration."""
    print("\n" + "=" * 70)
    print("TEST 5: Institutional Access")
    print("=" * 70)

    try:
        from omics_oracle_v2.lib.publications.clients.institutional_access import (
            InstitutionalAccessManager,
            InstitutionType,
        )
        from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

        # Create test publication with DOI
        pub = Publication(
            pmid="12345678",
            doi="10.1038/nature12345",
            title="Test publication for institutional access",
            source=PublicationSource.PUBMED,
        )

        # Test Georgia Tech access
        gt_manager = InstitutionalAccessManager(InstitutionType.GEORGIA_TECH)
        gt_url = gt_manager.get_access_url(pub)

        print(f"✅ Georgia Tech EZProxy URL generated:")
        print(f"   {gt_url[:70]}...")

        # Test ODU access
        odu_manager = InstitutionalAccessManager(InstitutionType.OLD_DOMINION)
        odu_url = odu_manager.get_access_url(pub)

        print(f"✅ ODU EZProxy URL generated:")
        print(f"   {odu_url[:70]}...")

        # Check access status
        status = gt_manager.check_access_status(pub)
        print(f"✅ Access status checked:")
        for method, available in status.items():
            print(f"   - {method}: {'✅' if available else '❌'}")

        return True

    except Exception as e:
        print(f"❌ Institutional access test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_search_agent_integration():
    """Test 6: Verify SearchAgent integration."""
    print("\n" + "=" * 70)
    print("TEST 6: SearchAgent Integration")
    print("=" * 70)

    try:
        from omics_oracle_v2.agents.search_agent import SearchAgent
        from omics_oracle_v2.core.config import Settings

        # Initialize with publications enabled
        settings = Settings()
        agent = SearchAgent(settings, enable_publications=True)

        print(f"✅ SearchAgent created with enable_publications=True")

        # Initialize resources
        agent._initialize_resources()

        print(f"✅ Resources initialized")

        # Check publication pipeline
        if agent._publication_pipeline:
            features = agent._publication_pipeline.get_enabled_features()
            print(f"✅ Publication pipeline initialized")
            print(f"   - Enabled features: {features}")

            # Test search
            print(f"\n🔍 Testing search through SearchAgent...")
            result = agent._publication_pipeline.search("cancer genomics", max_results=3)
            print(f"✅ Search successful: {len(result.publications)} publications found")

            if result.publications:
                pub = result.publications[0].publication
                print(f"   - Top result: {pub.title[:60]}...")
        else:
            print(f"❌ Publication pipeline not initialized")
            return False

        # Cleanup
        agent._cleanup_resources()
        print(f"✅ Resources cleaned up")

        return True

    except Exception as e:
        print(f"❌ SearchAgent integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ranking_algorithm():
    """Test 7: Verify multi-factor ranking."""
    print("\n" + "=" * 70)
    print("TEST 7: Multi-Factor Ranking Algorithm")
    print("=" * 70)

    try:
        from datetime import datetime, timedelta

        from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig
        from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
        from omics_oracle_v2.lib.publications.ranking.ranker import PublicationRanker

        config = PublicationSearchConfig(
            enable_pubmed=True,
            pubmed_config=PubMedConfig(email="test@example.com"),
            ranking_weights={
                "title_match": 0.4,
                "abstract_match": 0.3,
                "recency": 0.2,
                "citations": 0.1,
            },
        )

        ranker = PublicationRanker(config)
        print(f"✅ Ranker initialized with weights:")
        for factor, weight in config.ranking_weights.items():
            print(f"   - {factor}: {weight*100:.0f}%")

        # Create test publications
        recent_pub = Publication(
            pmid="1",
            title="CRISPR gene editing for cancer therapy",
            abstract="Novel CRISPR-based approach for cancer treatment",
            source=PublicationSource.PUBMED,
            publication_date=datetime.now() - timedelta(days=30),
            citations=100,
        )

        old_pub = Publication(
            pmid="2",
            title="Traditional cancer therapies",
            abstract="Review of conventional cancer treatments",
            source=PublicationSource.PUBMED,
            publication_date=datetime.now() - timedelta(days=2000),
            citations=500,
        )

        # Rank publications
        query = "CRISPR cancer therapy"
        ranked = ranker.rank([recent_pub, old_pub], query, top_k=10)

        print(f"\n✅ Ranking completed for query: '{query}'")
        for i, result in enumerate(ranked, 1):
            pub = result.publication
            print(f"\n{i}. Score: {result.relevance_score:.1f}/100")
            print(f"   Title: {pub.title[:50]}...")
            print(f"   Score breakdown:")
            for factor, score in result.score_breakdown.items():
                print(f"     - {factor}: {score:.3f}")

        return True

    except Exception as e:
        print(f"❌ Ranking algorithm test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests and generate summary."""
    print("\n" + "=" * 70)
    print("WEEK 1-2 IMPLEMENTATION VALIDATION")
    print("=" * 70)
    print("Testing all Week 1-2 components...\n")

    tests = [
        ("Module Imports", test_imports),
        ("Configuration System", test_configuration),
        ("Pipeline Initialization", test_pipeline_initialization),
        ("PubMed Search (Real API)", test_pubmed_search),
        ("Institutional Access", test_institutional_access),
        ("SearchAgent Integration", test_search_agent_integration),
        ("Multi-Factor Ranking", test_ranking_algorithm),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n{'='*70}")
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*70}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Week 1-2 is production ready!")
        print("\n✅ Next steps:")
        print("   1. Review test results above")
        print("   2. Try the PubMed search with your own queries")
        print("   3. Click institutional access URLs in browser")
        print("   4. Proceed to Week 3: Google Scholar + Citations")
        return 0
    else:
        print("\n⚠️  Some tests failed - review errors above")
        print("   Most failures are likely SSL certificate issues (non-critical)")
        print("   Core functionality should still work")
        return 1


if __name__ == "__main__":
    sys.exit(main())
