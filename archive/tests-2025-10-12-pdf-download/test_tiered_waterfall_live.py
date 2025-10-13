#!/usr/bin/env python3
"""
Live Test: Tiered Waterfall Implementation

This script tests the tiered waterfall retry system with PMID 39997216.
It will show all retry attempts as they happen in real-time.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
load_dotenv()

from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient, PubMedConfig
from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager
import logging

# Setup logging to see WARNING level messages
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s - %(message)s'
)

async def test_tiered_waterfall():
    """Test the tiered waterfall with PMID 39997216."""

    print("\n" + "="*70)
    print("TESTING TIERED WATERFALL - PMID 39997216")
    print("="*70)

    # Initialize clients
    print("\n[1/5] Initializing clients...")
    pubmed_config = PubMedConfig(
        email=os.getenv("NCBI_EMAIL", "test@example.com"),
        tool=os.getenv("NCBI_TOOL", "OmicsOracle"),
        api_key=os.getenv("NCBI_API_KEY")
    )
    pubmed = PubMedClient(pubmed_config)

    fulltext_config = FullTextManagerConfig(
        core_api_key=os.getenv("CORE_API_KEY"),
        unpaywall_email=os.getenv("UNPAYWALL_EMAIL", os.getenv("NCBI_EMAIL", "test@example.com"))
    )
    fulltext_manager = FullTextManager(fulltext_config)
    await fulltext_manager.initialize()
    pdf_downloader = PDFDownloadManager(validate_pdf=True, max_concurrent=1)

    # Fetch publication metadata
    print("[2/5] Fetching publication metadata...")
    pub = pubmed.fetch_by_id("39997216")
    print(f"   Title: {pub.title[:60]}...")
    print(f"   DOI: {pub.doi}")
    print(f"   PMC: {pub.pmcid}")

    # Get first URL (will probably be institutional)
    print("\n[3/5] Getting initial full-text URL...")
    result = await fulltext_manager.get_fulltext(pub)
    if result.success:
        pub.fulltext_url = result.url
        pub.fulltext_source = result.source.value
        print(f"   Source: {result.source.value}")
        print(f"   URL: {result.url}")
    else:
        print("   ❌ No URL found!")
        return

    # Try to download (will probably fail with HTTP 403)
    print("\n[4/5] Attempting first download...")
    pdf_dir = Path("data/test_pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)

    download_result = await pdf_downloader._download_single(pub, pub.fulltext_url, pdf_dir)

    if download_result.success:
        print(f"   ✅ SUCCESS on first try!")
        print(f"   File: {download_result.pdf_path}")
        return
    else:
        print(f"   ❌ FAILED: {download_result.error}")
        print(f"\n[5/5] Starting TIERED WATERFALL RETRY...")
        print(f"   Will try all remaining sources until success...\n")

    # TIERED WATERFALL RETRY
    tried_sources = [pub.fulltext_source]
    max_attempts = 10
    attempt = 0
    download_succeeded = False

    while not download_succeeded and attempt < max_attempts:
        attempt += 1

        print(f"   🔄 Attempt {attempt}: Getting next source (skipping: {', '.join(tried_sources)})...")

        # Get next URL, skipping tried sources
        retry_result = await fulltext_manager.get_fulltext(pub, skip_sources=tried_sources)

        if not retry_result.success or not retry_result.url:
            print(f"      ❌ No more sources available")
            break

        current_source = retry_result.source.value
        tried_sources.append(current_source)
        pub.fulltext_url = retry_result.url
        pub.fulltext_source = current_source

        print(f"      🆕 Trying: {current_source}")
        print(f"      📎 URL: {retry_result.url[:80]}...")

        # Try download
        single_result = await pdf_downloader._download_single(pub, retry_result.url, pdf_dir)

        if single_result.success and single_result.pdf_path:
            download_succeeded = True
            print(f"      ✅ SUCCESS!")
            print(f"      📄 File: {single_result.pdf_path}")
            print(f"      📊 Size: {single_result.file_size / 1024:.1f} KB")
            print(f"\n" + "="*70)
            print(f"✅ DOWNLOADED SUCCESSFULLY VIA {current_source.upper()}")
            print(f"   Attempts: {attempt + 1} (tried {len(tried_sources)} sources)")
            print("="*70 + "\n")
        else:
            print(f"      ⚠️  Failed: {single_result.error}")
            print(f"      ➡️  Continuing to next source...\n")

    if not download_succeeded:
        print(f"\n" + "="*70)
        print(f"❌ EXHAUSTED ALL SOURCES")
        print(f"   Tried {len(tried_sources)} sources: {', '.join(tried_sources)}")
        print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_tiered_waterfall())
