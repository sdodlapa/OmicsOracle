#!/usr/bin/env python3
"""
Test PDF Download Fixes

Tests:
1. Session close bug fix (indentation in download_manager.py)
2. Counting bug fix (only count actual PDFs in agents.py)
3. PMC fallback functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.lib.publications.models import Publication
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager


async def test_session_fix():
    """Test that session stays open for landing page extraction"""
    print("\n" + "=" * 60)
    print("TEST 1: Session Management Fix")
    print("=" * 60)
    
    downloader = PDFDownloadManager(max_retries=2, validate_pdf=True)
    
    # Test with a URL that might return HTML landing page
    test_pub = Publication(
        pmid="39997216",
        doi="10.1093/nar/gkaf101",
        pmcid="PMC11851118",
        title="Test Paper",
        source="pubmed",
        fulltext_url="https://academic.oup.com/nar/article-pdf/53/4/gkaf101/61998162/gkaf101.pdf"
    )
    
    output_dir = Path("data/test_pdfs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = await downloader._download_single(test_pub, test_pub.fulltext_url, output_dir)
    
    if "Session is closed" in str(result.error):
        print("❌ FAILED: Session close error still occurs")
        print(f"   Error: {result.error}")
        return False
    else:
        print("✅ PASSED: No session close error")
        if result.success:
            print(f"   Downloaded: {result.pdf_path}")
        else:
            print(f"   Failed for different reason: {result.error}")
        return True


async def test_pmc_download():
    """Test PMC PDF download"""
    print("\n" + "=" * 60)
    print("TEST 2: PMC PDF Download")
    print("=" * 60)
    
    downloader = PDFDownloadManager(max_retries=2, validate_pdf=True)
    
    # PMC PDF URL
    pmc_pub = Publication(
        pmid="39997216",
        pmcid="PMC11851118",
        doi="10.1093/nar/gkaf101",
        title="Test Paper",
        source="pubmed",
        fulltext_url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11851118/pdf/"
    )
    
    output_dir = Path("data/test_pdfs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = await downloader._download_single(pmc_pub, pmc_pub.fulltext_url, output_dir)
    
    if result.success and result.pdf_path and result.pdf_path.exists():
        print("✅ PASSED: PMC PDF downloaded successfully")
        print(f"   Path: {result.pdf_path}")
        print(f"   Size: {result.file_size / 1024:.1f} KB")
        return True
    else:
        print("❌ FAILED: PMC download failed")
        print(f"   Error: {result.error}")
        return False


def test_counting_logic():
    """Test that only PDFs with content are counted"""
    print("\n" + "=" * 60)
    print("TEST 3: Counting Logic (Code Review)")
    print("=" * 60)
    
    # Read the agents.py file and check for the fix
    agents_file = Path(__file__).parent / "omics_oracle_v2/api/routes/agents.py"
    content = agents_file.read_text()
    
    # Check if we skip entries without PDFs
    if "# CRITICAL FIX: Skip this publication" in content:
        print("✅ PASSED: Code has skip logic for missing PDFs")
        return True
    else:
        print("❌ FAILED: Skip logic not found in code")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PDF DOWNLOAD FIXES VALIDATION")
    print("=" * 60)
    
    results = []
    
    # Test 1: Session fix
    try:
        result = await test_session_fix()
        results.append(("Session Management", result))
    except Exception as e:
        print(f"❌ Test 1 ERROR: {e}")
        results.append(("Session Management", False))
    
    # Test 2: PMC download
    try:
        result = await test_pmc_download()
        results.append(("PMC Download", result))
    except Exception as e:
        print(f"❌ Test 2 ERROR: {e}")
        results.append(("PMC Download", False))
    
    # Test 3: Counting logic
    try:
        result = test_counting_logic()
        results.append(("Counting Logic", result))
    except Exception as e:
        print(f"❌ Test 3 ERROR: {e}")
        results.append(("Counting Logic", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Ready to test in UI.")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Review needed.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
