"""
Test GEO Citation Pipeline with a small example

This tests the end-to-end pipeline with a real query.
"""

import asyncio
import logging
from pathlib import Path

from omics_oracle_v2.lib.workflows import (
    GEOCitationPipeline,
    GEOCitationConfig
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_pipeline():
    """Test the pipeline with a simple query"""
    
    logger.info("="*80)
    logger.info("TESTING GEO CITATION PIPELINE")
    logger.info("="*80)
    
    # Configure pipeline (conservative settings for testing)
    config = GEOCitationConfig(
        # GEO search
        geo_max_results=2,  # Just 2 datasets for testing
        enable_synonym_expansion=False,  # Skip synonym expansion for speed
        
        # Citation discovery
        citation_max_results=20,  # Limit to 20 papers per dataset
        use_citation_strategy=True,
        use_mention_strategy=True,
        
        # Full-text retrieval
        enable_institutional=True,  # Georgia Tech access
        enable_unpaywall=True,
        enable_core=True,
        enable_scihub=False,  # Legal sources only for testing
        enable_libgen=False,
        
        # PDF download
        download_pdfs=True,
        max_concurrent_downloads=3,  # Conservative for testing
        pdf_validation=True,
        
        # Storage
        output_dir=Path("data/geo_citation_collections"),
        organize_by_geo_id=True
    )
    
    # Initialize pipeline
    pipeline = GEOCitationPipeline(config)
    
    # Test query
    query = "breast cancer RNA-seq"
    
    logger.info(f"Test Query: {query}")
    logger.info(f"Settings: 2 GEO datasets, 20 papers each, legal sources only")
    logger.info("")
    
    # Run collection
    try:
        result = await pipeline.collect(
            query=query,
            max_datasets=2,
            max_citing_papers=20
        )
        
        # Print summary
        logger.info("")
        logger.info("="*80)
        logger.info("TEST RESULTS")
        logger.info("="*80)
        logger.info(f"GEO datasets found: {len(result.datasets_found)}")
        for ds in result.datasets_found:
            logger.info(f"  - {ds.geo_id}: {ds.title[:60]}...")
        
        logger.info(f"")
        logger.info(f"Total citing papers: {result.total_citing_papers}")
        logger.info(f"Full-text coverage: {result.fulltext_coverage:.1%}")
        logger.info(f"")
        logger.info(f"Full-text by source:")
        for source, count in result.fulltext_by_source.items():
            logger.info(f"  {source}: {count} papers")
        
        logger.info(f"")
        logger.info(f"PDFs downloaded: {result.pdfs_downloaded}")
        if result.collection_dir:
            logger.info(f"Collection saved to: {result.collection_dir}")
        
        logger.info(f"")
        logger.info(f"Duration: {result.duration_seconds:.1f} seconds")
        logger.info(f"")
        
        # Success criteria
        logger.info("="*80)
        logger.info("SUCCESS CRITERIA")
        logger.info("="*80)
        
        checks = {
            "Found GEO datasets": len(result.datasets_found) > 0,
            "Found citing papers": result.total_citing_papers > 0,
            "Got full-text URLs": result.fulltext_coverage > 0,
            "Downloaded PDFs": result.pdfs_downloaded > 0 if config.download_pdfs else True,
            "Saved metadata": result.collection_dir is not None and result.collection_dir.exists()
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"{status} {check}")
        
        all_passed = all(checks.values())
        
        if all_passed:
            logger.info("")
            logger.info("🎉 ALL CHECKS PASSED - PIPELINE WORKING!")
        else:
            logger.error("")
            logger.error("⚠️  SOME CHECKS FAILED")
        
        return result
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_pipeline())
