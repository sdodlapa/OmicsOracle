"""
Comprehensive test of GEO Citation Pipeline with multiple queries.

Tests different scenarios:
1. Well-established datasets (should have citations)
2. Cancer genomics datasets
3. Disease-specific queries
4. Verify robustness across different data types
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime

from omics_oracle_v2.lib.workflows.geo_citation_pipeline import (
    GEOCitationPipeline,
    GEOCitationConfig
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_query(query: str, description: str, max_datasets: int = 3):
    """Test a single query"""
    logger.info("="*80)
    logger.info(f"TEST: {description}")
    logger.info(f"Query: '{query}'")
    logger.info("="*80)
    
    config = GEOCitationConfig(
        geo_max_results=max_datasets,
        enable_synonym_expansion=False,
        citation_max_results=30,  # Get more papers for testing
        use_citation_strategy=True,
        use_mention_strategy=True,
        enable_institutional=True,
        enable_unpaywall=True,
        enable_core=True,
        enable_scihub=False,
        enable_libgen=False,
        download_pdfs=False,  # Skip PDF download for speed
        output_dir=Path("data/geo_citation_collections"),
        organize_by_geo_id=True
    )
    
    pipeline = GEOCitationPipeline(config)
    
    try:
        result = await pipeline.collect(
            query=query,
            max_datasets=max_datasets,
            max_citing_papers=30
        )
        
        # Print results
        logger.info("")
        logger.info("RESULTS:")
        logger.info(f"  GEO datasets: {len(result.datasets_found)}")
        for ds in result.datasets_found:
            logger.info(f"    - {ds.geo_id}: {ds.title[:80]}...")
            logger.info(f"      PubMed IDs: {ds.pubmed_ids}")
            logger.info(f"      Samples: {ds.sample_count}")
        
        logger.info(f"  Citing papers: {result.total_citing_papers}")
        logger.info(f"  Full-text coverage: {result.fulltext_coverage:.1f}%")
        logger.info(f"  Duration: {result.duration_seconds:.1f}s")
        
        # Success criteria
        success = {
            "found_datasets": len(result.datasets_found) > 0,
            "found_citations": result.total_citing_papers > 0,
            "got_fulltext": result.fulltext_coverage > 0,
            "completed": True
        }
        
        logger.info("")
        logger.info("SUCCESS CHECKS:")
        logger.info(f"  ✅ Found datasets: {success['found_datasets']}")
        logger.info(f"  {'✅' if success['found_citations'] else '⚠️ '} Found citations: {success['found_citations']}")
        logger.info(f"  {'✅' if success['got_fulltext'] else '⚠️ '} Got full-text: {success['got_fulltext']}")
        logger.info(f"  ✅ Completed: {success['completed']}")
        
        return success
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return {
            "found_datasets": False,
            "found_citations": False,
            "got_fulltext": False,
            "completed": False,
            "error": str(e)
        }


async def main():
    """Run comprehensive test suite"""
    logger.info("")
    logger.info("="*80)
    logger.info("GEO CITATION PIPELINE - COMPREHENSIVE TEST SUITE")
    logger.info("="*80)
    logger.info("")
    
    test_cases = [
        # Test 1: Well-known cancer genomics (should have many citations)
        {
            "query": "TCGA breast cancer",
            "description": "TCGA breast cancer datasets (well-established)",
            "max_datasets": 2
        },
        
        # Test 2: Specific disease with RNA-seq
        {
            "query": "alzheimer disease RNA-seq",
            "description": "Alzheimer's disease RNA sequencing",
            "max_datasets": 2
        },
        
        # Test 3: Specific organism and technique
        {
            "query": "mouse liver ChIP-seq",
            "description": "Mouse liver ChIP sequencing",
            "max_datasets": 2
        },
        
        # Test 4: COVID-19 research (recent but should have citations)
        {
            "query": "COVID-19 transcriptomics",
            "description": "COVID-19 transcriptomics studies",
            "max_datasets": 2
        },
        
        # Test 5: Specific gene/biomarker
        {
            "query": "TP53 mutation cancer",
            "description": "TP53 mutations in cancer",
            "max_datasets": 2
        }
    ]
    
    results = []
    start_time = datetime.now()
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"TEST {i}/{len(test_cases)}")
        logger.info(f"{'='*80}\n")
        
        result = await test_query(**test_case)
        results.append({
            "test": test_case["description"],
            "query": test_case["query"],
            **result
        })
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    total_duration = (datetime.now() - start_time).total_seconds()
    
    # Final summary
    logger.info("")
    logger.info("="*80)
    logger.info("COMPREHENSIVE TEST SUMMARY")
    logger.info("="*80)
    logger.info("")
    
    total_tests = len(results)
    completed = sum(1 for r in results if r["completed"])
    found_datasets = sum(1 for r in results if r["found_datasets"])
    found_citations = sum(1 for r in results if r["found_citations"])
    got_fulltext = sum(1 for r in results if r["got_fulltext"])
    
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Completed: {completed}/{total_tests} ({completed/total_tests*100:.0f}%)")
    logger.info(f"Found datasets: {found_datasets}/{total_tests} ({found_datasets/total_tests*100:.0f}%)")
    logger.info(f"Found citations: {found_citations}/{total_tests} ({found_citations/total_tests*100:.0f}%)")
    logger.info(f"Got full-text: {got_fulltext}/{total_tests} ({got_fulltext/total_tests*100:.0f}%)")
    logger.info(f"Total duration: {total_duration:.1f}s")
    logger.info("")
    
    # Detailed results
    logger.info("DETAILED RESULTS:")
    logger.info("")
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["completed"] and result["found_datasets"] else "❌ FAIL"
        logger.info(f"{i}. {status} - {result['test']}")
        logger.info(f"   Query: '{result['query']}'")
        logger.info(f"   Datasets: {result['found_datasets']}, Citations: {result['found_citations']}, Full-text: {result['got_fulltext']}")
        if "error" in result:
            logger.info(f"   Error: {result['error']}")
        logger.info("")
    
    # Overall verdict
    logger.info("="*80)
    if completed == total_tests and found_datasets >= total_tests * 0.8:
        logger.info("✅ COMPREHENSIVE TEST SUITE: PASSED")
        logger.info(f"   All {total_tests} tests completed successfully!")
    else:
        logger.info("⚠️  COMPREHENSIVE TEST SUITE: PARTIAL SUCCESS")
        logger.info(f"   {completed}/{total_tests} tests completed")
        logger.info(f"   {found_datasets}/{total_tests} found datasets")
    logger.info("="*80)
    logger.info("")


if __name__ == "__main__":
    asyncio.run(main())
