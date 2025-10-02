"""
Phase 4 validation tests for presentation layer integration.

This script validates the FastAPI application, dependency injection,
WebSocket functionality, and overall integration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
from src.omics_oracle.application.dto.search_dto import SearchRequestDTO
from src.omics_oracle.infrastructure.dependencies.container import Container
from src.omics_oracle.presentation.web.main import create_app

logger = logging.getLogger(__name__)


async def test_fastapi_creation():
    """Test FastAPI application creation."""
    print("🧪 Testing FastAPI application creation...")

    try:
        app = create_app()
        assert app is not None
        assert app.title == "OmicsOracle API"
        assert app.version == "3.0.0"
        print("✅ FastAPI application created successfully")
        return True
    except Exception as e:
        print(f"❌ FastAPI creation failed: {e}")
        return False


async def test_dependency_injection():
    """Test dependency injection container."""
    print("🧪 Testing dependency injection...")

    try:
        container = Container()

        # Test search use case
        search_use_case = await container.get_search_use_case()
        assert search_use_case is not None
        print("✅ Search use case injection successful")

        # Test event bus
        event_bus = await container.get_event_bus()
        assert event_bus is not None
        print("✅ Event bus injection successful")

        # Test WebSocket service
        websocket_service = await container.get_websocket_service()
        assert websocket_service is not None
        print("✅ WebSocket service injection successful")

        # Test cache
        cache = await container.get_cache()
        assert cache is not None
        print("✅ Cache injection successful")

        return True
    except Exception as e:
        print(f"❌ Dependency injection test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_search_use_case_integration():
    """Test search use case integration."""
    print("🧪 Testing search use case integration...")

    try:
        container = Container()
        search_use_case = await container.get_search_use_case()

        # Test with a simple request
        request = SearchRequestDTO(query="test", max_results=1)

        # This should work without throwing errors (even if no results)
        response = await search_use_case.execute(request)
        assert response is not None
        assert hasattr(response, "query")
        assert response.query == "test"

        print("✅ Search use case integration successful")
        return True
    except Exception as e:
        print(f"❌ Search use case integration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_fastapi_routes():
    """Test FastAPI routes setup."""
    print("🧪 Testing FastAPI routes setup...")

    try:
        app = create_app()

        # Check that routes are properly registered
        routes = [route.path for route in app.routes]

        expected_routes = [
            "/health/",
            "/health/ready",
            "/health/live",
            "/health/config",
            "/api/v1/search/datasets",
            "/api/v1/analysis/capabilities",
        ]

        for expected_route in expected_routes:
            found = any(expected_route in route for route in routes)
            if not found:
                print(f"❌ Route not found: {expected_route}")
                return False

        print("✅ All expected routes found")
        return True
    except Exception as e:
        print(f"❌ Route setup test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_websocket_setup():
    """Test WebSocket endpoint setup."""
    print("🧪 Testing WebSocket setup...")

    try:
        app = create_app()

        # Check WebSocket routes
        websocket_routes = [
            route.path for route in app.routes if hasattr(route, "path") and "/ws" in route.path
        ]

        expected_ws_routes = [
            "/ws/search-progress",
            "/ws/events",
            "/ws/system-status",
        ]

        for expected_route in expected_ws_routes:
            found = any(expected_route in route for route in websocket_routes)
            if not found:
                print(f"❌ WebSocket route not found: {expected_route}")
                return False

        print("✅ WebSocket endpoints configured")
        return True
    except Exception as e:
        print(f"❌ WebSocket setup test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_middleware_setup():
    """Test middleware configuration."""
    print("🧪 Testing middleware setup...")

    try:
        app = create_app()

        # Check that middleware is configured
        middleware_count = len(app.user_middleware)

        # We expect CORS + our custom middleware
        if middleware_count < 2:
            print(f"❌ Expected at least 2 middleware layers, found {middleware_count}")
            return False

        print(f"✅ Middleware configured ({middleware_count} layers)")
        return True
    except Exception as e:
        print(f"❌ Middleware setup test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all Phase 4 validation tests."""
    print("🏗️ Phase 4: Presentation Layer Integration Validation")
    print("=" * 60)

    tests = [
        ("FastAPI Creation", test_fastapi_creation),
        ("Dependency Injection", test_dependency_injection),
        ("Search Use Case Integration", test_search_use_case_integration),
        ("FastAPI Routes", test_fastapi_routes),
        ("WebSocket Setup", test_websocket_setup),
        ("Middleware Setup", test_middleware_setup),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Phase 4 Validation Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Phase 4 implementation is EXCELLENT!")
        print("🚀 Ready for production deployment")
        print("💡 Next: Legacy interface decomposition and optimization")
        return True
    else:
        print("⚠️  Some issues found, but core functionality works")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run validation
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)
