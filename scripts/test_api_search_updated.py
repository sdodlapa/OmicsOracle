#!/usr/bin/env python3
"""
Test updated search API endpoint (without SearchAgent).

Tests that /api/agents/search still works after removing SearchAgent wrapper.
"""

import json
import time
from datetime import datetime

import requests

# API endpoint
API_URL = "http://localhost:8000/api/agents/search"

# Test queries (subset of baseline)
TEST_QUERIES = [
    {
        "name": "GEO-only query",
        "search_terms": ["diabetes", "RNA-seq"],
        "filters": {},
        "max_results": 10,
        "expected_type": "geo",
    },
    {
        "name": "Hybrid query",
        "search_terms": ["cancer", "genomics", "BRCA1"],
        "filters": {},
        "max_results": 10,
        "expected_type": "hybrid",
    },
]


def test_search_api():
    """Test search API with different queries."""
    print("=" * 80)
    print("TESTING UPDATED SEARCH API (WITHOUT SEARCHAGENT)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Endpoint: {API_URL}")
    print()

    results = []

    for i, test_case in enumerate(TEST_QUERIES, 1):
        print("=" * 80)
        print(f"Test {i}/{len(TEST_QUERIES)}: {test_case['name']}")
        print("=" * 80)

        query_str = " ".join(test_case["search_terms"])
        print(f"Query: '{query_str}'")
        print(f"Expected type: {test_case['expected_type']}")
        print()

        # Build request payload
        payload = {
            "search_terms": test_case["search_terms"],
            "filters": test_case["filters"],
            "max_results": test_case["max_results"],
            "enable_semantic": False,
        }

        # Execute request
        try:
            start_time = time.time()
            response = requests.post(API_URL, json=payload, timeout=120)
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                print(f"❌ FAILED with status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                results.append(
                    {"query": query_str, "status": "failed", "error": f"HTTP {response.status_code}"}
                )
                continue

            data = response.json()

            # Validate response structure
            assert "success" in data, "Missing 'success' field"
            assert data["success"], "Search reported failure"
            assert "datasets" in data, "Missing 'datasets' field"
            assert "publications" in data, "Missing 'publications' field"
            assert "search_logs" in data, "Missing 'search_logs' field"
            assert "filters_applied" in data, "Missing 'filters_applied' field"

            geo_count = len(data["datasets"])
            pub_count = len(data.get("publications", []))

            print(f"✅ SUCCESS")
            print(f"  Latency: {latency_ms:.1f}ms")
            print(f"  GEO datasets: {geo_count}")
            print(f"  Publications: {pub_count}")
            print(f"  Search logs: {len(data['search_logs'])} entries")

            # Show first few log entries
            print("\n  Log entries:")
            for log in data["search_logs"][:5]:
                print(f"    - {log}")
            if len(data["search_logs"]) > 5:
                print(f"    ... and {len(data['search_logs']) - 5} more")

            # Show top 3 datasets
            if geo_count > 0:
                print("\n  Top 3 datasets:")
                for j, dataset in enumerate(data["datasets"][:3], 1):
                    geo_id = dataset.get("geo_id", "N/A")
                    title = dataset.get("title", "")[:80]
                    score = dataset.get("relevance_score", 0)
                    print(f"    {j}. [{geo_id}] {title}... (score: {score:.3f})")

            # Show top 3 publications
            if pub_count > 0:
                print("\n  Top 3 publications:")
                for j, pub in enumerate(data["publications"][:3], 1):
                    title = pub.get("title", "")[:80]
                    year = pub.get("publication_date", "")[:4] if pub.get("publication_date") else "N/A"
                    print(f"    {j}. [{year}] {title}...")

            results.append(
                {
                    "query": query_str,
                    "status": "success",
                    "latency_ms": latency_ms,
                    "geo_count": geo_count,
                    "pub_count": pub_count,
                }
            )

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - Request timed out after 120s")
            results.append({"query": query_str, "status": "failed", "error": "Timeout"})
        except Exception as e:
            print(f"❌ FAILED - {type(e).__name__}: {e}")
            results.append({"query": query_str, "status": "failed", "error": str(e)})

        print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")

    print(f"Total queries: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if successful > 0:
        avg_latency = sum(r["latency_ms"] for r in results if r["status"] == "success") / successful
        avg_geo = sum(r["geo_count"] for r in results if r["status"] == "success") / successful
        avg_pub = sum(r["pub_count"] for r in results if r["status"] == "success") / successful

        print(f"\nAverages (successful queries):")
        print(f"  Latency: {avg_latency:.1f}ms")
        print(f"  GEO datasets: {avg_geo:.1f}")
        print(f"  Publications: {avg_pub:.1f}")

    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {failed} test(s) failed")
        for r in results:
            if r["status"] == "failed":
                print(f"  - {r['query']}: {r.get('error', 'Unknown error')}")

    return failed == 0


if __name__ == "__main__":
    success = test_search_api()
    exit(0 if success else 1)
