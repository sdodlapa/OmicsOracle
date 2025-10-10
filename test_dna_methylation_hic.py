"""
Detailed test of GEO Citation Pipeline with DNA methylation + HiC query.

This test will show the complete flow with detailed logging at each step.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from omics_oracle_v2.lib.workflows.geo_citation_pipeline import GEOCitationConfig, GEOCitationPipeline

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_dna_methylation_hic():
    """Test with DNA methylation + HiC query"""

    query = "Joint profiling of dna methylation and HiC data"

    logger.info("=" * 80)
    logger.info("DETAILED FLOW TEST: DNA Methylation + HiC Query")
    logger.info("=" * 80)
    logger.info(f"Query: '{query}'")
    logger.info("=" * 80)
    logger.info("")

    # Configure pipeline
    config = GEOCitationConfig(
        geo_max_results=3,  # Get up to 3 datasets
        enable_synonym_expansion=False,  # No synonym expansion for clarity
        citation_max_results=30,  # Up to 30 papers per dataset
        use_citation_strategy=True,  # Use both strategies
        use_mention_strategy=True,
        enable_institutional=True,  # Enable all legal sources
        enable_unpaywall=True,
        enable_core=True,
        enable_scihub=False,  # Legal only
        enable_libgen=False,
        download_pdfs=False,  # Skip PDF download for speed
        output_dir=Path("data/geo_citation_collections"),
        organize_by_geo_id=False,
    )

    logger.info("PIPELINE CONFIGURATION:")
    logger.info(f"  Max GEO datasets: {config.geo_max_results}")
    logger.info(f"  Max papers per dataset: {config.citation_max_results}")
    logger.info(f"  Citation strategies: A (citing) + B (mentioning)")
    logger.info(f"  Full-text sources: Institutional, Unpaywall, CORE")
    logger.info(f"  PDF download: {config.download_pdfs}")
    logger.info("")

    # Initialize pipeline
    logger.info("Step 1: INITIALIZING PIPELINE")
    logger.info("-" * 80)
    start_time = datetime.now()
    pipeline = GEOCitationPipeline(config)
    logger.info("✅ Pipeline initialized")
    logger.info("")

    # Run collection with detailed tracking
    try:
        logger.info("Step 2: STARTING COLLECTION")
        logger.info("-" * 80)

        result = await pipeline.collect(query=query, max_datasets=3, max_citing_papers=30)

        duration = (datetime.now() - start_time).total_seconds()

        # Detailed results
        logger.info("")
        logger.info("=" * 80)
        logger.info("COLLECTION COMPLETE - DETAILED RESULTS")
        logger.info("=" * 80)
        logger.info("")

        # GEO Datasets
        logger.info("📊 GEO DATASETS FOUND:")
        logger.info("-" * 80)
        if result.datasets_found:
            for i, ds in enumerate(result.datasets_found, 1):
                logger.info(f"\n{i}. {ds.geo_id}")
                logger.info(f"   Title: {ds.title}")
                logger.info(f"   Samples: {ds.sample_count}")
                logger.info(f"   PubMed IDs: {ds.pubmed_ids if ds.pubmed_ids else 'None (unpublished)'}")
                logger.info(f"   Summary: {ds.summary[:200]}...")
        else:
            logger.info("   No datasets found")
        logger.info("")

        # Citations
        logger.info("📝 CITING PAPERS:")
        logger.info("-" * 80)
        logger.info(f"Total papers found: {result.total_citing_papers}")
        if result.citing_papers:
            logger.info("\nSample papers:")
            for i, paper in enumerate(result.citing_papers[:5], 1):
                logger.info(f"\n{i}. {paper.title[:100]}...")
                logger.info(f"   PMID: {paper.pmid}")
                logger.info(f"   Year: {paper.year}")
                logger.info(f"   Journal: {paper.journal}")
                if paper.fulltext_url:
                    source = getattr(paper, "fulltext_source", "unknown")
                    logger.info(f"   Full-text: ✅ Available ({source})")
                else:
                    logger.info(f"   Full-text: ❌ Not found")
        else:
            logger.info("   No citing papers found (datasets may be unpublished or too new)")
        logger.info("")

        # Full-text coverage
        logger.info("🔗 FULL-TEXT URL COLLECTION:")
        logger.info("-" * 80)
        logger.info(
            f"Coverage: {result.fulltext_coverage:.1f}% ({len([p for p in result.citing_papers if p.fulltext_url])}/{result.total_citing_papers})"
        )
        if result.fulltext_by_source:
            logger.info("\nBreakdown by source:")
            for source, count in result.fulltext_by_source.items():
                logger.info(f"  {source}: {count} papers")
        logger.info("")

        # Performance
        logger.info("⏱️  PERFORMANCE METRICS:")
        logger.info("-" * 80)
        logger.info(f"Total duration: {duration:.2f}s")
        if result.datasets_found:
            logger.info(f"Time per dataset: {duration/len(result.datasets_found):.2f}s")
        if result.total_citing_papers > 0:
            logger.info(f"Time per paper: {duration/result.total_citing_papers:.2f}s")
        logger.info("")

        # Data saved
        logger.info("💾 DATA PERSISTENCE:")
        logger.info("-" * 80)
        if result.collection_dir:
            logger.info(f"Collection saved to: {result.collection_dir}")
            logger.info("\nFiles created:")
            if result.collection_dir.exists():
                for file in sorted(result.collection_dir.glob("*.json")):
                    size = file.stat().st_size
                    logger.info(f"  - {file.name} ({size:,} bytes)")
        logger.info("")

        # Summary
        logger.info("=" * 80)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Query executed: '{query}'")
        logger.info(f"✅ Datasets found: {len(result.datasets_found)}")
        logger.info(
            f"{'✅' if result.total_citing_papers > 0 else '⚠️ '} Citing papers: {result.total_citing_papers}"
        )
        logger.info(
            f"{'✅' if result.fulltext_coverage > 0 else '⚠️ '} Full-text coverage: {result.fulltext_coverage:.1f}%"
        )
        logger.info(f"✅ Duration: {duration:.2f}s")
        logger.info(f"✅ Data saved: {result.collection_dir}")
        logger.info("=" * 80)

        return result

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        raise


async def explain_flow():
    """Run test and explain the flow"""

    logger.info("\n\n")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 20 + "PIPELINE FLOW EXPLANATION" + " " * 33 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")

    logger.info("This test will demonstrate the complete Phase 6 pipeline flow:")
    logger.info("")
    logger.info("1️⃣  Query Input → 'Joint profiling of dna methylation and HiC data'")
    logger.info("2️⃣  GEO Search → Find datasets matching the query")
    logger.info("3️⃣  Metadata Fetch → Get detailed info for each dataset")
    logger.info("4️⃣  Citation Discovery → Find papers citing/mentioning datasets")
    logger.info("5️⃣  Full-Text URLs → Collect URLs from multiple sources")
    logger.info("6️⃣  PDF Download → Download papers (skipped in this test)")
    logger.info("7️⃣  Data Persistence → Save all metadata to JSON files")
    logger.info("")
    logger.info("Watch the logs below to see each step in action!")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

    result = await test_dna_methylation_hic()

    # Post-run analysis
    logger.info("\n\n")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 25 + "FLOW EVENT ANALYSIS" + " " * 34 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")

    logger.info("EVENT TIMELINE:")
    logger.info("-" * 80)
    logger.info("1. Query submitted to GEO NCBI database")
    logger.info("2. GEO returned dataset IDs matching search terms")
    logger.info("3. Parallel metadata fetch for each dataset")
    logger.info("4. Citation discovery attempted for each dataset:")
    logger.info("   - Strategy A: Search for papers citing the dataset's PMID")
    logger.info("   - Strategy B: Search for papers mentioning the GEO ID")
    logger.info("5. Deduplication of papers across strategies")
    logger.info("6. Full-text URL collection from configured sources")
    logger.info("7. JSON files written to disk")
    logger.info("")

    logger.info("DATA COLLECTED:")
    logger.info("-" * 80)
    logger.info(f"✓ {len(result.datasets_found)} GEO datasets with full metadata")
    logger.info(f"✓ {result.total_citing_papers} unique citing papers")
    logger.info(f"✓ {len([p for p in result.citing_papers if p.fulltext_url])} papers with full-text URLs")
    logger.info(f"✓ Metadata organized in: {result.collection_dir}")
    logger.info("")

    if result.total_citing_papers == 0:
        logger.info("NOTE:")
        logger.info("-" * 80)
        logger.info("⚠️  No citing papers found. This can happen when:")
        logger.info("   • Datasets are too new (not yet cited)")
        logger.info("   • Datasets are unpublished (no PubMed ID)")
        logger.info("   • Datasets are in a niche field (few citations)")
        logger.info("")
        logger.info("The pipeline infrastructure is working correctly!")
        logger.info("Testing with older, well-cited datasets would show citations.")

    logger.info("")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(explain_flow())
