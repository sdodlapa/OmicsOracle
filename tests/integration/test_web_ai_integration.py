#!/usr/bin/env python3
"""
Test script for Web AI Integration

This tests the web API with AI summarization features.
"""

import asyncio
import sys
from pathlib import Path

import aiohttp

# Add the src directory to the Python path


async def test_web_ai_integration():
    """Test the web API with AI features."""
    print("🌐 Testing Web AI Integration")
    print("=" * 50)

    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Basic search endpoint
            print("🔍 Testing basic search endpoint...")
            search_data = {
                "query": "diabetes pancreatic beta cells",
                "max_results": 3,
                "include_sra": False,
            }

            async with session.post(f"{base_url}/api/search", json=search_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ Basic search successful: {len(result.get('geo_ids', []))} results")
                else:
                    print(f"❌ Basic search failed: {resp.status}")
                    return False

            # Test 2: AI summarization endpoint
            print("\n🤖 Testing AI summarization endpoint...")
            ai_data = {
                "query": "diabetes pancreatic beta cells",
                "max_results": 3,
                "include_batch_summary": True,
                "include_individual_summaries": True,
            }

            async with session.post(f"{base_url}/api/ai/summarize", json=ai_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print("✅ AI summarization successful!")

                    # Check if we have AI summaries
                    if "ai_summaries" in result:
                        summaries = result["ai_summaries"]
                        print(f"   📊 Batch summary: {'✓' if 'batch_summary' in summaries else '✗'}")
                        print(
                            f"   📚 Individual summaries: {'✓' if 'individual_summaries' in summaries else '✗'}"
                        )

                        # Show a bit of the batch summary
                        if "batch_summary" in summaries:
                            batch = summaries["batch_summary"]
                            print(f"   🔬 Overview: {batch.get('overview', 'N/A')[:100]}...")
                    else:
                        print("   ⚠️  No AI summaries in response")
                else:
                    print(f"❌ AI summarization failed: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Error: {error_text}")
                    return False

            # Test 3: Check if the web interface is serving the updated HTML
            print("\n🖥️  Testing web interface...")
            async with session.get(f"{base_url}/") as resp:
                if resp.status == 200:
                    html_content = await resp.text()
                    if "AI Summarization" in html_content:
                        print("✅ Web interface includes AI features")
                    else:
                        print("⚠️  Web interface may not have AI features enabled")
                else:
                    print(f"❌ Web interface failed: {resp.status}")
                    return False

            return True

        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """Run the web AI integration test."""
    print("🚀 Starting Web AI Integration Test")
    print("Make sure the web server is running on localhost:8000")
    print()

    success = await test_web_ai_integration()

    if success:
        print("\n🎉 Web AI Integration Test Completed Successfully!")
        print("\n💡 Next steps:")
        print("   1. Open http://localhost:8000 in your browser")
        print("   2. Try a search with 'AI Summarization' enabled")
        print("   3. Check that AI summaries appear in the results")
    else:
        print("\n❌ Test failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
