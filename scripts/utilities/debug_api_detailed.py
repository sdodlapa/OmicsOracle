#!/usr/bin/env python3
"""
Debug the actual API response to see what data is really being returned
"""

import asyncio
import json

import aiohttp


async def debug_api_response():
    """Get the raw API response and analyze the actual data structure"""

    search_payload = {
        "query": "dna methylation data for bovine embryo development",
        "max_results": 3,  # Just test 3 for faster debugging
        "search_type": "comprehensive",
    }

    print("🔍 Debugging API Response...")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8001/api/search",
                json=search_payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    print(f"✅ API Status: {response.status}")
                    print(f"📊 Total Results: {result.get('total_found', 0)}")
                    print(f"⏱️ Search Time: {result.get('search_time', 0):.2f}s")
                    print("\n🔬 RAW RESULT ANALYSIS:")
                    print("=" * 50)

                    for i, dataset in enumerate(result.get("results", [])[:3]):
                        print(f"\n📋 DATASET {i+1}: {dataset.get('geo_id', 'Unknown')}")
                        print(f"   Title: '{dataset.get('title', 'N/A')}'")
                        print(f"   Summary Length: {len(dataset.get('summary', ''))}")
                        print(f"   Summary Preview: '{dataset.get('summary', '')[:100]}...'")
                        print(f"   AI Insights: '{dataset.get('ai_insights', 'N/A')}'")
                        print(f"   Organism: '{dataset.get('organism', 'N/A')}'")
                        print(f"   Date: '{dataset.get('publication_date', 'N/A')}'")
                        print(f"   Sample Count: {dataset.get('sample_count', 'N/A')}")
                        print(f"   Platform: {dataset.get('platform', 'N/A')}")
                        print(f"   Relevance: {dataset.get('relevance_score', 0):.2f}")

                    # Save full response for detailed analysis
                    with open("debug_api_response.json", "w") as f:
                        json.dump(result, f, indent=2, default=str)

                    print(f"\n💾 Full response saved to debug_api_response.json")

                else:
                    error_text = await response.text()
                    print(f"❌ API Error: {response.status}")
                    print(f"Error Details: {error_text}")

        except Exception as e:
            print(f"💥 Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(debug_api_response())
