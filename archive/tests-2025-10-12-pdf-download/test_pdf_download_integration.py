#!/usr/bin/env python
"""
Integration Test: PDF Download with PDFDownloadManager

This test verifies that:
1. FullTextManager returns URLs only (no download logic)
2. PDFDownloadManager handles all actual downloads
3. PDFs are validated (magic bytes check)
4. No imports of deprecated download_utils.py exist

Author: OmicsOracle Team
Date: October 12, 2025
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager
from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient, PubMedConfig


async def test_pdf_download_flow():
    """Test the complete PDF download flow."""

    print("\n" + "="*70)
    print("  PDF Download Integration Test")
    print("="*70 + "\n")

    # Test PMID 39997216 (the problematic case)
    test_pmid = "39997216"

    print(f"📋 Testing PMID: {test_pmid}")
    print(f"   Expected DOI: 10.1093/nar/gkaf101")
    print(f"   Expected PMC: PMC11851118\n")

    # Step 1: Fetch full metadata from PubMed
    print("STEP 1: Fetching metadata from PubMed...")
    pubmed_client = PubMedClient(PubMedConfig(email="research@omicsoracle.ai"))
    publication = pubmed_client.fetch_by_id(test_pmid)

    if not publication:
        print("❌ FAIL: Could not fetch publication metadata")
        return False

    print(f"✅ PASS: Fetched metadata")
    print(f"   Title: {publication.title[:60]}...")
    print(f"   DOI: {publication.doi}")
    print(f"   PMC ID: {publication.pmcid if hasattr(publication, 'pmcid') else 'None'}\n")

    # Step 2: Get URL from FullTextManager (should NOT download)
    print("STEP 2: Getting PDF URL from FullTextManager...")
    fulltext_config = FullTextManagerConfig(
        enable_institutional=True,
        enable_pmc=True,
        enable_unpaywall=True,
        download_pdfs=False,  # CRITICAL: Should NOT download
    )

    async with FullTextManager(fulltext_config) as manager:
        result = await manager.get_fulltext(publication)

        if not result.success:
            print(f"❌ FAIL: Could not find PDF URL")
            print(f"   Error: {result.error}")
            return False

        print(f"✅ PASS: Found PDF URL")
        print(f"   Source: {result.source.value}")
        print(f"   URL: {result.url}")

        # VERIFY: No pdf_path should be set (FullTextManager doesn't download)
        if result.pdf_path:
            print(f"⚠️  WARNING: FullTextManager set pdf_path (should be None)")
            print(f"   This means download_utils.py is still being used!")
            return False

        print(f"✅ PASS: FullTextManager returned URL only (no download)\n")

        # Set URL on publication for PDFDownloadManager
        publication.fulltext_url = result.url
        publication.fulltext_source = result.source.value

    # Step 3: Download PDF using PDFDownloadManager
    print("STEP 3: Downloading PDF with PDFDownloadManager...")

    pdf_dir = Path("data/test_pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)

    pdf_downloader = PDFDownloadManager(
        max_concurrent=1,
        validate_pdf=True,  # CRITICAL: Must validate magic bytes
        max_retries=2,
    )

    download_report = await pdf_downloader.download_batch(
        publications=[publication],
        output_dir=pdf_dir,
        url_field="fulltext_url"
    )

    if download_report.successful == 0:
        print(f"❌ FAIL: PDF download failed")
        print(f"   Total: {download_report.total}")
        print(f"   Successful: {download_report.successful}")
        print(f"   Failed: {download_report.failed}")
        return False

    print(f"✅ PASS: PDF downloaded successfully")
    print(f"   Successful: {download_report.successful}/{download_report.total}")

    # Step 4: Verify PDF file exists and is valid
    print("\nSTEP 4: Validating downloaded PDF...")

    if not hasattr(publication, 'pdf_path') or not publication.pdf_path:
        print(f"❌ FAIL: pdf_path not set on publication")
        return False

    pdf_path = Path(publication.pdf_path)
    if not pdf_path.exists():
        print(f"❌ FAIL: PDF file does not exist at {pdf_path}")
        return False

    print(f"✅ PASS: PDF file exists: {pdf_path.name}")

    # Validate PDF magic bytes
    with open(pdf_path, 'rb') as f:
        magic_bytes = f.read(4)
        if magic_bytes != b'%PDF':
            print(f"❌ FAIL: Invalid PDF (magic bytes: {magic_bytes})")
            return False

    print(f"✅ PASS: PDF validated (magic bytes: %PDF)")

    # Get file size
    file_size_kb = pdf_path.stat().st_size // 1024
    print(f"   File size: {file_size_kb} KB")

    if file_size_kb < 10:
        print(f"⚠️  WARNING: PDF seems too small (might be HTML)")
        return False

    print(f"✅ PASS: PDF size looks good\n")

    # Step 5: Verify no imports of deprecated download_utils
    print("STEP 5: Checking for deprecated code usage...")

    import subprocess
    result = subprocess.run(
        ["grep", "-r", "from omics_oracle_v2.lib.fulltext.download_utils import",
         "omics_oracle_v2/", "--include=*.py"],
        capture_output=True,
        text=True
    )

    # Filter out archived files
    matches = [line for line in result.stdout.split('\n') if line and 'archive' not in line]

    if matches:
        print(f"❌ FAIL: Found imports of deprecated download_utils.py:")
        for match in matches:
            print(f"   {match}")
        return False

    print(f"✅ PASS: No deprecated code usage found\n")

    # All tests passed!
    print("="*70)
    print("  ✅ ALL TESTS PASSED!")
    print("="*70)
    print("\nSummary:")
    print("  ✅ FullTextManager returns URLs only (no download)")
    print("  ✅ PDFDownloadManager handles all downloads")
    print("  ✅ PDF validation works (magic bytes check)")
    print("  ✅ No deprecated code usage")
    print(f"  ✅ Downloaded PDF: {pdf_path.name} ({file_size_kb} KB)")
    print("\n")

    return True


async def test_api_endpoint():
    """Test the API endpoint with the new flow."""

    print("\n" + "="*70)
    print("  API Endpoint Integration Test")
    print("="*70 + "\n")

    import aiohttp

    # Test the enrich-fulltext endpoint
    print("Testing /api/agents/enrich-fulltext endpoint...")

    test_data = {
        "datasets": [
            {
                "geo_id": "GSE281238",
                "title": "Joint profiling of DNA methylation and HiC data",
                "description": "Test dataset",
                "pubmed_ids": ["39997216"]
            }
        ],
        "max_papers": 1
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/agents/enrich-fulltext",
            json=test_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status != 200:
                print(f"❌ FAIL: API returned status {response.status}")
                text = await response.text()
                print(f"   Error: {text[:200]}")
                return False

            data = await response.json()

            if not data or len(data) == 0:
                print(f"❌ FAIL: No datasets returned")
                return False

            dataset = data[0]

            if not dataset.get('fulltext') or len(dataset['fulltext']) == 0:
                print(f"❌ FAIL: No fulltext data")
                return False

            fulltext = dataset['fulltext'][0]

            print(f"✅ PASS: API endpoint returned fulltext data")
            print(f"   PMID: {fulltext.get('pmid')}")
            print(f"   Source: {fulltext.get('source')}")
            print(f"   URL: {fulltext.get('url')}")
            print(f"   PDF Path: {fulltext.get('pdf_path')}")

            # Verify pdf_path is set
            if not fulltext.get('pdf_path'):
                print(f"⚠️  WARNING: pdf_path is None (PDF not downloaded)")
                return False

            # Verify PDF file exists
            pdf_path = Path(fulltext['pdf_path'])
            if not pdf_path.exists():
                print(f"❌ FAIL: PDF file doesn't exist: {pdf_path}")
                return False

            print(f"✅ PASS: PDF downloaded and exists")

            # Check if parsed content is available
            if fulltext.get('abstract'):
                print(f"✅ PASS: Parsed content available (abstract: {len(fulltext['abstract'])} chars)")
            else:
                print(f"⚠️  INFO: No parsed content (abstract empty)")

            print(f"\n✅ API ENDPOINT TEST PASSED\n")
            return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  COMPREHENSIVE PDF DOWNLOAD VALIDATION")
    print("  Testing PDFDownloadManager Integration")
    print("="*70)

    # Run tests
    success = True

    try:
        # Test 1: Direct flow
        success = asyncio.run(test_pdf_download_flow())

        if not success:
            print("\n❌ BASIC TESTS FAILED\n")
            sys.exit(1)

        # Test 2: API endpoint
        api_success = asyncio.run(test_api_endpoint())

        if not api_success:
            print("\n❌ API TESTS FAILED\n")
            sys.exit(1)

        print("\n" + "="*70)
        print("  🎉 ALL VALIDATION TESTS PASSED! 🎉")
        print("="*70)
        print("\nConclusion:")
        print("  ✅ download_utils.py successfully removed")
        print("  ✅ PDFDownloadManager is the ONLY download system")
        print("  ✅ FullTextManager returns URLs only")
        print("  ✅ API endpoint works end-to-end")
        print("  ✅ PDFs are properly validated")
        print("\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION:\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
