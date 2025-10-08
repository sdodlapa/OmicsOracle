#!/usr/bin/env python3
"""
Test the specific query "dna methylation data for human brain cancer tissue"
and monitor the full response structure
"""

import asyncio
import json
import sys

import aiohttp

BASE_URL = "http://localhost:8001"


async def test_specific_query():
    """Test the specific query and analyze the full response"""

    print("🧪 Testing: 'dna methylation data for human brain cancer tissue'")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:
        # Test the specific query
        print("🔍 Sending search query...")
        try:
            search_data = {"query": "dna methylation data for human brain cancer tissue", "max_results": 10}

            async with session.post(
                f"{BASE_URL}/api/search", json=search_data, headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    print(f"✅ API Response received successfully")
                    print(f"📊 Query: {result.get('query', 'N/A')}")
                    print(f"📊 Total found: {result.get('total_found', 0)}")
                    print(f"⏱️  Search time: {result.get('search_time', 0):.2f}s")
                    print(f"🕒 Timestamp: {result.get('timestamp', 0)}")

                    results = result.get("results", [])
                    print(f"\n📋 Analyzing {len(results)} results:")
                    print("-" * 50)

                    for i, dataset in enumerate(results, 1):
                        print(f"\n🔬 Dataset {i}:")
                        print(f"   📁 GEO ID: {dataset.get('geo_id', 'N/A')}")
                        print(f"   📝 Title: {dataset.get('title', 'N/A')[:100]}...")
                        print(f"   🧬 Organism: {dataset.get('organism', 'N/A')}")
                        print(f"   📊 Samples: {dataset.get('sample_count', 'N/A')}")
                        print(f"   🖥️  Platform: {dataset.get('platform', 'N/A')}")
                        print(f"   📅 Date: {dataset.get('publication_date', 'N/A')}")
                        print(f"   📈 Relevance: {dataset.get('relevance_score', 'N/A')}")

                        # Check summary
                        summary = dataset.get("summary", "")
                        if summary:
                            print(f"   📄 Summary: {summary[:150]}...")
                        else:
                            print(f"   📄 Summary: Missing")

                        # Check AI insights
                        ai_insights = dataset.get("ai_insights", "")
                        if ai_insights:
                            print(f"   🤖 AI Insights: {ai_insights[:100]}...")
                        else:
                            print(f"   🤖 AI Insights: Missing")

                        # Check for any None/null values
                        none_fields = [k for k, v in dataset.items() if v is None]
                        if none_fields:
                            print(f"   ⚠️  Null fields: {none_fields}")

                    # Full JSON for debugging (first result only)
                    if results:
                        print(f"\n🔍 Full JSON structure (first result):")
                        print(json.dumps(results[0], indent=2, default=str))

                else:
                    print(f"❌ API failed with status {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")

        except Exception as e:
            print(f"❌ Query test failed: {e}")

    print(f"\n🌐 Now opening browser to test frontend rendering...")
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_specific_query())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
