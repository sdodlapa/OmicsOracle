#!/usr/bin/env python3
"""
Test HTTP/2 Protocol Error Fix
===============================

Tests the fix for net::ERR_HTTP2_PROTOCOL_ERROR in AI analysis.

**Problem:** Frontend sends full dataset (with all parsed text) to /analyze endpoint
**Solution:** Strip full-text content before sending, backend loads from disk

Date: October 13, 2025
Author: OmicsOracle Team
"""

import asyncio
import json
import sys
from pathlib import Path

import aiohttp

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class HTTP2ErrorTester:
    """Test the HTTP/2 error fix."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health(self) -> bool:
        """Test if server is running."""
        try:
            async with self.session.get(f"{self.base_url}/health") as resp:
                return resp.status == 200
        except Exception as e:
            print(f"❌ Server not running: {e}")
            return False

    async def test_search(self, query: str = "breast cancer gene expression") -> dict:
        """Search for datasets."""
        print(f"\n1️⃣ Testing /search with query: '{query}'")

        async with self.session.post(
            f"{self.base_url}/api/agents/search",
            json={
                "search_terms": query.split(),  # Split into list of terms
                "max_results": 2,
                "enable_semantic": False,
            },
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Search failed: {resp.status}\n{error_text}")

            data = await resp.json()
            print(f"   ✓ Found {len(data.get('datasets', []))} datasets")
            return data

    async def test_enrich_fulltext(self, datasets: list) -> dict:
        """Enrich datasets with full-text (metadata only)."""
        print(f"\n2️⃣ Testing /enrich-fulltext with include_full_content=False")

        geo_ids = [ds["geo_id"] for ds in datasets]

        async with self.session.post(
            f"{self.base_url}/api/agents/enrich-fulltext?include_full_content=false",
            json={"geo_ids": geo_ids},
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Enrichment failed: {resp.status}")

            data = await resp.json()
            enriched_datasets = data.get("datasets", [])

            # Check response size
            response_text = await resp.text()
            response_size = len(response_text)
            print(f"   ✓ Response size: {response_size:,} bytes ({response_size/1024:.1f} KB)")

            # Verify no full-text content in response
            has_full_content = False
            for ds in enriched_datasets:
                if ds.get("fulltext"):
                    for ft in ds["fulltext"]:
                        if ft.get("abstract") or ft.get("methods") or ft.get("results"):
                            has_full_content = True
                            print(f"   ⚠️ WARNING: Full-text content found in response!")
                            break

            if not has_full_content:
                print(f"   ✓ No full-text content in response (only metadata)")

            return data

    async def test_analyze_with_stripped_content(self, datasets: list, query: str) -> dict:
        """Test AI analysis with stripped full-text content."""
        print(f"\n3️⃣ Testing /analyze with STRIPPED full-text content")

        # Strip full-text content (simulate frontend fix)
        stripped_datasets = []
        for ds in datasets:
            clean_ds = {**ds}
            if clean_ds.get("fulltext"):
                clean_ds["fulltext"] = [
                    {
                        "pmid": ft.get("pmid"),
                        "title": ft.get("title"),
                        "url": ft.get("url"),
                        "pdf_path": ft.get("pdf_path"),
                        # Only metadata, no content
                        "has_abstract": ft.get("has_abstract", False),
                        "has_methods": ft.get("has_methods", False),
                        "has_results": ft.get("has_results", False),
                        "has_discussion": ft.get("has_discussion", False),
                        "content_length": ft.get("content_length", 0),
                    }
                    for ft in clean_ds["fulltext"]
                ]
            stripped_datasets.append(clean_ds)

        # Check stripped size
        stripped_size = len(json.dumps(stripped_datasets))
        print(f"   Request size: {stripped_size:,} bytes ({stripped_size/1024:.1f} KB)")

        async with self.session.post(
            f"{self.base_url}/api/agents/analyze",
            json={"datasets": stripped_datasets, "query": query, "max_datasets": 2},
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Analysis failed: {resp.status}\n{error_text}")

            # Check response size
            response_text = await resp.text()
            response_size = len(response_text)
            print(f"   ✓ Response size: {response_size:,} bytes ({response_size/1024:.1f} KB)")

            # Check if response is under Chrome 16MB limit
            if response_size < 16 * 1024 * 1024:
                print(f"   ✓ Response under Chrome 16MB limit")
            else:
                print(f"   ❌ Response exceeds Chrome 16MB limit!")

            data = await resp.json()

            # Verify AI analysis is meaningful (not just "N/A")
            analysis_text = data.get("analysis", "")
            if "N/A" in analysis_text or "not available" in analysis_text.lower():
                print(f"   ⚠️ WARNING: AI analysis contains 'N/A' - may not have loaded content from disk")
            else:
                print(f"   ✓ AI analysis looks good (no 'N/A' placeholders)")

            return data

    async def test_analyze_with_full_content(self, datasets: list, query: str) -> dict:
        """Test AI analysis with FULL content (should fail or be huge)."""
        print(f"\n4️⃣ Testing /analyze with FULL content (expected to be large)")

        # Don't strip - send full datasets as-is
        request_size = len(json.dumps(datasets))
        print(f"   Request size: {request_size:,} bytes ({request_size/1024:.1f} KB)")

        try:
            async with self.session.post(
                f"{self.base_url}/api/agents/analyze",
                json={"datasets": datasets, "query": query, "max_datasets": 2},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                response_text = await resp.text()
                response_size = len(response_text)
                print(f"   Response size: {response_size:,} bytes ({response_size/1024:.1f} KB)")

                if response_size > 16 * 1024 * 1024:
                    print(f"   ⚠️ Response exceeds 16MB - would cause HTTP/2 error in Chrome!")
                    return None
                else:
                    print(f"   ✓ Response under 16MB limit")
                    return await resp.json()

        except Exception as e:
            print(f"   ❌ Request failed (expected): {e}")
            return None

    async def run_tests(self):
        """Run all tests."""
        print("=" * 80)
        print("HTTP/2 Protocol Error Fix - Test Suite")
        print("=" * 80)

        # Test 1: Health check
        print("\n0️⃣ Checking server health...")
        if not await self.test_health():
            print("\n❌ Server not running. Start with: make start-api")
            return False
        print("   ✓ Server is running")

        # Test 2: Search
        query = "breast cancer gene expression"
        search_results = await self.test_search(query)
        datasets = search_results.get("datasets", [])

        if not datasets:
            print("\n❌ No datasets found. Try a different query.")
            return False

        # Test 3: Enrich with metadata only
        enrich_results = await self.test_enrich_fulltext(datasets)
        enriched_datasets = enrich_results.get("datasets", [])

        # Test 4: Analyze with stripped content (FIXED)
        try:
            await self.test_analyze_with_stripped_content(enriched_datasets, query)
            print("\n✅ TEST PASSED: AI analysis works with stripped content!")
        except Exception as e:
            print(f"\n❌ TEST FAILED: AI analysis failed with stripped content: {e}")
            return False

        # Test 5: Analyze with full content (comparison)
        # Skip this if no full content was returned
        has_full_content = any(
            ds.get("fulltext", [])
            and any(ft.get("abstract") or ft.get("methods") for ft in ds.get("fulltext", []))
            for ds in enriched_datasets
        )

        if has_full_content:
            await self.test_analyze_with_full_content(enriched_datasets, query)
        else:
            print(f"\n4️⃣ Skipping full-content test (no full-text in enrichment response)")

        print("\n" + "=" * 80)
        print("✅ All tests completed successfully!")
        print("=" * 80)
        return True


async def main():
    """Run tests."""
    async with HTTP2ErrorTester() as tester:
        success = await tester.run_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
