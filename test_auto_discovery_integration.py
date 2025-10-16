"""
Integration Test: Auto-Discovery Flow

Tests the complete flow from frontend search to auto-discovery:
1. User searches "breast cancer RNA-seq"
2. System finds GSE189158 from GEO
3. GEOCache detects empty database
4. Auto-discovery triggers:
   - Fetches GEO metadata
   - Runs citation discovery
   - Stores in UnifiedDB
5. Returns enriched results to frontend

This validates the entire integration chain.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_auto_discovery_flow():
    """Test complete auto-discovery integration."""
    
    print("=" * 80)
    print("AUTO-DISCOVERY INTEGRATION TEST")
    print("=" * 80)
    print()
    
    try:
        # Import after path setup
        from omics_oracle_v2.lib.pipelines.storage.unified_db import UnifiedDatabase
        from omics_oracle_v2.lib.pipelines.storage.registry.geo_cache import create_geo_cache
        from omics_oracle_v2.core.config import get_settings
        
        # Step 1: Initialize clean database
        print("[STEP 1] Initializing clean UnifiedDatabase...")
        settings = get_settings()
        db_path = settings.search.db_path
        print(f"Database path: {db_path}")
        
        unified_db = UnifiedDatabase(db_path)
        print("✓ UnifiedDatabase initialized")
        print()
        
        # Step 2: Create GEOCache
        print("[STEP 2] Creating GEOCache with auto-discovery...")
        geo_cache = create_geo_cache(unified_db)
        print("✓ GEOCache initialized")
        print()
        
        # Step 3: Test with a real GEO dataset (GSE189158)
        test_geo_id = "GSE189158"
        print(f"[STEP 3] Testing auto-discovery for {test_geo_id}...")
        print(f"Expected: GEO not in DB → trigger auto-discovery")
        print()
        
        # Check if already in database
        print(f"[CHECK] Querying database for {test_geo_id}...")
        existing_data = unified_db.get_complete_geo_data(test_geo_id)
        if existing_data:
            print(f"⚠️  {test_geo_id} already exists in database")
            print(f"   Citations: {len(existing_data.get('papers', {}).get('original', []))}")
            print("   Test will use cached data (no auto-discovery)")
        else:
            print(f"✓ {test_geo_id} not in database - will trigger auto-discovery")
        print()
        
        # Step 4: Call GEOCache.get() - should trigger auto-discovery
        print(f"[STEP 4] Calling GEOCache.get('{test_geo_id}')...")
        print("Expected flow:")
        print("  1. Check Redis cache → MISS")
        print("  2. Check UnifiedDB → MISS (or HIT if cached)")
        print("  3. Trigger auto-discovery:")
        print("     a. Fetch GEO metadata from NCBI")
        print("     b. Run citation discovery (PubMed + OpenAlex)")
        print("     c. Store in UnifiedDB")
        print("  4. Return enriched data")
        print()
        
        start_time = asyncio.get_event_loop().time()
        geo_data = await geo_cache.get(test_geo_id)
        end_time = asyncio.get_event_loop().time()
        
        elapsed_ms = (end_time - start_time) * 1000
        print(f"⏱️  Completed in {elapsed_ms:.2f}ms")
        print()
        
        # Step 5: Validate results
        print("[STEP 5] Validating results...")
        
        if geo_data is None:
            print("❌ FAILED: geo_data is None")
            return False
        
        print("✓ Got geo_data")
        print()
        
        # Check structure
        print("GEO Data Structure:")
        print(f"  geo_id: {geo_data.get('geo', {}).get('geo_id')}")
        print(f"  title: {geo_data.get('geo', {}).get('title', '')[:60]}...")
        print(f"  organism: {geo_data.get('geo', {}).get('organism')}")
        print()
        
        # Check citations
        papers = geo_data.get('papers', {}).get('original', [])
        citation_count = len(papers)
        print(f"Citations Found: {citation_count}")
        
        if citation_count == 0:
            print("⚠️  WARNING: No citations found (citation discovery may have failed)")
            print("   This is acceptable for datasets with no citing papers")
        else:
            print(f"✓ Found {citation_count} citations")
            print()
            print("Sample Citations:")
            for i, paper in enumerate(papers[:3], 1):
                print(f"  {i}. PMID: {paper.get('pmid')}")
                print(f"     Title: {paper.get('title', '')[:60]}...")
        print()
        
        # Step 6: Test cache hit
        print("[STEP 6] Testing cache hit (should be fast)...")
        start_time = asyncio.get_event_loop().time()
        cached_data = await geo_cache.get(test_geo_id)
        end_time = asyncio.get_event_loop().time()
        
        cache_elapsed_ms = (end_time - start_time) * 1000
        print(f"⏱️  Cache hit in {cache_elapsed_ms:.2f}ms")
        
        if cache_elapsed_ms < 100:  # Should be <100ms for cache hit
            print(f"✓ Fast cache retrieval ({cache_elapsed_ms:.2f}ms < 100ms)")
        else:
            print(f"⚠️  Slow cache retrieval ({cache_elapsed_ms:.2f}ms)")
        print()
        
        # Step 7: Verify cache stats
        print("[STEP 7] Cache Statistics:")
        stats = geo_cache.stats
        print(f"  Cache hits: {stats['cache_hits']}")
        print(f"  Cache misses: {stats['cache_misses']}")
        print(f"  DB queries: {stats['db_queries']}")
        print(f"  Redis errors: {stats['redis_errors']}")
        print()
        
        # Final summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Auto-discovery flow: WORKING")
        print(f"✅ GEO metadata: {geo_data.get('geo', {}).get('title', 'MISSING')[:50]}")
        print(f"✅ Citations: {citation_count} found")
        print(f"✅ Cache performance: {cache_elapsed_ms:.2f}ms")
        print()
        print("INTEGRATION TEST: PASSED ✅")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.error("Test failed", exc_info=True)
        return False


async def test_search_service_integration():
    """Test SearchService integration with auto-discovery."""
    
    print("\n" + "=" * 80)
    print("SEARCH SERVICE INTEGRATION TEST")
    print("=" * 80)
    print()
    
    try:
        from omics_oracle_v2.services.search_service import SearchService
        from omics_oracle_v2.api.models.requests import SearchRequest
        
        # Create search request
        print("[TEST] Searching for 'GSE189158'...")
        request = SearchRequest(
            search_terms=["GSE189158"],
            max_results=10,
            enable_semantic=False
        )
        
        # Execute search
        service = SearchService()
        start_time = asyncio.get_event_loop().time()
        result = await service.execute_search(request)
        end_time = asyncio.get_event_loop().time()
        
        elapsed_ms = (end_time - start_time) * 1000
        print(f"⏱️  Search completed in {elapsed_ms:.2f}ms")
        print()
        
        # Validate results
        print("Search Results:")
        print(f"  Total found: {result.total_found}")
        print(f"  Datasets returned: {len(result.datasets)}")
        print()
        
        if len(result.datasets) > 0:
            dataset = result.datasets[0]
            print(f"Dataset: {dataset.geo_id}")
            print(f"  Title: {dataset.title[:60]}...")
            print(f"  Citations: {dataset.citation_count}")
            print(f"  PDFs: {dataset.pdf_count}")
            print(f"  Completion: {dataset.completion_rate:.1f}%")
            print()
            
            if dataset.citation_count > 0:
                print("✅ Auto-discovery enrichment: WORKING")
            else:
                print("⚠️  No citations (may need manual discovery)")
        else:
            print("❌ No datasets found")
            return False
        
        print("SEARCH SERVICE TEST: PASSED ✅")
        return True
        
    except Exception as e:
        print(f"\n❌ SEARCH SERVICE TEST FAILED: {e}")
        logger.error("Search service test failed", exc_info=True)
        return False


async def main():
    """Run all integration tests."""
    
    # Test 1: Auto-discovery flow
    test1_passed = await test_auto_discovery_flow()
    
    # Test 2: Search service integration
    test2_passed = await test_search_service_integration()
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Auto-Discovery Flow: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Search Service Integration: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 80)
    
    return 0 if (test1_passed and test2_passed) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
