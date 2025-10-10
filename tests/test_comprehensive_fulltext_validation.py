"""
Comprehensive Full-Text Validation Test
Tests the complete full-text retrieval system with 100 diverse papers.

This demonstrates:
1. Coverage across all sources (Unpaywall, Sci-Hub, LibGen, arXiv, etc.)
2. Robustness with different paper types and publishers
3. Performance metrics and statistics
4. Real-world applicability
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment
os.environ["PYTHONHTTPSVERIFY"] = "0"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import the 100-paper dataset
import importlib.util

from omics_oracle_v2.lib.publications.fulltext_manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

spec = importlib.util.spec_from_file_location(
    "diverse_papers", Path(__file__).parent / "test_datasets" / "100_diverse_papers.py"
)
diverse_papers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diverse_papers)
COMPREHENSIVE_100_PAPERS = diverse_papers.COMPREHENSIVE_100_PAPERS


async def validate_comprehensive_fulltext():
    """
    Comprehensive validation test with 100 diverse papers.

    Tests all sources: Unpaywall + Sci-Hub + LibGen + arXiv + bioRxiv + CORE + Crossref
    """
    print("=" * 80)
    print("COMPREHENSIVE FULL-TEXT VALIDATION TEST")
    print("=" * 80)
    print()
    print(f"Testing {len(COMPREHENSIVE_100_PAPERS)} diverse papers")
    print("Sources: Unpaywall + Sci-Hub + LibGen + arXiv + bioRxiv + CORE + Crossref")
    print()

    # Create publications from dataset
    publications = []
    for i, paper in enumerate(COMPREHENSIVE_100_PAPERS):
        # Generate a descriptive title from metadata (dataset doesn't include titles)
        title_parts = []
        if paper.get("publisher"):
            title_parts.append(paper["publisher"])
        if paper.get("year"):
            title_parts.append(str(paper["year"]))
        if paper.get("type"):
            title_parts.append(paper["type"])
        if paper.get("doi"):
            title_parts.append(f"DOI:{paper['doi'][:20]}...")

        title = " - ".join(title_parts) if title_parts else f"Test Paper {i+1}"

        pub = Publication(
            title=title,
            doi=paper.get("doi"),
            pmid=paper.get("pmid"),
            source=PublicationSource.PUBMED,
        )
        publications.append(pub)

    # Phase 1: Test with OPTIMIZED sources (institutional first!)
    print("PHASE 1: OPTIMIZED - All Sources (Institutional + Unpaywall + Sci-Hub + LibGen)")
    print("-" * 80)

    config = FullTextManagerConfig(
        enable_institutional=True,  # ✅ NEW - Priority 1 (Georgia Tech)
        enable_unpaywall=True,  # Priority 2: Legal OA
        enable_core=True,  # Priority 3: CORE.ac.uk
        enable_openalex=True,  # Priority 4: OA metadata
        enable_crossref=True,  # Priority 5: Publisher links
        enable_biorxiv=True,  # Priority 6: Preprints
        enable_arxiv=True,
        enable_scihub=True,  # Priority 7: Sci-Hub (optimized - 4 mirrors, 2 patterns)
        enable_libgen=True,  # Priority 8: LibGen
        core_api_key=os.getenv("CORE_API_KEY"),  # Load from .env
        unpaywall_email="sdodl001@odu.edu",
        max_concurrent=3,
    )

    start_time = time.time()

    async with FullTextManager(config) as manager:
        results = []

        # Process in smaller batches for progress tracking
        batch_size = 10
        for i in range(0, len(publications), batch_size):
            batch = publications[i : i + batch_size]
            print(f"\nProcessing papers {i+1}-{min(i+batch_size, len(publications))}...")

            batch_results = await manager.get_fulltext_batch(batch)
            results.extend(batch_results)

            # Show progress
            success_count = sum(1 for r in batch_results if r.success)
            print(
                f"  Batch results: {success_count}/{len(batch)} found ({success_count/len(batch)*100:.1f}%)"
            )

        elapsed = time.time() - start_time

        # Analyze results
        print()
        print("=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        print()

        total_found = sum(1 for r in results if r.success)
        total_papers = len(results)

        print(f"Overall Coverage: {total_found}/{total_papers} ({total_found/total_papers*100:.1f}%)")
        print(f"Total Time: {elapsed:.1f}s ({elapsed/total_papers:.2f}s per paper)")
        print()

        # Breakdown by source
        source_counts = {}
        for result in results:
            if result.success:
                source = result.source.value
                source_counts[source] = source_counts.get(source, 0) + 1

        print("Breakdown by Source:")
        print("-" * 80)
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_papers * 100
            print(f"  {source:15} → {count:3} papers ({percentage:5.1f}%)")
        print()

        # Breakdown by paper type
        type_stats = {}
        for i, result in enumerate(results):
            paper_type = COMPREHENSIVE_100_PAPERS[i].get("type", "unknown")
            if paper_type not in type_stats:
                type_stats[paper_type] = {"total": 0, "found": 0}
            type_stats[paper_type]["total"] += 1
            if result.success:
                type_stats[paper_type]["found"] += 1

        print("Coverage by Paper Type:")
        print("-" * 80)
        for paper_type, stats in sorted(type_stats.items()):
            percentage = stats["found"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"  {paper_type:15} → {stats['found']:3}/{stats['total']:3} ({percentage:5.1f}%)")
        print()

        # Publisher breakdown (for paywalled papers)
        publisher_stats = {}
        for i, result in enumerate(results):
            if COMPREHENSIVE_100_PAPERS[i].get("type") == "paywalled":
                publisher = COMPREHENSIVE_100_PAPERS[i].get("publisher", "unknown")
                if publisher not in publisher_stats:
                    publisher_stats[publisher] = {"total": 0, "found": 0}
                publisher_stats[publisher]["total"] += 1
                if result.success:
                    publisher_stats[publisher]["found"] += 1

        if publisher_stats:
            print("Coverage by Publisher (Paywalled Papers Only):")
            print("-" * 80)
            for publisher, stats in sorted(
                publisher_stats.items(), key=lambda x: x[1]["total"], reverse=True
            ):
                percentage = stats["found"] / stats["total"] * 100 if stats["total"] > 0 else 0
                print(f"  {publisher:20} → {stats['found']:2}/{stats['total']:2} ({percentage:5.1f}%)")
            print()

        # Papers not found (for debugging)
        not_found = []
        for i, result in enumerate(results):
            if not result.success:
                not_found.append(
                    {
                        "title": COMPREHENSIVE_100_PAPERS[i]["title"][:60],
                        "doi": COMPREHENSIVE_100_PAPERS[i].get("doi"),
                        "type": COMPREHENSIVE_100_PAPERS[i].get("type"),
                        "year": COMPREHENSIVE_100_PAPERS[i].get("year"),
                    }
                )

        if not_found:
            print(f"Papers Not Found ({len(not_found)}):")
            print("-" * 80)
            for paper in not_found[:10]:  # Show first 10
                print(f"  [{paper['type']:10}] {paper['year']} - {paper['title']}")
            if len(not_found) > 10:
                print(f"  ... and {len(not_found) - 10} more")
            print()

        # Save detailed results to JSON
        output_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_papers": total_papers,
            "found": total_found,
            "coverage_percentage": total_found / total_papers * 100,
            "elapsed_seconds": elapsed,
            "seconds_per_paper": elapsed / total_papers,
            "sources": source_counts,
            "by_type": type_stats,
            "by_publisher": publisher_stats,
            "not_found": not_found,
        }

        output_file = Path("fulltext_validation_results.json")
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"✓ Detailed results saved to: {output_file}")
        print()

        # Final assessment
        print("=" * 80)
        print("ASSESSMENT")
        print("=" * 80)
        print()

        if total_found / total_papers >= 0.85:
            print("✅ EXCELLENT: Coverage >= 85%")
            print("   System is production-ready for research use.")
        elif total_found / total_papers >= 0.70:
            print("✅ GOOD: Coverage >= 70%")
            print("   System provides strong coverage for most research needs.")
        elif total_found / total_papers >= 0.50:
            print("⚠️  MODERATE: Coverage >= 50%")
            print("   System works but may miss some papers.")
        else:
            print("❌ LOW: Coverage < 50%")
            print("   System needs optimization.")
        print()

        return total_found / total_papers >= 0.70


if __name__ == "__main__":
    success = asyncio.run(validate_comprehensive_fulltext())
    sys.exit(0 if success else 1)
