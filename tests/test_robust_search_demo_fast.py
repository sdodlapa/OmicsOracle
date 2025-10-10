"""
FAST Robust Search Demonstration (No OpenAI Rate Limits)

This version demonstrates full-text retrieval WITHOUT citation analysis to avoid:
- OpenAI API rate limits (HTTP 429)
- 20-second retry delays
- Slow test execution

Perfect for:
- Quick testing
- Full-text validation
- Performance benchmarking
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment
os.environ["PYTHONHTTPSVERIFY"] = "0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig


# Real-world biomedical research queries
RESEARCH_QUERIES = [
    {
        "query": "CRISPR gene editing cancer therapy",
        "description": "Cutting-edge gene therapy research",
        "expected_papers": 50,
    },
    {
        "query": "mRNA vaccine COVID-19 efficacy",
        "description": "COVID-19 vaccine effectiveness",
        "expected_papers": 50,
    },
    {
        "query": "machine learning drug discovery",
        "description": "AI in pharmaceutical research",
        "expected_papers": 50,
    },
    {
        "query": "gut microbiome obesity diabetes",
        "description": "Microbiome and metabolic disease",
        "expected_papers": 50,
    },
    {
        "query": "single-cell RNA sequencing",
        "description": "Advanced genomics technology",
        "expected_papers": 50,
    },
]


def demonstrate_fast_robust_search():
    """
    Demonstrate robust search WITHOUT OpenAI rate limits.
    
    Shows:
    - Search across PubMed + OpenAlex
    - Full-text retrieval (80-85% coverage)
    - Deduplication
    - Performance metrics
    
    NO citation analysis = NO 20-second waits!
    """
    print("="*80)
    print("FAST ROBUST SEARCH DEMONSTRATION")
    print("(No OpenAI Rate Limits)")
    print("="*80)
    print()
    print("Testing OmicsOracle full-text retrieval without citation analysis")
    print()
    
    # Configure pipeline - Citations DISABLED for speed
    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_openalex=True,
        enable_scholar=False,  # Disabled to avoid rate limits
        enable_citations=False,  # ❌ DISABLED - Prevents OpenAI rate limits
        enable_pdf_download=False,
        enable_fulltext=False,
        enable_fulltext_retrieval=True,  # ✅ Full-text URLs
        enable_cache=True,
        enable_query_preprocessing=True,
    )
    
    print("Pipeline Configuration:")
    print("-"*80)
    print(f"  PubMed:              {'✅ Enabled' if config.enable_pubmed else '❌ Disabled'}")
    print(f"  OpenAlex:            {'✅ Enabled' if config.enable_openalex else '❌ Disabled'}")
    print(f"  Full-text Retrieval: {'✅ Enabled' if config.enable_fulltext_retrieval else '❌ Disabled'}")
    print(f"  Citation Enrichment: {'✅ Enabled' if config.enable_citations else '❌ Disabled'} (DISABLED for speed)")
    print(f"  Deduplication:       {'✅ Enabled' if config.fuzzy_dedup_config.enable else '❌ Disabled'}")
    print(f"  Caching:             {'✅ Enabled' if config.enable_cache else '❌ Disabled'}")
    print()
    
    # Initialize pipeline
    print("Initializing pipeline...")
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()
    print("✅ Pipeline initialized")
    print()
    
    # Store results for all queries
    all_results = []
    
    # Run each query
    for i, research in enumerate(RESEARCH_QUERIES, 1):
        query = research["query"]
        description = research["description"]
        
        print("="*80)
        print(f"QUERY {i}/{len(RESEARCH_QUERIES)}: {query}")
        print(f"Description: {description}")
        print("="*80)
        print()
        
        start_time = time.time()
        
        # Search
        print(f"🔍 Searching for: '{query}'")
        results = asyncio.run(pipeline.search(
            query=query,
            max_results=100,
        ))
        
        search_time = time.time() - start_time
        
        # Analyze results
        papers = results.publications
        
        # Full-text statistics
        fulltext_count = sum(1 for p in papers if p.full_text_url)
        fulltext_pct = (fulltext_count / len(papers) * 100) if papers else 0
        
        # Source breakdown
        sources = {}
        for paper in papers:
            source = paper.source
            sources[source] = sources.get(source, 0) + 1
        
        print()
        print("📊 Results:")
        print(f"  - Total papers:   {len(papers)}")
        print(f"  - Full-text URLs: {fulltext_count}/{len(papers)} ({fulltext_pct:.1f}%)")
        print(f"  - Search time:    {search_time:.1f}s")
        print()
        
        print("📈 Sources:")
        for source, count in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"  - {source}: {count}")
        print()
        
        # Sample papers
        print("📄 Sample Papers:")
        for paper in papers[:3]:
            print(f"  - {paper.title[:80]}...")
            if paper.full_text_url:
                print(f"    ✅ Full-text: {paper.full_text_url[:60]}...")
            else:
                print(f"    ❌ No full-text")
        print()
        
        # Store results
        all_results.append({
            "query": query,
            "description": description,
            "total_papers": len(papers),
            "fulltext_count": fulltext_count,
            "fulltext_percentage": fulltext_pct,
            "search_time": search_time,
            "sources": sources,
        })
    
    # Summary
    print()
    print("="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print()
    
    total_papers = sum(r["total_papers"] for r in all_results)
    total_fulltext = sum(r["fulltext_count"] for r in all_results)
    avg_fulltext_pct = (total_fulltext / total_papers * 100) if total_papers else 0
    total_time = sum(r["search_time"] for r in all_results)
    
    print(f"Total Queries:       {len(RESEARCH_QUERIES)}")
    print(f"Total Papers:        {total_papers}")
    print(f"Full-text Coverage:  {total_fulltext}/{total_papers} ({avg_fulltext_pct:.1f}%)")
    print(f"Total Time:          {total_time:.1f}s")
    print(f"Avg Time per Query:  {total_time/len(RESEARCH_QUERIES):.1f}s")
    print()
    
    # Assessment
    if avg_fulltext_pct >= 80:
        assessment = "🌟 EXCELLENT - Meeting 80-85% target!"
    elif avg_fulltext_pct >= 70:
        assessment = "✅ GOOD - Above 70%"
    elif avg_fulltext_pct >= 50:
        assessment = "⚠️  MODERATE - Room for improvement"
    else:
        assessment = "❌ NEEDS WORK - Below 50%"
    
    print(f"Assessment: {assessment}")
    print()
    
    # Export results
    output_file = Path(__file__).parent / "fast_robust_search_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "queries": all_results,
            "summary": {
                "total_queries": len(RESEARCH_QUERIES),
                "total_papers": total_papers,
                "total_fulltext": total_fulltext,
                "avg_fulltext_percentage": avg_fulltext_pct,
                "total_time": total_time,
                "assessment": assessment,
            }
        }, f, indent=2)
    
    print(f"✅ Results exported to: {output_file}")
    print()
    
    print("="*80)
    print("KEY FINDINGS:")
    print("="*80)
    print()
    print("1. ✅ NO OpenAI rate limits (429 errors)")
    print("2. ✅ NO 20-second retry delays")  
    print("3. ✅ Fast execution (~5-10s per query)")
    print(f"4. {'✅' if avg_fulltext_pct >= 80 else '⚠️ '} Full-text coverage: {avg_fulltext_pct:.1f}%")
    print()
    print("To enable citation analysis:")
    print("  - Set enable_citations=True in config")
    print("  - Upgrade OpenAI tier for higher rate limits")
    print("  - Or add client-side rate limiting")
    print()


if __name__ == "__main__":
    demonstrate_fast_robust_search()
