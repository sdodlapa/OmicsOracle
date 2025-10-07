#!/usr/bin/env python3
"""
Direct test of PDF download and extraction functionality.

Tests without depending on PubMed API (which has SSL issues).
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.lib.publications.clients.institutional_access import (
    InstitutionalAccessManager,
    InstitutionType,
)
from omics_oracle_v2.lib.publications.fulltext_extractor import FullTextExtractor
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
from omics_oracle_v2.lib.publications.pdf_downloader import PDFDownloader

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_pdf_download():
    """Test PDF download with known open access papers."""

    print("=" * 80)
    print("PDF DOWNLOAD TEST - Direct Download from Known OA Sources")
    print("=" * 80)

    # Test publications with known open access PDFs (PLOS ONE - always OA with direct PDFs)
    test_pubs = [
        Publication(
            title="Single-Cell RNA Sequencing Identifies Diverse Roles of Epithelial Cells in Idiopathic Pulmonary Fibrosis",
            doi="10.1371/journal.pone.0090558",
            pmid="24651512",
            source=PublicationSource.PUBMED,
            pdf_url="https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0090558&type=printable",
            metadata={},
        ),
        Publication(
            title="Single-Cell Transcriptome Analysis Reveals Dynamic Changes in lncRNA Expression during Reprogramming",
            doi="10.1371/journal.pone.0193392",
            pmid="29451881",
            source=PublicationSource.PUBMED,
            pdf_url="https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0193392&type=printable",
            metadata={},
        ),
    ]

    # Initialize components
    print("\n1. Initializing institutional access (Georgia Tech)...")
    institutional_manager = InstitutionalAccessManager(InstitutionType.GEORGIA_TECH)

    print("2. Initializing PDF downloader...")
    downloader = PDFDownloader(download_dir=Path("data/pdfs"), institutional_manager=institutional_manager)

    print("3. Initializing full-text extractor...")
    extractor = FullTextExtractor()

    # Get PDF URLs
    print("\n4. Getting PDF URLs via institutional access...")
    for pub in test_pubs:
        pdf_url = institutional_manager.get_pdf_url(pub)
        print(f"\n   Paper: {pub.title[:60]}...")
        print(f"   PMID: {pub.pmid}, PMC: {pub.pmcid}")
        print(f"   PDF URL: {pdf_url[:100] if pdf_url else 'NOT FOUND'}")
        if pdf_url:
            pub.pdf_url = pdf_url

    # Download PDFs
    print("\n5. Downloading PDFs...")
    downloaded = downloader.download_batch(test_pubs, max_workers=3)

    print(f"\n   ✅ Downloaded {len(downloaded)} PDFs")

    # Extract full text
    print("\n6. Extracting full text from PDFs...")
    extracted_count = 0

    for pub in test_pubs:
        if pub.pdf_path and Path(pub.pdf_path).exists():
            print(f"\n   Processing: {Path(pub.pdf_path).name}")

            # Extract text
            full_text = extractor.extract_from_pdf(Path(pub.pdf_path))

            if full_text:
                pub.full_text = full_text
                pub.full_text_source = "pdf"
                pub.text_length = len(full_text)
                pub.extraction_date = datetime.now()

                stats = extractor.get_text_stats(full_text)
                print(f"      ✅ Extracted {stats['words']:,} words ({stats['characters']:,} chars)")
                print(f"      Preview: {full_text[:100]}...")
                extracted_count += 1
            else:
                print(f"      ❌ Extraction failed")

    # Summary
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Test publications: {len(test_pubs)}")
    print(f"PDFs downloaded: {len(downloaded)}")
    print(f"Full-text extracted: {extracted_count}")

    # Check directory
    stats = downloader.get_download_stats()
    print(f"\nDownload directory: data/pdfs")
    print(f"Total PDFs: {stats['total_pdfs']}")
    print(f"Total size: {stats['total_size_mb']} MB")
    print(f"\nBreakdown by source:")
    for source, source_stats in stats["by_source"].items():
        print(f"  {source}/: {source_stats['count']} PDFs ({source_stats['size_mb']} MB)")

    # Display results
    print("\n" + "=" * 80)
    print("PUBLICATION DETAILS")
    print("=" * 80)

    for i, pub in enumerate(test_pubs, 1):
        print(f"\n#{i} {pub.title}")
        print(f"   PMID: {pub.pmid}")
        print(f"   PDF Downloaded: {'✅ Yes' if pub.metadata.get('pdf_downloaded') else '❌ No'}")
        if pub.pdf_path:
            print(f"   PDF Path: {pub.pdf_path}")
            print(f"   PDF Size: {Path(pub.pdf_path).stat().st_size / 1024:.1f} KB")
        if pub.full_text:
            print(f"   Full-text: ✅ Yes ({len(pub.full_text):,} chars)")
            print(f"   Word count: {pub.full_text.split().__len__():,}")
        else:
            print(f"   Full-text: ❌ No")

    # Success criteria
    success = len(downloaded) > 0 and extracted_count > 0

    print("\n" + "=" * 80)
    if success:
        print("✅ SUCCESS: PDF download and full-text extraction working!")
        return True
    else:
        print("❌ FAILED: Check errors above")
        return False


def test_with_sample_pdf():
    """Test extraction with a manually placed sample PDF if available."""
    print("\n" + "=" * 80)
    print("SAMPLE PDF TEST (if available)")
    print("=" * 80)

    # Look for any existing PDFs
    pdf_dir = Path("data/pdfs")
    if pdf_dir.exists():
        pdfs = list(pdf_dir.rglob("*.pdf"))
        if pdfs:
            print(f"\nFound {len(pdfs)} existing PDFs")

            # Test extraction on first PDF
            test_pdf = pdfs[0]
            print(f"\nTesting: {test_pdf}")

            extractor = FullTextExtractor()
            text = extractor.extract_from_pdf(test_pdf)

            if text:
                stats = extractor.get_text_stats(text)
                print(f"✅ Success!")
                print(f"   Words: {stats['words']:,}")
                print(f"   Characters: {stats['characters']:,}")
                print(f"   Lines: {stats['lines']:,}")
                print(f"\n   First 200 chars: {text[:200]}...")
                return True
            else:
                print("❌ Extraction failed")
                return False

    print("ℹ️  No existing PDFs found")
    return None


if __name__ == "__main__":
    print(
        """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           Direct PDF Download & Extraction Test (No PubMed API)              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    )

    try:
        # Test 1: Download from PMC
        test1 = test_pdf_download()

        # Test 2: Sample PDF if available
        test2 = test_with_sample_pdf()

        # Summary
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)

        if test1:
            print("✅ PDF Download & Extraction: WORKING")
        else:
            print("❌ PDF Download & Extraction: FAILED")

        if test2 is True:
            print("✅ Sample PDF Extraction: WORKING")
        elif test2 is False:
            print("❌ Sample PDF Extraction: FAILED")
        else:
            print("⏭️  Sample PDF Extraction: SKIPPED")

        if test1:
            print("\n🎉 PDF PIPELINE IS FULLY FUNCTIONAL!")
            sys.exit(0)
        else:
            print("\n⚠️  Some issues detected")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
