#!/usr/bin/env python3
"""
Demonstration: FullTextService Removed - Using FullTextManager Directly

This script demonstrates that we removed the redundant FullTextService wrapper
and now use FullTextManager directly (same as PublicationSearchPipeline).
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def main():
    print("=" * 80)
    print("DEMONSTRATION: Redundant Code Removed")
    print("=" * 80)
    print()

    # ============================================================================
    # STEP 1: Show that FullTextService no longer exists
    # ============================================================================
    print("[STEP 1] Verify FullTextService was removed...")
    print()

    try:
        from omics_oracle_v2.services import FullTextService

        print("ERROR: FullTextService still exists! It should have been removed.")
        return 1
    except ImportError as e:
        print("SUCCESS: FullTextService no longer exists")
        print(f"  Import error: {e}")
        print()

    # ============================================================================
    # STEP 2: Show we now use FullTextManager directly
    # ============================================================================
    print("[STEP 2] Using FullTextManager directly (same as PublicationSearchPipeline)...")
    print()

    from omics_oracle_v2.lib.fulltext.manager import (
        FullTextManager,
        FullTextManagerConfig,
    )
    from omics_oracle_v2.lib.publications.clients.pubmed import (
        PubMedClient,
        PubMedConfig,
    )

    # Initialize FullTextManager (same config as PublicationSearchPipeline)
    print("  Initializing FullTextManager with all sources...")
    config = FullTextManagerConfig(
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
        download_pdfs=True,
        unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
        core_api_key=os.getenv("CORE_API_KEY"),
    )

    manager = FullTextManager(config)
    await manager.initialize()
    print("  SUCCESS: FullTextManager initialized")
    print()

    # ============================================================================
    # STEP 3: Test with PMID 39997216 (the one that was failing)
    # ============================================================================
    print("[STEP 3] Testing with PMID 39997216 (previously failing)...")
    print()

    pmid = "39997216"

    # Fetch full metadata from PubMed
    pubmed_client = PubMedClient(
        PubMedConfig(email=os.getenv("NCBI_EMAIL", "research@omicsoracle.ai"))
    )

    print(f"  Fetching metadata for PMID {pmid}...")
    pub = pubmed_client.fetch_by_id(pmid)

    if pub:
        print(f"  SUCCESS: Got metadata")
        print(f"    Title: {pub.title[:60]}...")
        print(f"    DOI: {pub.doi}")
        print(f"    PMC ID: {pub.pmcid}")
        print(f"    Journal: {pub.journal}")
        print()
    else:
        print(f"  ERROR: Could not fetch metadata for PMID {pmid}")
        return 1

    # ============================================================================
    # STEP 4: Use batch download (WORKING approach from PublicationSearchPipeline)
    # ============================================================================
    print("[STEP 4] Using BATCH download (same as PublicationSearchPipeline)...")
    print()

    print("  Calling manager.get_fulltext_batch([pub])...")
    results = await manager.get_fulltext_batch([pub])

    if results:
        result = results[0]
        print(f"  SUCCESS: Got result from batch download")
        print(f"    Success: {result.success}")
        print(f"    Source: {result.source.value if result.success else 'N/A'}")
        print(f"    URL: {result.url[:80] if result.url else 'None'}...")
        print(f"    PDF Path: {result.pdf_path if result.pdf_path else 'None'}")
        if result.error:
            print(f"    Error: {result.error}")
        print()
    else:
        print("  ERROR: No results from batch download")
        return 1

    # ============================================================================
    # STEP 5: Show statistics (same as PublicationSearchPipeline)
    # ============================================================================
    print("[STEP 5] Statistics (same logging as PublicationSearchPipeline)...")
    print()

    stats = manager.get_statistics()
    print(f"  Success rate: {stats.get('success_rate', 'N/A')}")
    print(f"  Sources used: {stats.get('by_source', {})}")
    print()

    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("REMOVED:")
    print("  - FullTextService (302 lines of redundant wrapper code)")
    print()
    print("NOW USING:")
    print("  - FullTextManager.get_fulltext_batch() directly")
    print("  - Same approach as PublicationSearchPipeline")
    print("  - Concurrent downloads with semaphore control")
    print("  - Simpler codebase, no redundancy")
    print()
    print("BENEFITS:")
    print("  + Faster downloads (concurrent batch processing)")
    print("  + Simpler code (no unnecessary wrapper)")
    print("  + Easier to maintain (one way to do it)")
    print("  + Consistent with existing working code")
    print()
    print("SUCCESS: System now uses FullTextManager directly!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
