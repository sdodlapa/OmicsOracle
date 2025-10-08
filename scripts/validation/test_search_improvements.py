#!/usr/bin/env python3
"""
Test the improved search results display and AI analysis fixes
"""

import asyncio
import json

import aiohttp


async def test_improved_search_results():
    """Test the fixes for search query display and AI analysis issues"""

    print("🧪 Testing Improved Search Results Display & AI Analysis Fixes")
    print("=" * 70)

    test_queries = ["DNA methylation rumen development", "breast cancer microarray", "cardiac development"]

    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 50)

        search_payload = {"query": query, "max_results": 3, "search_type": "comprehensive"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "http://localhost:8001/api/search",
                    json=search_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        print(f"✅ Query: {result.get('query')}")
                        print(f"📊 Results: {result.get('total_found')} datasets")
                        print(f"⏱️ Time: {result.get('search_time', 0):.2f}s")
                        print()

                        # Analyze AI insights diversity
                        ai_insights = []
                        for i, dataset in enumerate(result.get("results", [])):
                            print(f"📋 Dataset {i+1}: {dataset.get('geo_id')}")
                            print(f"   Title: {dataset.get('title')[:80]}...")
                            print(f"   Organism: {dataset.get('organism')}")
                            print(f"   Samples: {dataset.get('sample_count')}")

                            ai_text = dataset.get("ai_insights", "")[:100]
                            ai_insights.append(ai_text)
                            print(f"   AI: {ai_text}...")
                            print()

                        # Check for AI duplication
                        unique_ai = set(ai_insights)
                        if len(unique_ai) == len(ai_insights):
                            print("✅ All AI insights are unique!")
                        else:
                            print(
                                f"❌ AI insights duplicated! {len(ai_insights)} total, {len(unique_ai)} unique"
                            )

                    else:
                        print(f"❌ API Error: {response.status}")

            except Exception as e:
                print(f"❌ Test failed: {e}")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_improved_search_results())
