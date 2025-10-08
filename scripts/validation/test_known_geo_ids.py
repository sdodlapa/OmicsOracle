#!/usr/bin/env python3
"""
Test with known good GEO IDs to verify the pipeline works with available data
"""

import asyncio
import json

import aiohttp


async def test_with_known_geo_ids():
    """Test with established GEO series that should have metadata"""

    # These are well-established GEO series that should have available metadata
    test_queries = [
        "GSE68849",  # Well-known breast cancer dataset
        "GSE32323",  # Established diabetes study
        "GSE15852",  # Older microarray study
        "breast cancer microarray",  # Should find older, established datasets
    ]

    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("=" * 50)

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

                        print(f"✅ API Status: {response.status}")
                        print(f"📊 Results found: {result.get('total_found', 0)}")
                        print(f"⏱️ Search time: {result.get('search_time', 0):.2f}s")

                        # Check first result quality
                        if result.get("results"):
                            first = result["results"][0]
                            print(f"\n📋 First Result Analysis:")
                            print(f"   GEO ID: {first.get('geo_id')}")
                            print(f"   Title: '{first.get('title')}'")
                            # Check for real metadata vs placeholder
                            title = first.get("title", "")
                            geo_id = first.get("geo_id", "")
                            has_real_title = title != f"Dataset {geo_id}"
                            has_real_ai = first.get("ai_insights") != "AI analysis pending for this dataset."

                            print(f"   Real metadata: {'Yes' if has_real_title else 'No'}")
                            print(f"   AI insights: {'Yes' if has_real_ai else 'No'}")
                            print(f"   Sample count: {first.get('sample_count', 'N/A')}")
                            print(f"   Date: {first.get('publication_date')}")

                    else:
                        error_text = await response.text()
                        print(f"❌ API Error: {response.status} - {error_text}")

            except Exception as e:
                print(f"💥 Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_with_known_geo_ids())
