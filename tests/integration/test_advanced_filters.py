#!/usr/bin/env python3
"""
Test script for advanced filters functionality.
"""

import asyncio
import json

import requests


def test_advanced_filters():
    """Test the advanced filters in the web interface."""
    base_url = "http://localhost:8000"

    # Test 1: Basic search without filters
    print("🔍 Test 1: Basic search without filters")
    basic_search = {
        "query": "diabetes",
        "max_results": 5,
        "include_sra": False,
        "output_format": "json",
    }

    response = requests.post(f"{base_url}/api/search", json=basic_search)
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Basic search successful: {len(results.get('metadata', []))} results")
    else:
        print(f"❌ Basic search failed: {response.status_code} - {response.text}")
        return

    # Test 2: Search with organism filter
    print("\n🧬 Test 2: Search with organism filter")
    organism_search = {
        "query": "diabetes",
        "max_results": 5,
        "include_sra": False,
        "output_format": "json",
        "organism": "homo sapiens",
    }

    response = requests.post(f"{base_url}/api/search", json=organism_search)
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Organism filter search successful: {len(results.get('metadata', []))} results")
        # Check if results contain human data
        for dataset in results.get("metadata", [])[:3]:
            organism = dataset.get("organism", "Unknown")
            print(f"   - {dataset.get('id', 'N/A')}: {organism}")
    else:
        print(f"❌ Organism filter search failed: {response.status_code} - {response.text}")

    # Test 3: Search with assay type filter
    print("\n🔬 Test 3: Search with assay type filter")
    assay_search = {
        "query": "diabetes",
        "max_results": 5,
        "include_sra": False,
        "output_format": "json",
        "assay_type": "RNA-seq",
    }

    response = requests.post(f"{base_url}/api/search", json=assay_search)
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Assay type filter search successful: {len(results.get('metadata', []))} results")
        # Check if results contain RNA-seq data
        for dataset in results.get("metadata", [])[:3]:
            title = dataset.get("title", "")
            platform = dataset.get("platform", "")
            print(f"   - {dataset.get('id', 'N/A')}: {title[:50]}...")
    else:
        print(f"❌ Assay type filter search failed: {response.status_code} - {response.text}")

    # Test 4: Search with date filter
    print("\n📅 Test 4: Search with date filter")
    date_search = {
        "query": "diabetes",
        "max_results": 5,
        "include_sra": False,
        "output_format": "json",
        "date_from": "2020-01-01",
    }

    response = requests.post(f"{base_url}/api/search", json=date_search)
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Date filter search successful: {len(results.get('metadata', []))} results")
        # Check publication dates
        for dataset in results.get("metadata", [])[:3]:
            pub_date = dataset.get("publication_date", "Unknown")
            print(f"   - {dataset.get('id', 'N/A')}: Published {pub_date}")
    else:
        print(f"❌ Date filter search failed: {response.status_code} - {response.text}")

    # Test 5: AI summarization with filters
    print("\n🤖 Test 5: AI summarization with filters")
    ai_search = {
        "query": "diabetes",
        "max_results": 3,
        "organism": "homo sapiens",
        "summary_type": "brief",
    }

    response = requests.post(f"{base_url}/api/summarize", json=ai_search)
    if response.status_code == 200:
        results = response.json()
        print(f"✅ AI summarization with filters successful: {len(results.get('metadata', []))} results")
        if results.get("ai_summaries"):
            print("   - AI summaries generated successfully")
        else:
            print("   - No AI summaries in response")
    else:
        print(f"❌ AI summarization with filters failed: {response.status_code} - {response.text}")

    print("\n🎉 Advanced filters test completed!")


if __name__ == "__main__":
    test_advanced_filters()
