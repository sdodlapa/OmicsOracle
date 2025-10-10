"""
Quick Sci-Hub exploration - 10 papers across all mirrors
This is a sanity check before running the full 100-paper exploration.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the exploration code
import importlib.util

spec = importlib.util.spec_from_file_location(
    "exploration", Path(__file__).parent / "test_scihub_comprehensive_exploration.py"
)
exploration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exploration)

# Import dataset
spec2 = importlib.util.spec_from_file_location(
    "diverse_papers", Path(__file__).parent / "test_datasets" / "100_diverse_papers.py"
)
diverse_papers = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(diverse_papers)

# Select 10 diverse papers
QUICK_TEST_PAPERS = [
    # Old paywalled
    diverse_papers.COMPREHENSIVE_100_PAPERS[0],  # Science 2001
    diverse_papers.COMPREHENSIVE_100_PAPERS[1],  # Nature 2001
    # Recent paywalled
    diverse_papers.COMPREHENSIVE_100_PAPERS[10],  # Nature 2020
    diverse_papers.COMPREHENSIVE_100_PAPERS[14],  # Science 2021
    # Very new
    diverse_papers.COMPREHENSIVE_100_PAPERS[20],  # Science 2024
    # OA journals
    diverse_papers.COMPREHENSIVE_100_PAPERS[40],  # PLOS
    diverse_papers.COMPREHENSIVE_100_PAPERS[43],  # BMC
    # Preprints
    diverse_papers.COMPREHENSIVE_100_PAPERS[47],  # bioRxiv
    # Special cases
    diverse_papers.COMPREHENSIVE_100_PAPERS[-5],  # Watson & Crick DNA
    diverse_papers.COMPREHENSIVE_100_PAPERS[50],  # ACS
]


async def quick_test():
    """Quick test with 10 papers."""
    print("=" * 80)
    print("QUICK SCI-HUB EXPLORATION - 10 Papers")
    print("=" * 80)
    print(f"Testing {len(QUICK_TEST_PAPERS)} papers across {len(exploration.SCIHUB_MIRRORS)} mirrors")
    print(f"Estimated time: 2-3 minutes")
    print("=" * 80)
    print()

    async with exploration.SciHubExplorer() as explorer:
        # Test each mirror with quick papers
        for mirror in exploration.SCIHUB_MIRRORS:
            results = await explorer.test_all_papers_on_mirror(
                mirror, QUICK_TEST_PAPERS, rate_limit_delay=1.0  # Faster for quick test
            )
            explorer.results["mirrors"][mirror] = results

        # Compile statistics
        explorer.compile_statistics()

        # Save results
        explorer.save_results("scihub_quick_exploration_results.json")

        # Print summary
        explorer.print_summary()


if __name__ == "__main__":
    asyncio.run(quick_test())
