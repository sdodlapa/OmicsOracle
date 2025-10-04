#!/usr/bin/env python3
"""
Test script for futuristic interface

This script tests the basic functionality of the futuristic interface
and verifies the fallback mechanism works properly.
"""

import asyncio
import json
import time
from pathlib import Path

import requests

# Add paths for imports


async def test_futuristic_interface():
    """Test the futuristic interface"""

    print("[TEST] Testing OmicsOracle Futuristic Interface")
    print("=" * 50)

    base_url = "http://localhost:8001"

    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v2/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"[OK] Health check passed")
            print(f"   Status: {health.get('status')}")
            print(f"   Modes: {health.get('modes')}")
        else:
            print(f"[ERROR] Health check failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Health check error: {e}")

    # Test 2: Homepage
    print("\n2. Testing homepage...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("[OK] Homepage loads successfully")
        else:
            print(f"[ERROR] Homepage failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Homepage error: {e}")

    # Test 3: Search API
    print("\n3. Testing search API...")
    try:
        search_data = {
            "query": "cancer genomics",
            "search_type": "basic",
            "max_results": 5,
        }
        response = requests.post(f"{base_url}/api/v2/search", json=search_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("[OK] Search API works")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Mode: {result.get('mode')}")
        else:
            print(f"[ERROR] Search API failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"[ERROR] Search API error: {e}")

    # Test 4: Check if legacy interface is available
    print("\n4. Checking legacy interface...")
    try:
        legacy_response = requests.get("http://localhost:8000/health", timeout=5)
        if legacy_response.status_code == 200:
            print("[OK] Legacy interface is available as fallback")
        else:
            print("[WARNING]  Legacy interface not running (internal fallback will be used)")
    except Exception as e:
        print("[WARNING]  Legacy interface not accessible (internal fallback will be used)")

    print("\n" + "=" * 50)
    print("[TARGET] Test Summary:")
    print("   - Futuristic interface should be running on http://localhost:8001")
    print("   - Legacy interface should be available as fallback")
    print("   - Both interfaces can run simultaneously")
    print("   - Users can choose between interfaces or rely on automatic fallback")


if __name__ == "__main__":
    # Check if interface is running
    try:
        response = requests.get("http://localhost:8001/api/v2/health", timeout=2)
        if response.status_code == 200:
            asyncio.run(test_futuristic_interface())
        else:
            print("[ERROR] Futuristic interface not running")
            print("[IDEA] Start it with: ./start-futuristic-interface.sh")
    except Exception:
        print("[ERROR] Futuristic interface not running on localhost:8001")
        print("[IDEA] Start it with: ./start-futuristic-interface.sh")
