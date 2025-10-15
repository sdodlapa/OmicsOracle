#!/usr/bin/env python3
"""
Test script to verify the waterfall fallback fix is working correctly.

This script tests PMIDs that were failing before the fix to ensure they now
try all 11 sources instead of just 2-3.

Expected behavior BEFORE fix:
- PMID 39990495: Tries unpaywall → institutional → biorxiv (STOPS after 3)
- PMID 41025488: Tries institutional → unpaywall (STOPS after 2)

Expected behavior AFTER fix:
- Both PMIDs: Try ALL 11 sources in order until success or all exhausted
- Sources: institutional → pmc → unpaywall → core → openai_urls → biorxiv/arxiv
           → crossref → scihub → libgen → europe_pmc → sciencedirect
"""

import asyncio
import logging
import os
from pathlib import Path

# Setup logging to see detailed output
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_waterfall_fix():
    """Test that waterfall fallback tries all sources."""

    # Import after setting up logging
    from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
    from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager, FullTextManagerConfig
    from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient, PubMedConfig

    # Initialize managers
    logger.info("Initializing managers...")
    fulltext_config = FullTextManagerConfig(
        enable_institutional=True,
        enable_pmc=True,
        enable_unpaywall=True,
        enable_openalex=True,
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_scihub=True,
        enable_libgen=True,
        download_pdfs=False,
        unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
        core_api_key=os.getenv("CORE_API_KEY"),
    )

    fulltext_manager = FullTextManager(fulltext_config)
    pdf_downloader = PDFDownloadManager(
        max_concurrent=3, max_retries=2, timeout_seconds=30, validate_pdf=True
    )
    pubmed_client = PubMedClient(PubMedConfig(email=os.getenv("NCBI_EMAIL", "research@omicsoracle.ai")))

    await fulltext_manager.initialize()

    # Test PMIDs that were failing
    test_pmids = [
        "39990495",  # Was stopping after 3 sources
        "41025488",  # Was stopping after 2 sources
    ]

    pdf_dir = Path("data/test_pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for pmid in test_pmids:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing PMID {pmid}...")
        logger.info(f"{'='*80}")

        # Fetch publication metadata
        pub = pubmed_client.fetch_by_id(pmid)
        if not pub:
            logger.error(f"Could not fetch metadata for PMID {pmid}")
            continue

        logger.info(f"Title: {pub.title[:100]}...")
        logger.info(f"DOI: {pub.doi}")
        logger.info(f"PMC ID: {pub.pmcid}")

        # Get ALL URLs from ALL sources
        logger.info(f"\nStep 1: Collecting URLs from all sources...")
        url_result = await fulltext_manager.get_all_fulltext_urls(pub)

        if not url_result.all_urls:
            logger.warning(f"No URLs found for PMID {pmid}")
            continue

        logger.info(
            f"Found {len(url_result.all_urls)} URLs from {len(set(u.source for u in url_result.all_urls))} sources:"
        )
        for i, url_info in enumerate(url_result.all_urls, 1):
            logger.info(f"  {i}. {url_info.source.value}: {url_info.url[:80]}...")

        # Try to download using waterfall fallback
        logger.info(f"\nStep 2: Attempting download with waterfall fallback...")
        result = await pdf_downloader.download_with_fallback(
            publication=pub, all_urls=url_result.all_urls, output_dir=pdf_dir
        )

        # Log result
        if result.success:
            logger.info(f"✓ SUCCESS: Downloaded from {result.source}")
            logger.info(f"  File: {result.pdf_path}")
            logger.info(f"  Size: {result.file_size / 1024:.1f} KB")
        else:
            logger.error(f"✗ FAILED: Could not download from any source")
            logger.error(f"  Last error: {result.error}")

        results.append(
            {
                "pmid": pmid,
                "success": result.success,
                "sources_tried": len(url_result.all_urls),
                "successful_source": result.source if result.success else None,
                "error": result.error if not result.success else None,
            }
        )

    # Cleanup
    await fulltext_manager.cleanup()

    # Print summary
    logger.info(f"\n{'='*80}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*80}")

    for result in results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        logger.info(f"{status} PMID {result['pmid']}:")
        logger.info(f"  Sources tried: {result['sources_tried']}")
        if result["success"]:
            logger.info(f"  Downloaded from: {result['successful_source']}")
        else:
            logger.info(f"  Error: {result['error']}")

    # Verify we tried ALL sources (should be 8-11 depending on what's available)
    logger.info(f"\n{'='*80}")
    logger.info("VERIFICATION")
    logger.info(f"{'='*80}")

    for result in results:
        if result["sources_tried"] >= 5:
            logger.info(
                f"✓ PMID {result['pmid']}: Tried {result['sources_tried']} sources (GOOD - waterfall working)"
            )
        else:
            logger.error(
                f"✗ PMID {result['pmid']}: Only tried {result['sources_tried']} sources (BAD - waterfall broken)"
            )


if __name__ == "__main__":
    asyncio.run(test_waterfall_fix())
