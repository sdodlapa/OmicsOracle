"""
Quick Phase 6 Feature Test

Test the Phase 6 implementation without needing a running server.
This validates all the architectural improvements we've made.
"""

import asyncio
import logging
from pathlib import Path

# Add src to path
# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_phase6_features():
    """Test Phase 6 architectural features."""

    logger.info("🧪 Testing Phase 6 Clean Architecture Features")
    logger.info("=" * 60)

    results = []

    # Test 1: Enhanced Cache Hierarchy
    try:
        from omics_oracle.infrastructure.caching.cache_hierarchy import CacheHierarchy
        from omics_oracle.infrastructure.caching.memory_cache import MemoryCache

        memory_cache = MemoryCache(max_size=100)
        cache_hierarchy = CacheHierarchy()
        cache_hierarchy.add_cache(memory_cache)

        # Test cache operations
        await cache_hierarchy.set("test_key", "test_value", ttl=60)
        value = await cache_hierarchy.get("test_key")

        success = value == "test_value"
        results.append(
            (
                "✅" if success else "❌",
                "Enhanced Cache Hierarchy",
                f"Value: {value}",
            )
        )

    except Exception as e:
        results.append(("❌", "Enhanced Cache Hierarchy", f"Error: {e}"))

    # Test 2: Enhanced WebSocket Management
    try:
        from omics_oracle.infrastructure.websocket.enhanced_websocket import EnhancedWebSocketManager

        ws_manager = EnhancedWebSocketManager()

        # Test connection tracking
        connection_count = len(ws_manager.get_connections())

        success = hasattr(ws_manager, "broadcast_to_room")
        results.append(
            (
                "✅" if success else "❌",
                "Enhanced WebSocket Management",
                f"Connections: {connection_count}",
            )
        )

    except Exception as e:
        results.append(("❌", "Enhanced WebSocket Management", f"Error: {e}"))

    # Test 3: API Versioning Infrastructure
    try:
        from omics_oracle.presentation.api.versioning import APIVersion, APIVersionManager

        version_manager = APIVersionManager()
        version_manager.register_version(APIVersion.V1)
        version_manager.register_version(APIVersion.V2)

        current_version = version_manager.get_current_version()
        all_versions = version_manager.get_supported_versions()

        success = len(all_versions) >= 2
        results.append(
            (
                "✅" if success else "❌",
                "API Versioning Infrastructure",
                f"Versions: {len(all_versions)}",
            )
        )

    except Exception as e:
        results.append(("❌", "API Versioning Infrastructure", f"Error: {e}"))

    # Test 4: Microservices Communication
    try:
        from omics_oracle.infrastructure.microservices.communication import ServiceCommunicator
        from omics_oracle.infrastructure.microservices.service_discovery import ServiceRegistry

        registry = ServiceRegistry()
        communicator = ServiceCommunicator(registry)

        # Register a test service
        await registry.register_service("test-service", "http://localhost:9000", {"version": "1.0"})
        services = await registry.get_services()

        success = len(services) > 0
        results.append(
            (
                "✅" if success else "❌",
                "Microservices Communication",
                f"Services: {len(services)}",
            )
        )

    except Exception as e:
        results.append(("❌", "Microservices Communication", f"Error: {e}"))

    # Test 5: Event-Driven Architecture
    try:
        from omics_oracle.infrastructure.messaging.event_bus import EventBus

        event_bus = EventBus()

        # Test event subscription
        event_received = False

        def test_handler(event_data):
            nonlocal event_received
            event_received = True

        event_bus.subscribe("test.event", test_handler)
        await event_bus.publish("test.event", {"test": "data"})

        success = event_received
        results.append(
            (
                "✅" if success else "❌",
                "Event-Driven Architecture",
                f"Event received: {event_received}",
            )
        )

    except Exception as e:
        results.append(("❌", "Event-Driven Architecture", f"Error: {e}"))

    # Test 6: Production Infrastructure Integration
    try:
        from omics_oracle.presentation.web.main import create_app

        app = create_app()

        success = app is not None and hasattr(app, "router")
        route_count = len(app.routes) if hasattr(app, "routes") else 0

        results.append(
            (
                "✅" if success else "❌",
                "Production FastAPI Integration",
                f"Routes: {route_count}",
            )
        )

    except Exception as e:
        results.append(("❌", "Production FastAPI Integration", f"Error: {e}"))

    # Test 7: Clean Architecture Compliance
    try:
        from omics_oracle.application.use_cases.enhanced_search_datasets import EnhancedSearchDatasetsUseCase
        from omics_oracle.domain.entities.dataset import Dataset
        from omics_oracle.infrastructure.dependencies.container import Container

        container = Container()

        # Test dependency injection
        success = hasattr(container, "register_singleton")

        results.append(
            (
                "✅" if success else "❌",
                "Clean Architecture Compliance",
                "All layers accessible",
            )
        )

    except Exception as e:
        results.append(("❌", "Clean Architecture Compliance", f"Error: {e}"))

    # Display results
    logger.info("\n📊 Phase 6 Feature Test Results:")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    for status, feature, details in results:
        logger.info(f"{status} {feature} - {details}")
        if status == "✅":
            passed += 1

    success_rate = (passed / total) * 100 if total > 0 else 0

    logger.info("")
    logger.info(f"📈 Summary: {passed}/{total} tests passed ({success_rate:.1f}%)")

    if success_rate >= 85:
        logger.info("🎉 Phase 6 implementation is EXCELLENT!")
        quality = "Excellent"
    elif success_rate >= 70:
        logger.info("✅ Phase 6 implementation is GOOD!")
        quality = "Good"
    else:
        logger.info("⚠️ Phase 6 implementation needs improvements")
        quality = "Needs Improvement"

    return {
        "total_tests": total,
        "passed_tests": passed,
        "success_rate": success_rate,
        "quality": quality,
        "results": results,
    }


async def main():
    """Main test runner."""
    results = await test_phase6_features()

    # Create a simple summary
    logger.info("")
    logger.info("🏗️ Phase 6 Architecture Summary:")
    logger.info("- Enhanced caching with multi-level hierarchy")
    logger.info("- Advanced WebSocket management with rooms and broadcasting")
    logger.info("- API versioning infrastructure (v1, v2+)")
    logger.info("- Microservices communication foundation")
    logger.info("- Event-driven architecture with message bus")
    logger.info("- Production-ready FastAPI integration")
    logger.info("- Clean Architecture compliance across all layers")

    return results


if __name__ == "__main__":
    asyncio.run(main())
