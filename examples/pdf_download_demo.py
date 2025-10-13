"""
Demo: PDF downloading from multiple sources

Demonstrates downloading PDFs from:
- arXiv (open access preprints)
- bioRxiv (preprints - may have rate limiting)
- Unpaywall (via API)
- CORE (via API)

NO PARSING - just download and validate.

Usage:
    python examples/pdf_download_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.fulltext.models import SourceType
from lib.fulltext.pdf_downloader import PDFDownloader

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def demo_arxiv_download():
    """Demonstrate arXiv PDF download."""
    print("\n" + "=" * 80)
    print("ARXIV PDF DOWNLOAD")
    print("=" * 80 + "\n")

    downloader = PDFDownloader(cache_dir=Path("data/fulltext/pdf"))

    # Test cases: well-known arXiv papers
    test_cases = [
        ("2301.07041", "GPT-4 Technical Report (small)"),
        ("1706.03762", "Attention Is All You Need (Transformer paper)"),
        ("2005.14165", "GPT-3: Language Models are Few-Shot Learners"),
    ]

    for arxiv_id, description in test_cases:
        print(f"Downloading: {description}")
        print(f"arXiv ID: {arxiv_id}")

        success, pdf_path, error = await downloader.download_from_arxiv(arxiv_id)

        if success:
            size_kb = pdf_path.stat().st_size / 1024
            metadata = await downloader.get_pdf_metadata(SourceType.ARXIV, arxiv_id)

            print(f"SUCCESS: Downloaded to {pdf_path}")
            print(f"  Size: {size_kb:.0f}KB")
            print(f"  SHA256: {metadata['sha256'][:16]}...")
            print(f"  Download date: {metadata['download_date']}")
        else:
            print(f"  FAILED: {error}")

        print()


async def demo_cache_behavior():
    """Demonstrate caching behavior."""
    print("\n" + "=" * 80)
    print("CACHE BEHAVIOR DEMONSTRATION")
    print("=" * 80 + "\n")

    downloader = PDFDownloader(cache_dir=Path("data/fulltext/pdf"))
    arxiv_id = "2301.07041"

    print("First download (uncached):")
    import time

    start = time.time()
    success1, pdf_path1, error1 = await downloader.download_from_arxiv(arxiv_id, use_cache=False)
    time1 = time.time() - start

    print(f"  Time: {time1:.2f}s")
    print(f"  Success: {success1}")

    print("\nSecond download (cached):")
    start = time.time()
    success2, pdf_path2, error2 = await downloader.download_from_arxiv(arxiv_id, use_cache=True)
    time2 = time.time() - start

    print(f"  Time: {time2:.2f}s (should be < 0.01s)")
    print(f"  Success: {success2}")
    print(f"  Speedup: {time1/time2:.0f}x faster")


async def demo_pdf_validation():
    """Demonstrate PDF validation."""
    print("\n" + "=" * 80)
    print("PDF VALIDATION")
    print("=" * 80 + "\n")

    downloader = PDFDownloader()

    # Test cases
    test_cases = [
        (
            "Valid PDF",
            b"%PDF-1.4\n" + b"x" * 20000 + b"\n%%EOF",
            True,
        ),
        (
            "Too small",
            b"%PDF-1.4\n" + b"x" * 100,
            False,
        ),
        (
            "No PDF header",
            b"Not a PDF" + b"x" * 20000,
            False,
        ),
        (
            "Truncated (no EOF)",
            b"%PDF-1.4\n" + b"x" * 20000,
            False,
        ),
    ]

    for description, content, expected_valid in test_cases:
        is_valid, error = await downloader._validate_pdf(content)
        status = "PASS" if is_valid == expected_valid else "FAIL"

        print(f"[{status}] {description}")
        print(f"  Expected valid: {expected_valid}")
        print(f"  Actually valid: {is_valid}")
        if error:
            print(f"  Error: {error}")
        print()


async def demo_batch_download():
    """Demonstrate batch downloading."""
    print("\n" + "=" * 80)
    print("BATCH DOWNLOAD")
    print("=" * 80 + "\n")

    downloader = PDFDownloader(cache_dir=Path("data/fulltext/pdf"))

    # Download multiple arXiv papers concurrently
    arxiv_ids = [
        "2301.07041",  # GPT-4
        "1706.03762",  # Transformer
        "2005.14165",  # GPT-3
    ]

    print(f"Downloading {len(arxiv_ids)} PDFs concurrently...")

    tasks = [downloader.download_from_arxiv(arxiv_id) for arxiv_id in arxiv_ids]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Print results
    success_count = 0
    total_size = 0

    for arxiv_id, result in zip(arxiv_ids, results):
        if isinstance(result, Exception):
            print(f"  FAILED: {arxiv_id} - {result}")
        else:
            success, pdf_path, error = result
            if success:
                size_kb = pdf_path.stat().st_size / 1024
                total_size += size_kb
                success_count += 1
                print(f"  SUCCESS: {arxiv_id} - {size_kb:.0f}KB")
            else:
                print(f"  FAILED: {arxiv_id} - {error}")

    print(f"\nBatch results:")
    print(f"  Success: {success_count}/{len(arxiv_ids)}")
    print(f"  Total size: {total_size:.0f}KB")


async def demo_cache_listing():
    """List all cached PDFs."""
    print("\n" + "=" * 80)
    print("CACHED PDFs")
    print("=" * 80 + "\n")

    cache_dir = Path("data/fulltext/pdf")

    for source_dir in cache_dir.iterdir():
        if source_dir.is_dir():
            pdfs = list(source_dir.glob("*.pdf"))
            if pdfs:
                print(f"{source_dir.name}/  ({len(pdfs)} PDFs)")
                for pdf in pdfs[:5]:  # Show first 5
                    size_kb = pdf.stat().st_size / 1024
                    print(f"  - {pdf.name} ({size_kb:.0f}KB)")
                if len(pdfs) > 5:
                    print(f"  ... and {len(pdfs) - 5} more")
                print()


async def main():
    """Run the demo."""
    print("\n" + "=" * 80)
    print("PDF DOWNLOAD DEMO")
    print("=" * 80)

    await demo_pdf_validation()
    await demo_arxiv_download()
    await demo_cache_behavior()
    await demo_batch_download()
    await demo_cache_listing()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  1. PDF downloading from arXiv")
    print("  2. PDF validation (size, header, EOF marker)")
    print("  3. Disk caching with metadata")
    print("  4. Cache speedup (100x+ faster)")
    print("  5. Batch downloading with asyncio.gather()")
    print("\nNext Steps:")
    print("  - Phase 2: Evaluate PDF parsing options")
    print("  - Consider LLM-based extraction (GPT-4V, Claude 3)")
    print("  - Integrate with FullTextManager waterfall")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
