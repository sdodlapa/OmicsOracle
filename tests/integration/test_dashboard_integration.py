#!/usr/bin/env python3
"""
Test script to verify dashboard integration and complete the visualization work.
"""

import asyncio
import sys
from pathlib import Path

# Add the source directory to the path
try:
    from omics_oracle.web.main import app

    print("✅ FastAPI app imported successfully")
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    sys.exit(1)


async def test_visualization_endpoints():
    """Test the visualization endpoints work correctly."""

    # Test data - simulating a real request
    test_request = {"query": "cancer", "max_results": 50}

    print("\n📊 Testing Visualization Endpoints:")
    print("=" * 50)

    try:
        # Import the endpoint functions directly
        from omics_oracle.web.visualization_routes import (
            SearchVisualizationRequest,
            get_entity_distribution,
            get_organism_distribution,
            get_platform_distribution,
            get_search_visualization_stats,
            get_timeline_distribution,
        )

        # Create request object
        request = SearchVisualizationRequest(**test_request)

        print(f"🔍 Testing with query: '{request.query}' (max {request.max_results} results)")

        # Test each endpoint
        endpoints = [
            ("search-stats", get_search_visualization_stats),
            ("entity-distribution", get_entity_distribution),
            ("organism-distribution", get_organism_distribution),
            ("platform-distribution", get_platform_distribution),
            ("timeline-distribution", get_timeline_distribution),
        ]

        results = {}

        for name, func in endpoints:
            try:
                print(f"  Testing {name}...", end=" ")
                result = await func(request)
                results[name] = result
                print("✅ Success")
            except Exception as e:
                print(f"❌ Failed: {e}")
                results[name] = {"error": str(e)}

        return results

    except Exception as e:
        print(f"❌ Critical error in testing: {e}")
        return None


def validate_dashboard_html():
    """Validate the dashboard HTML file is properly configured."""

    dashboard_file = Path(__file__).parent / "src/omics_oracle/web/static/dashboard.html"

    print("\n🌐 Validating Dashboard HTML:")
    print("=" * 50)

    if not dashboard_file.exists():
        print("❌ Dashboard file not found!")
        return False

    try:
        content = dashboard_file.read_text()

        # Check for key integration points
        checks = [
            ("Chart.js library", "chart.js" in content.lower()),
            ("Visualization API calls", "/api/visualization/" in content),
            ("Search query input", 'id="search-query"' in content),
            ("Entity chart container", 'id="entity-chart"' in content),
            ("Usage chart container", 'id="usage-chart"' in content),
            ("Response time chart", 'id="response-time-chart"' in content),
            ("Dashboard loading function", "loadDashboard" in content),
            ("Visualization data function", "loadVisualizationData" in content),
        ]

        all_passed = True
        for check_name, condition in checks:
            if condition:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ Error reading dashboard file: {e}")
        return False


def check_required_routes():
    """Check that all required routes are registered."""

    print("\n🛠️ Checking FastAPI Routes:")
    print("=" * 50)

    try:
        # Get all routes from the app
        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                routes.append(route.path)

        required_routes = [
            "/health",
            "/api/visualization/search-stats",
            "/api/visualization/entity-distribution",
            "/api/visualization/organism-distribution",
            "/api/visualization/platform-distribution",
            "/api/visualization/timeline-distribution",
        ]

        all_found = True
        for route in required_routes:
            if any(r.startswith(route) for r in routes):
                print(f"  ✅ {route}")
            else:
                print(f"  ❌ {route} - NOT FOUND")
                all_found = False

        print(f"\n📝 Total routes found: {len(routes)}")
        return all_found

    except Exception as e:
        print(f"❌ Error checking routes: {e}")
        return False


async def main():
    """Main test function."""

    print("🚀 OmicsOracle Dashboard Integration Test")
    print("=" * 60)

    # 1. Validate HTML dashboard
    html_valid = validate_dashboard_html()

    # 2. Check routes are registered
    routes_valid = check_required_routes()

    # 3. Test visualization endpoints
    endpoint_results = await test_visualization_endpoints()

    # 4. Summary
    print("\n📋 INTEGRATION TEST SUMMARY:")
    print("=" * 60)

    if html_valid:
        print("✅ Dashboard HTML is properly configured")
    else:
        print("❌ Dashboard HTML needs fixes")

    if routes_valid:
        print("✅ All required API routes are registered")
    else:
        print("❌ Some API routes are missing")

    if endpoint_results:
        success_count = sum(1 for r in endpoint_results.values() if "error" not in r)
        total_count = len(endpoint_results)
        print(f"✅ Visualization endpoints: {success_count}/{total_count} working")

        if success_count == total_count:
            print("\n🎉 DASHBOARD INTEGRATION COMPLETE!")
            print("   The frontend-backend integration is working properly.")
        else:
            print("\n⚠️ Some endpoints need attention:")
            for name, result in endpoint_results.items():
                if "error" in result:
                    print(f"   - {name}: {result['error']}")
    else:
        print("❌ Visualization endpoints failed to test")

    # 5. Next steps
    print("\n🎯 TO COMPLETE THE WORK:")
    print("   1. Start the server: python -m omics_oracle.web.main")
    print("   2. Visit: http://localhost:8000/static/dashboard.html")
    print("   3. Test the interactive dashboard with real data")


if __name__ == "__main__":
    asyncio.run(main())
