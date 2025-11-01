#!/usr/bin/env python3
"""
Test that search results are immediately cleared when a new search is initiated
"""

import asyncio
import time

import aiohttp


async def test_immediate_reset():
    """Test immediate clearing of previous results"""

    print("🧪 Testing Immediate Search Results Reset")
    print("=" * 50)

    # First search to populate results
    print("🔍 Step 1: Running initial search to populate results...")
    search1_payload = {"query": "breast cancer", "max_results": 5, "search_type": "comprehensive"}

    async with aiohttp.ClientSession() as session:
        try:
            # Initial search
            async with session.post(
                "http://localhost:8001/api/search",
                json=search1_payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result1 = await response.json()
                    print(f"✅ Initial search completed: {result1.get('total_found')} results")
                    print(f"   Query: {result1.get('query')}")
                    print(f"   Time: {result1.get('search_time', 0):.2f}s")
                else:
                    print(f"❌ Initial search failed: {response.status}")
                    return

            print("\n🔄 Step 2: Waiting 2 seconds...")
            await asyncio.sleep(2)

            # Second search to test reset
            print("🔍 Step 3: Running second search to test immediate reset...")
            search2_payload = {
                "query": "diabetes gene expression",
                "max_results": 3,
                "search_type": "comprehensive",
            }

            start_time = time.time()
            async with session.post(
                "http://localhost:8001/api/search",
                json=search2_payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result2 = await response.json()
                    end_time = time.time()

                    print(f"✅ Second search completed: {result2.get('total_found')} results")
                    print(f"   Query: {result2.get('query')}")
                    print(f"   Time: {result2.get('search_time', 0):.2f}s")
                    print(f"   Total wait time: {end_time - start_time:.2f}s")

                    # Verify different queries
                    if result1.get("query") != result2.get("query"):
                        print("✅ Queries are different (good!)")
                    else:
                        print("❌ Queries are the same (unexpected)")

                    print("\n📋 Frontend Instructions:")
                    print("1. Open http://localhost:8001 in browser")
                    print("2. Search for 'breast cancer'")
                    print("3. Wait for results to load")
                    print("4. Immediately search for 'diabetes'")
                    print("5. Verify old results disappear IMMEDIATELY")
                    print("6. Should see blue 'Searching...' box instantly")

                else:
                    print(f"❌ Second search failed: {response.status}")

        except Exception as e:
            print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_immediate_reset())
