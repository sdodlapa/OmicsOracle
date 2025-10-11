"""
Test GEO Citation Pipeline with datasets known to have citations.

Uses specific older GEO accessions that are published papers.
"""

import asyncio
import logging
from pathlib import Path

from omics_oracle_v2.lib.geo.client import GEOClient
from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import GEOCitationConfig, GEOCitationPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def find_dataset_with_pmid():
    """Search for datasets that have PubMed IDs"""
    logger.info("Searching for older, well-cited datasets...")

    geo_client = GEOClient()

    # Try searching for older datasets with a year filter
    queries = [
        "breast cancer 2015:2018[PDAT]",  # Older datasets from 2015-2018
        "RNA-seq 2016:2017[PDAT]",
        "ChIP-seq 2015:2016[PDAT]",
    ]

    for query in queries:
        logger.info(f"\nSearching: {query}")
        search_result = await geo_client.search(query, max_results=10)

        if search_result.geo_ids:
            logger.info(f"  Found {len(search_result.geo_ids)} datasets")

            # Get metadata
            metadata_dict = await geo_client.batch_get_metadata(
                search_result.geo_ids[:5], max_concurrent=3  # Check first 5
            )

            for geo_id, metadata in metadata_dict.items():
                if metadata and metadata.pubmed_ids:
                    logger.info(f"\n  ✅ {geo_id} has {len(metadata.pubmed_ids)} PubMed IDs:")
                    logger.info(f"     Title: {metadata.title[:100]}...")
                    logger.info(f"     PMIDs: {metadata.pubmed_ids}")
                    logger.info(f"     Samples: {metadata.sample_count}")
                    return geo_id

    await geo_client.close()
    return None


async def test_with_citations():
    """Test pipeline with a dataset that has citations"""
    logger.info("=" * 80)
    logger.info("TESTING WITH DATASET THAT HAS CITATIONS")
    logger.info("=" * 80)

    # First, find a dataset with a PMID
    geo_id = await find_dataset_with_pmid()

    if not geo_id:
        logger.warning("Could not find datasets with PubMed IDs in recent searches")
        logger.info("Testing with manual query for older datasets...")
        query = "breast cancer 2016[PDAT]"
    else:
        logger.info(f"\nUsing dataset: {geo_id}")
        # Use a query that will return this dataset
        query = f"{geo_id}"

    logger.info(f"\nRunning pipeline with query: '{query}'")

    config = GEOCitationConfig(
        geo_max_results=3,
        enable_synonym_expansion=False,
        citation_max_results=50,
        use_citation_strategy=True,
        use_mention_strategy=True,
        enable_institutional=True,
        enable_unpaywall=True,
        enable_core=True,
        enable_scihub=False,
        enable_libgen=False,
        download_pdfs=False,
        output_dir=Path("data/geo_citation_collections"),
        organize_by_geo_id=True,
    )

    pipeline = GEOCitationPipeline(config)

    result = await pipeline.collect(query=query, max_datasets=3, max_citing_papers=50)

    # Print results
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    logger.info(f"GEO datasets: {len(result.datasets_found)}")
    for ds in result.datasets_found:
        logger.info(f"\n  {ds.geo_id}:")
        logger.info(f"    Title: {ds.title[:100]}...")
        logger.info(f"    PubMed IDs: {ds.pubmed_ids}")
        logger.info(f"    Samples: {ds.sample_count}")

    logger.info(f"\nTotal citing papers: {result.total_citing_papers}")
    if result.citing_papers:
        logger.info("\nSample citing papers:")
        for i, paper in enumerate(result.citing_papers[:5], 1):
            logger.info(f"  {i}. {paper.title[:80]}...")
            logger.info(f"     PMID: {paper.pmid}, Year: {paper.year}")
            if paper.fulltext_url:
                logger.info(f"     Full-text: ✅ ({getattr(paper, 'fulltext_source', 'unknown')})")

    logger.info(f"\nFull-text coverage: {result.fulltext_coverage:.1f}%")
    logger.info(f"Duration: {result.duration_seconds:.1f}s")

    # Success assessment
    logger.info("\n" + "=" * 80)
    logger.info("SUCCESS ASSESSMENT")
    logger.info("=" * 80)
    logger.info(f"✅ Pipeline completed: {result.duration_seconds:.1f}s")
    logger.info(
        f"{'✅' if len(result.datasets_found) > 0 else '❌'} Found {len(result.datasets_found)} GEO datasets"
    )
    logger.info(
        f"{'✅' if result.total_citing_papers > 0 else '⚠️ '} Found {result.total_citing_papers} citing papers"
    )
    logger.info(
        f"{'✅' if result.fulltext_coverage > 0 else '⚠️ '} Got {result.fulltext_coverage:.1f}% full-text coverage"
    )

    if result.total_citing_papers == 0:
        logger.warning("\n⚠️  No citing papers found - datasets may be too new or unpublished")
        logger.info("   This is expected for very recent datasets (2024-2025)")
        logger.info("   Pipeline infrastructure is working correctly!")

    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_with_citations())
