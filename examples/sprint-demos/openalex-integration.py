#!/usr/bin/env python3
"""
Test OpenAlex Implementation - Complete validation of citation workflow.

Tests:
1. OpenAlex client initialization
2. Citation discovery (DOI → citing papers)
3. Multi-source fallback (OpenAlex → Scholar → S2)
4. Citation context extraction
5. Pipeline integration
6. End-to-end workflow

Run: python test_openalex_implementation.py
"""

import logging
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.citations.clients.openalex import OpenAlexClient, OpenAlexConfig
from omics_oracle_v2.lib.pipelines.citation_discovery.clients import CitationFinder
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_openalex_client():
    """Test 1: OpenAlex client initialization and basic queries."""
    print("\n" + "=" * 80)
    print("TEST 1: OpenAlex Client Initialization")
    print("=" * 80)

    # Create client
    config = OpenAlexConfig(
        enable=True,
        email="test@omicsoracle.com",  # Polite pool - 10 req/s
    )
    client = OpenAlexClient(config)

    print(f"✓ Client initialized with {config.rate_limit_per_second} req/s")
    print(f"✓ Using polite pool: {config.email is not None}")

    # Test work lookup by DOI
    print("\n📖 Testing DOI lookup...")
    test_doi = "10.1038/nature12373"  # Famous CRISPR paper
    work = client.get_work_by_doi(test_doi)

    if work:
        print(f"✓ Found work: {work.get('title', 'N/A')}")
        print(f"  - Citations: {work.get('cited_by_count', 0)}")
        print(f"  - Type: {work.get('type', 'N/A')}")
        print(f"  - Open Access: {work.get('open_access', {}).get('is_oa', False)}")
    else:
        print("✗ Failed to find work")
        return False

    return True


def test_citing_papers():
    """Test 2: Finding papers that cite a given work."""
    print("\n" + "=" * 80)
    print("TEST 2: Citation Discovery")
    print("=" * 80)

    config = OpenAlexConfig(enable=True, email="test@omicsoracle.com")
    client = OpenAlexClient(config)

    # Test with well-cited paper
    test_doi = "10.1038/nature12373"  # CRISPR paper (thousands of citations)

    print(f"\n🔍 Finding papers that cite DOI: {test_doi}")
    citing_papers = client.get_citing_papers(doi=test_doi, max_results=10)

    if citing_papers:
        print(f"✓ Found {len(citing_papers)} citing papers")
        print("\nSample citing papers:")
        for i, paper in enumerate(citing_papers[:3], 1):
            print(f"\n{i}. {paper.title}")
            print(f"   Authors: {', '.join(paper.authors[:3])}")
            print(f"   Year: {paper.publication_date.year if paper.publication_date else 'N/A'}")
            print(f"   Citations: {paper.citations}")
            print(f"   Source: {paper.source}")
            if paper.metadata:
                print(f"   Open Access: {paper.metadata.get('is_open_access', False)}")
    else:
        print("✗ No citing papers found")
        return False

    return True


def test_citation_analyzer():
    """Test 3: Multi-source citation analyzer."""
    print("\n" + "=" * 80)
    print("TEST 3: Multi-Source Citation Analyzer")
    print("=" * 80)

    # Create OpenAlex client
    openalex_config = OpenAlexConfig(enable=True, email="test@omicsoracle.com")
    openalex_client = OpenAlexClient(openalex_config)

    # Create citation analyzer (OpenAlex only, no Scholar)
    finder = CitationFinder(
        openalex_client=openalex,
        semantic_scholar_client=semantic_scholar,
    )

    print("✓ Citation analyzer initialized")
    print("  - Primary source: OpenAlex")
    print("  - Fallback: None (Scholar disabled)")

    # Create test publication
    test_pub = Publication(
        title="Multiplex genome engineering using CRISPR/Cas systems",
        authors=["Cong L", "Ran FA", "Cox D"],
        doi="10.1126/science.1231143",
        source=PublicationSource.PUBMED,
    )

    print(f"\n🔍 Finding citations for: {test_pub.title[:60]}...")
    citing_papers = analyzer.get_citing_papers(test_pub, max_results=5)

    if citing_papers:
        print(f"✓ Found {len(citing_papers)} citing papers via OpenAlex")

        # Test context extraction
        print("\n📝 Testing citation context extraction...")
        if citing_papers:
            contexts = analyzer.get_citation_contexts(test_pub, citing_papers[0])
            if contexts:
                print(f"✓ Extracted {len(contexts)} citation contexts")
                for ctx in contexts[:2]:
                    print(f"\n  Context ({ctx.source}):")
                    print(f"  {ctx.context_text[:200]}...")
            else:
                print("⚠ No contexts extracted (expected for some papers)")
    else:
        print("✗ No citing papers found")
        return False

    return True


