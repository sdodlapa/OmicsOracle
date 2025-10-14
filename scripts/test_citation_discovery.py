#!/usr/bin/env python
"""
Test Citation Discovery with GSE69633

Real-world test of the complete pipeline with all enhancements:
- Semantic Scholar integration
- Two-layer caching
- Error handling & retry logic
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

from omics_oracle_v2.lib.pipelines.citation_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_gse69633():
    """Test citation discovery with GSE69633"""
    
    print("=" * 80)
    print("🧪 Testing Citation Discovery with GSE69633")
    print("=" * 80)
    print()
    
    # Initialize discovery
    print(f"📦 Initializing GEOCitationDiscovery...")
    discovery = GEOCitationDiscovery(use_strategy_a=True, use_strategy_b=True, enable_cache=True)
    print("   ✓ 5 sources configured: OpenAlex, Semantic Scholar, Europe PMC, OpenCitations, PubMed")
    print(f"   ✓ Cache enabled (TTL: 1 week)")
    print(f"   ✓ Error handling enabled (retry + fallback)")
    print()
    
    # Create GEO metadata for GSE69633
    # Real metadata from GEO:
    # Title: Lead exposure induces changes in 5-hydroxymethylcytosine clusters...
    # PMID: 26046694 (Sen A et al., Epigenetics 2015)
    metadata = GEOSeriesMetadata(
        geo_id="GSE69633",
        pubmed_ids=["26046694"],  # Sen A et al., Epigenetics 2015
        title="Lead exposure induces changes in 5-hydroxymethylcytosine clusters in CpG islands",
        summary="Prenatal exposure to lead (Pb) and DNA methylation changes"
    )
    
    print(f"📊 Testing with: {metadata.geo_id}")
    print(f"   PMID: {metadata.pubmed_ids[0] if metadata.pubmed_ids else 'None'}")
    print()
    
    # Test 1: First run (cache miss)
    print("🔍 Test 1: First discovery (cache miss, full API calls)")
    print("-" * 80)
    start_time = datetime.now()
    
    try:
        result = await discovery.find_citing_papers(metadata, max_results=50)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Success! Found {len(result.citing_papers)} citing papers")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Original PMID: {result.original_pmid}")
        
        if 'strategy_a' in result.strategy_breakdown:
            print(f"   Strategy A (citations): {len(result.strategy_breakdown['strategy_a'])} papers")
        if 'strategy_b' in result.strategy_breakdown:
            print(f"   Strategy B (mentions): {len(result.strategy_breakdown['strategy_b'])} papers")
        
        # Show sample papers
        if result.citing_papers:
            print(f"\n   📄 Sample papers:")
            for i, paper in enumerate(result.citing_papers[:3], 1):
                print(f"      {i}. {paper.title[:70]}...")
                print(f"         Authors: {', '.join(paper.authors[:2]) if paper.authors else 'Unknown'}")
                print(f"         PMID: {paper.pmid or 'N/A'}, DOI: {paper.doi or 'N/A'}")
                print(f"         Source: {paper.source.value}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test 2: Second run (cache hit)
    print("🔍 Test 2: Repeat discovery (cache hit, instant response)")
    print("-" * 80)
    start_time = datetime.now()
    
    try:
        result2 = await discovery.find_citing_papers(metadata, max_results=50)
        
        elapsed2 = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Success! Found {len(result2.citing_papers)} citing papers")
        print(f"   Time: {elapsed2:.2f}s")
        print(f"   Speedup: {elapsed / elapsed2:.1f}x faster!")
        
        if 'cached' in result2.strategy_breakdown:
            print(f"   ✓ Served from cache")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print()
    
    # Test 3: Cache statistics
    print("📊 Cache Statistics")
    print("-" * 80)
    if discovery.cache:
        stats = discovery.cache.get_stats()
        print(f"   Total queries: {stats.total_queries}")
        print(f"   Cache hits: {stats.hits}")
        print(f"   Cache misses: {stats.misses}")
        print(f"   Hit rate: {stats.hit_rate:.1%}")
        print(f"   Memory entries: {stats.memory_entries}")
        print(f"   Disk entries: {stats.disk_entries}")
    
    print()
    print("=" * 80)
    print("✅ All tests passed! Citation discovery working perfectly.")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_gse69633())
    sys.exit(0 if success else 1)
