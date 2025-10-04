#!/usr/bin/env python3
"""
Quick route diagnosis using our existing FastAPI app.
"""

import os

# Set up environment
os.environ.setdefault("NCBI_EMAIL", "omicsoracle@example.com")
for line in open(".env.development"):
    if line.strip() and not line.startswith("#"):
        key, value = line.strip().split("=", 1)
        os.environ[key] = value

# Add src to path


def main():
    try:
        print("🔍 Diagnosing FastAPI Routes...")
        print("=" * 50)

        # Import the app
        from src.omics_oracle.presentation.web.main import app

        print("✅ App imported successfully")
        print(f"📱 App title: {app.title}")
        print(f"📱 App version: {app.version}")

        print("\n📋 Registered Routes:")
        print("-" * 30)

        route_count = 0
        api_routes = []

        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                route_count += 1
                methods = list(route.methods) if route.methods else ["N/A"]
                path = route.path
                print(f"  {methods[0]:8} {path}")

                if path.startswith("/api"):
                    api_routes.append((methods[0], path))

        print(f"\n📊 Route Summary:")
        print(f"  Total routes: {route_count}")
        print(f"  API routes: {len(api_routes)}")

        if api_routes:
            print(f"\n🎯 API Routes Found:")
            for method, path in api_routes:
                print(f"  {method:8} {path}")
        else:
            print(f"\n❌ No API routes found!")

        # Test route imports individually
        print(f"\n🧪 Testing Route Module Imports:")
        print("-" * 30)

        try:
            from src.omics_oracle.presentation.web.routes.v1 import router as v1_router

            print(f"  ✅ v1 router: {len(v1_router.routes)} routes")
            for route in v1_router.routes[:3]:  # Show first 3
                if hasattr(route, "path"):
                    print(f"     - {route.path}")
        except Exception as e:
            print(f"  ❌ v1 router failed: {e}")

        try:
            from src.omics_oracle.presentation.web.routes.v2 import router as v2_router

            print(f"  ✅ v2 router: {len(v2_router.routes)} routes")
            for route in v2_router.routes[:3]:  # Show first 3
                if hasattr(route, "path"):
                    print(f"     - {route.path}")
        except Exception as e:
            print(f"  ❌ v2 router failed: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
