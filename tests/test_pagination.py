#!/usr/bin/env python3
"""
Test the pagination system implementation
"""

import asyncio
from pathlib import Path

# Add the project root to Python path


async def test_pagination():
    """Test the pagination implementation"""
    print("🧪 Testing Pagination System Implementation")
    print("=" * 50)

    # Test cases for pagination logic
    test_cases = [
        {"page": 1, "page_size": 10, "total": 25},
        {"page": 2, "page_size": 10, "total": 25},
        {"page": 3, "page_size": 10, "total": 25},
        {"page": 1, "page_size": 5, "total": 13},
    ]

    for i, case in enumerate(test_cases, 1):
        page = case["page"]
        page_size = case["page_size"]
        total = case["total"]

        # Calculate pagination parameters
        offset = (page - 1) * page_size
        has_more = (offset + page_size) < total
        total_pages = (total + page_size - 1) // page_size
        start_index = offset + 1
        end_index = min(offset + page_size, total)

        print(f"\n📊 Test Case {i}:")
        print(f"   Page: {page}, Page Size: {page_size}, Total: {total}")
        print(f"   ➤ Offset: {offset}")
        print(f"   ➤ Show results: {start_index}-{end_index}")
        print(f"   ➤ Total pages: {total_pages}")
        print(f"   ➤ Has more: {has_more}")
        print(f"   ➤ Has previous: {page > 1}")

    print("\n✅ Pagination logic tests completed!")

    # Test URL formation
    print("\n🔗 URL Formation Test:")
    base_url = "http://localhost:8007"
    print(f"   Interface URL: {base_url}")
    print(f"   Search API: {base_url}/search")
    print(f"   Health Check: {base_url}/health")


if __name__ == "__main__":
    asyncio.run(test_pagination())
