#!/usr/bin/env python3
"""
Test script to display detailed relevance scores.
Shows how papers are ranked and why.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.pipelines.citation_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata


async def test_relevance_scoring():
    """Test relevance scoring with GSE69633"""
    
    print("=" * 80)
    print("🧪 Testing Relevance Scoring with GSE69633")
    print("=" * 80)
    print()
    
    # Initialize discovery
    discovery = GEOCitationDiscovery(
        use_strategy_a=True,
        use_strategy_b=True,
        enable_cache=True,
    )
    
    # Test dataset
    geo_id = "GSE69633"
    pmid = "26046694"
    
    print(f"📊 Dataset: {geo_id}")
    print(f"   PMID: {pmid}")
    print()
    
    # Create GEO metadata (using actual metadata from GSE69633)
    geo_metadata = GEOSeriesMetadata(
        geo_id=geo_id,
        title="DNA methylation profiles in lead-exposed children",
        summary="This study examines DNA methylation changes in children exposed to environmental lead",
        organism="Homo sapiens",
        sample_count=127,
        platform_ids=["GPL13534"],
        pubmed_id=pmid,
    )
    
    # Find citing papers
    print("🔍 Finding and scoring papers...")
    print()
    
    result = await discovery.find_citing_papers(geo_metadata, max_results=100)
    papers = result.citing_papers
    
    if not papers:
        print("❌ No papers found")
        return
    
    print(f"✅ Found {len(papers)} papers")
    print()
    print("=" * 80)
    print("📊 TOP 10 PAPERS BY RELEVANCE SCORE")
    print("=" * 80)
    print()
    
    # Display top 10 papers with detailed scores
    for i, paper in enumerate(papers[:10], 1):
        # Get score breakdown
        score = getattr(paper, '_relevance_score', None)
        
        print(f"{i}. {paper.title[:70]}...")
        print(f"   Authors: {', '.join(paper.authors[:2])}{'...' if len(paper.authors) > 2 else ''}")
        print(f"   Year: {paper.publication_date.year if paper.publication_date else 'Unknown'}")
        print(f"   Citations: {paper.citations or 0}")
        print(f"   Source: {paper.source.value if paper.source else 'Unknown'}")
        
        if score:
            breakdown = score.breakdown
            print(f"   ")
            print(f"   📈 RELEVANCE SCORE: {breakdown['total']:.3f}")
            print(f"      • Content similarity: {breakdown['content_similarity']:.3f} (40% weight)")
            print(f"      • Keyword matching:   {breakdown['keyword_match']:.3f} (30% weight)")
            print(f"      • Recency:            {breakdown['recency']:.3f} (20% weight)")
            print(f"      • Citation count:     {breakdown['citation_count']:.3f} (10% weight)")
        
        print()
    
    # Show statistics
    print("=" * 80)
    print("📊 SCORE STATISTICS")
    print("=" * 80)
    print()
    
    scores = [getattr(p, '_relevance_score', None) for p in papers]
    scores = [s.total for s in scores if s]
    
    if scores:
        print(f"   Average score: {sum(scores) / len(scores):.3f}")
        print(f"   Highest score: {max(scores):.3f}")
        print(f"   Lowest score:  {min(scores):.3f}")
        print(f"   Range:         {max(scores) - min(scores):.3f}")
    
    print()
    
    # Show year distribution
    print("=" * 80)
    print("📅 YEAR DISTRIBUTION")
    print("=" * 80)
    print()
    
    year_counts = {}
    for paper in papers:
        if paper.publication_date:
            year = paper.publication_date.year
            year_counts[year] = year_counts.get(year, 0) + 1
    
    for year in sorted(year_counts.keys(), reverse=True)[:5]:
        count = year_counts[year]
        bar = "█" * (count // 2)
        print(f"   {year}: {count:2d} papers {bar}")
    
    print()


if __name__ == "__main__":
    asyncio.run(test_relevance_scoring())
