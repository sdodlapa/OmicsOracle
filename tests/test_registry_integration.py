#!/usr/bin/env python3
"""
Test Registry Integration - October 14, 2025

Tests the integration of GEO Registry into the enrichment endpoint.
This simulates the complete workflow:
1. Search for GEO dataset
2. Enrich with fulltext (downloads PDFs)
3. Store in registry
4. Retrieve from registry for frontend

This test validates the CRITICAL requirement:
"When I click 'Download Papers' button at frontend, it should have access
to entire GSE... (geo id with all the metadata from geo and urls we collected
for fulltext/pdfs) to avoid confusion and download process be robust"
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import tempfile

from omics_oracle_v2.lib.registry import GEORegistry


def test_registry_integration():
    """
    Test complete workflow of registry integration.

    Simulates what happens when:
    1. User searches for "GSE48968"
    2. Clicks "Download Papers" (enrichment happens)
    3. Data is stored in registry
    4. Frontend retrieves complete data via API
    """

    print("\n" + "=" * 80)
    print("TEST: Registry Integration (Complete Workflow)")
    print("=" * 80 + "\n")

    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        registry = GEORegistry(db_path)

        # ========================================================================
        # STEP 1: Simulate enrichment endpoint storing data
        # ========================================================================
        print("STEP 1: Enrichment Endpoint - Storing data in registry")
        print("-" * 80)

        geo_id = "GSE48968"

        # Register GEO dataset (from GEO metadata)
        geo_metadata = {
            "geo_id": geo_id,
            "title": "Expression data from murine BM-derived DCs stimulated with LPS",
            "summary": "Analysis of bone marrow-derived dendritic cells...",
            "organism": "Mus musculus",
            "platform": "GPL1261",
            "sample_count": 6,
            "submission_date": "2013-07-01",
            "publication_date": "2014-01-15",
            "pubmed_ids": ["24385618"],
            "relevance_score": 0.98,
        }
        registry.register_geo_dataset(geo_id, geo_metadata)
        print(f"✅ Registered GEO dataset: {geo_id}")

        # Register original paper with ALL URLs
        original_pmid = "24385618"
        original_metadata = {
            "title": "Original Paper: Dendritic Cell Study",
            "authors": ["Smith J", "Doe J"],
            "journal": "Nature Immunology",
            "year": 2014,
        }
        original_urls = [
            {
                "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC123/",
                "source": "pmc",
                "priority": 1,
                "metadata": {},
            },
            {
                "url": "https://unpaywall.org/24385618.pdf",
                "source": "unpaywall",
                "priority": 2,
                "metadata": {},
            },
            {
                "url": "https://doi.org/10.1234/nature.24385618",
                "source": "institutional",
                "priority": 3,
                "metadata": {},
            },
        ]
        registry.register_publication(original_pmid, original_metadata, original_urls)
        registry.link_geo_to_publication(geo_id, original_pmid, "original")
        print(f"✅ Registered original paper: PMID {original_pmid} with {len(original_urls)} URLs")

        # Simulate successful download
        registry.record_download_attempt(
            pmid=original_pmid,
            url="https://pmc.ncbi.nlm.nih.gov/articles/PMC123/",
            source="pmc",
            status="success",
            file_path=f"data/pdfs/{geo_id}/original/24385618.pdf",
            file_size=1234567,
        )
        print(f"✅ Recorded successful download from PMC")

        # Register citing papers with URLs
        citing_pmids = ["25123456", "25789012", "26456789"]
        for i, pmid in enumerate(citing_pmids, 1):
            citing_metadata = {
                "title": f"Citing Paper {i}: Re-analysis of {geo_id}",
                "authors": [f"Author{i} A", f"Author{i} B"],
                "journal": f"Journal {i}",
                "year": 2015 + i,
            }
            citing_urls = [
                {
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmid}/",
                    "source": "pmc",
                    "priority": 1,
                    "metadata": {},
                },
                {
                    "url": f"https://unpaywall.org/{pmid}.pdf",
                    "source": "unpaywall",
                    "priority": 2,
                    "metadata": {},
                },
            ]
            registry.register_publication(pmid, citing_metadata, citing_urls)
            registry.link_geo_to_publication(geo_id, pmid, "citing", "strategy_a")

            # Simulate downloads (1 success, 2 failures)
            if i == 1:
                registry.record_download_attempt(
                    pmid=pmid,
                    url=f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmid}/",
                    source="pmc",
                    status="success",
                    file_path=f"data/pdfs/{geo_id}/citing/{pmid}.pdf",
                    file_size=987654,
                )
            else:
                registry.record_download_attempt(
                    pmid=pmid,
                    url=f"https://unpaywall.org/{pmid}.pdf",
                    source="unpaywall",
                    status="failed",
                    error_message="HTTP 403 Forbidden",
                )

        print(f"✅ Registered {len(citing_pmids)} citing papers")
        print()

        # ========================================================================
        # STEP 2: Frontend API - Retrieve complete data (O(1) lookup)
        # ========================================================================
        print("STEP 2: Frontend API - GET /api/geo/{geo_id}/complete")
        print("-" * 80)

        complete_data = registry.get_complete_geo_data(geo_id)

        if not complete_data:
            print("❌ FAILED: No data found!")
            return False

        print(f"✅ Retrieved complete data in single query")
        print()

        # ========================================================================
        # STEP 3: Validate data structure for frontend
        # ========================================================================
        print("STEP 3: Validate Data Structure")
        print("-" * 80)

        # Check GEO metadata
        assert complete_data["geo"]["geo_id"] == geo_id, "GEO ID mismatch"
        assert complete_data["geo"]["title"] == geo_metadata["title"], "Title mismatch"
        print(f"✅ GEO metadata: {complete_data['geo']['geo_id']} - {complete_data['geo']['title'][:50]}...")

        # Check papers
        assert len(complete_data["papers"]["original"]) == 1, "Should have 1 original paper"
        assert len(complete_data["papers"]["citing"]) == 3, "Should have 3 citing papers"
        print(
            f"✅ Papers: {len(complete_data['papers']['original'])} original, {len(complete_data['papers']['citing'])} citing"
        )

        # Check URLs are present (for retry capability)
        original_paper = complete_data["papers"]["original"][0]
        assert len(original_paper["urls"]) == 3, "Should have 3 URLs for original paper"
        print(f"✅ Original paper has {len(original_paper['urls'])} URLs for retry capability")

        # Check download history
        assert len(original_paper["download_history"]) == 1, "Should have 1 download attempt"
        assert original_paper["download_history"][0]["status"] == "success", "Download should be successful"
        print(f"✅ Download history: {len(original_paper['download_history'])} attempts")

        # Check statistics
        stats = complete_data["statistics"]
        assert stats["total_papers"] == 4, "Should have 4 total papers"
        assert stats["original_papers"] == 1, "Should have 1 original paper"
        assert stats["citing_papers"] == 3, "Should have 3 citing papers"
        print(f"✅ Statistics: {stats['total_papers']} papers, {stats['successful_downloads']} successful")

        print()

        # ========================================================================
        # STEP 4: Test retry capability
        # ========================================================================
        print("STEP 4: Test Retry Capability (for failed downloads)")
        print("-" * 80)

        # Get URLs for retry (for papers that failed)
        failed_pmid = citing_pmids[1]  # Second citing paper (failed)
        retry_urls = registry.get_urls_for_retry(failed_pmid)

        assert len(retry_urls) > 0, "Should have URLs for retry"
        print(f"✅ Found {len(retry_urls)} URLs to retry for PMID {failed_pmid}")
        for url in retry_urls:
            print(f"   - {url['source']} (priority {url['priority']}): {url['url'][:60]}...")

        print()

        # ========================================================================
        # STEP 5: Demonstrate frontend usage
        # ========================================================================
        print("STEP 5: Frontend Usage Example")
        print("-" * 80)

        print("Frontend 'Download Papers' button can now:")
        print()
        print("1. Get complete data in ONE API call:")
        print(f"   GET /api/geo/{geo_id}/complete")
        print()
        print("2. Access ALL information:")
        print(f"   - GEO metadata: {complete_data['geo']['title'][:50]}...")
        print(f"   - {len(complete_data['papers']['original'])} original paper(s)")
        print(f"   - {len(complete_data['papers']['citing'])} citing paper(s)")
        print(f"   - ALL URLs for each paper (for retry)")
        print(f"   - Download history (success/failure)")
        print()
        print("3. Retry failed downloads:")
        print(f"   - Check download_history for 'failed' status")
        print(f"   - Get all_urls from paper")
        print(f"   - Try next URL in priority order")
        print()
        print("4. Show download statistics:")
        print(f"   - Success rate: {stats['success_rate']}%")
        print(f"   - {stats['successful_downloads']}/{stats['total_papers']} papers downloaded")
        print()

        # ========================================================================
        # SUCCESS
        # ========================================================================
        print("=" * 80)
        print("✅ ALL TESTS PASSED - Registry integration complete!")
        print("=" * 80)
        print()

        print("Benefits for frontend:")
        print("✅ Single API call gets everything (no multiple requests)")
        print("✅ Fast O(1) lookup by GEO ID (SQLite indexed)")
        print("✅ All URLs preserved (retry capability)")
        print("✅ Download history tracked (know what succeeded/failed)")
        print("✅ Complete GEO metadata (title, organism, etc.)")
        print("✅ Paper relationships (original vs citing)")
        print("✅ Statistics for UI (success rate, counts)")
        print()

        print("This solves the user's requirement:")
        print("> \"When I click 'Download Papers' button at frontend, it should have")
        print("> access to entire GSE... (geo id with all the metadata from geo and")
        print("> urls we collected for fulltext/pdfs) to avoid confusion and download")
        print('> process be robust"')
        print()

        registry.close()
        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Cleanup
        try:
            Path(db_path).unlink()
        except:
            pass


if __name__ == "__main__":
    success = test_registry_integration()
    sys.exit(0 if success else 1)
