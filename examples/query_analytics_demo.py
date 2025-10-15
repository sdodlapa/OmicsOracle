"""
Query and Analytics Interface Demonstration

This example shows how to use the high-level query and analytics
interface to:
- Query publications by various criteria
- Generate statistics and reports
- Export GEO datasets
- Analyze quality and performance
- Verify data integrity

Usage:
    python examples/query_analytics_demo.py
"""

import logging
from pathlib import Path

from omics_oracle_v2.lib.storage import Analytics, DatabaseQueries

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def demo_basic_queries():
    """Demonstrate basic query operations."""
    logger.info("\n" + "=" * 60)
    logger.info("BASIC QUERIES DEMONSTRATION")
    logger.info("=" * 60)

    queries = DatabaseQueries("data/database/omics_oracle.db")

    # Query publications for a GEO dataset
    logger.info("\n1. Get all publications for a GEO dataset:")
    geo_id = "GSE12345"
    publications = queries.get_geo_publications(geo_id)
    logger.info(f"  [OK] Found {len(publications)} publications for {geo_id}")

    if publications:
        pub = publications[0]
        logger.info(f"  Example: {pub.get('title', 'N/A')[:50]}...")
        logger.info(f"  Quality: {pub.get('quality_score')} " f"(Grade: {pub.get('quality_grade')})")

    # Get publication details
    if publications:
        logger.info("\n2. Get detailed information for a publication:")
        pmid = publications[0]["pmid"]
        details = queries.get_publication_details(pmid)
        if details:
            logger.info(f"  [OK] PMID: {pmid}")
            logger.info(f"  Title: {details.get('title', 'N/A')[:60]}...")
            logger.info(f"  URLs found: {details.get('urls_found', 0)}")
            logger.info(f"  PDF path: {details.get('pdf_path', 'N/A')}")
            logger.info(f"  Word count: {details.get('word_count', 'N/A')}")

    # Query by quality
    logger.info("\n3. Get high-quality publications:")
    high_quality = queries.get_publications_by_quality(min_quality=0.8, quality_grades=["A", "B"], limit=10)
    logger.info(f"  [OK] Found {len(high_quality)} high-quality publications")

    for i, pub in enumerate(high_quality[:3], 1):
        logger.info(
            f"  {i}. {pub['title'][:40]}... "
            f"(Score: {pub['quality_score']}, Grade: {pub['quality_grade']})"
        )

    # Find incomplete publications
    logger.info("\n4. Find publications with missing data:")
    incomplete = queries.get_incomplete_publications()
    logger.info(f"  [OK] Found {len(incomplete)} incomplete publications")

    if incomplete:
        pub = incomplete[0]
        logger.info(f"  Example: {pub['title'][:50]}...")
        logger.info(f"  Has URLs: {bool(pub['has_urls'])}")
        logger.info(f"  Has PDF: {bool(pub['has_pdf'])}")
        logger.info(f"  Has extraction: {bool(pub['has_extraction'])}")
        logger.info(f"  Has enriched: {bool(pub['has_enriched'])}")

    # Search publications
    logger.info("\n5. Search publications by text:")
    results = queries.search_publications("machine learning", search_fields=["title", "authors"])
    logger.info(f"  [OK] Found {len(results)} publications matching 'machine learning'")


