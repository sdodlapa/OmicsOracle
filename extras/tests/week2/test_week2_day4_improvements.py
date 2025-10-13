"""
Test script to verify Week 2 Day 4 improvements.

Tests:
1. GEO deduplication
2. Smart citation scoring
3. Recency bonus
4. Redis cache with correct signature
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import OmicsSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.models import Publication
from omics_oracle_v2.lib.publications.ranking.ranker import PublicationRanker
from setup_logging import setup_logging

# Set up logging
log_file = setup_logging(log_name="week2_day4_verification")
logger = logging.getLogger(__name__)


def test_geo_deduplication():
    """Test GEO dataset deduplication."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: GEO Dataset Deduplication")
    logger.info("=" * 80)

    # Create mock GEO datasets with duplicates
    datasets = [
        GEOSeriesMetadata(accession="GSE123456", title="Study 1", summary="Test"),
        GEOSeriesMetadata(accession="GSE789012", title="Study 2", summary="Test"),
        GEOSeriesMetadata(accession="GSE123456", title="Study 1 Duplicate", summary="Test"),  # Duplicate
        GEOSeriesMetadata(accession="GSE345678", title="Study 3", summary="Test"),
        GEOSeriesMetadata(accession="GSE789012", title="Study 2 Duplicate", summary="Test"),  # Duplicate
    ]

    logger.info(f"Created {len(datasets)} GEO datasets (2 duplicates expected)")
    logger.info(f"Accessions: {[d.accession for d in datasets]}")

    # Test deduplication
    pipeline = OmicsSearchPipeline()
    unique_datasets = pipeline._deduplicate_geo_datasets(datasets)

    logger.info(f"\nAfter deduplication: {len(unique_datasets)} unique datasets")
    logger.info(f"Unique accessions: {[d.accession for d in unique_datasets]}")

    # Verify
    expected_count = 3
    if len(unique_datasets) == expected_count:
        logger.info(f"✓ SUCCESS: Removed {len(datasets) - len(unique_datasets)} duplicates")
        logger.info(f"✓ Expected {expected_count} unique datasets, got {len(unique_datasets)}")
        return True
    else:
        logger.error(f"✗ FAILED: Expected {expected_count} unique, got {len(unique_datasets)}")
        return False


def test_smart_citation_scoring():
    """Test smart citation dampening."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Smart Citation Scoring")
    logger.info("=" * 80)

    # Create mock publications with different citation counts
    test_cases = [
        ("Brand new paper", 0),
        ("Standard paper", 50),
        ("Good paper", 100),
        ("High-impact", 500),
        ("Very high-impact", 1000),
        ("Highly cited", 5000),
        ("Seminal work", 10000),
        ("HOMA-IR (foundational)", 30828),  # From log
        ("Diabetes classification", 20055),  # From log
        ("Insulin resistance", 12860),  # From log
    ]

    config = PublicationSearchConfig()
    ranker = PublicationRanker(config)

    logger.info("\nCitation Score Analysis:")
    logger.info("-" * 80)
    logger.info(f"{'Paper Type':<30} {'Citations':>10} {'Score':>10} {'Tier':<15}")
    logger.info("-" * 80)

    for paper_type, citations in test_cases:
        score = ranker._calculate_citation_score(citations)

        # Determine tier
        if citations <= 100:
            tier = "Linear"
        elif citations <= 1000:
            tier = "Sqrt dampening"
        else:
            tier = "Log dampening"

        logger.info(f"{paper_type:<30} {citations:>10,} {score:>10.3f} {tier:<15}")

    # Verify key expectations
    score_0 = ranker._calculate_citation_score(0)
    score_100 = ranker._calculate_citation_score(100)
    score_1000 = ranker._calculate_citation_score(1000)
    score_30k = ranker._calculate_citation_score(30828)

    logger.info("\nVerification:")
    checks = [
        (score_0 == 0.0, f"0 citations → {score_0:.3f} (expected 0.000)"),
        (0.59 <= score_100 <= 0.61, f"100 citations → {score_100:.3f} (expected ~0.600)"),
        (0.79 <= score_1000 <= 0.81, f"1,000 citations → {score_1000:.3f} (expected ~0.800)"),
        (0.92 <= score_30k <= 0.94, f"30,828 citations → {score_30k:.3f} (expected ~0.930)"),
        (score_30k < 1.0, f"Score capped below 1.0: {score_30k:.3f}"),
    ]

    all_pass = True
    for passed, msg in checks:
        if passed:
            logger.info(f"✓ {msg}")
        else:
            logger.error(f"✗ {msg}")
            all_pass = False

    return all_pass


def test_recency_bonus():
    """Test recency bonus for recent papers."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Recency Bonus")
    logger.info("=" * 80)

    config = PublicationSearchConfig()
    ranker = PublicationRanker(config)

    now = datetime.now()
    test_dates = [
        ("Brand new (2025)", now - timedelta(days=0)),
        ("1 year old (2024)", now - timedelta(days=365)),
        ("2 years old (2023)", now - timedelta(days=730)),
        ("3 years old (2022)", now - timedelta(days=1095)),
        ("5 years old (2020)", now - timedelta(days=1825)),
        ("10 years old (2015)", now - timedelta(days=3650)),
        ("20 years old (2005)", now - timedelta(days=7300)),
        ("37 years old (1988 - HOMA-IR)", now - timedelta(days=13505)),
    ]

    logger.info("\nRecency Score Analysis:")
    logger.info("-" * 80)
    logger.info(f"{'Paper Age':<35} {'Date':>12} {'Score':>10} {'Note':<20}")
    logger.info("-" * 80)

    for label, date in test_dates:
        score = ranker._calculate_recency_score(date)
        note = "BONUS!" if score > 1.0 else "Exponential decay" if score >= 0.3 else "Old"
        logger.info(f"{label:<35} {date.year:>12} {score:>10.3f} {note:<20}")

    # Verify expectations
    score_new = ranker._calculate_recency_score(now)
    score_1y = ranker._calculate_recency_score(now - timedelta(days=365))
    score_2y = ranker._calculate_recency_score(now - timedelta(days=730))
    score_old = ranker._calculate_recency_score(now - timedelta(days=13505))

    logger.info("\nVerification:")
    checks = [
        (score_new >= 1.25, f"Brand new (2025) → {score_new:.3f} (expected ≥1.25)"),
        (score_1y >= 1.10, f"1 year old (2024) → {score_1y:.3f} (expected ≥1.10)"),
        (0.95 <= score_2y <= 1.05, f"2 years old (2023) → {score_2y:.3f} (expected ~1.00)"),
        (score_old < 0.20, f"37 years old (1988) → {score_old:.3f} (expected <0.20)"),
    ]

    all_pass = True
    for passed, msg in checks:
        if passed:
            logger.info(f"✓ {msg}")
        else:
            logger.error(f"✗ {msg}")
            all_pass = False

    return all_pass


