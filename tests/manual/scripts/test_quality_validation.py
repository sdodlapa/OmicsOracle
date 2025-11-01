#!/usr/bin/env python3
"""
Test script for Phase 8: Quality Validation System

Tests the new quality validation system with real citation data.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.pipelines.citation_discovery.cache import DiscoveryCache
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.pipelines.citation_discovery.quality_validation import (
    QualityConfig,
    QualityLevel,
    QualityValidator,
    filter_by_quality,
)
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource
from omics_oracle_v2.lib.search_engines.geo.client import GEOClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_publications():
    """Create test publications with varying quality levels."""
    now = datetime.now()
    
    publications = [
        # EXCELLENT: Complete metadata, high citations, top journal
        Publication(
            pmid="12345678",
            doi="10.1038/nature12345",
            title="High-Impact Study on Chromatin Accessibility in Human T Cells Using ATAC-seq Analysis",
            abstract="This comprehensive study examines chromatin accessibility patterns in human T cells across multiple activation states. We performed ATAC-seq on 150 samples and identified novel regulatory elements controlling T cell differentiation. Our findings reveal previously unknown mechanisms of gene regulation during immune responses. The data has been deposited in GEO and provides a valuable resource for the immunology community." * 2,
            authors=["Smith J", "Johnson K", "Williams L", "Brown M", "Jones P"],
            journal="Nature",
            publication_date=now - timedelta(days=365),
            source=PublicationSource.PUBMED,
            citations=125,
            mesh_terms=["Chromatin", "T-Lymphocytes", "Gene Expression Regulation"],
            keywords=["ATAC-seq", "chromatin accessibility", "T cells", "immune response"],
        ),
        
        # GOOD: Complete metadata, decent citations, good journal
        Publication(
            pmid="23456789",
            doi="10.1186/s13059-023-12345",
            title="RNA-seq Analysis of Gene Expression in Cancer Cell Lines",
            abstract="We performed RNA-seq analysis on multiple cancer cell lines to identify differentially expressed genes. This study provides insights into cancer biology and potential therapeutic targets. Data is available in GEO.",
            authors=["Garcia M", "Martinez R", "Lopez A"],
            journal="Genome Biology",
            publication_date=now - timedelta(days=730),
            source=PublicationSource.PUBMED,
            citations=45,
            mesh_terms=["RNA-seq", "Neoplasms", "Gene Expression"],
        ),
        
        # ACCEPTABLE: Missing some metadata, low citations
        Publication(
            pmid="34567890",
            doi="10.1371/journal.pone.0123456",
            title="Study on Gene Expression",
            abstract="Brief analysis of gene expression patterns.",
            authors=["Chen W"],
            journal="PLoS ONE",
            publication_date=now - timedelta(days=1095),
            source=PublicationSource.PUBMED,
            citations=8,
        ),
        
        # POOR: Very old, low citations, minimal abstract
        Publication(
            pmid="45678901",
            doi="10.1234/oldjournal.2005.123",
            title="Old Study",
            abstract="Short abstract.",
            authors=["OldAuthor A"],
            journal="Old Journal",
            publication_date=datetime(2005, 1, 1),
            source=PublicationSource.PUBMED,
            citations=3,
        ),
        
        # REJECTED: Missing critical metadata
        Publication(
            doi="10.1111/unknown.123",
            title="Unknown Paper",
            # No abstract
            # No authors
            source=PublicationSource.CROSSREF,
            citations=0,
        ),
        
        # PREPRINT: bioRxiv preprint (test preprint handling)
        Publication(
            doi="10.1101/2024.01.15.123456",
            title="Novel Findings in Single-Cell Sequencing: A Comprehensive Analysis",
            abstract="This preprint presents novel findings from single-cell RNA sequencing experiments. We analyzed thousands of cells and identified new cell types and states. The data has been made publicly available for the research community.",
            authors=["Lee S", "Kim J", "Park H"],
            publication_date=now - timedelta(days=90),
            source=PublicationSource.BIORXIV,
            citations=2,  # Few citations (recent preprint)
        ),
        
        # PREDATORY: Potential predatory journal pattern
        Publication(
            pmid="56789012",
            doi="10.9999/ijrset.2023.456",
            title="International Journal of Recent Scientific and Engineering Technology Article",
            abstract="This paper discusses various scientific topics with limited depth and questionable peer review process.",
            authors=["Unknown Author"],
            journal="International Journal of Recent Scientific Engineering Technology",
            publication_date=now - timedelta(days=180),
            source=PublicationSource.PUBMED,
            citations=1,
        ),
    ]
    
    return publications


def test_quality_validation():
    """Test quality validation with synthetic data."""
    logger.info("=" * 80)
    logger.info("🧪 Phase 8: Quality Validation System Test")
    logger.info("=" * 80)
    logger.info("")
    
    # Create test publications
    logger.info("Creating test publications with varying quality...")
    publications = create_test_publications()
    logger.info(f"Created {len(publications)} test publications")
    logger.info("")
    
    # Test 1: Validate all publications
    logger.info("Test 1: Validating all publications")
    logger.info("-" * 80)
    validator = QualityValidator()
    assessments = validator.validate_publications(publications)
    logger.info("")
    
    # Display individual assessments
    logger.info("Individual Quality Assessments:")
    logger.info("=" * 80)
    for assessment in assessments:
        pub = assessment.publication
        logger.info(f"\nPublication: {pub.title[:60]}...")
        logger.info(f"  PMID: {pub.pmid or 'N/A'}")
        logger.info(f"  Journal: {pub.journal or 'N/A'}")
        logger.info(f"  Quality Level: {assessment.quality_level.value.upper()}")
        logger.info(f"  Overall Score: {assessment.quality_score:.3f}")
        logger.info(f"  Action: {assessment.recommended_action}")
        logger.info(f"  Score Breakdown:")
        for key, value in assessment.breakdown.items():
            logger.info(f"    {key:12s}: {value:.3f}")
        
        if assessment.strengths:
            logger.info(f"  Strengths:")
            for strength in assessment.strengths:
                logger.info(f"    ✅ {strength}")
        
        if assessment.issues:
            logger.info(f"  Issues:")
            for issue in assessment.issues:
                icon = "🔴" if issue.severity == "critical" else "⚠️" if issue.severity == "warning" else "ℹ️"
                logger.info(f"    {icon} [{issue.severity}] {issue.message}")
    
    logger.info("\n" + "=" * 80)
    
    # Test 2: Filter by quality levels
    logger.info("\n\nTest 2: Filter by Different Quality Levels")
    logger.info("-" * 80)
    
    for min_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD, QualityLevel.ACCEPTABLE]:
        filtered, _ = filter_by_quality(publications, min_level=min_level)
        logger.info(f"Min level: {min_level.value:12s} -> {len(filtered):2d} papers included")
    
    # Test 3: Custom config (strict mode)
    logger.info("\n\nTest 3: Strict Configuration")
    logger.info("-" * 80)
    strict_config = QualityConfig(
        require_abstract=True,
        require_authors=True,
        min_abstract_length=200,
        min_citations_recent=10,
        min_citations_older=20,
        check_predatory=True,
        allow_preprints=False,
        min_quality_score=0.5,
    )
    
    strict_validator = QualityValidator(config=strict_config)
    strict_assessments = strict_validator.validate_publications(publications)
    
    strict_filtered = [a.publication for a in strict_assessments if a.recommended_action != "exclude"]
    logger.info(f"Strict filtering: {len(publications)} -> {len(strict_filtered)} papers")
    logger.info("")
    
    return assessments


def test_with_real_data():
    """Test quality validation with real GEO citation data."""
    logger.info("\n" + "=" * 80)
    logger.info("🔬 Testing with Real GEO Citation Data")
    logger.info("=" * 80)
    logger.info("")
    
    # Use cached data if available
    test_geo_id = "GSE52564"
    
    logger.info(f"Fetching citations for {test_geo_id}...")
    
    # Initialize GEO client
    import asyncio
    geo_client = GEOClient()
    geo_metadata = asyncio.run(geo_client.get_metadata(test_geo_id, include_sra=False))
    
    if not geo_metadata:
        logger.error(f"Could not fetch metadata for {test_geo_id}")
        return
    
    logger.info(f"GEO Dataset: {geo_metadata.title}")
    logger.info(f"Original PMID: {geo_metadata.pubmed_ids[0] if geo_metadata.pubmed_ids else 'None'}")
    logger.info("")
    
    # Run citation discovery
    discovery = GEOCitationDiscovery(enable_cache=True)
    result = asyncio.run(discovery.find_citing_papers(geo_metadata, max_results=50))
    
    logger.info(f"Found {len(result.citing_papers)} citing papers")
    logger.info("")
    
    # Validate quality
    logger.info("Validating quality of discovered papers...")
    validator = QualityValidator()
    assessments = validator.validate_publications(result.citing_papers)
    
    # Filter by quality
    logger.info("\n\nFiltering by Quality Levels:")
    logger.info("-" * 80)
    
    for min_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD, QualityLevel.ACCEPTABLE]:
        filtered = [
            a.publication for a in assessments
            if a.quality_level.value in [lvl.value for lvl in QualityLevel if 
                                         list(QualityLevel).index(lvl) >= list(QualityLevel).index(min_level)]
            and a.recommended_action != "exclude"
        ]
        logger.info(f"Min level: {min_level.value:12s} -> {len(filtered):2d} papers ({(len(filtered)/len(result.citing_papers))*100:.1f}%)")
    
    # Show top quality papers
    logger.info("\n\nTop 10 Highest Quality Papers:")
    logger.info("=" * 80)
    sorted_assessments = sorted(assessments, key=lambda a: a.quality_score, reverse=True)
    
    for i, assessment in enumerate(sorted_assessments[:10], 1):
        pub = assessment.publication
        logger.info(f"\n{i}. {pub.title[:70]}...")
        logger.info(f"   Quality: {assessment.quality_level.value.upper()} (score: {assessment.quality_score:.3f})")
        logger.info(f"   PMID: {pub.pmid or 'N/A'} | Citations: {pub.citations or 0} | Year: {pub.publication_date.year if pub.publication_date else 'N/A'}")
        logger.info(f"   Journal: {pub.journal or 'N/A'}")
        if assessment.strengths:
            logger.info(f"   Strengths: {', '.join(assessment.strengths[:3])}")
    
    logger.info("\n" + "=" * 80)


def main():
    """Main test function."""
    try:
        # Test 1: Synthetic data
        test_quality_validation()
        
        # Test 2: Real GEO data
        test_with_real_data()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ Phase 8 Quality Validation Tests Complete!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
