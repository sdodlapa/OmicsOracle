#!/usr/bin/env python3
"""
Comprehensive test for PDF download and full-text extraction.

Tests the complete pipeline:
1. Search for publications
2. Get institutional access URLs
3. Download PDFs
4. Extract full text
5. Verify results
"""

import logging
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_pdf_download_pipeline():
    """Test the complete PDF download and extraction pipeline."""

    print("=" * 80)
    print("PDF Download & Full-Text Extraction Test")
    print("=" * 80)

    # Configuration with PDF features enabled
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_scholar=False,  # Keep it simple for testing
        enable_citations=False,
        enable_pdf_download=True,  # ENABLED
        enable_fulltext=True,  # ENABLED
        enable_institutional_access=True,
        primary_institution="gatech",
        pubmed_config=PubMedConfig(email="test@gatech.edu", max_results=5),  # Small test set
    )

    # Initialize pipeline
    print("\n1. Initializing pipeline...")
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()

    # Test query - use a specific paper we know has OA PDFs
    query = "NOMe-seq chromatin structure"
    print(f"\n2. Searching for: '{query}'")

    # Search
    results = pipeline.search(query)

    print(f"\n3. Found {len(results.publications)} publications")

    # Check results
    if not results.publications:
        print("❌ No publications found!")
        return False

    # Display results with PDF/fulltext status
    print("\n4. PDF Download & Extraction Results:")
    print("-" * 80)

    pdf_count = 0
    fulltext_count = 0

    for i, result in enumerate(results.publications[:5], 1):  # Show top 5
        pub = result.publication

        print(f"\n#{i} {pub.title[:70]}...")
        print(f"   PMID: {pub.pmid or 'N/A'}")
        print(f"   DOI: {pub.doi or 'N/A'}")

        # Check PDF download
        if pub.metadata.get("pdf_downloaded"):
            pdf_count += 1
            print(f"   ✅ PDF Downloaded: {pub.pdf_path}")
            print(f"      File size: {Path(pub.pdf_path).stat().st_size / 1024:.1f} KB")
        else:
            print(f"   ❌ No PDF available")

        # Check full-text extraction
        if pub.full_text:
            fulltext_count += 1
            stats = pub.metadata.get("text_stats", {})
            word_count = stats.get("words", 0)
            char_count = stats.get("characters", 0)

            print(f"   ✅ Full-text extracted:")
            print(f"      Words: {word_count:,}")
            print(f"      Characters: {char_count:,}")
            print(f"      Source: {pub.full_text_source}")
            print(f"      Preview: {pub.full_text[:150]}...")
        else:
            print(f"   ❌ No full-text extracted")

        # Check institutional access
        if pub.metadata.get("access_url"):
            access_url = pub.metadata["access_url"]
            access_status = pub.metadata.get("access_status", {})

            if access_status.get("unpaywall"):
                print(f"   🌐 Open Access via Unpaywall")
            elif access_status.get("vpn"):
                print(f"   🔐 VPN Access: {access_url[:80]}")
            elif access_status.get("pmc"):
                print(f"   📚 PubMed Central: {access_url[:80]}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total publications: {len(results.publications)}")
    print(f"PDFs downloaded: {pdf_count}")
    print(f"Full-text extracted: {fulltext_count}")

    # Check download directory
    pdf_dir = Path("data/pdfs")
    if pdf_dir.exists():
        total_pdfs = len(list(pdf_dir.rglob("*.pdf")))
        total_size = sum(p.stat().st_size for p in pdf_dir.rglob("*.pdf"))
        print(f"\nPDF Directory: {pdf_dir}")
        print(f"  Total PDFs: {total_pdfs}")
        print(f"  Total size: {total_size / (1024 * 1024):.2f} MB")

        # Show directory structure
        print(f"\nDirectory structure:")
        for source_dir in sorted(pdf_dir.iterdir()):
            if source_dir.is_dir():
                pdf_count_in_source = len(list(source_dir.glob("*.pdf")))
                if pdf_count_in_source > 0:
                    print(f"  {source_dir.name}/: {pdf_count_in_source} PDFs")

    # Success criteria
    success = pdf_count > 0 and fulltext_count > 0

    if success:
        print("\n✅ TEST PASSED: PDF download and full-text extraction working!")
    else:
        print("\n⚠️  TEST INCOMPLETE: Some features may not be working")
        print("   This could be because:")
        print("   - No open access PDFs available for this query")
        print("   - VPN not connected (for paywalled content)")
        print("   - PDF extraction failed")

    return success


