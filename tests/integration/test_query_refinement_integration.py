#!/usr/bin/env python3
"""
Test script for query refinement functionality
"""
import json
import sys

import requests

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"


def test_backend_health():
    """Test if backend is healthy"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        return response.status_code == 200
    except:
        return False


def test_query_refinement_endpoints():
    """Test query refinement endpoints"""
    print("Testing query refinement endpoints...")

    # Test query that should return no results
    test_query = "nonexistent gene xyz123"

    # Test suggestions endpoint
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/refinement/suggestions",
            json={"query": test_query},
        )
        print(f"✅ Suggestions endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Suggestions: {len(data.get('suggestions', []))}")
            print(f"   - Analysis: {data.get('analysis', {})}")
    except Exception as e:
        print(f"❌ Suggestions endpoint failed: {e}")

    # Test similar queries endpoint
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/refinement/similar-queries",
            json={"query": test_query},
        )
        print(f"✅ Similar queries endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Similar queries: {len(data.get('similar_queries', []))}")
    except Exception as e:
        print(f"❌ Similar queries endpoint failed: {e}")

    # Test enhanced search endpoint
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/refinement/search/enhanced",
            json={
                "query": "BRCA1",
                "use_synonyms": True,
                "expand_abbreviations": True,
                "relaxed_matching": False,
            },
        )
        print(f"✅ Enhanced search endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Results: {data.get('total_count', 0)}")
    except Exception as e:
        print(f"❌ Enhanced search endpoint failed: {e}")


def test_frontend_availability():
    """Test if frontend is available"""
    try:
        response = requests.get(FRONTEND_URL)
        return response.status_code == 200
    except:
        return False


def main():
    print("🧬 OmicsOracle Query Refinement Test Suite")
    print("=" * 50)

    # Test backend health
    if test_backend_health():
        print("✅ Backend is healthy")
    else:
        print("❌ Backend is not responding")
        sys.exit(1)

    # Test frontend availability
    if test_frontend_availability():
        print("✅ Frontend is available")
    else:
        print("❌ Frontend is not responding")

    print("\n" + "=" * 50)

    # Test query refinement endpoints
    test_query_refinement_endpoints()

    print("\n" + "=" * 50)
    print("🎉 Test completed! Check the results above.")
    print("\n📝 Manual testing steps:")
    print("1. Open http://localhost:5173 in your browser")
    print("2. Try searching for a query that returns no results (e.g., 'nonexistent gene xyz123')")
    print("3. Verify that query refinement suggestions appear")
    print("4. Test clicking on suggestions to refine the search")
    print("5. Verify feedback functionality works")


if __name__ == "__main__":
    main()
