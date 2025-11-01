#!/usr/bin/env python3
"""
Stage 3 Pass 1a Baseline Testing

Test 5 queries before making any changes to establish baseline results.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.pipelines.unified_search_pipeline import OmicsSearchPipeline, UnifiedSearchConfig


async def run_baseline_tests():
    """Run baseline tests with 5 diverse queries."""

    # Test queries covering different use cases
    test_queries = [
        "diabetes RNA-seq",
        "cancer genomics BRCA1",
        "Alzheimer's disease proteomics",
        "CRISPR gene editing",
        "COVID-19 vaccine development",
    ]

    print("=" * 80)
    print("STAGE 3 PASS 1a - BASELINE TESTING")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Test queries: {len(test_queries)}")
    print()

    # Initialize pipeline
    print("Initializing OmicsSearchPipeline...")
    config = UnifiedSearchConfig(
        enable_geo_search=True,
        enable_publication_search=True,
        enable_query_optimization=True,
        enable_sapbert=True,
        enable_ner=True,
        enable_caching=True,
        enable_deduplication=True,
        max_geo_results=10,
        max_publication_results=10,
    )

    # Initialize with reduced features to avoid async issues
    from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

    pub_config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_openalex=True,
        enable_scholar=False,
        enable_citations=False,
        enable_pdf_download=False,  # Disable to avoid async issues
        enable_fulltext=False,  # Disable to avoid async issues
        enable_fulltext_retrieval=False,  # Disable to avoid async issues
        deduplication=True,
    )

    config.publication_config = pub_config

    pipeline = OmicsSearchPipeline(config)
    print("Pipeline initialized ✓\n")

    # Store results
    baseline_results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "enable_query_optimization": True,
            "enable_sapbert": True,
            "enable_ner": True,
            "max_geo_results": 10,
            "max_publication_results": 10,
        },
        "queries": [],
    }

    # Test each query
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Query {i}/{len(test_queries)}: '{query}'")
        print("=" * 80)

        try:
            start_time = time.time()

            # Execute search
            result = await pipeline.search(
                query=query,
                max_geo_results=10,
                max_publication_results=10,
            )

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            # Extract key metrics
            geo_count = len(result.geo_datasets) if result.geo_datasets else 0
            pub_count = len(result.publications) if result.publications else 0

            # Get top 3 GEO titles
            geo_titles = []
            if result.geo_datasets:
                for dataset in result.geo_datasets[:3]:
                    geo_titles.append(
                        {
                            "geo_id": dataset.geo_id,
                            "title": dataset.title[:100] + "..."
                            if len(dataset.title) > 100
                            else dataset.title,
                        }
                    )

            # Get top 3 publication titles
            pub_titles = []
            if result.publications:
                for pub in result.publications[:3]:
                    # Handle publication_date which might be datetime or string
                    pub_year = "unknown"
                    if pub.publication_date:
                        if isinstance(pub.publication_date, str):
                            pub_year = (
                                pub.publication_date[:4]
                                if len(pub.publication_date) >= 4
                                else pub.publication_date
                            )
                        elif hasattr(pub.publication_date, "year"):
                            pub_year = str(pub.publication_date.year)

                    pub_titles.append(
                        {
                            "title": pub.title[:100] + "..." if len(pub.title) > 100 else pub.title,
                            "year": pub_year,
                        }
                    )

            # Print results
            print(f"✓ Search completed in {latency_ms:.1f}ms")
            print(f"  Query type: {result.query_type}")
            print(f"  Optimized query: {result.optimized_query}")
            print(f"  Cache hit: {result.cache_hit}")
            print(f"  GEO datasets: {geo_count}")
            print(f"  Publications: {pub_count}")

            if geo_titles:
                print("\n  Top 3 GEO datasets:")
                for j, ds in enumerate(geo_titles, 1):
                    print(f"    {j}. [{ds['geo_id']}] {ds['title']}")

            if pub_titles:
                print("\n  Top 3 Publications:")
                for j, pub in enumerate(pub_titles, 1):
                    print(f"    {j}. [{pub['year']}] {pub['title']}")

            # Store results
            query_result = {
                "query": query,
                "latency_ms": latency_ms,
                "query_type": result.query_type,
                "optimized_query": result.optimized_query,
                "cache_hit": result.cache_hit,
                "geo_count": geo_count,
                "publication_count": pub_count,
                "top_geo_titles": geo_titles,
                "top_publication_titles": pub_titles,
            }
            baseline_results["queries"].append(query_result)

        except Exception as e:
            print(f"✗ Query failed: {e}")
            baseline_results["queries"].append(
                {
                    "query": query,
                    "error": str(e),
                }
            )

    # Save baseline results
    output_file = Path("data/test_results/stage3_pass1a_baseline.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert to JSON-serializable format
    import json

    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    with open(output_file, "w") as f:
        json.dump(baseline_results, f, indent=2, cls=DateTimeEncoder)

    print(f"\n{'=' * 80}")
    print("BASELINE TESTING COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {output_file}")
    print()

    # Print summary
    successful_queries = [q for q in baseline_results["queries"] if "error" not in q]
    failed_queries = [q for q in baseline_results["queries"] if "error" in q]

    print("Summary:")
    print(f"  Total queries: {len(test_queries)}")
    print(f"  Successful: {len(successful_queries)}")
    print(f"  Failed: {len(failed_queries)}")

    if successful_queries:
        avg_latency = sum(q["latency_ms"] for q in successful_queries) / len(successful_queries)
        avg_geo = sum(q["geo_count"] for q in successful_queries) / len(successful_queries)
        avg_pub = sum(q["publication_count"] for q in successful_queries) / len(successful_queries)

        print(f"  Avg latency: {avg_latency:.1f}ms")
        print(f"  Avg GEO results: {avg_geo:.1f}")
        print(f"  Avg publication results: {avg_pub:.1f}")

    print()
    return baseline_results


if __name__ == "__main__":
    asyncio.run(run_baseline_tests())
