#!/usr/bin/env python3
"""
Debug script to check what routes are actually registered in FastAPI.
"""

import os

# Add src to path
try:
    from omics_oracle.presentation.web.main import app

    print("🔍 Debugging FastAPI Routes Registration")
    print("=" * 60)

    print(f"📱 FastAPI App Title: {app.title}")
    print(f"📱 FastAPI App Version: {app.version}")
    print()

    print("📋 Registered Routes:")
    print("-" * 40)

    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = list(route.methods) if route.methods else ["N/A"]
            print(f"  {methods[0]:6} {route.path}")
            if hasattr(route, "name") and route.name:
                print(f"         Name: {route.name}")
            if len(methods) > 1:
                print(f"         Methods: {methods}")
        elif hasattr(route, "path"):
            print(f"  {'MOUNT':6} {route.path}")

    print()
    print("🔍 Route Summary:")
    print("-" * 40)

    api_routes = [r for r in app.routes if hasattr(r, "path") and r.path.startswith("/api")]
    health_routes = [r for r in app.routes if hasattr(r, "path") and "health" in r.path]
    websocket_routes = [r for r in app.routes if hasattr(r, "path") and r.path.startswith("/ws")]

    print(f"  API routes: {len(api_routes)}")
    print(f"  Health routes: {len(health_routes)}")
    print(f"  WebSocket routes: {len(websocket_routes)}")
    print(f"  Total routes: {len(app.routes)}")

    print()
    print("🧪 Testing Route Access:")
    print("-" * 40)

    # Test imports
    try:
        from omics_oracle.presentation.web.routes.v1 import router as v1_router

        print(f"  ✅ v1_router imported: {len(v1_router.routes)} routes")
        for route in v1_router.routes:
            if hasattr(route, "path"):
                print(f"     - {route.path}")
    except Exception as e:
        print(f"  ❌ v1_router import failed: {e}")

    try:
        from omics_oracle.presentation.web.routes.v2 import router as v2_router

        print(f"  ✅ v2_router imported: {len(v2_router.routes)} routes")
        for route in v2_router.routes:
            if hasattr(route, "path"):
                print(f"     - {route.path}")
    except Exception as e:
        print(f"  ❌ v2_router import failed: {e}")

except Exception as e:
    print(f"❌ Error importing FastAPI app: {e}")
    import traceback

    traceback.print_exc()
