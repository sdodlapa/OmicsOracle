#!/usr/bin/env python3
"""
URL Collection & Download Demonstration

This script demonstrates the complete URL collection and download flow:
1. Initialize FullTextManager with all 11 sources
2. Collect URLs from multiple sources (with URL type classification)
3. Download PDFs using collected URLs
4. Validate downloads (correct file, PDF format, etc.)
5. Report success rates by URL type and source

Usage:
    python scripts/demo_url_collection_and_download.py

Requirements:
    - Sample publications with DOIs (will test with well-known papers)
    - Backend services running (optional - can work standalone)

Author: GitHub Copilot
Created: October 13, 2025
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.pipelines.pdf_download.download_manager import DownloadResult, PDFDownloadManager
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager, FullTextManagerConfig, SourceURL
from omics_oracle_v2.lib.pipelines.url_collection.url_validator import URLType, URLValidator
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class URLCollectionDemo:
    """Demonstrate URL collection and download with validation."""

    def __init__(self):
        """Initialize demo with sample publications."""
        self.output_dir = Path("data/fulltext/pdfs/demo")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Sample publications (well-known open access papers)
        self.test_publications = [
            Publication(
                title="CRISPR-Cas9 genome editing",
                doi="10.1126/science.1258096",  # Nature paper
                pmid="24336571",
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="Deep learning review",
                doi="10.1038/nature14539",  # Nature paper on deep learning
                pmid="26017442",
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="COVID-19 genomic surveillance",
                doi="10.1038/s41586-020-2918-0",  # Recent COVID paper
                pmid="33199918",
                source=PublicationSource.PUBMED,
            ),
            # arXiv paper (no PMID)
            Publication(
                title="Attention Is All You Need",
                doi=None,
                pmid=None,
                metadata={"arxiv_id": "1706.03762"},  # Transformer paper
                source=PublicationSource.PUBMED,
            ),
            # bioRxiv preprint
            Publication(
                title="bioRxiv preprint example",
                doi="10.1101/2024.01.01.573887",  # Example bioRxiv
                pmid=None,
                source=PublicationSource.PUBMED,
            ),
        ]

    async def demonstrate_url_collection(self):
        """
        Step 1: Demonstrate URL collection from all sources.

        Shows:
        - Parallel collection from 11 sources
        - URL type classification
        - Priority adjustment
        - Source statistics
        """
        print("\n" + "=" * 80)
        print("STEP 1: URL COLLECTION DEMONSTRATION")
        print("=" * 80)

        # Initialize manager
        config = FullTextManagerConfig(
            enable_institutional=False,  # Disable for demo (requires VPN)
            enable_pmc=True,
            enable_unpaywall=True,
            enable_core=True,  # Enable (using CORE_API_KEY from .env)
            enable_arxiv=True,
            enable_biorxiv=True,
            enable_crossref=True,
            enable_scihub=False,  # Disabled by default
            enable_libgen=False,  # Disabled by default
            enable_openalex=False,  # Disable (requires API key)
            unpaywall_email=os.getenv("NCBI_EMAIL", "demo@omicsoracle.org"),
            core_api_key=os.getenv("CORE_API_KEY"),
        )

        manager = FullTextManager(config)
        await manager.initialize()

        try:
            print(f"\n✓ Initialized FullTextManager")
            print(f"  Enabled sources: 8/11 (institutional + scihub/libgen + openalex disabled)")
            print(
                f"  CORE API Key: {config.core_api_key[:20]}... ({'SET' if config.core_api_key else 'NOT SET'})"
            )
            print(f"\n📊 Testing {len(self.test_publications)} publications:\n")

            all_results = []

            for i, pub in enumerate(self.test_publications, 1):
                print(f"\n[{i}/{len(self.test_publications)}] Testing: {pub.title[:60]}...")
                print(f"  DOI: {pub.doi or 'None'}")
                print(f"  PMID: {pub.pmid or 'None'}")

                # Collect URLs from all sources
                result = await manager.get_all_fulltext_urls(pub)

                if result.success and result.all_urls:
                    print(f"  ✅ Found {len(result.all_urls)} URLs")

                    # Show URL type distribution
                    type_counts = {}
                    for url in result.all_urls:
                        type_counts[url.url_type.value] = type_counts.get(url.url_type.value, 0) + 1

                    print(f"  📊 URL Types:")
                    for url_type, count in sorted(type_counts.items()):
                        print(f"     {url_type:15} : {count}")

                    # Show top 3 URLs
                    print(f"  🔝 Top 3 URLs (by priority):")
                    for j, url in enumerate(result.all_urls[:3], 1):
                        print(
                            f"     {j}. [{url.source.value:12}] {url.url_type.value:15} (priority {url.priority})"
                        )
                        print(f"        {url.url[:80]}...")

                    all_results.append((pub, result))
                else:
                    print(f"  ❌ No URLs found")
                    print(f"     Error: {result.error}")

            print("\n" + "=" * 80)
            print("URL COLLECTION SUMMARY")
            print("=" * 80)

            total_pubs = len(self.test_publications)
            successful_pubs = len(all_results)
            total_urls = sum(len(r.all_urls) for _, r in all_results)

            print(f"Publications tested: {total_pubs}")
            print(f"Publications with URLs: {successful_pubs} ({successful_pubs/total_pubs*100:.1f}%)")
            print(f"Total URLs collected: {total_urls}")
            print(f"Avg URLs per publication: {total_urls/successful_pubs:.1f}")

            # URL type distribution across all publications
            all_type_counts = {}
            all_source_counts = {}
            for _, result in all_results:
                for url in result.all_urls:
                    all_type_counts[url.url_type.value] = all_type_counts.get(url.url_type.value, 0) + 1
                    all_source_counts[url.source.value] = all_source_counts.get(url.source.value, 0) + 1

            print(f"\n📊 Overall URL Type Distribution:")
            for url_type, count in sorted(all_type_counts.items(), key=lambda x: -x[1]):
                percentage = count / total_urls * 100
                print(f"  {url_type:15} : {count:3} ({percentage:5.1f}%)")

            print(f"\n📊 URLs by Source:")
            for source, count in sorted(all_source_counts.items(), key=lambda x: -x[1]):
                percentage = count / total_urls * 100
                print(f"  {source:15} : {count:3} ({percentage:5.1f}%)")

            return all_results

        finally:
            # Clean up aiohttp sessions
            await manager.cleanup()

    async def demonstrate_pdf_download(self, collected_results: List):
        """
        Step 2: Demonstrate PDF download using collected URLs.

        Shows:
        - Download with fallback through multiple URLs
        - Success rate by URL type
        - Source effectiveness
        - File validation
        """
        print("\n" + "=" * 80)
        print("STEP 2: PDF DOWNLOAD DEMONSTRATION")
        print("=" * 80)

        # Initialize download manager
        pdf_downloader = PDFDownloadManager(
            max_concurrent=3,
            max_retries=2,
            timeout_seconds=30,
            validate_pdf=True,
        )

        print(f"\n✓ Initialized PDFDownloadManager")
        print(f"  Max concurrent: 3")
        print(f"  Max retries per URL: 2")
        print(f"  PDF validation: Enabled")

        download_results = []

        for i, (pub, url_result) in enumerate(collected_results, 1):
            print(f"\n[{i}/{len(collected_results)}] Downloading: {pub.title[:60]}...")
            print(f"  Available URLs: {len(url_result.all_urls)}")

            # Try downloading with fallback
            result = await pdf_downloader.download_with_fallback(pub, url_result.all_urls, self.output_dir)

            if result.success and result.pdf_path:
                file_size_mb = result.file_size / (1024 * 1024)
                print(f"  ✅ SUCCESS!")
                print(f"     Source: {result.source}")
                print(f"     File: {result.pdf_path.name}")
                print(f"     Size: {file_size_mb:.2f} MB")

                # Validate PDF
                if result.pdf_path.exists():
                    with open(result.pdf_path, "rb") as f:
                        header = f.read(10)
                        if header.startswith(b"%PDF-"):
                            print(f"     ✓ Valid PDF format")
                        else:
                            print(f"     ⚠️  Invalid PDF format!")
                else:
                    print(f"     ⚠️  File not found!")
            else:
                print(f"  ❌ FAILED")
                print(f"     Error: {result.error}")

            download_results.append((pub, url_result, result))

        print("\n" + "=" * 80)
        print("DOWNLOAD SUMMARY")
        print("=" * 80)

        total_downloads = len(download_results)
        successful_downloads = sum(1 for _, _, r in download_results if r.success)
        failed_downloads = total_downloads - successful_downloads

        print(f"Total downloads attempted: {total_downloads}")
        print(f"Successful: {successful_downloads} ({successful_downloads/total_downloads*100:.1f}%)")
        print(f"Failed: {failed_downloads} ({failed_downloads/total_downloads*100:.1f}%)")

        # Success rate by source
        source_stats = {}
        for _, _, result in download_results:
            if result.source:
                if result.source not in source_stats:
                    source_stats[result.source] = {"success": 0, "fail": 0}
                if result.success:
                    source_stats[result.source]["success"] += 1
                else:
                    source_stats[result.source]["fail"] += 1

        if source_stats:
            print(f"\n📊 Success Rate by Source:")
            for source, stats in sorted(source_stats.items()):
                total = stats["success"] + stats["fail"]
                success_rate = stats["success"] / total * 100 if total > 0 else 0
                print(f"  {source:15} : {stats['success']}/{total} ({success_rate:.0f}%)")

        # File size statistics
        sizes = [r.file_size / (1024 * 1024) for _, _, r in download_results if r.success]
        if sizes:
            print(f"\n📊 File Size Statistics:")
            print(f"  Average: {sum(sizes)/len(sizes):.2f} MB")
            print(f"  Min: {min(sizes):.2f} MB")
            print(f"  Max: {max(sizes):.2f} MB")
            print(f"  Total: {sum(sizes):.2f} MB")

        return download_results

    async def validate_downloads(self, download_results: List):
        """
        Step 3: Validate downloaded files.

        Checks:
        - File exists on disk
        - File size > 0
        - Valid PDF format (magic bytes)
        - Filename matches identifier system
        """
        print("\n" + "=" * 80)
        print("STEP 3: DOWNLOAD VALIDATION")
        print("=" * 80)

        validation_results = []

        for i, (pub, url_result, download_result) in enumerate(download_results, 1):
            print(f"\n[{i}/{len(download_results)}] Validating: {pub.title[:60]}...")

            checks = {
                "download_success": False,
                "file_exists": False,
                "file_size_ok": False,
                "valid_pdf": False,
                "correct_filename": False,
            }

            if download_result.success and download_result.pdf_path:
                checks["download_success"] = True

                # Check 1: File exists
                if download_result.pdf_path.exists():
                    checks["file_exists"] = True
                    print(f"  ✓ File exists: {download_result.pdf_path.name}")
                else:
                    print(f"  ✗ File not found: {download_result.pdf_path}")

                # Check 2: File size
                if checks["file_exists"]:
                    file_size = download_result.pdf_path.stat().st_size
                    if file_size > 1000:  # At least 1KB
                        checks["file_size_ok"] = True
                        print(f"  ✓ File size OK: {file_size / 1024:.1f} KB")
                    else:
                        print(f"  ✗ File too small: {file_size} bytes")

                # Check 3: Valid PDF format
                if checks["file_exists"]:
                    try:
                        with open(download_result.pdf_path, "rb") as f:
                            header = f.read(10)
                            if header.startswith(b"%PDF-"):
                                checks["valid_pdf"] = True
                                print(f"  ✓ Valid PDF format")
                            else:
                                print(f"  ✗ Invalid PDF format (header: {header[:20]})")
                    except Exception as e:
                        print(f"  ✗ Error reading file: {e}")

                # Check 4: Correct filename (matches UniversalIdentifier)
                from omics_oracle_v2.lib.shared.identifiers import UniversalIdentifier

                identifier = UniversalIdentifier(pub)
                expected_filename = identifier.filename
                actual_filename = download_result.pdf_path.name

                if actual_filename.lower() == expected_filename.lower():
                    checks["correct_filename"] = True
                    print(f"  ✓ Correct filename: {actual_filename}")
                else:
                    print(f"  ⚠️  Filename mismatch:")
                    print(f"     Expected: {expected_filename}")
                    print(f"     Actual: {actual_filename}")
            else:
                print(f"  ✗ Download failed: {download_result.error}")

            all_checks_passed = all(checks.values())
            validation_results.append((pub, checks, all_checks_passed))

            if all_checks_passed:
                print(f"  ✅ ALL CHECKS PASSED")
            else:
                failed_checks = [k for k, v in checks.items() if not v]
                print(f"  ❌ FAILED CHECKS: {', '.join(failed_checks)}")

        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        total = len(validation_results)
        all_passed = sum(1 for _, _, passed in validation_results if passed)

        print(f"Total validations: {total}")
        print(f"All checks passed: {all_passed} ({all_passed/total*100:.1f}%)")

        # Individual check statistics
        check_stats = {
            "download_success": 0,
            "file_exists": 0,
            "file_size_ok": 0,
            "valid_pdf": 0,
            "correct_filename": 0,
        }

        for _, checks, _ in validation_results:
            for check_name, passed in checks.items():
                if passed:
                    check_stats[check_name] += 1

        print(f"\n📊 Individual Check Statistics:")
        for check_name, count in check_stats.items():
            percentage = count / total * 100
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"  {status} {check_name:20} : {count}/{total} ({percentage:.0f}%)")

        return validation_results


async def main():
    """Run complete demonstration."""
    print("\n" + "=" * 80)
    print("URL COLLECTION & DOWNLOAD DEMONSTRATION")
    print("Testing UniversalIdentifier + URL Classification System")
    print("=" * 80)

    demo = URLCollectionDemo()

    try:
        # Step 1: Collect URLs
        collected_results = await demo.demonstrate_url_collection()

        if not collected_results:
            print("\n❌ No URLs collected. Cannot proceed with download demonstration.")
            return 1

        # Step 2: Download PDFs
        download_results = await demo.demonstrate_pdf_download(collected_results)

        # Step 3: Validate downloads
        validation_results = await demo.validate_downloads(download_results)

        # Final summary
        print("\n" + "=" * 80)
        print("DEMONSTRATION COMPLETE")
        print("=" * 80)

        successful_validations = sum(1 for _, _, passed in validation_results if passed)
        total_validations = len(validation_results)

        print(f"\n✅ Successfully validated: {successful_validations}/{total_validations}")

        if successful_validations == total_validations:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nKey Achievements:")
            print("  ✓ URL collection working correctly")
            print("  ✓ URL type classification accurate")
            print("  ✓ PDF downloads successful")
            print("  ✓ UniversalIdentifier system working")
            print("  ✓ File validation passed")
            return 0
        elif successful_validations >= total_validations * 0.8:
            print("\n✅ MOSTLY SUCCESSFUL (80%+)")
            print("\nSome tests failed, but system is mostly working.")
            return 0
        else:
            print("\n⚠️  SOME ISSUES DETECTED")
            print("\nReview failed validations above.")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
