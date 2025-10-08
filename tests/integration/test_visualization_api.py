#!/usr/bin/env python3
"""
Test script for visualization API endpoints.
"""

import json

import requests


def test_visualization_endpoints():
    """Test the visualization API endpoints."""
    base_url = "http://localhost:8000"

    # Test data
    test_request = {"query": "diabetes", "max_results": 20}

    print("🎨 Testing Visualization API Endpoints")
    print("=" * 50)

    # Test 1: Health check
    print("\n🏥 Test 1: Visualization health check")
    try:
        response = requests.get(f"{base_url}/api/visualization/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check successful")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Available endpoints: {len(health_data.get('endpoints', []))}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")

    # Test 2: Search stats
    print("\n📊 Test 2: Search statistics")
    try:
        response = requests.post(f"{base_url}/api/visualization/search-stats", json=test_request)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Search stats successful")
            print(f"   Total datasets: {stats.get('total_datasets')}")
            print(f"   Total samples: {stats.get('total_samples')}")
            print(f"   Unique organisms: {stats.get('unique_organisms')}")
            print(f"   Unique platforms: {stats.get('unique_platforms')}")
            print(f"   Average samples: {stats.get('avg_samples')}")
            print(f"   Date range: {stats.get('date_range')}")
        else:
            print(f"❌ Search stats failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Search stats error: {str(e)}")

    # Test 3: Entity distribution
    print("\n🏷️ Test 3: Entity distribution")
    try:
        response = requests.post(
            f"{base_url}/api/visualization/entity-distribution",
            json=test_request,
        )
        if response.status_code == 200:
            entities = response.json()
            print(f"✅ Entity distribution successful")
            print(f"   Total entities: {entities.get('total_entities')}")
            print(f"   Entity types: {len(entities.get('labels', []))}")
            if entities.get("labels"):
                for label, count in zip(entities["labels"][:5], entities["counts"][:5]):
                    print(f"     - {label}: {count}")
        else:
            print(f"❌ Entity distribution failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Entity distribution error: {str(e)}")

    # Test 4: Organism distribution
    print("\n🧬 Test 4: Organism distribution")
    try:
        response = requests.post(
            f"{base_url}/api/visualization/organism-distribution",
            json=test_request,
        )
        if response.status_code == 200:
            organisms = response.json()
            print(f"✅ Organism distribution successful")
            print(f"   Organism types: {len(organisms.get('labels', []))}")
            if organisms.get("labels"):
                for label, count in zip(organisms["labels"][:5], organisms["counts"][:5]):
                    print(f"     - {label}: {count}")
        else:
            print(f"❌ Organism distribution failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Organism distribution error: {str(e)}")

    # Test 5: Platform distribution
    print("\n🔬 Test 5: Platform distribution")
    try:
        response = requests.post(
            f"{base_url}/api/visualization/platform-distribution",
            json=test_request,
        )
        if response.status_code == 200:
            platforms = response.json()
            print(f"✅ Platform distribution successful")
            print(f"   Platform types: {len(platforms.get('labels', []))}")
            if platforms.get("labels"):
                for label, count in zip(platforms["labels"][:5], platforms["counts"][:5]):
                    print(f"     - {label}: {count}")
        else:
            print(f"❌ Platform distribution failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Platform distribution error: {str(e)}")

    # Test 6: Timeline distribution
    print("\n📅 Test 6: Timeline distribution")
    try:
        response = requests.post(
            f"{base_url}/api/visualization/timeline-distribution",
            json=test_request,
        )
        if response.status_code == 200:
            timeline = response.json()
            print(f"✅ Timeline distribution successful")
            print(f"   Years covered: {len(timeline.get('years', []))}")
            if timeline.get("years"):
                years = timeline["years"]
                counts = timeline["counts"]
                print(f"   Year range: {years[0]} - {years[-1]}")
                # Show a few sample years
                for year, count in list(zip(years, counts))[-5:]:
                    print(f"     - {year}: {count} datasets")
        else:
            print(f"❌ Timeline distribution failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Timeline distribution error: {str(e)}")

    print("\n🎉 Visualization API tests completed!")


if __name__ == "__main__":
    test_visualization_endpoints()