def demo_statistics():
    """Demonstrate statistics and analytics."""
    logger.info("\n" + "=" * 60)
    logger.info("STATISTICS & ANALYTICS DEMONSTRATION")
    logger.info("=" * 60)

    queries = DatabaseQueries("data/database/omics_oracle.db")

    # Overall processing statistics
    logger.info("\n1. Overall processing statistics:")
    stats = queries.get_processing_statistics()
    logger.info(f"  Total publications: {stats['total_publications']}")
    logger.info(f"  Total GEO datasets: {stats['total_geo_datasets']}")
    logger.info(f"  Average quality: {stats.get('average_quality_score', 'N/A')}")

    logger.info("  Pipeline completion:")
    for pipeline, count in stats["pipeline_completion"].items():
        logger.info(f"    - {pipeline}: {count}")

    logger.info("  Quality distribution:")
    for grade, count in stats.get("quality_distribution", {}).items():
        logger.info(f"    - Grade {grade}: {count}")

    logger.info("  Storage:")
    storage = stats.get("storage", {})
    logger.info(f"    - PDFs: {storage.get('pdf_count', 0)} files, " f"{storage.get('total_pdf_mb', 0)} MB")

    # GEO-specific statistics
    logger.info("\n2. GEO dataset statistics:")
    geo_id = "GSE12345"
    geo_stats = queries.get_geo_statistics(geo_id)

    if geo_stats.get("dataset_info"):
        logger.info(f"  Dataset: {geo_id}")
        logger.info(f"  Total publications: " f"{geo_stats['publication_counts']['total']}")
        logger.info(f"  With PDFs: {geo_stats['publication_counts']['with_pdf']}")
        logger.info(f"  Extracted: " f"{geo_stats['publication_counts']['with_extraction']}")
        logger.info(f"  Completion rate: {geo_stats['completion_rate']}%")
        logger.info(f"  Average quality: {geo_stats.get('average_quality', 'N/A')}")

    # Pipeline performance
    logger.info("\n3. Pipeline performance metrics:")
    performance = queries.get_pipeline_performance()

    for pipeline_data in performance.get("pipelines", []):
        logger.info(f"  {pipeline_data['pipeline_name']}:")
        logger.info(f"    - Total operations: {pipeline_data['total_operations']}")
        logger.info(f"    - Success rate: {pipeline_data['success_rate']}%")
        logger.info(f"    - Avg duration: {pipeline_data.get('avg_duration', 'N/A')}s")

    # Recent errors
    logger.info("\n4. Recent processing errors:")
    errors = queries.get_recent_errors(limit=5)
    logger.info(f"  [OK] Retrieved {len(errors)} recent errors")

    for error in errors:
        logger.info(f"  - {error['pipeline_name']}: {error['pmid']}")
        logger.info(f"    {error.get('error_message', 'N/A')[:60]}...")

    # Database size
    logger.info("\n5. Database information:")
    db_info = queries.get_database_size()
    logger.info(f"  Path: {db_info.get('path', 'N/A')}")
    logger.info(f"  Size: {db_info.get('size_mb', 0)} MB")
    logger.info("  Table row counts:")
    for table, count in db_info.get("table_row_counts", {}).items():
        logger.info(f"    - {table}: {count}")


def demo_analytics():
    """Demonstrate analytics and export operations."""
    logger.info("\n" + "=" * 60)
    logger.info("ANALYTICS & EXPORT DEMONSTRATION")
    logger.info("=" * 60)

    analytics = Analytics(db_path="data/database/omics_oracle.db", storage_path="data")

    # Quality distribution analysis
    logger.info("\n1. Quality distribution analysis:")
    quality_dist = analytics.calculate_quality_distribution()
    logger.info(f"  Total extracted: {quality_dist['total_extracted']}")
    logger.info(f"  Average score: {quality_dist.get('average_score', 'N/A')}")

    logger.info("  Grade distribution:")
    for grade, count in quality_dist.get("grade_distribution", {}).items():
        logger.info(f"    - Grade {grade}: {count}")

    if quality_dist.get("percentiles"):
        logger.info("  Score percentiles:")
        for percentile, value in quality_dist["percentiles"].items():
            logger.info(f"    - {percentile}: {value}")

    # Storage efficiency
    logger.info("\n2. Storage efficiency analysis:")
    storage_eff = analytics.get_storage_efficiency()

    logger.info(
        f"  Database: {storage_eff['database']['size_mb']} MB "
        f"({storage_eff['database'].get('table_counts', {}).get('universal_identifiers', 0)} pubs)"
    )
    logger.info(
        f"  PDFs: {storage_eff['pdfs']['total_mb']} MB "
        f"({storage_eff['pdfs']['file_count']} files, "
        f"{storage_eff['pdfs']['geo_dataset_count']} datasets)"
    )
    logger.info(
        f"  Enriched: {storage_eff['enriched']['total_mb']} MB "
        f"({storage_eff['enriched']['file_count']} files)"
    )
    logger.info(f"  Total storage: {storage_eff['total_storage_mb']} MB")

    # Quality issues
    logger.info("\n3. Identify quality issues:")
    issues = analytics.identify_quality_issues(threshold=0.5)
    logger.info(f"  [OK] Found {len(issues)} publications with quality < 0.5")

    for i, issue in enumerate(issues[:3], 1):
        logger.info(
            f"  {i}. {issue['title'][:40]}... "
            f"(Score: {issue['quality_score']}, "
            f"Method: {issue.get('extraction_method', 'N/A')})"
        )

    # Export demonstration (without actually writing files)
    logger.info("\n4. Export capabilities:")
    logger.info("  Available export operations:")
    logger.info("    - export_geo_dataset(): Export complete GEO dataset")
    logger.info("    - export_quality_report(): Generate quality analysis")
    logger.info("    - export_processing_summary(): Comprehensive summary")
    logger.info("  Example: analytics.export_geo_dataset('GSE12345', 'output/')")

    # Data integrity verification
    logger.info("\n5. Data integrity verification:")
    logger.info("  Verifying first 10 PDFs...")

    # Get a sample GEO ID
    queries = DatabaseQueries("data/database/omics_oracle.db")
    stats = queries.get_processing_statistics()
    if stats["total_publications"] > 0:
        # Just demonstrate the capability without full verification
        logger.info("  [OK] Integrity verification available")
        logger.info("  Use: analytics.verify_data_integrity(geo_id='GSE12345')")
    else:
        logger.info("  [WARN] No data to verify yet")


