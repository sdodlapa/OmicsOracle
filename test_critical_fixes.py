"""
Test Critical Fixes:
1. PMC download for PMID 39997216
2. Hybrid search returning publications

Run: python test_critical_fixes.py
"""

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_pmc_download():
    """Test PMC download for PMID 39997216 which exists at PMC11851118"""
    print("\n" + "="*80)
    print("TEST 1: PMC Download for PMID 39997216")
    print("="*80)
    
    from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
    from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
    
    # Configure with PMC enabled
    config = FullTextManagerConfig(
        enable_pmc=True,
        enable_institutional=False,
        enable_unpaywall=False,
        enable_core=False,
        enable_scihub=False,
        enable_libgen=False,
        timeout_per_source=30
    )
    
    manager = FullTextManager(config)
    await manager.initialize()
    
    # Create publication with PMID
    publication = Publication(
        pmid="39997216",
        title="Test Publication",
        source=PublicationSource.PUBMED
    )
    
    print(f"\n📄 Testing PMID: {publication.pmid}")
    print(f"Expected PMC ID: PMC11851118")
    print(f"Expected URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11851118/")
    
    # Try to get full-text
    result = await manager.get_fulltext(publication)
    
    print(f"\n✅ Result:")
    print(f"  - Success: {result.success}")
    print(f"  - Source: {result.source}")
    print(f"  - URL: {result.url}")
    print(f"  - PDF Path: {result.pdf_path}")
    print(f"  - Error: {result.error}")
    print(f"  - Metadata: {result.metadata}")
    
    if result.success:
        print(f"\n🎉 SUCCESS! PMC download is working!")
    else:
        print(f"\n❌ FAILED! PMC download not working. Error: {result.error}")
    
    return result.success


async def test_hybrid_search():
    """Test hybrid search returns publications"""
    print("\n" + "="*80)
    print("TEST 2: Hybrid Search Returns Publications")
    print("="*80)
    
    from omics_oracle_v2.lib.pipelines.unified_search_pipeline import UnifiedSearchPipeline, UnifiedSearchConfig
    
    # Configure pipeline
    config = UnifiedSearchConfig(
        enable_geo_search=True,
        enable_publication_search=True,  # CRITICAL!
        enable_llm_ranking=False,  # Disable LLM to speed up test
        enable_semantic_search=False,
    )
    
    pipeline = UnifiedSearchPipeline(config)
    
    query = "DNA methylation HiC"
    print(f"\n🔍 Testing query: '{query}'")
    
    # Run search
    result = await pipeline.search(query, max_results=5)
    
    print(f"\n📊 Results:")
    print(f"  - GEO Datasets: {result.datasets_count}")
    print(f"  - Publications: {result.publications_count}")
    print(f"  - Search Type: {result.search_type}")
    print(f"  - Search Logs: {result.search_logs[:3] if result.search_logs else []}")
    
    if result.publications_count > 0:
        print(f"\n✅ Publications returned:")
        for i, pub in enumerate(result.publications[:3], 1):
            print(f"  {i}. {pub.title[:80]}...")
            print(f"     PMID: {pub.pmid}, DOI: {pub.doi}")
    
    if result.publications_count > 0:
        print(f"\n🎉 SUCCESS! Hybrid search is working!")
        success = True
    else:
        print(f"\n❌ FAILED! Hybrid search not returning publications")
        success = False
    
    return success


async def main():
    """Run all tests"""
    print("\n🧪 CRITICAL FIXES VALIDATION TEST")
    print("="*80)
    
    # Test 1: PMC Download
    pmc_success = await test_pmc_download()
    
    # Test 2: Hybrid Search
    hybrid_success = await test_hybrid_search()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ PMC Download: {'PASS' if pmc_success else 'FAIL'}")
    print(f"✅ Hybrid Search: {'PASS' if hybrid_success else 'FAIL'}")
    
    if pmc_success and hybrid_success:
        print("\n🎉 ALL TESTS PASSED! Both critical issues are fixed!")
    else:
        print("\n⚠️ SOME TESTS FAILED - see details above")


if __name__ == "__main__":
    asyncio.run(main())
