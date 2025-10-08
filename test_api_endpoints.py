"""
Quick test to validate API endpoints
"""
import asyncio
import httpx

async def test_endpoints():
    """Test various API endpoints to find working ones"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test health
        print("\n[TEST] Health Check")
        try:
            response = await client.get("http://localhost:8000/health/")
            print(f"  [OK] /health/ - {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] /health/ - {e}")
        
        # Test search endpoint
        print("\n[TEST] Search Endpoints")
        search_payload = {
            "query": "CRISPR",
            "workflow_type": "comprehensive",
            "max_results": 5
        }
        
        endpoints = [
            "/api/agents/search",
            "/api/v1/agents/search",
            "/api/workflows/execute",
            "/api/v1/workflows/execute",
            "/search"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.post(
                    f"http://localhost:8000{endpoint}",
                    json=search_payload
                )
                print(f"  [{response.status_code}] {endpoint}")
                if response.status_code == 200:
                    print(f"       SUCCESS! This endpoint works!")
                    data = response.json()
                    print(f"       Response keys: {list(data.keys())[:5]}")
            except Exception as e:
                print(f"  [ERROR] {endpoint} - {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
