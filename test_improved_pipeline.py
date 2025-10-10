"""
Test improved GEO citation pipeline with optimized query builder.

Demonstrates how query optimization finds more datasets with PMIDs.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Set environment
os.environ['SSL_VERIFY'] = 'false'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Test improved pipeline with optimized queries."""
    from omics_oracle_v2.lib.workflows.geo_citation_pipeline import GEOCitationPipeline, GEOCitationConfig
    from omics_oracle_v2.core.config import get_settings
    
    # Get settings
    settings = get_settings()
    
    # Configure pipeline for testing
    config = GEOCitationConfig(
        geo_max_results=10,  # Get top 10 datasets
        enable_synonym_expansion=False,  # Disabled - using query builder instead
        citation_max_results=50,
        use_citation_strategy=True,
        use_mention_strategy=True
    )
    
    # Initialize pipeline
    pipeline = GEOCitationPipeline(settings, config)
    
    # Test query
    query = "Joint profiling of dna methylation and HiC data"
    
    print("\n" + "="*80)
    print("IMPROVED GEO CITATION PIPELINE TEST")
    print("="*80)
    print(f"Query: {query}")
    print(f"Expected: ~10 datasets with PMIDs (vs previous 1)")
    print()
    
    # Run pipeline
    result = await pipeline.collect(
        query=query,
        max_datasets=10
    )
    
    # Display results
    print("\n" + "="*80)
    print("COLLECTION RESULTS")
    print("="*80)
    print(f"Duration: {result.duration_seconds:.2f}s")
    print()
    
    print(f"GEO Datasets: {len(result.datasets)}")
    print(f"Citing Papers: {len(result.citing_papers)}")
    print(f"PDFs Downloaded: {result.pdf_download_count}")
    print()
    
    if result.datasets:
        print("="*80)
        print("DATASETS FOUND (with PMIDs):")
        print("="*80)
        
        datasets_with_pmids = [d for d in result.datasets if d.pubmed_ids]
        print(f"\n{len(datasets_with_pmids)}/{len(result.datasets)} datasets have PMIDs\n")
        
        for i, dataset in enumerate(result.datasets[:10], 1):
            print(f"{i}. {dataset.geo_id}: {dataset.title[:60]}...")
            print(f"   Organism: {dataset.organism}")
            print(f"   Samples: {dataset.sample_count}")
            pmid_str = dataset.pubmed_ids[0] if dataset.pubmed_ids else "None"
            print(f"   PMID: {pmid_str}")
            print()
    
    if result.citing_papers:
        print("="*80)
        print("CITING PAPERS FOUND:")
        print("="*80)
        print()
        
        for i, paper in enumerate(result.citing_papers[:5], 1):
            print(f"{i}. {paper.title[:70]}...")
            print(f"   PMID: {paper.pmid}")
            print(f"   Year: {paper.year}")
            print()
        
        if len(result.citing_papers) > 5:
            print(f"... and {len(result.citing_papers) - 5} more papers")
            print()
    
    # Performance summary
    print("="*80)
    print("PERFORMANCE METRICS")
    print("="*80)
    per_dataset = result.duration_seconds / len(result.datasets) if result.datasets else 0
    print(f"Total time: {result.duration_seconds:.2f}s")
    print(f"Time per dataset: {per_dataset:.2f}s")
    print(f"Datasets/second: {1/per_dataset if per_dataset > 0 else 0:.2f}")
    print()
    
    # Comparison with previous approach
    print("="*80)
    print("IMPROVEMENT vs PREVIOUS APPROACH")
    print("="*80)
    print(f"Previous query (exact phrase): 1 dataset, 0 citations")
    print(f"Improved query (optimized):    {len(result.datasets)} datasets, {len(result.citing_papers)} citations")
    print(f"Improvement: {len(result.datasets)}x more datasets!")
    print()
    
    await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