def demo_advanced_queries():
    """Demonstrate advanced query patterns."""
    logger.info("\n" + "=" * 60)
    logger.info("ADVANCED QUERIES DEMONSTRATION")
    logger.info("=" * 60)

    queries = DatabaseQueries("data/database/omics_oracle.db")

    # Date range queries
    logger.info("\n1. Query by date range:")
    from datetime import datetime, timedelta

    end_date = datetime.now().isoformat()
    start_date = (datetime.now() - timedelta(days=30)).isoformat()

    recent = queries.get_publications_by_date_range(start_date=start_date, end_date=end_date)
    logger.info(f"  [OK] Found {len(recent)} publications from last 30 days")

    # Combined quality and date filters
    logger.info("\n2. High-quality publications from last month:")
    high_quality_recent = [p for p in recent if p.get("quality_score") and p["quality_score"] >= 0.8]
    logger.info(f"  [OK] Found {len(high_quality_recent)} high-quality recent publications")

    # Pipeline-specific performance
    logger.info("\n3. Pipeline-specific performance:")
    for pipeline in ["P1_citation", "P2_url", "P3_pdf", "P4_extraction"]:
        perf = queries.get_pipeline_performance(pipeline_name=pipeline)
        if perf.get("pipelines"):
            data = perf["pipelines"][0]
            logger.info(
                f"  {pipeline}: {data['success_rate']}% success, " f"avg {data.get('avg_duration', 'N/A')}s"
            )


def main():
    """Run all demonstrations."""
    logger.info("\n" + "=" * 60)
    logger.info("QUERY & ANALYTICS INTERFACE DEMO")
    logger.info("=" * 60)

    try:
        # Check if database exists
        db_path = Path("data/database/omics_oracle.db")
        if not db_path.exists():
            logger.warning(f"\nDatabase not found: {db_path}")
            logger.warning("Please run the complete_pipeline_integration.py example first")
            logger.warning("to create and populate the database.")
            return

        # Run demonstrations
        demo_basic_queries()
        demo_statistics()
        demo_analytics()
        demo_advanced_queries()

        logger.info("\n" + "=" * 60)
        logger.info("DEMONSTRATION COMPLETE")
        logger.info("=" * 60)
        logger.info("\nAll query and analytics features demonstrated!")
        logger.info("\nNext steps:")
        logger.info("  1. Use DatabaseQueries for flexible querying")
        logger.info("  2. Use Analytics for exports and reports")
        logger.info("  3. Integrate into your analysis workflow")

    except Exception as e:
        logger.error(f"Error during demonstration: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
