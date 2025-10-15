#!/usr/bin/env python3
"""
Test Registry URL Type Storage

Verifies that url_type is properly stored in the registry.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path FIRST
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.pipelines.url_collection.url_validator import URLType
from omics_oracle_v2.lib.registry.geo_registry import GEORegistry
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

# Load environment variables
load_dotenv()


async def test_url_type_storage():
    """Test that URL types are properly stored in registry"""

    print("\n" + "=" * 80)
    print("Test: URL Type Storage in Registry")
    print("=" * 80)

    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Create registry
        registry = GEORegistry(db_path=db_path)

        # Get URLs from Unpaywall (we know this returns url_type)
        publication = Publication(
            pmid="27240256",
            doi="10.1371/journal.pone.0100000",
            title="Test paper",
            authors=[],
            source=PublicationSource.PUBMED,
        )

        print(f"\nTest Publication:")
        print(f"  PMID: {publication.pmid}")
        print(f"  DOI: {publication.doi}")

        # Get URLs
        config = FullTextManagerConfig(
            enable_unpaywall=True,
            unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
            enable_pmc=True,
            enable_core=False,
            enable_institutional=False,
        )
        manager = FullTextManager(config=config)
        await manager.initialize()

        print("\nCollecting URLs from all sources...")
        url_result = await manager.get_all_fulltext_urls(publication)

        if not url_result.all_urls:
            print("\n[FAILED] No URLs found!")
            return False

        print(f"\nFound {len(url_result.all_urls)} URLs")

        # Store in registry
        print("\nStoring in registry...")
        urls_for_storage = [
            {
                "url": u.url,
                "source": u.source.value,
                "priority": u.priority,
                "url_type": u.url_type.value if u.url_type else "unknown",
                "confidence": u.confidence,
                "requires_auth": u.requires_auth,
                "metadata": u.metadata or {},
            }
            for u in url_result.all_urls
        ]

        registry.register_publication(
            pmid=publication.pmid,
            metadata={
                "title": publication.title,
                "doi": publication.doi,
                "authors": [],
            },
            urls=urls_for_storage,
            doi=publication.doi,
        )

        # Retrieve and verify
        print("\nRetrieving from registry...")
        conn = registry.conn
        cursor = conn.execute("SELECT urls FROM publications WHERE pmid = ?", (publication.pmid,))
        row = cursor.fetchone()

        if not row:
            print("\n[FAILED] Publication not found in registry!")
            return False

        stored_urls = json.loads(row[0])

        print(f"\nStored {len(stored_urls)} URLs")
        print("\nURL Details:")
        print("-" * 80)

        all_have_url_type = True
        for i, url_info in enumerate(stored_urls, 1):
            url_type = url_info.get("url_type", "MISSING")
            if url_type == "MISSING":
                all_have_url_type = False

            print(
                f"{i}. Source: {url_info['source']:15s} | Type: {url_type:15s} | Priority: {url_info['priority']}"
            )
            print(f"   URL: {url_info['url'][:70]}...")

        print("-" * 80)

        await manager.cleanup()

        if all_have_url_type:
            print("\n[SUCCESS] All URLs have url_type field stored!")
            return True
        else:
            print("\n[FAILED] Some URLs missing url_type field!")
            return False

    finally:
        # Cleanup
        if Path(db_path).exists():
            Path(db_path).unlink()


async def main():
    """Run test"""
    try:
        success = await test_url_type_storage()
        return 0 if success else 1
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