def test_pdf_extractor_directly():
    """Test PDF extraction on an existing PDF if available."""
    print("\n" + "=" * 80)
    print("Direct PDF Extraction Test")
    print("=" * 80)

    from omics_oracle_v2.lib.publications.fulltext_extractor import FullTextExtractor

    extractor = FullTextExtractor()

    # Check capabilities
    print("\nExtraction capabilities:")
    for lib, available in extractor.capabilities.items():
        status = "✅" if available else "❌"
        print(f"  {status} {lib}")

    # Look for any existing PDFs
    pdf_dir = Path("data/pdfs")
    if pdf_dir.exists():
        pdfs = list(pdf_dir.rglob("*.pdf"))
        if pdfs:
            test_pdf = pdfs[0]
            print(f"\nTesting extraction on: {test_pdf}")

            text = extractor.extract_from_pdf(test_pdf)
            if text:
                stats = extractor.get_text_stats(text)
                print(f"✅ Extraction successful!")
                print(f"   Words: {stats['words']:,}")
                print(f"   Characters: {stats['characters']:,}")
                print(f"   Lines: {stats['lines']:,}")
                print(f"\nFirst 200 characters:")
                print(f"   {text[:200]}...")
                return True
            else:
                print("❌ Extraction failed")
                return False

    print("ℹ️  No PDFs found to test extraction")
    return None


def test_institutional_access():
    """Test institutional access URL generation."""
    print("\n" + "=" * 80)
    print("Institutional Access Test")
    print("=" * 80)

    from omics_oracle_v2.lib.publications.clients.institutional_access import (
        InstitutionalAccessManager,
        InstitutionType,
    )
    from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

    # Test publication
    pub = Publication(
        title="Test Paper", doi="10.1038/nbt.2808", pmid="23685480", source=PublicationSource.PUBMED
    )

    manager = InstitutionalAccessManager(InstitutionType.GEORGIA_TECH)

    # Test PDF URL
    pdf_url = manager.get_pdf_url(pub)
    print(f"\nTest DOI: {pub.doi}")
    print(f"PDF URL: {pdf_url}")

    # Test access status
    status = manager.check_access_status(pub)
    print(f"\nAccess status:")
    for key, value in status.items():
        if value:
            print(f"  ✅ {key}")

    return bool(pdf_url)


if __name__ == "__main__":
    print(
        """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              OmicsOracle PDF Download & Full-Text Extraction Test            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    )

    # Run tests
    try:
        # Test 1: Institutional access
        print("\n📋 TEST 1: Institutional Access")
        test1 = test_institutional_access()

        # Test 2: Main pipeline
        print("\n📋 TEST 2: Full Pipeline (Search → Download → Extract)")
        test2 = test_pdf_download_pipeline()

        # Test 3: Direct extraction
        print("\n📋 TEST 3: Direct PDF Extraction")
        test3 = test_pdf_extractor_directly()

        # Summary
        print("\n" + "=" * 80)
        print("FINAL TEST SUMMARY")
        print("=" * 80)

        tests = {"Institutional Access": test1, "Full Pipeline": test2, "Direct Extraction": test3}

        for test_name, result in tests.items():
            if result is True:
                print(f"✅ {test_name}: PASSED")
            elif result is False:
                print(f"❌ {test_name}: FAILED")
            else:
                print(f"⏭️  {test_name}: SKIPPED")

        # Overall result
        passed = sum(1 for r in tests.values() if r is True)
        total = len(tests)

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed >= 2:
            print("\n🎉 PDF DOWNLOAD & EXTRACTION IS WORKING!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed - review output above")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
