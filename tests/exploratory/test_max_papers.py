#!/usr/bin/env python3
"""Test AI Analysis with configurable max_papers_per_dataset parameter."""

import asyncio

import httpx


async def test_analysis_with_max_papers(max_papers: int = 5):
    """Test AI analysis with custom max_papers_per_dataset."""

    base_url = "http://localhost:8000"

    # Build minimal dataset structure for analysis request
    # This will be enriched from database automatically
    dataset = {
        "geo_id": "GSE570",
        "title": "Reactivation of HIV from latency",
        "organism": "Homo sapiens",
        "sample_count": 8,
        "summary": "HIV latency study",
        "relevance_score": 1.0,
        "match_reasons": ["Test dataset for max_papers parameter"],
        "pubmed_ids": ["16537587", "16526095", "15780141", "16988414", "17143293"],
        "fulltext": [],  # Will be enriched from database
    }

    print(f"\nRunning AI Analysis with max_papers_per_dataset={max_papers}...")

    request_body = {
        "datasets": [dataset],
        "query": "HIV latency and reactivation",
        "max_datasets": 1,
        "max_papers_per_dataset": max_papers,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{base_url}/api/agents/analyze", json=request_body
        )

        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return None

        result = response.json()

        print(f"✅ Analysis completed!")
        print(f"   Execution time: {result['execution_time_ms']:.0f} ms")

        # Count papers analyzed from the analysis text
        analysis_text = result.get("analysis", "")

        # Save to file for debugging
        with open(f"/tmp/analysis_max{max_papers}.txt", "w") as f:
            f.write(f"Max papers: {max_papers}\n")
            f.write("=" * 80 + "\n")
            f.write(analysis_text)

        print(f"   📝 Saved full analysis to /tmp/analysis_max{max_papers}.txt")

        # Extract unique PMIDs mentioned in the analysis
        import re

        pmids = set(re.findall(r"PMID[:\s]+(\d+)", analysis_text))
        papers_analyzed = len(pmids)

        if papers_analyzed > 0:
            print(
                f"   📄 Analyzed {papers_analyzed} papers (PMIDs: {', '.join(sorted(pmids))})"
            )
        else:
            print(f"   ⚠️  No PMIDs found in analysis")

        return papers_analyzed


if __name__ == "__main__":
    print("=" * 80)
    print("Testing Configurable max_papers_per_dataset Parameter")
    print("=" * 80)

    # Test with 2 papers (default)
    print("\n" + "=" * 80)
    print("TEST 1: Default (max_papers_per_dataset=2)")
    print("=" * 80)
    result1 = asyncio.run(test_analysis_with_max_papers(2))

    # Test with 5 papers
    print("\n" + "=" * 80)
    print("TEST 2: Increased (max_papers_per_dataset=5)")
    print("=" * 80)
    result2 = asyncio.run(test_analysis_with_max_papers(5))

    # Test with 10 papers (max allowed)
    print("\n" + "=" * 80)
    print("TEST 3: Maximum (max_papers_per_dataset=10)")
    print("=" * 80)
    result3 = asyncio.run(test_analysis_with_max_papers(10))

    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"   Test 1 (max=2):  {result1} papers analyzed")
    print(f"   Test 2 (max=5):  {result2} papers analyzed")
    print(f"   Test 3 (max=10): {result3} papers analyzed")
    print("\n✅ All tests completed!")
    print("=" * 80)
