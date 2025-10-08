"""
Debug test - raw HTTP client
"""
import asyncio

import httpx


async def test_raw_http():
    """Test with raw HTTP client to isolate the issue"""
    print("\n[TEST] Raw HTTP POST to /api/agents/search")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8000/api/agents/search", json={"search_terms": ["CRISPR"], "max_results": 3}
        )

        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response length: {len(response.text)} bytes")

        if response.status_code == 200:
            data = response.json()
            print("\n[OK] Success!")
            print(f"Total found: {data.get('total_found')}")
            print(f"Datasets: {len(data.get('datasets', []))}")
            if data.get("datasets"):
                print(f"First result: {data['datasets'][0]['title'][:100]}...")
        else:
            print(f"\n[ERROR] {response.status_code}")
            print(f"Body: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_raw_http())
