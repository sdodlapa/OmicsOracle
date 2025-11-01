#!/usr/bin/env python3
"""
Quick test to verify search functionality is working.
"""

import json
import time

import requests
from colorama import Fore, Style


def test_search_endpoint():
    """Test the search endpoint directly."""

    backend_url = "http://localhost:8000"

    print(f"{Fore.BLUE}🔍 Testing OmicsOracle Search Endpoint{Style.RESET_ALL}")
    print(f"Backend URL: {backend_url}")

    # Test 1: Health check
    print(f"\n{Fore.YELLOW}1. Health Check{Style.RESET_ALL}")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check passed")
            print(f"   - Pipeline initialized: {health_data.get('pipeline_initialized', 'unknown')}")
            print(f"   - Config loaded: {health_data.get('config_loaded', 'unknown')}")
            print(f"   - Active queries: {health_data.get('active_queries', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

    # Test 2: Simple search query
    print(f"\n{Fore.YELLOW}2. Simple Search Query{Style.RESET_ALL}")

    search_queries = [
        "BRCA1 breast cancer",
        "dna methylation brain",
        "RNA-seq human",
    ]

    for query in search_queries:
        print(f"\n   🔍 Testing query: '{query}'")

        try:
            start_time = time.time()
            response = requests.post(
                f"{backend_url}/api/search",
                json={
                    "query": query,
                    "max_results": 5,
                    "output_format": "json",
                },
                timeout=60,
            )
            end_time = time.time()

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Search successful ({end_time - start_time:.2f}s)")
                print(f"   - Status: {data.get('status', 'unknown')}")
                print(f"   - Results: {data.get('total_count', 0)}")
                print(f"   - Query ID: {data.get('query_id', 'unknown')}")

                # Check response structure
                if "metadata" in data:
                    metadata = data["metadata"]
                    if metadata:
                        sample_result = metadata[0]
                        print(f"   - Sample result: {sample_result.get('title', 'No title')[:50]}...")
                else:
                    print("   ⚠️  No metadata in response")

            else:
                print(f"   ❌ Search failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   - Error: {error_data}")
                except:
                    print(f"   - Response: {response.text[:200]}...")

        except requests.exceptions.Timeout:
            print(f"   ❌ Search timed out (>60s)")
        except Exception as e:
            print(f"   ❌ Search error: {e}")

    # Test 3: Frontend compatibility test
    print(f"\n{Fore.YELLOW}3. Frontend Compatibility Test{Style.RESET_ALL}")

    try:
        response = requests.post(
            f"{backend_url}/api/search",
            json={"query": "BRCA1", "max_results": 3, "output_format": "json"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()

            # Check required fields for frontend
            required_fields = ["metadata", "total_count", "query_id", "status"]
            missing_fields = [field for field in required_fields if field not in data]

            if not missing_fields:
                print(f"   ✅ All required fields present")

                # Check metadata structure
                if data.get("metadata"):
                    metadata_item = data["metadata"][0]
                    metadata_fields = ["id", "title", "summary"]
                    present_fields = [field for field in metadata_fields if field in metadata_item]
                    print(f"   - Metadata fields present: {present_fields}")

                print(f"   - Response structure looks compatible with frontend")
            else:
                print(f"   ❌ Missing required fields: {missing_fields}")

        else:
            print(f"   ❌ Compatibility test failed: {response.status_code}")

    except Exception as e:
        print(f"   ❌ Compatibility test error: {e}")

    print(f"\n{Fore.GREEN}✅ Search endpoint test completed{Style.RESET_ALL}")
    return True


if __name__ == "__main__":
    test_search_endpoint()
