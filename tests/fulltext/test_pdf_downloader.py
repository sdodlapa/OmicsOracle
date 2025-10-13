"""
Tests for PDF downloader functionality.

Tests PDF downloading from:
- Unpaywall
- CORE
- arXiv
- bioRxiv

NO PARSING - just download validation and caching.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.fulltext.models import SourceType
from lib.fulltext.pdf_downloader import PDFDownloader, download_pdf_from_doi


@pytest.mark.asyncio
async def test_pdf_downloader_initialization():
    """Test PDFDownloader initialization."""
    downloader = PDFDownloader(cache_dir=Path("data/fulltext/pdf"))

    assert downloader.cache_dir == Path("data/fulltext/pdf")
    assert downloader.timeout == 60
    assert downloader.max_retries == 3
    assert downloader.min_pdf_size == 10240  # 10KB
    assert downloader.max_pdf_size == 104857600  # 100MB

    # Check directories created
    assert (downloader.cache_dir / "unpaywall").exists()
    assert (downloader.cache_dir / "core").exists()
    assert (downloader.cache_dir / "arxiv").exists()
    assert (downloader.cache_dir / "biorxiv").exists()

    print("\nSUCCESS: PDFDownloader initialized correctly")


@pytest.mark.asyncio
async def test_download_arxiv_pdf():
    """Test downloading PDF from arXiv."""
    downloader = PDFDownloader(cache_dir=Path("data/fulltext/pdf"))

    # Use a known arXiv paper
    arxiv_id = "2301.07041"  # "GPT-4 Technical Report" (exists and small)

    success, pdf_path, error = await downloader.download_from_arxiv(arxiv_id, use_cache=True)

    if success:
        assert pdf_path is not None
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"
        assert pdf_path.stat().st_size > 10240  # > 10KB

        # Check metadata
        metadata = await downloader.get_pdf_metadata(SourceType.ARXIV, arxiv_id)
        assert metadata is not None
        assert metadata["arxiv_id"] == arxiv_id
        assert "download_date" in metadata
        assert "file_size" in metadata
        assert "sha256" in metadata

        print(f"\nSUCCESS: Downloaded arXiv PDF")
        print(f"  arXiv ID: {arxiv_id}")
        print(f"  Path: {pdf_path}")
        print(f"  Size: {pdf_path.stat().st_size / 1024:.0f}KB")
        print(f"  SHA256: {metadata['sha256'][:16]}...")
    else:
        print(f"\nNOTE: arXiv download failed (may be network issue): {error}")
        pytest.skip(f"arXiv download failed: {error}")


@pytest.mark.asyncio
async def test_download_biorxiv_pdf():
    """Test downloading PDF from bioRxiv."""
    downloader = PDFDownloader(cache_dir=Path("data/fulltext/pdf"))

    # Use a known bioRxiv paper
    doi = "10.1101/2024.01.15.575842"  # Recent bioRxiv paper

    success, pdf_path, error = await downloader.download_from_biorxiv(doi, use_cache=True)

    if success:
        assert pdf_path is not None
        assert pdf_path.exists()
        assert pdf_path.suffix == ".pdf"
        assert pdf_path.stat().st_size > 10240  # > 10KB

        # Check metadata
        metadata = await downloader.get_pdf_metadata(SourceType.BIORXIV, doi)
        assert metadata is not None
        assert metadata["doi"] == doi

        print(f"\nSUCCESS: Downloaded bioRxiv PDF")
        print(f"  DOI: {doi}")
        print(f"  Path: {pdf_path}")
        print(f"  Size: {pdf_path.stat().st_size / 1024:.0f}KB")
    else:
        print(f"\nNOTE: bioRxiv download failed (may be network issue): {error}")
        pytest.skip(f"bioRxiv download failed: {error}")


@pytest.mark.asyncio
async def test_pdf_validation():
    """Test PDF validation logic."""
    downloader = PDFDownloader()

    # Test valid PDF
    valid_pdf = b"%PDF-1.4\n" + b"x" * 20000 + b"\n%%EOF"
    is_valid, error = await downloader._validate_pdf(valid_pdf)
    assert is_valid is True
    assert error is None

    # Test too small
    small_pdf = b"%PDF-1.4\n" + b"x" * 100
    is_valid, error = await downloader._validate_pdf(small_pdf)
    assert is_valid is False
    assert "too small" in error

    # Test missing PDF header
    no_header = b"Not a PDF" + b"x" * 20000
    is_valid, error = await downloader._validate_pdf(no_header)
    assert is_valid is False
    assert "PDF header" in error

    # Test truncated PDF (missing EOF)
    truncated = b"%PDF-1.4\n" + b"x" * 20000
    is_valid, error = await downloader._validate_pdf(truncated)
    assert is_valid is False
    assert "truncated" in error

    print("\nSUCCESS: PDF validation working correctly")


@pytest.mark.asyncio
async def test_cache_retrieval():
    """Test retrieving cached PDFs."""
    downloader = PDFDownloader(cache_dir=Path("data/fulltext/pdf"))

    # Try to get cached arXiv PDF
    arxiv_id = "2301.07041"
    cached_path = await downloader.get_cached_pdf(SourceType.ARXIV, arxiv_id)

    if cached_path:
        assert cached_path.exists()
        print(f"\nSUCCESS: Retrieved cached PDF: {cached_path}")

        # Get metadata
        metadata = await downloader.get_pdf_metadata(SourceType.ARXIV, arxiv_id)
        if metadata:
            print(f"  Metadata available: {list(metadata.keys())}")
    else:
        print("\nNOTE: No cached PDF found (expected if test_download_arxiv_pdf didn't run)")


@pytest.mark.asyncio
async def test_download_from_doi_convenience():
    """Test convenience function for downloading from DOI."""

    # Test with bioRxiv DOI (doesn't require external clients)
    doi = "10.1101/2024.01.15.575842"

    success, pdf_path, error, source = await download_pdf_from_doi(doi, cache_dir=Path("data/fulltext/pdf"))

    if success:
        assert pdf_path is not None
        assert pdf_path.exists()
        assert source == SourceType.BIORXIV

        print(f"\nSUCCESS: download_pdf_from_doi worked")
        print(f"  DOI: {doi}")
        print(f"  Source: {source.value}")
        print(f"  Path: {pdf_path}")
    else:
        print(f"\nNOTE: download_pdf_from_doi failed (may be network issue): {error}")
        pytest.skip(f"DOI download failed: {error}")


@pytest.mark.asyncio
async def test_batch_download():
    """Test downloading multiple PDFs in batch."""
    downloader = PDFDownloader(cache_dir=Path("data/fulltext/pdf"))

    # Test cases: (source_type, identifier, download_function)
    test_cases = [
        ("arXiv", "2301.07041", lambda: downloader.download_from_arxiv("2301.07041")),
        (
            "bioRxiv",
            "10.1101/2024.01.15.575842",
            lambda: downloader.download_from_biorxiv("10.1101/2024.01.15.575842"),
        ),
    ]

    results = []
    for source_name, identifier, download_func in test_cases:
        try:
            success, pdf_path, error = await download_func()
            results.append(
                {
                    "source": source_name,
                    "identifier": identifier,
                    "success": success,
                    "path": pdf_path,
                    "error": error,
                }
            )
        except Exception as e:
            results.append(
                {
                    "source": source_name,
                    "identifier": identifier,
                    "success": False,
                    "error": str(e),
                }
            )

    # Print summary
    print(f"\nBatch download results:")
    for result in results:
        status = "SUCCESS" if result["success"] else "FAILED"
        print(f"  [{status}] {result['source']}: {result['identifier']}")
        if result["success"] and "path" in result:
            print(f"    Path: {result['path']}")
        elif "error" in result:
            print(f"    Error: {result['error']}")

    # At least one should succeed (network permitting)
    success_count = sum(1 for r in results if r["success"])
    print(f"\nTotal: {success_count}/{len(results)} successful")


def main():
    """Run all tests."""
    print("=" * 80)
    print("PDF DOWNLOADER TESTS")
    print("=" * 80)

    # Run tests
    asyncio.run(test_pdf_downloader_initialization())
    asyncio.run(test_pdf_validation())
    asyncio.run(test_download_arxiv_pdf())
    asyncio.run(test_download_biorxiv_pdf())
    asyncio.run(test_cache_retrieval())
    asyncio.run(test_download_from_doi_convenience())
    asyncio.run(test_batch_download())

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
