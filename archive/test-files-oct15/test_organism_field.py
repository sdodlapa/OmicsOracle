#!/usr/bin/env python3
"""
Test organism field population across diverse GEO datasets.

This script tests Phase 2 improvements:
1. Organism trace logging
2. E-Summary API fallback
3. 100% organism field population
"""

import asyncio
import json
from typing import Dict, List

import aiohttp


async def test_dataset(session: aiohttp.ClientSession, geo_id: str) -> Dict:
    """Test a single dataset and return organism info."""
    url = "http://localhost:8000/api/agents/search"
    payload = {"search_terms": [geo_id], "max_results": 1}

    try:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                return {
                    "geo_id": geo_id,
                    "status": "error",
                    "organism": None,
                    "error": f"HTTP {response.status}",
                }

            data = await response.json()

            if not data.get("datasets"):
                return {
                    "geo_id": geo_id,
                    "status": "not_found",
                    "organism": None,
                    "error": "No datasets returned",
                }

            dataset = data["datasets"][0]
            organism = dataset.get("organism", "")

            return {
                "geo_id": geo_id,
                "status": "success" if organism else "empty",
                "organism": organism,
                "title": dataset.get("title", "")[:80],
                "error": None if organism else "Organism field is empty",
            }

    except Exception as e:
        return {"geo_id": geo_id, "status": "error", "organism": None, "error": str(e)}


async def main():
    """Test organism field across diverse datasets."""

    # Diverse test datasets (different organisms, years, data types)
    # Using verified GSE Series IDs (not platforms/samples)
    test_datasets = [
        "GSE189158",  # Homo sapiens - NOMe-HiC (2022)
        "GSE100000",  # Mus musculus - transdifferentiation (2017)
        "GSE68849",  # Homo sapiens - RNA-seq, influenza (2015)
        "GSE30000",  # Bacillus subtilis - daptomycin resistance (2011)
        "GSE16449",  # Drosophila melanogaster - ChIP-seq (2009)
        "GSE10246",  # Saccharomyces cerevisiae - verified series (2008)
        "GSE8671",  # Mus musculus - microarray (2007)
        "GSE2000",  # Arabidopsis thaliana - development (2005)
        "GSE1133",  # Homo sapiens - tissue expression (2004)
        "GSE500",  # Homo sapiens - CD34+ cells (2003)
        "GSE361",  # Rattus norvegicus - early GEO (2002)
        "GSE29",  # Saccharomyces cerevisiae - very early (2001)
    ]

    print("=" * 80)
    print("ORGANISM FIELD POPULATION TEST - Phase 2")
    print("=" * 80)
    print(f"\nTesting {len(test_datasets)} diverse GEO datasets...")
    print("\nDatasets:")
    for i, geo_id in enumerate(test_datasets, 1):
        print(f"  {i:2d}. {geo_id}")
    print("\n" + "-" * 80)

    # Test all datasets concurrently
    async with aiohttp.ClientSession() as session:
        tasks = [test_dataset(session, geo_id) for geo_id in test_datasets]
        results = await asyncio.gather(*tasks)

    # Analyze results
    success_count = sum(1 for r in results if r["status"] == "success")
    empty_count = sum(1 for r in results if r["status"] == "empty")
    error_count = sum(1 for r in results if r["status"] == "error")
    not_found_count = sum(1 for r in results if r["status"] == "not_found")

    # Print results
    print("\nRESULTS:")
    print("-" * 80)

    for result in results:
        status_emoji = {"success": "✅", "empty": "⚠️ ", "error": "❌", "not_found": "🔍"}[
            result["status"]
        ]

        organism_display = result["organism"] or "(empty)"
        print(f"{status_emoji} {result['geo_id']}: {organism_display}")

        if result["status"] != "success":
            print(f"   Error: {result['error']}")
        elif result.get("title"):
            print(f"   Title: {result['title']}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"  Total tested:     {len(test_datasets)}")
    print(
        f"  ✅ Success:       {success_count} ({success_count/len(test_datasets)*100:.1f}%)"
    )
    print(
        f"  ⚠️  Empty:        {empty_count} ({empty_count/len(test_datasets)*100:.1f}%)"
    )
    print(
        f"  ❌ Error:         {error_count} ({error_count/len(test_datasets)*100:.1f}%)"
    )
    print(
        f"  🔍 Not found:     {not_found_count} ({not_found_count/len(test_datasets)*100:.1f}%)"
    )
    print("=" * 80)

    # Phase 2 success criteria
    success_rate = success_count / len(test_datasets) * 100

    if success_rate == 100:
        print("\n🎉 PHASE 2 SUCCESS: 100% organism field population!")
    elif success_rate >= 90:
        print(f"\n✅ PHASE 2 GOOD: {success_rate:.1f}% organism field population")
    elif success_rate >= 75:
        print(
            f"\n⚠️  PHASE 2 NEEDS IMPROVEMENT: {success_rate:.1f}% organism field population"
        )
    else:
        print(f"\n❌ PHASE 2 FAILED: Only {success_rate:.1f}% organism field population")

    # Save detailed results
    with open("data/test_results/organism_field_test.json", "w") as f:
        json.dump(
            {
                "timestamp": "2025-10-15",
                "phase": "Phase 2: Organism Trace Logging + E-Summary",
                "test_count": len(test_datasets),
                "success_count": success_count,
                "success_rate": success_rate,
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\nDetailed results saved to: data/test_results/organism_field_test.json")


if __name__ == "__main__":
    asyncio.run(main())
