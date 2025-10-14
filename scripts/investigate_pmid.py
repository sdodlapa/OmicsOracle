#!/usr/bin/env python3
"""
Investigate PMID 40375322 Download Failure

This script will:
1. Check if the PMID exists in PubMed
2. Try each source individually to diagnose the issue
3. Provide detailed logging of what's happening
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

from omics_oracle_v2.lib.config.settings import load_config
from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager
from omics_oracle_v2.lib.models.publication import Publication

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def investigate_pmid(pmid: str):
    """Investigate why a specific PMID is failing"""

    print("=" * 80)
    print(f"INVESTIGATING PMID: {pmid}")
    print("=" * 80)
    print()

    # Load config
    print("📋 Loading configuration...")
    config = await load_config()

    # Initialize manager
    print("🔧 Initializing FullTextManager...")
    manager = FullTextManager(config)
    await manager.initialize()
    print("✅ Manager initialized")
    print()

    # Create publication object
    pub = Publication()
    pub.pmid = pmid

    # First, let's get metadata from PubMed
    print(f"🔍 Step 1: Fetching PubMed metadata for PMID {pmid}...")
    try:
        from omics_oracle_v2.lib.pubmed.client import PubMedClient

        pubmed_client = PubMedClient()
        await pubmed_client.initialize()

        metadata = await pubmed_client.fetch_publication_details(pmid)

        if metadata:
            print(f"✅ Found in PubMed:")
            print(f"   Title: {metadata.title[:100]}...")
            print(f"   DOI: {metadata.doi or 'Not available'}")
            print(f"   PMCID: {metadata.pmcid or 'Not available'}")
            print(
                f"   Authors: {', '.join(metadata.authors[:3]) if metadata.authors else 'Not available'}..."
            )
            print(f"   Journal: {metadata.journal or 'Not available'}")
            print(f"   Year: {metadata.publication_date or 'Not available'}")

            # Update publication with metadata
            pub.doi = metadata.doi
            pub.pmcid = metadata.pmcid
            pub.title = metadata.title
            pub.journal = metadata.journal

        else:
            print(f"❌ PMID {pmid} not found in PubMed!")
            print("   This PMID may not exist or may be very new.")
            return

    except Exception as e:
        print(f"❌ Error fetching PubMed metadata: {e}")
        print()

    print()
    print("=" * 80)
    print("🔍 Step 2: Trying each full-text source individually")
    print("=" * 80)
    print()

    # Try each source individually
    sources_to_try = [
        ("Institutional Access", manager._try_institutional),
        ("PubMed Central", manager._try_pmc),
        ("Unpaywall", manager._try_unpaywall),
        ("CORE", manager._try_core),
        ("OpenAlex", manager._try_openlex),
        ("bioRxiv/arXiv", manager._try_biorxiv),
        ("Crossref", manager._try_crossref),
    ]

    # Add optional sources if enabled
    if config.fulltext.enable_scihub:
        sources_to_try.append(("Sci-Hub", manager._try_scihub))

    if config.fulltext.enable_libgen:
        sources_to_try.append(("LibGen", manager._try_libgen))

    results = []

    for source_name, source_func in sources_to_try:
        print(f"📡 Trying {source_name}...")
        try:
            result = await source_func(pub)

            if result.success:
                print(f"   ✅ SUCCESS: {result.url}")
                print(f"      Metadata: {result.metadata}")
                results.append((source_name, "SUCCESS", result.url))
            else:
                print(f"   ❌ Failed: {result.error}")
                results.append((source_name, "FAILED", result.error))

        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append((source_name, "ERROR", str(e)))

        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print()

    successful = [r for r in results if r[1] == "SUCCESS"]
    failed = [r for r in results if r[1] != "SUCCESS"]

    print(f"Successful sources: {len(successful)}/{len(results)}")
    print()

    if successful:
        print("✅ URLs found:")
        for source_name, status, url in successful:
            print(f"   • {source_name}: {url}")
    else:
        print("❌ No URLs found from any source")

    print()
    print("❌ Failed sources:")
    for source_name, status, error in failed:
        print(f"   • {source_name}: {error}")

    print()
    print("=" * 80)
    print("🔍 DIAGNOSIS")
    print("=" * 80)
    print()

    if successful:
        print("✅ GOOD NEWS: At least one source has the paper!")
        print("   The parallel collection should have found this.")
        print("   The download may have failed due to:")
        print("   - Network issues")
        print("   - Invalid PDF at the URL")
        print("   - Access restrictions")
        print()
        print("   Try downloading from the successful URL(s) manually to verify.")
    else:
        print("❌ BAD NEWS: No sources have this paper")
        print()

        if not pub.doi:
            print("   ⚠️  Missing DOI - many sources require a DOI")
            print("   Recommendation: This paper may be too new or not indexed properly")

        if not pub.pmcid:
            print("   ⚠️  Missing PMCID - paper not in PubMed Central")
            print("   Recommendation: Paper may be behind a paywall")

        print()
        print("   Possible reasons:")
        print("   1. Paper is very recent and not yet indexed")
        print("   2. Paper is behind a paywall (subscription required)")
        print("   3. Paper is not open access")
        print("   4. Journal doesn't provide PDFs publicly")
        print()
        print("   Recommendations:")
        print("   1. Wait a few days if paper is very new")
        print("   2. Check if your institution has access")
        print("   3. Contact the authors for a copy")
        print("   4. Use the GEO metadata for analysis instead")


async def main():
    """Main function"""

    # The problematic PMID from the error message
    pmid = "40375322"

    print()
    print("🔬 OmicsOracle - PMID Investigation Tool")
    print("=" * 80)
    print()
    print(f"This tool will investigate why PMID {pmid} failed to download")
    print("and provide detailed diagnostics.")
    print()

    await investigate_pmid(pmid)

    print()
    print("=" * 80)
    print("Investigation complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
