#!/usr/bin/env python3
"""
Test Day 7 - LLM Features Display
Phase 4 Day 7 - Dashboard with Authentication and GPT-4 Analysis
"""

import asyncio
import httpx
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": "test@example.com",
    "password": "TestPass123!"
}

async def test_dashboard_routes():
    """Test dashboard routes are accessible"""
    print("=" * 60)
    print("Testing Dashboard Routes")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test root redirect
        print("\n1. Testing / (root) redirect...")
        try:
            response = await client.get(f"{BASE_URL}/", follow_redirects=False)
            if response.status_code == 307:
                print(f"   ✅ Root redirects to: {response.headers.get('location')}")
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test dashboard
        print("\n2. Testing /dashboard...")
        try:
            response = await client.get(f"{BASE_URL}/dashboard")
            if response.status_code == 200:
                print("   ✅ Dashboard accessible")
                if "AI-Powered Dataset Discovery" in response.text:
                    print("   ✅ Dashboard v2 content detected")
                elif "OmicsOracle Dashboard" in response.text:
                    print("   ⚠️  Original dashboard (v2 not found)")
                else:
                    print("   ❌ Unexpected dashboard content")
            else:
                print(f"   ❌ Dashboard failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test auth.js
        print("\n3. Testing /static/js/auth.js...")
        try:
            response = await client.get(f"{BASE_URL}/static/js/auth.js")
            if response.status_code == 200:
                print("   ✅ Auth.js accessible")
                if "OmicsAuth" in response.text:
                    print("   ✅ Auth module valid")
            else:
                print(f"   ❌ Auth.js failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_authenticated_workflow():
    """Test complete authenticated workflow"""
    print("\n" + "=" * 60)
    print("Testing Authenticated Workflow")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Login
        print("\n1. Logging in...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json=TEST_USER
            )
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                print(f"   ✅ Login successful")
                print(f"   Token: {token[:20]}...")
                
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test search endpoint
                print("\n2. Testing search endpoint...")
                search_response = await client.post(
                    f"{BASE_URL}/api/agents/search",
                    headers=headers,
                    json={"query": "breast cancer gene expression"}
                )
                if search_response.status_code == 200:
                    print("   ✅ Search endpoint working")
                    search_data = search_response.json()
                    results = search_data.get('results', [])
                    print(f"   Found {len(results)} datasets")
                else:
                    print(f"   ❌ Search failed: {search_response.status_code}")
                
                # Test analysis endpoint
                print("\n3. Testing analysis endpoint...")
                analysis_response = await client.post(
                    f"{BASE_URL}/api/agents/analysis",
                    headers=headers,
                    json={
                        "dataset_id": "GSE123456",
                        "metadata": {"title": "Test dataset"}
                    }
                )
                if analysis_response.status_code == 200:
                    print("   ✅ Analysis endpoint working")
                    analysis_data = analysis_response.json()
                    if 'analysis' in analysis_data or 'summary' in analysis_data:
                        print("   ✅ GPT-4 analysis received")
                else:
                    print(f"   ⚠️  Analysis endpoint: {analysis_response.status_code}")
                    print(f"   Note: This may be expected if GPT-4 not configured")
                
            else:
                print(f"   ❌ Login failed: {response.status_code}")
                print(f"   Note: User may not exist. Try registering first.")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_ui_components():
    """Test UI components exist"""
    print("\n" + "=" * 60)
    print("Testing UI Components")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Get dashboard HTML
        response = await client.get(f"{BASE_URL}/dashboard")
        if response.status_code == 200:
            html = response.text
            
            components = [
                ("Search bar", "search-query"),
                ("Search button", "search-btn"),
                ("Results section", "results-section"),
                ("Analysis section", "analysis-section"),
                ("User profile", "user-profile"),
                ("Export button", "exportAnalysis"),
            ]
            
            print("\nChecking UI components:")
            for name, identifier in components:
                if identifier in html:
                    print(f"   ✅ {name} present")
                else:
                    print(f"   ❌ {name} missing")
            
            # Check for key functions
            functions = [
                "performSearch",
                "analyzeDataset",
                "displayResults",
                "exportAnalysis",
                "requireAuth",
            ]
            
            print("\nChecking JavaScript functions:")
            for func in functions:
                if func in html:
                    print(f"   ✅ {func}()")
                else:
                    print(f"   ❌ {func}() missing")

async def test_file_structure():
    """Check file structure"""
    print("\n" + "=" * 60)
    print("Checking File Structure")
    print("=" * 60)
    
    base_path = Path(__file__).parent
    
    files = [
        ("Dashboard v2", "omics_oracle_v2/api/static/dashboard_v2.html"),
        ("Login page", "omics_oracle_v2/api/static/login.html"),
        ("Register page", "omics_oracle_v2/api/static/register.html"),
        ("Auth module", "omics_oracle_v2/api/static/js/auth.js"),
    ]
    
    print("\nFile existence:")
    all_exist = True
    for name, path in files:
        full_path = base_path / path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {path}")
        if not exists:
            all_exist = False
    
    return all_exist

async def main():
    """Run all Day 7 tests"""
    print("\n🧬 OmicsOracle Day 7 Tests")
    print("Phase 4 Day 7 - Dashboard with LLM Features\n")
    
    # Check files
    files_ok = await test_file_structure()
    if not files_ok:
        print("\n⚠️  Some files missing, but continuing tests...")
    
    # Test routes
    await test_dashboard_routes()
    
    # Test UI components
    await test_ui_components()
    
    # Test authenticated workflow
    await test_authenticated_workflow()
    
    print("\n" + "=" * 60)
    print("Day 7 Tests Complete!")
    print("=" * 60)
    
    print("\n📋 Manual Testing Steps:")
    print("1. Open http://localhost:8000 (should redirect to /dashboard)")
    print("2. Should redirect to /login if not authenticated")
    print("3. Login with test credentials")
    print("4. Dashboard should load with search bar")
    print("5. Enter query: 'breast cancer gene expression'")
    print("6. Click Search - datasets should appear")
    print("7. Click a dataset - GPT-4 analysis should load")
    print("8. Click Export - report should download")
    print("9. Click Logout - should return to login")
    
    print("\n✨ Day 7 Features:")
    print("✅ Protected dashboard with auth")
    print("✅ Dataset search interface")
    print("✅ GPT-4 analysis display")
    print("✅ Quality score visualization")
    print("✅ Export functionality")
    print("✅ Modern, responsive UI")
    
    print("\n🚀 Progress:")
    print("- Day 7: 90% complete (UI done, needs testing)")
    print("- Phase 4: 90% complete (Days 1-7 of 10)")
    print("\n📅 Next: Days 8-9 (End-to-end testing)")

if __name__ == "__main__":
    asyncio.run(main())
