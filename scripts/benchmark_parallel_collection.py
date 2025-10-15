#!/usr/bin/env python3
"""
Real Workload Benchmark: Parallel URL Collection vs Sequential Waterfall

This script measures actual performance improvements with real papers.

Usage:
    python scripts/benchmark_parallel_collection.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.config.settings import load_config
from omics_oracle_v2.lib.models.publication import Publication
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(text: str):
    """Print section header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{CYAN}ℹ️  {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


# Test dataset: Real PubMed IDs with known full-text availability
TEST_PUBLICATIONS = [
    # PMC Open Access papers (high success rate)
    {"pmid": "34158443", "doi": "10.1093/nar/gkab507", "title": "NCBI paper 1"},
    {"pmid": "33156329", "doi": "10.1093/nar/gkaa1100", "title": "NCBI paper 2"},
    {"pmid": "32442275", "doi": "10.1093/nar/gkaa344", "title": "NCBI paper 3"},
    {"pmid": "31701145", "doi": "10.1093/nar/gkz957", "title": "NCBI paper 4"},
    {"pmid": "30395331", "doi": "10.1093/nar/gky1069", "title": "NCBI paper 5"},
    # Popular bioinformatics papers
    {
        "pmid": "32053187",
        "doi": "10.1093/bioinformatics/btaa102",
        "title": "Bioinfo paper 1",
    },
    {
        "pmid": "31510660",
        "doi": "10.1093/bioinformatics/btz682",
        "title": "Bioinfo paper 2",
    },
    {
        "pmid": "30395289",
        "doi": "10.1093/bioinformatics/bty847",
        "title": "Bioinfo paper 3",
    },
    # Nature/Science papers (may require institutional access)
    {"pmid": "32015508", "doi": "10.1038/s41586-020-1969-6", "title": "Nature paper 1"},
    {"pmid": "31776509", "doi": "10.1038/s41586-019-1823-5", "title": "Nature paper 2"},
]


async def create_test_publications() -> List[Publication]:
    """Create test publication objects"""
    publications = []

    for pub_data in TEST_PUBLICATIONS:
        pub = Publication()
        pub.pmid = pub_data["pmid"]
        pub.doi = pub_data["doi"]
        pub.title = pub_data["title"]
        publications.append(pub)

    return publications


async def benchmark_parallel_collection(
    manager: FullTextManager, publications: List[Publication]
) -> Dict[str, Any]:
    """
    Benchmark NEW parallel collection method

    Returns metrics dict
    """
    print_info(f"Testing PARALLEL collection with {len(publications)} papers...")

    start_time = time.time()

    # Run with parallel collection (collect_all_urls=True)
    results = await manager.get_fulltext_batch(publications, collect_all_urls=True)

    elapsed = time.time() - start_time

    # Analyze results
    success_count = sum(1 for r in results if r.success)
    total_urls = sum(len(r.all_urls) for r in results if r.all_urls)
    avg_urls_per_paper = total_urls / len(results) if results else 0

    # Count URLs by source
    sources_used = {}
    for result in results:
        if result.all_urls:
            for url_obj in result.all_urls:
                source = url_obj.source
                sources_used[source] = sources_used.get(source, 0) + 1

    return {
        "method": "Parallel Collection",
        "total_papers": len(publications),
        "success_count": success_count,
        "success_rate": (success_count / len(publications) * 100)
        if publications
        else 0,
        "total_time": elapsed,
        "avg_time_per_paper": elapsed / len(publications) if publications else 0,
        "total_urls_collected": total_urls,
        "avg_urls_per_paper": avg_urls_per_paper,
        "sources_used": sources_used,
        "urls_per_second": total_urls / elapsed if elapsed > 0 else 0,
    }


async def benchmark_sequential_waterfall(
    manager: FullTextManager, publications: List[Publication]
) -> Dict[str, Any]:
    """
    Benchmark OLD sequential waterfall method

    Returns metrics dict
    """
    print_info(f"Testing SEQUENTIAL waterfall with {len(publications)} papers...")

    start_time = time.time()

    # Run with sequential waterfall (collect_all_urls=False)
    results = await manager.get_fulltext_batch(publications, collect_all_urls=False)

    elapsed = time.time() - start_time

    # Analyze results
    success_count = sum(1 for r in results if r.success)

    # In waterfall mode, we only get 1 URL per paper (first success)
    total_urls = sum(1 for r in results if r.success and r.url)
    avg_urls_per_paper = total_urls / len(results) if results else 0

    # Count sources used (only the successful one)
    sources_used = {}
    for result in results:
        if result.success and result.source:
            source = result.source.value
            sources_used[source] = sources_used.get(source, 0) + 1

    return {
        "method": "Sequential Waterfall",
        "total_papers": len(publications),
        "success_count": success_count,
        "success_rate": (success_count / len(publications) * 100)
        if publications
        else 0,
        "total_time": elapsed,
        "avg_time_per_paper": elapsed / len(publications) if publications else 0,
        "total_urls_collected": total_urls,
        "avg_urls_per_paper": avg_urls_per_paper,
        "sources_used": sources_used,
        "urls_per_second": total_urls / elapsed if elapsed > 0 else 0,
    }


def print_comparison(parallel: Dict[str, Any], sequential: Dict[str, Any]):
    """Print detailed comparison of both methods"""

    print_header("BENCHMARK RESULTS COMPARISON")

    # Calculate improvements
    time_improvement = (
        (sequential["total_time"] - parallel["total_time"])
        / sequential["total_time"]
        * 100
    )
    url_improvement = (
        (
            (parallel["total_urls_collected"] - sequential["total_urls_collected"])
            / sequential["total_urls_collected"]
            * 100
        )
        if sequential["total_urls_collected"] > 0
        else 0
    )
    success_improvement = parallel["success_rate"] - sequential["success_rate"]

    # Overall summary
    print(
        "┌─────────────────────────────────────────────────────────────────────────────┐"
    )
    print(
        "│                           OVERALL PERFORMANCE                               │"
    )
    print(
        "├─────────────────────────────────────────────────────────────────────────────┤"
    )
    print(
        f"│  Test Papers: {parallel['total_papers']:>4}                                                           │"
    )
    print(
        "└─────────────────────────────────────────────────────────────────────────────┘"
    )
    print()

    # Time comparison
    print(f"{CYAN}⏱️  TIME PERFORMANCE:{RESET}")
    print("┌──────────────────────────┬──────────────┬──────────────┬──────────────┐")
    print("│ Metric                   │ Parallel     │ Sequential   │ Improvement  │")
    print("├──────────────────────────┼──────────────┼──────────────┼──────────────┤")
    print(
        f"│ Total Time               │ {parallel['total_time']:>7.2f} sec │ {sequential['total_time']:>7.2f} sec │ {time_improvement:>6.1f}%     │"
    )
    print(
        f"│ Avg Time/Paper           │ {parallel['avg_time_per_paper']:>7.2f} sec │ {sequential['avg_time_per_paper']:>7.2f} sec │ {((sequential['avg_time_per_paper'] - parallel['avg_time_per_paper']) / sequential['avg_time_per_paper'] * 100):>6.1f}%     │"
    )
    print("└──────────────────────────┴──────────────┴──────────────┴──────────────┘")
    print()

    # URL collection comparison
    print(f"{CYAN}🔗 URL COLLECTION:{RESET}")
    print("┌──────────────────────────┬──────────────┬──────────────┬──────────────┐")
    print("│ Metric                   │ Parallel     │ Sequential   │ Difference   │")
    print("├──────────────────────────┼──────────────┼──────────────┼──────────────┤")
    print(
        f"│ Total URLs Collected     │ {parallel['total_urls_collected']:>12} │ {sequential['total_urls_collected']:>12} │ {url_improvement:>6.1f}%     │"
    )
    print(
        f"│ Avg URLs/Paper           │ {parallel['avg_urls_per_paper']:>12.1f} │ {sequential['avg_urls_per_paper']:>12.1f} │ {(parallel['avg_urls_per_paper'] - sequential['avg_urls_per_paper']):>+12.1f} │"
    )
    print(
        f"│ URLs/Second              │ {parallel['urls_per_second']:>12.1f} │ {sequential['urls_per_second']:>12.1f} │ {((parallel['urls_per_second'] - sequential['urls_per_second']) / sequential['urls_per_second'] * 100) if sequential['urls_per_second'] > 0 else 0:>6.1f}%     │"
    )
    print("└──────────────────────────┴──────────────┴──────────────┴──────────────┘")
    print()

    # Success rate comparison
    print(f"{CYAN}✅ SUCCESS RATES:{RESET}")
    print("┌──────────────────────────┬──────────────┬──────────────┬──────────────┐")
    print("│ Metric                   │ Parallel     │ Sequential   │ Difference   │")
    print("├──────────────────────────┼──────────────┼──────────────┼──────────────┤")
    print(
        f"│ Papers with URLs         │ {parallel['success_count']:>12} │ {sequential['success_count']:>12} │ {(parallel['success_count'] - sequential['success_count']):>+12} │"
    )
    print(
        f"│ Success Rate             │ {parallel['success_rate']:>11.1f}% │ {sequential['success_rate']:>11.1f}% │ {success_improvement:>+11.1f}% │"
    )
    print("└──────────────────────────┴──────────────┴──────────────┴──────────────┘")
    print()

    # Sources used
    print(f"{CYAN}📊 SOURCES UTILIZED:{RESET}")
    print()
    print(f"  {BLUE}Parallel Collection:{RESET}")
    for source, count in sorted(parallel["sources_used"].items(), key=lambda x: -x[1]):
        print(f"    • {source:<20} : {count:>3} URLs")

    print()
    print(f"  {BLUE}Sequential Waterfall:{RESET}")
    for source, count in sorted(
        sequential["sources_used"].items(), key=lambda x: -x[1]
    ):
        print(f"    • {source:<20} : {count:>3} papers")

    print()

    # Final verdict
    print_header("VERDICT")

    if time_improvement > 0:
        print_success(f"Parallel collection is {time_improvement:.1f}% FASTER")
    else:
        print_warning(f"Parallel collection is {abs(time_improvement):.1f}% slower")

    if url_improvement > 0:
        print_success(
            f"Parallel collects {url_improvement:.1f}% MORE URLs (better fallback)"
        )
    else:
        print_info("Sequential only gets first success (no fallback options)")

    if success_improvement > 0:
        print_success(f"Parallel has {success_improvement:.1f}% HIGHER success rate")
    elif success_improvement < 0:
        print_warning(
            f"Parallel has {abs(success_improvement):.1f}% lower success rate"
        )
    else:
        print_info("Both methods have equal success rates")

    print()
    print(f"{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}RECOMMENDATION: Use parallel collection (already default!){RESET}")
    print(f"{GREEN}{'='*80}{RESET}")


async def main():
    """Run benchmark comparison"""

    print_header("REAL WORKLOAD BENCHMARK: Parallel vs Sequential")

    print_info("This benchmark uses real PubMed papers to measure actual performance")
    print_info("It will test both methods and compare results")
    print()

    # Load config
    print_info("Loading configuration...")
    config = await load_config()

    # Initialize manager
    print_info("Initializing FullTextManager...")
    manager = FullTextManager(config)
    await manager.initialize()
    print_success("Manager initialized")
    print()

    # Create test publications
    print_info(f"Creating test dataset ({len(TEST_PUBLICATIONS)} papers)...")
    publications = await create_test_publications()
    print_success(f"Created {len(publications)} test publications")

    # Show test papers
    print()
    print("Test Papers:")
    for i, pub in enumerate(publications[:5], 1):
        print(f"  {i}. PMID {pub.pmid}: {pub.title}")
    if len(publications) > 5:
        print(f"  ... and {len(publications) - 5} more")
    print()

    input(f"{YELLOW}Press ENTER to start benchmark...{RESET}")

    # Run benchmarks
    print()
    print_header("BENCHMARK 1: Parallel Collection (NEW)")
    parallel_results = await benchmark_parallel_collection(manager, publications)
    print_success(f"Completed in {parallel_results['total_time']:.2f} seconds")
    print_info(
        f"Collected {parallel_results['total_urls_collected']} URLs from {len(parallel_results['sources_used'])} sources"
    )

    print()
    input(f"{YELLOW}Press ENTER to run sequential benchmark...{RESET}")
    print()

    print_header("BENCHMARK 2: Sequential Waterfall (OLD)")
    sequential_results = await benchmark_sequential_waterfall(manager, publications)
    print_success(f"Completed in {sequential_results['total_time']:.2f} seconds")
    print_info(
        f"Found {sequential_results['success_count']} papers from {len(sequential_results['sources_used'])} sources"
    )

    # Compare results
    print()
    print_comparison(parallel_results, sequential_results)

    # Save results
    results_file = (
        project_root / "data/test_results/parallel_vs_sequential_benchmark.json"
    )
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(
            {
                "benchmark_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "test_papers_count": len(publications),
                "parallel_collection": parallel_results,
                "sequential_waterfall": sequential_results,
                "improvements": {
                    "time_savings_percent": (
                        (
                            sequential_results["total_time"]
                            - parallel_results["total_time"]
                        )
                        / sequential_results["total_time"]
                        * 100
                    ),
                    "additional_urls_collected": parallel_results[
                        "total_urls_collected"
                    ]
                    - sequential_results["total_urls_collected"],
                    "success_rate_improvement": parallel_results["success_rate"]
                    - sequential_results["success_rate"],
                },
            },
            f,
            indent=2,
        )

    print()
    print_success(f"Results saved to: {results_file}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