def test_ranking_comparison():
    """Compare ranking scores: recent vs. highly-cited."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Ranking Comparison (Recent vs. Highly-Cited)")
    logger.info("=" * 80)

    config = PublicationSearchConfig()
    ranker = PublicationRanker(config)

    now = datetime.now()

    # Recent paper: 2025, 50 citations, high relevance
    recent_pub = Publication(
        title="Diabetes Insulin Resistance in Type 2 Diabetes: New Insights",
        abstract="This study investigates insulin resistance mechanisms in diabetes patients...",
        publication_date=now - timedelta(days=30),  # 1 month old
        citations=50,
        pmid="39999999",
    )

    # Classic paper: 1988, 30,828 citations (HOMA-IR), partial relevance
    classic_pub = Publication(
        title="Homeostasis Model Assessment: Insulin Resistance and Beta-Cell Function",
        abstract="We describe a model for assessment of insulin resistance and beta-cell function...",
        publication_date=datetime(1988, 1, 1),
        citations=30828,
        pmid="3899825",
    )

    query = "diabetes insulin resistance"

    # Rank both
    results_recent = ranker.rank([recent_pub], query)
    results_classic = ranker.rank([classic_pub], query)

    recent_score = results_recent[0].relevance_score
    recent_breakdown = results_recent[0].score_breakdown

    classic_score = results_classic[0].relevance_score
    classic_breakdown = results_classic[0].score_breakdown

    logger.info("\nRecent Paper (2025, 50 citations):")
    logger.info(f"  Title: {recent_pub.title}")
    logger.info(f"  Score breakdown:")
    for component, value in recent_breakdown.items():
        logger.info(f"    {component:<20}: {value:.4f}")
    logger.info(f"  Total score: {recent_score:.2f}")

    logger.info("\nClassic Paper (1988, 30,828 citations):")
    logger.info(f"  Title: {classic_pub.title}")
    logger.info(f"  Score breakdown:")
    for component, value in classic_breakdown.items():
        logger.info(f"    {component:<20}: {value:.4f}")
    logger.info(f"  Total score: {classic_score:.2f}")

    # Compare
    logger.info("\nComparison:")
    logger.info(f"  Recent paper:  {recent_score:.2f} points")
    logger.info(f"  Classic paper: {classic_score:.2f} points")
    logger.info(f"  Difference:    {recent_score - classic_score:+.2f} points")

    if recent_score > classic_score:
        logger.info("  ✓ Recent relevant paper scores higher than classic (as expected)")
        logger.info("  ✓ Recency bonus + title match overcame dampened citations")
        return True
    else:
        logger.error("  ✗ Classic paper scored higher (unexpected)")
        logger.error("  ✗ Smart dampening may need adjustment")
        return False


def main():
    """Run all verification tests."""
    logger.info("=" * 80)
    logger.info("Week 2 Day 4: Improvement Verification")
    logger.info("=" * 80)
    logger.info(f"Test started: {datetime.now()}")
    logger.info(f"Log file: {log_file}")

    tests = [
        ("GEO Deduplication", test_geo_deduplication),
        ("Smart Citation Scoring", test_smart_citation_scoring),
        ("Recency Bonus", test_recency_bonus),
        ("Ranking Comparison", test_ranking_comparison),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            logger.info(f"\nRunning test: {test_name}")
            passed = test_func()
            results[test_name] = "PASSED" if passed else "FAILED"
        except Exception as e:
            logger.error(f"Test {test_name} raised exception: {e}", exc_info=True)
            results[test_name] = "ERROR"

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    for test_name, status in results.items():
        symbol = "✓" if status == "PASSED" else "✗"
        logger.info(f"{symbol} {test_name:<40} {status}")

    passed_count = sum(1 for status in results.values() if status == "PASSED")
    total_count = len(results)

    logger.info("")
    logger.info(f"Results: {passed_count}/{total_count} tests passed")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 80)

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
