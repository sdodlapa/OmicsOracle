#!/usr/bin/env python3
"""
Quick validation test for the OmicsOracle Futuristic Interface
Tests the core functionality including search and display.
"""

import asyncio
import sys

import aiohttp

BASE_URL = "http://localhost:8001"


async def test_interface():
    """Test the futuristic interface functionality"""

    print("🧪 OmicsOracle Futuristic Interface Validation")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        # Test 1: Check if the main page loads
        print("1️⃣ Testing main page...")
        try:
            async with session.get(BASE_URL) as response:
                if response.status == 200:
                    content = await response.text()
                    if "OmicsOracle" in content and (
                        "Next-Generation" in content or "Biomedical Research" in content
                    ):
                        print("   ✅ Main page loads correctly")
                    else:
                        print("   ❌ Main page content incomplete")
                        # Debug: print what we actually found
                        if "OmicsOracle" in content:
                            print("     Found OmicsOracle, but missing expected subtitle")
                        else:
                            print("     Missing OmicsOracle title entirely")
                else:
                    print(f"   ❌ Main page failed with status {response.status}")
        except Exception as e:
            print(f"   ❌ Main page error: {e}")
            return False

        # Test 2: Check CSS loads
        print("2️⃣ Testing CSS resources...")
        try:
            async with session.get(f"{BASE_URL}/static/css/main_clean.css") as response:
                if response.status == 200:
                    print("   ✅ CSS loads correctly")
                else:
                    print(f"   ❌ CSS failed with status {response.status}")
        except Exception as e:
            print(f"   ❌ CSS error: {e}")

        # Test 3: Check JavaScript loads
        print("3️⃣ Testing JavaScript resources...")
        try:
            async with session.get(f"{BASE_URL}/static/js/main_clean.js") as response:
                if response.status == 200:
                    content = await response.text()
                    if "/api/performance" in content:
                        print("   ⚠️ JavaScript still contains legacy API calls")
                    else:
                        print("   ✅ JavaScript loads correctly (no legacy API calls)")
                else:
                    print(f"   ❌ JavaScript failed with status {response.status}")
        except Exception as e:
            print(f"   ❌ JavaScript error: {e}")

        # Test 4: Test search API
        print("4️⃣ Testing search API...")
        try:
            search_data = {
                "query": "DNA methylation breast cancer",
                "max_results": 5,
            }
            async with session.post(
                f"{BASE_URL}/api/search",
                json=search_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("results") and len(result["results"]) > 0:
                        print(f"   ✅ Search API working - found {len(result['results'])} results")
                        print(f"   🔍 Query time: {result.get('search_time', 0):.2f}s")

                        # Check first result structure
                        first_result = result["results"][0]
                        if "geo_accession" in first_result and "title" in first_result:
                            print("   ✅ Result structure looks correct")
                        else:
                            print("   ⚠️ Result structure may be incomplete")
                    else:
                        print("   ⚠️ Search API returned no results")
                else:
                    print(f"   ❌ Search API failed with status {response.status}")
        except Exception as e:
            print(f"   ❌ Search API error: {e}")

        # Test 5: Check for 404s (legacy endpoints)
        print("5️⃣ Testing for legacy 404 errors...")
        try:
            async with session.get(f"{BASE_URL}/api/performance") as response:
                if response.status == 404:
                    print("   ✅ Legacy /api/performance correctly returns 404")
                else:
                    print(f"   ⚠️ Unexpected response from /api/performance: {response.status}")
        except Exception as e:
            print(f"   ❌ Legacy endpoint test error: {e}")

    print("\n🎉 Validation complete!")
    print("\n💡 To test the interface:")
    print(f"   1. Open: {BASE_URL}")
    print("   2. Try searching for: 'DNA methylation', 'breast cancer', 'cancer RNA-seq'")
    print("   3. Verify results display correctly with working NCBI links")
    print("   4. Check browser console for any JavaScript errors")

    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_interface())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
