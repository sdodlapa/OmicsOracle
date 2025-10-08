#!/usr/bin/env python3
"""
Test authentication UI implementation
Phase 4 Day 6 - Dashboard Authentication
"""

import asyncio
import httpx
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123!"
}

async def test_ui_pages():
    """Test that UI pages are accessible"""
    print("=" * 60)
    print("Testing Authentication UI Pages")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test login page
        print("\n1. Testing /login page...")
        try:
            response = await client.get(f"{BASE_URL}/login")
            if response.status_code == 200:
                print("   ✅ Login page accessible")
                if "OmicsOracle" in response.text:
                    print("   ✅ Login page content valid")
                else:
                    print("   ❌ Login page content invalid")
            else:
                print(f"   ❌ Login page failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test register page
        print("\n2. Testing /register page...")
        try:
            response = await client.get(f"{BASE_URL}/register")
            if response.status_code == 200:
                print("   ✅ Register page accessible")
                if "Create your account" in response.text:
                    print("   ✅ Register page content valid")
                else:
                    print("   ❌ Register page content invalid")
            else:
                print(f"   ❌ Register page failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test auth.js file
        print("\n3. Testing /static/js/auth.js...")
        try:
            response = await client.get(f"{BASE_URL}/static/js/auth.js")
            if response.status_code == 200:
                print("   ✅ Auth.js file accessible")
                if "OmicsAuth" in response.text:
                    print("   ✅ Auth.js content valid")
                else:
                    print("   ❌ Auth.js content invalid")
            else:
                print(f"   ❌ Auth.js failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_auth_flow():
    """Test complete authentication flow"""
    print("\n" + "=" * 60)
    print("Testing Authentication Flow")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test registration
        print("\n1. Testing registration...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/register",
                json=TEST_USER
            )
            if response.status_code == 200:
                print("   ✅ Registration successful")
                data = response.json()
                print(f"   User ID: {data.get('id')}")
                print(f"   Email: {data.get('email')}")
            elif response.status_code == 400:
                print("   ⚠️  User already exists (expected)")
            else:
                print(f"   ❌ Registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test login
        print("\n2. Testing login...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            if response.status_code == 200:
                print("   ✅ Login successful")
                data = response.json()
                token = data.get('access_token')
                print(f"   Token received: {token[:20]}...")
                
                # Test authenticated endpoint
                print("\n3. Testing authenticated endpoint...")
                headers = {"Authorization": f"Bearer {token}"}
                me_response = await client.get(
                    f"{BASE_URL}/api/auth/me",
                    headers=headers
                )
                if me_response.status_code == 200:
                    print("   ✅ /api/auth/me successful")
                    user_data = me_response.json()
                    print(f"   Name: {user_data.get('name')}")
                    print(f"   Email: {user_data.get('email')}")
                else:
                    print(f"   ❌ /api/auth/me failed: {me_response.status_code}")
                
                # Test logout
                print("\n4. Testing logout...")
                logout_response = await client.post(
                    f"{BASE_URL}/api/auth/logout",
                    headers=headers
                )
                if logout_response.status_code == 200:
                    print("   ✅ Logout successful")
                else:
                    print(f"   ❌ Logout failed: {logout_response.status_code}")
            else:
                print(f"   ❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_file_existence():
    """Check that all required files exist"""
    print("\n" + "=" * 60)
    print("Checking File Existence")
    print("=" * 60)
    
    base_path = Path(__file__).parent
    
    files = [
        "omics_oracle_v2/api/static/login.html",
        "omics_oracle_v2/api/static/register.html",
        "omics_oracle_v2/api/static/js/auth.js",
    ]
    
    all_exist = True
    for file_path in files:
        full_path = base_path / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist

async def main():
    """Run all tests"""
    print("\n🧬 OmicsOracle Authentication UI Tests")
    print("Phase 4 Day 6 - Dashboard Authentication\n")
    
    # Check files
    files_ok = await test_file_existence()
    if not files_ok:
        print("\n❌ Some files are missing. Please check the implementation.")
        return
    
    # Test UI pages
    await test_ui_pages()
    
    # Test auth flow
    await test_auth_flow()
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Open browser to http://localhost:8000/login")
    print("2. Test registration flow")
    print("3. Test login flow")
    print("4. Verify protected routes redirect to login")
    print("5. Test logout functionality")
    print("\n✨ Day 6 Progress: Authentication UI Complete!")

if __name__ == "__main__":
    asyncio.run(main())
