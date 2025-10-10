"""
Comprehensive Sci-Hub testing with different access strategies.

This test will try:
1. Different identifier types (DOI vs PMID)
2. Different mirror selection strategies
3. Direct PDF extraction methods
4. Rate limiting variations
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.publications.clients.oa_sources.scihub_client import (
    SciHubClient,
    SciHubConfig,
)

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

# Test papers that failed in previous test (should be in Sci-Hub)
TEST_PAPERS = [
    # Failed OA papers (from BMC, eLife, Frontiers)
    {
        "title": "BMC Genomics 2024",
        "doi": "10.1186/s13059-024-03154-0",
        "pmid": None,
        "expected": "Should be OA but failed Unpaywall",
    },
    {
        "title": "BMC Biology 2024",
        "doi": "10.1186/s12915-024-01821-w",
        "pmid": None,
        "expected": "Should be OA but failed Unpaywall",
    },
    {
        "title": "eLife 2024",
        "doi": "10.7554/eLife.89410",
        "pmid": None,
        "expected": "Should be OA but failed Unpaywall",
    },
    {
        "title": "Frontiers Immunology 2024",
        "doi": "10.3389/fimmu.2024.1352169",
        "pmid": None,
        "expected": "Should be OA but failed Unpaywall",
    },
    # New paywalled papers
    {
        "title": "Science 2024",
        "doi": "10.1126/science.adi4415",
        "pmid": None,
        "expected": "Very recent, might not be in Sci-Hub yet",
    },
    {
        "title": "Springer 2024",
        "doi": "10.1007/s10719-024-10198-7",
        "pmid": None,
        "expected": "Recent, might not be in Sci-Hub yet",
    },
    # Known working papers (control)
    {
        "title": "Science 2001 (control)",
        "doi": "10.1126/science.1058040",
        "pmid": "11235003",
        "expected": "Should work (worked in previous test)",
    },
    {
        "title": "Cell 2013 (control)",
        "doi": "10.1016/j.cell.2013.05.039",
        "pmid": "23746838",
        "expected": "Older paper, likely in Sci-Hub",
    },
]


async def test_strategy_1_default():
    """Strategy 1: Default configuration."""
    print("\n" + "=" * 80)
    print("STRATEGY 1: Default Sci-Hub Configuration")
    print("=" * 80)
    print("Settings: Default mirrors, 2s delay, max 2 retries")
    print()
    
    config = SciHubConfig(
        rate_limit_delay=2.0,
        retry_count=2,
        timeout=15,
    )
    
    results = []
    async with SciHubClient(config) as client:
        for paper in TEST_PAPERS:
            doi = paper["doi"]
            pdf_url = await client.get_pdf_url(doi)
            
            if pdf_url:
                print(f"✅ {paper['title'][:40]:40} → FOUND")
                results.append((paper['title'], True, "doi", pdf_url[:60]))
            else:
                print(f"❌ {paper['title'][:40]:40} → NOT FOUND")
                results.append((paper['title'], False, "doi", None))
    
    found = sum(1 for _, success, _, _ in results if success)
    print(f"\nStrategy 1 Results: {found}/{len(TEST_PAPERS)} ({found/len(TEST_PAPERS)*100:.1f}%)")
    return results


async def test_strategy_2_pmid_fallback():
    """Strategy 2: Try PMID if DOI fails."""
    print("\n" + "=" * 80)
    print("STRATEGY 2: DOI First, PMID Fallback")
    print("=" * 80)
    print("Settings: Try DOI first, if fails try PMID")
    print()
    
    config = SciHubConfig(
        rate_limit_delay=2.0,
        retry_count=1,  # Less retries since we try both identifiers
        timeout=15,
    )
    
    results = []
    async with SciHubClient(config) as client:
        for paper in TEST_PAPERS:
            # Try DOI first
            pdf_url = await client.get_pdf_url(paper["doi"])
            method = "doi"
            
            # If DOI failed and PMID available, try PMID
            if not pdf_url and paper.get("pmid"):
                pdf_url = await client.get_pdf_url(paper["pmid"])
                method = "pmid"
            
            if pdf_url:
                print(f"✅ {paper['title'][:40]:40} → FOUND (via {method})")
                results.append((paper['title'], True, method, pdf_url[:60]))
            else:
                print(f"❌ {paper['title'][:40]:40} → NOT FOUND")
                results.append((paper['title'], False, method, None))
    
    found = sum(1 for _, success, _, _ in results if success)
    print(f"\nStrategy 2 Results: {found}/{len(TEST_PAPERS)} ({found/len(TEST_PAPERS)*100:.1f}%)")
    return results


async def test_strategy_3_aggressive():
    """Strategy 3: Aggressive - more retries, more mirrors."""
    print("\n" + "=" * 80)
    print("STRATEGY 3: Aggressive Configuration")
    print("=" * 80)
    print("Settings: 3 retries, all mirrors, 1s delay")
    print()
    
    config = SciHubConfig(
        rate_limit_delay=1.0,  # Faster (but riskier)
        retry_count=3,  # More retries
        timeout=20,  # Longer timeout
    )
    
    results = []
    async with SciHubClient(config) as client:
        for paper in TEST_PAPERS:
            # Try DOI
            pdf_url = await client.get_pdf_url(paper["doi"])
            method = "doi"
            
            # Try PMID if available
            if not pdf_url and paper.get("pmid"):
                pdf_url = await client.get_pdf_url(paper["pmid"])
                method = "pmid"
            
            if pdf_url:
                print(f"✅ {paper['title'][:40]:40} → FOUND (via {method})")
                results.append((paper['title'], True, method, pdf_url[:60]))
            else:
                print(f"❌ {paper['title'][:40]:40} → NOT FOUND")
                results.append((paper['title'], False, method, None))
    
    found = sum(1 for _, success, _, _ in results if success)
    print(f"\nStrategy 3 Results: {found}/{len(TEST_PAPERS)} ({found/len(TEST_PAPERS)*100:.1f}%)")
    return results


async def test_strategy_4_manual_mirrors():
    """Strategy 4: Try specific mirrors manually."""
    print("\n" + "=" * 80)
    print("STRATEGY 4: Test Each Mirror Individually")
    print("=" * 80)
    print("Settings: Try each mirror separately to find best one")
    print()
    
    # Test which mirrors work best
    mirrors = [
        "https://sci-hub.se",
        "https://sci-hub.st",
        "https://sci-hub.ru",
        "https://sci-hub.ren",
        "https://sci-hub.si",
    ]
    
    mirror_results = {mirror: 0 for mirror in mirrors}
    best_results = []
    
    for mirror in mirrors:
        print(f"\nTesting mirror: {mirror}")
        print("-" * 60)
        
        config = SciHubConfig(
            mirrors=[mirror],  # Only this mirror
            rate_limit_delay=1.5,
            retry_count=1,
            timeout=15,
        )
        
        async with SciHubClient(config) as client:
            for paper in TEST_PAPERS:
                pdf_url = await client.get_pdf_url(paper["doi"])
                
                if pdf_url:
                    mirror_results[mirror] += 1
                    print(f"  ✅ {paper['title'][:35]:35}")
                else:
                    print(f"  ❌ {paper['title'][:35]:35}")
    
    print(f"\n{'Mirror Performance':^60}")
    print("-" * 60)
    for mirror, count in sorted(mirror_results.items(), key=lambda x: x[1], reverse=True):
        print(f"{mirror:30} → {count}/{len(TEST_PAPERS)} ({count/len(TEST_PAPERS)*100:.1f}%)")
    
    best_mirror = max(mirror_results.items(), key=lambda x: x[1])
    print(f"\nBest mirror: {best_mirror[0]} with {best_mirror[1]} papers found")
    
    return mirror_results


async def compare_all_strategies():
    """Run all strategies and compare results."""
    print("=" * 80)
    print("SCI-HUB COMPREHENSIVE STRATEGY TESTING")
    print("=" * 80)
    print(f"Testing {len(TEST_PAPERS)} papers with different access strategies")
    print()
    
    # Run all strategies
    strategy1 = await test_strategy_1_default()
    await asyncio.sleep(3)  # Cooling off period
    
    strategy2 = await test_strategy_2_pmid_fallback()
    await asyncio.sleep(3)
    
    strategy3 = await test_strategy_3_aggressive()
    await asyncio.sleep(3)
    
    mirror_performance = await test_strategy_4_manual_mirrors()
    
    # Final comparison
    print("\n\n" + "=" * 80)
    print("FINAL COMPARISON")
    print("=" * 80)
    
    s1_found = sum(1 for _, success, _, _ in strategy1 if success)
    s2_found = sum(1 for _, success, _, _ in strategy2 if success)
    s3_found = sum(1 for _, success, _, _ in strategy3 if success)
    
    print(f"Strategy 1 (Default):           {s1_found}/{len(TEST_PAPERS)} ({s1_found/len(TEST_PAPERS)*100:.1f}%)")
    print(f"Strategy 2 (DOI+PMID fallback): {s2_found}/{len(TEST_PAPERS)} ({s2_found/len(TEST_PAPERS)*100:.1f}%)")
    print(f"Strategy 3 (Aggressive):        {s3_found}/{len(TEST_PAPERS)} ({s3_found/len(TEST_PAPERS)*100:.1f}%)")
    print()
    
    # Determine best strategy
    best_count = max(s1_found, s2_found, s3_found)
    if best_count == s1_found:
        best = "Strategy 1 (Default)"
    elif best_count == s2_found:
        best = "Strategy 2 (DOI+PMID fallback)"
    else:
        best = "Strategy 3 (Aggressive)"
    
    print(f"🏆 Best Strategy: {best}")
    print()
    
    # Check which papers were found by ANY strategy
    all_found = set()
    for title, success, _, _ in strategy1 + strategy2 + strategy3:
        if success:
            all_found.add(title)
    
    print(f"Papers found by at least one strategy: {len(all_found)}/{len(TEST_PAPERS)}")
    print()
    
    # Papers that NO strategy could find
    all_titles = {p['title'] for p in TEST_PAPERS}
    not_found = all_titles - all_found
    
    if not_found:
        print(f"❌ Papers NOT found by any strategy ({len(not_found)}):")
        for title in not_found:
            paper = next(p for p in TEST_PAPERS if p['title'] == title)
            print(f"   {title}")
            print(f"      DOI: {paper['doi']}")
            print(f"      Note: {paper['expected']}")
        print()
        print("Likely reasons:")
        print("  - Too new (2024) - not yet in Sci-Hub database")
        print("  - All Sci-Hub mirrors currently down for these DOIs")
        print("  - DOI format/metadata issues")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS FOR PIPELINE INTEGRATION")
    print("=" * 80)
    
    if s2_found > s1_found:
        print("✅ RECOMMENDATION: Use Strategy 2 (DOI+PMID fallback)")
        print("   - Try DOI first")
        print("   - If DOI fails and PMID available, try PMID")
        print(f"   - Improvement: +{s2_found - s1_found} papers")
    else:
        print("✅ RECOMMENDATION: Keep current default strategy")
        print("   - DOI-only approach is sufficient")
        print("   - PMID fallback doesn't provide significant benefit")
    
    print()
    print("Mirror selection:")
    best_mirror = max(mirror_performance.items(), key=lambda x: x[1])
    print(f"   Best performing mirror: {best_mirror[0]}")
    print(f"   Found: {best_mirror[1]}/{len(TEST_PAPERS)} papers")
    print()


if __name__ == "__main__":
    asyncio.run(compare_all_strategies())
