#!/usr/bin/env python3
"""
Quick automated test of search page functionality
Tests API endpoints and basic functionality
"""

import time

import requests

BASE_URL = "http://localhost:8000"


def print_status(test_name, passed, details=""):
    """Print test status with color"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")


def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = response.status_code == 200
        data = response.json() if passed else {}
        print_status("Server Health Check", passed, f"Status: {data.get('status', 'N/A')}")
        return passed
    except Exception as e:
        print_status("Server Health Check", False, str(e))
        return False


def test_search_endpoint():
    """Test search endpoint (no auth required)"""
    try:
        payload = {
            "search_terms": ["breast cancer"],
            "enable_semantic": False,
            "filters": {},
            "max_results": 3,
        }
        response = requests.post(f"{BASE_URL}/api/agents/search", json=payload, timeout=10)
        passed = response.status_code == 200
        data = response.json() if passed else {}

        if passed:
            result_count = data.get("total_found", 0)
            exec_time = data.get("execution_time_ms", 0)
            print_status(
                "Search Endpoint (Keyword)", passed, f"Found {result_count} results in {exec_time:.0f}ms"
            )
        else:
            print_status("Search Endpoint (Keyword)", False, f"Status: {response.status_code}")

        return passed
    except Exception as e:
        print_status("Search Endpoint (Keyword)", False, str(e))
        return False


def test_search_page():
    """Test search page loads"""
    try:
        response = requests.get(f"{BASE_URL}/search", timeout=5)
        passed = response.status_code == 200
        content_length = len(response.text) if passed else 0
        print_status("Search Page Load", passed, f"Page size: {content_length:,} bytes")
        return passed
    except Exception as e:
        print_status("Search Page Load", False, str(e))
        return False


def test_static_files():
    """Test static files are accessible"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        passed = response.status_code == 200
        data = response.json() if passed else {}
        print_status("Root Endpoint", passed, f"Version: {data.get('version', 'N/A')}")
        return passed
    except Exception as e:
        print_status("Root Endpoint", False, str(e))
        return False


def test_api_docs():
    """Test API documentation is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        passed = response.status_code == 200
        print_status("API Documentation", passed)
        return passed
    except Exception as e:
        print_status("API Documentation", False, str(e))
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OmicsOracle Quick Functionality Test")
    print("=" * 60 + "\n")

    start_time = time.time()

    tests = [
        ("Server Health", test_server_health),
        ("Root Endpoint", test_static_files),
        ("Search Page", test_search_page),
        ("Search API", test_search_endpoint),
        ("API Docs", test_api_docs),
    ]

    results = []
    for test_name, test_func in tests:
        results.append(test_func())
        print()

    # Summary
    elapsed = time.time() - start_time
    passed = sum(results)
    total = len(results)

    print("=" * 60)
    print(f"Test Summary: {passed}/{total} tests passed in {elapsed:.2f}s")
    print("=" * 60 + "\n")

    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED - System is working correctly!")
        print("\nNext Steps:")
        print("   1. Open http://localhost:8000/search in browser")
        print("   2. Test UI features using QUICK_TESTING_GUIDE.md")
        print("   3. Report any visual or functional issues")
    else:
        print(f"[WARNING] {total - passed} test(s) failed")
        print("\nCheck:")
        print("   1. Is the server running?")
        print("   2. Check terminal for error messages")
        print("   3. Try restarting the server")

    print("\n" + "=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