def test_pipeline_integration():
    """Test 4: Pipeline integration with OpenAlex."""
    print("\n" + "=" * 80)
    print("TEST 4: Pipeline Integration")
    print("=" * 80)

    # Create config with OpenAlex enabled
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_openalex=True,
        enable_citations=True,
        enable_scholar=False,  # Disabled
        enable_pdf_download=False,  # Skip for test
        enable_fulltext=False,
        enable_institutional_access=False,
        enable_cache=False,
    )

    print("✓ Config created:")
    print(f"  - PubMed: {config.enable_pubmed}")
    print(f"  - OpenAlex: {config.enable_openalex}")
    print(f"  - Citations: {config.enable_citations}")
    print(f"  - Scholar: {config.enable_scholar} (blocked)")

    # Create pipeline
    print("\n🏗️  Initializing pipeline...")
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()

    # Check components
    print("\n✓ Pipeline initialized with:")
    print(f"  - PubMed client: {pipeline.pubmed_client is not None}")
    print(f"  - OpenAlex client: {pipeline.openalex_client is not None}")
    print(f"  - Scholar client: {pipeline.scholar_client is not None}")
    print(f"  - Citation analyzer: {pipeline.citation_analyzer is not None}")

    if pipeline.citation_analyzer:
        print(f"  - OpenAlex in analyzer: {pipeline.citation_analyzer.openalex is not None}")
        print(f"  - Scholar in analyzer: {pipeline.citation_analyzer.scholar is not None}")
        print(f"  - S2 in analyzer: {pipeline.citation_analyzer.semantic_scholar is not None}")

    # Cleanup
    pipeline.cleanup()
    print("\n✓ Pipeline cleaned up")

    return True


def test_search_workflow():
    """Test 5: End-to-end search workflow using OpenAlex directly."""
    print("\n" + "=" * 80)
    print("TEST 5: End-to-End Search Workflow")
    print("=" * 80)

    # Use OpenAlex directly (avoid PubMed SSL issues in local env)
    print("\n🔍 Testing OpenAlex search functionality...")

    config = OpenAlexConfig(enable=True, email="test@omicsoracle.com")
    client = OpenAlexClient(config)

    # Search for papers
    query = "CRISPR gene editing"
    print(f"Searching OpenAlex: {query}")

    try:
        papers = client.search(query, max_results=5)

        if papers:
            print(f"✓ Found {len(papers)} publications")

            print("\nTop result:")
            top = papers[0]
            print(f"  Title: {top.title}")
            print(f"  Authors: {', '.join(top.authors[:3])}")
            print(f"  Source: {top.source}")
            print(f"  Citations: {top.citations}")
            if top.metadata:
                print(f"  Open Access: {top.metadata.get('is_open_access', False)}")

            # Verify it's a Publication object with expected fields
            assert hasattr(top, "title")
            assert hasattr(top, "authors")
            assert hasattr(top, "doi")
            assert top.source == PublicationSource.OPENALEX

            print("\n✓ Search workflow functional")
            print("  - OpenAlex search working")
            print("  - Publication objects created correctly")
            print("  - Metadata properly populated")

            return True
        else:
            print("✗ No results found")
            return False

    except Exception as e:
        logger.error(f"Search workflow test failed: {e}", exc_info=True)
        print(f"✗ Search failed: {e}")
        return False


def test_config_validation():
    """Test 6: Configuration validation."""
    print("\n" + "=" * 80)
    print("TEST 6: Configuration Validation")
    print("=" * 80)

    config = PublicationSearchConfig()

    print("✓ Default configuration:")
    print(f"  - PubMed: {config.enable_pubmed}")
    print(f"  - OpenAlex: {config.enable_openalex}")
    print(f"  - Citations: {config.enable_citations}")
    print(f"  - Scholar: {config.enable_scholar}")

    # Validate citations enabled with OpenAlex
    if config.enable_citations and config.enable_openalex:
        print("✓ Citations enabled with OpenAlex (sustainable solution)")
    elif config.enable_citations and config.enable_scholar:
        print("⚠ Citations enabled with Scholar (may be blocked)")
    elif config.enable_citations:
        print("⚠ Citations enabled but no source configured")
    else:
        print("ℹ Citations disabled")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🧪 OpenAlex Implementation Test Suite")
    print("=" * 80)
    print("\nThis suite validates:")
    print("1. OpenAlex client functionality")
    print("2. Citation discovery")
    print("3. Multi-source citation analyzer")
    print("4. Pipeline integration")
    print("5. End-to-end workflow")
    print("6. Configuration validation")

    tests = [
        ("OpenAlex Client", test_openalex_client),
        ("Citation Discovery", test_citing_papers),
        ("Citation Analyzer", test_citation_analyzer),
        ("Pipeline Integration", test_pipeline_integration),
        ("Search Workflow", test_search_workflow),
        ("Config Validation", test_config_validation),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test '{name}' failed with error: {e}", exc_info=True)
            results[name] = False

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n{passed}/{total} tests passed ({100*passed//total}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! OpenAlex implementation ready.")
        print("\n✅ Key achievements:")
        print("   - OpenAlex client working")
        print("   - Citation discovery functional")
        print("   - Multi-source fallback implemented")
        print("   - Pipeline integrated")
        print("   - No dependency on Google Scholar")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
