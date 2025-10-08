#!/usr/bin/env python3
"""
Test the improved honest messaging system
"""

import asyncio
import json

import aiohttp


async def test_honest_messaging():
    """Test the new honest messaging instead of fallback text"""

    print("🧪 Testing Honest Messaging System")
    print("=" * 50)

    search_payload = {"query": "breast cancer methylation", "max_results": 3, "search_type": "comprehensive"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8001/api/search",
                json=search_payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result_data = await response.json()

                    print(f"📊 Query: {result_data.get('query')}")
                    print(f"📈 Total Results: {result_data.get('total_found')}")
                    print(f"⏱️ Search Time: {result_data.get('search_time', 0):.2f}s")
                    print()

                    # Analyze the honesty of the messaging
                    for i, result in enumerate(result_data.get("results", [])):
                        print(f"📋 Dataset {i+1}: {result.get('geo_id')}")
                        print(f"   Title: {result.get('title')}")
                        print(f"   Summary: {result.get('summary')[:100]}...")
                        print(f"   AI Insights: {result.get('ai_insights')[:80]}...")
                        print(f"   Organism: {result.get('organism')}")
                        print(f"   Sample Count: {result.get('sample_count')}")
                        print(f"   Date: {result.get('publication_date')}")
                        print()

                        # Check for honest vs misleading text
                        if "not available" in str(result.get("title", "")).lower():
                            print("   ✅ Honest title messaging")
                        elif result.get("title", "").startswith("Dataset GSE"):
                            print("   ❌ Still using misleading title")

                        if "not available" in str(result.get("summary", "")).lower():
                            print("   ✅ Honest summary messaging")
                        elif "biomedical dataset related to" in str(result.get("summary", "")).lower():
                            print("   ❌ Still using misleading summary")

                        if "unavailable" in str(result.get("ai_insights", "")).lower():
                            print("   ✅ Honest AI insights messaging")
                        elif "pending" in str(result.get("ai_insights", "")).lower():
                            print("   ❌ Still using misleading AI messaging")
                        print("-" * 40)
                else:
                    print(f"❌ API Error: {response.status}")

        except Exception as e:
            print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_honest_messaging())
