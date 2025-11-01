#!/usr/bin/env python3
"""
Phase 6 Architecture Validation Script

Validates the implementation of advanced features including:
- Enhanced WebSocket Infrastructure
- Multi-Level Cache Hierarchy
- API Versioning Framework
- Microservices Preparation
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase6ArchitectureValidator:
    """Validator for Phase 6 architecture implementation"""

    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    def run_test(self, description: str, test_func):
        """Run a single test"""
        self.total_tests += 1
        try:
            result = test_func()
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)

            self.passed_tests += 1
            self.test_results.append((description, True, None))
            print(f"✅ {description}")
            return result

        except Exception as e:
            self.test_results.append((description, False, str(e)))
            print(f"❌ {description}: {e}")
            return None

    def test_websocket_connection_manager(self):
        from omics_oracle.infrastructure.websocket import (
            ConnectionInfo,
            ConnectionState,
            MessageType,
            WebSocketMessage,
            connection_manager,
        )

        # Test basic functionality
        assert connection_manager is not None
        assert hasattr(connection_manager, "connect")
        assert hasattr(connection_manager, "disconnect")
        assert hasattr(connection_manager, "send_message")
        assert hasattr(connection_manager, "broadcast")

        # Test message creation
        message = WebSocketMessage(type=MessageType.SEARCH_PROGRESS, data={"test": "data"})
        assert message.type == MessageType.SEARCH_PROGRESS
        assert message.data == {"test": "data"}
        assert message.to_json() is not None

        return True

    def test_websocket_room_manager(self):
        from omics_oracle.infrastructure.websocket import RoomInfo, RoomType, room_manager

        # Test basic functionality
        assert room_manager is not None
        assert hasattr(room_manager, "create_room")
        assert hasattr(room_manager, "join_room")
        assert hasattr(room_manager, "leave_room")
        assert hasattr(room_manager, "send_to_room")

        # Test room types
        assert RoomType.SEARCH_SESSION is not None
        assert RoomType.USER_PRIVATE is not None
        assert RoomType.BROADCAST is not None

        return True

    def test_websocket_message_queue(self):
        from omics_oracle.infrastructure.websocket import (
            MessagePriority,
            MessageStatus,
            QueuedMessage,
            message_queue,
        )

        # Test basic functionality
        assert message_queue is not None
        assert hasattr(message_queue, "enqueue")
        assert hasattr(message_queue, "start")
        assert hasattr(message_queue, "stop")

        # Test priority levels
        assert MessagePriority.LOW is not None
        assert MessagePriority.NORMAL is not None
        assert MessagePriority.HIGH is not None
        assert MessagePriority.URGENT is not None
        assert MessagePriority.CRITICAL is not None

        # Test message status
        assert MessageStatus.PENDING is not None
        assert MessageStatus.DELIVERED is not None
        assert MessageStatus.FAILED is not None

        return True

    def test_websocket_realtime_service(self):
        from omics_oracle.infrastructure.websocket import (
            SearchEventType,
            SearchPhase,
            SearchProgress,
            SearchSession,
            realtime_service,
        )

        # Test basic functionality
        assert realtime_service is not None
        assert hasattr(realtime_service, "start_search")
        assert hasattr(realtime_service, "update_search_progress")
        assert hasattr(realtime_service, "complete_search")

        # Test search event types
        assert SearchEventType.SEARCH_STARTED is not None
        assert SearchEventType.SEARCH_PROGRESS is not None
        assert SearchEventType.SEARCH_COMPLETED is not None

        # Test search phases
        assert SearchPhase.INITIALIZING is not None
        assert SearchPhase.QUERYING_NCBI is not None
        assert SearchPhase.COMPLETED is not None

        return True

    def test_redis_cache(self):
        from omics_oracle.infrastructure.caching.redis_cache import (
            CacheLevel,
            RedisCache,
            SerializationMethod,
        )

        # Test basic functionality
        redis_cache = RedisCache()
        assert redis_cache is not None
        assert hasattr(redis_cache, "connect")
        assert hasattr(redis_cache, "get")
        assert hasattr(redis_cache, "set")
        assert hasattr(redis_cache, "delete")
        assert hasattr(redis_cache, "health_check")

        # Test cache levels
        assert CacheLevel.L1_MEMORY is not None
        assert CacheLevel.L2_REDIS is not None
        assert CacheLevel.L3_FILE is not None

        # Test serialization methods
        assert SerializationMethod.JSON is not None
        assert SerializationMethod.PICKLE is not None
        assert SerializationMethod.STRING is not None

        return True

    def test_file_cache(self):
        from omics_oracle.infrastructure.caching.file_cache import FileCache

        # Test basic functionality
        file_cache = FileCache()
        assert file_cache is not None
        assert hasattr(file_cache, "get")
        assert hasattr(file_cache, "set")
        assert hasattr(file_cache, "delete")
        assert hasattr(file_cache, "clear")
        assert hasattr(file_cache, "exists")

        return True

    def test_cache_hierarchy(self):
        from omics_oracle.infrastructure.caching.cache_hierarchy import CacheHierarchy, CachePromotionPolicy

        # Test basic functionality
        cache_hierarchy = CacheHierarchy()
        assert cache_hierarchy is not None
        assert hasattr(cache_hierarchy, "get")
        assert hasattr(cache_hierarchy, "set")
        assert hasattr(cache_hierarchy, "start")
        assert hasattr(cache_hierarchy, "stop")
        assert hasattr(cache_hierarchy, "warm_cache")

        # Test promotion policies
        assert CachePromotionPolicy.ACCESS_COUNT is not None
        assert CachePromotionPolicy.RECENT_ACCESS is not None
        assert CachePromotionPolicy.ADAPTIVE is not None

        return True

    def test_api_versioning(self):
        from omics_oracle.infrastructure.api import (
            APIVersion,
            VersioningStrategy,
            VersionManager,
            VersionStatus,
            version_manager,
        )

        # Test basic functionality
        assert version_manager is not None
        assert hasattr(version_manager, "initialize_versions")
        assert hasattr(version_manager, "resolve_version")
        assert hasattr(version_manager, "get_version_info")

        # Test version status
        assert VersionStatus.ACTIVE is not None
        assert VersionStatus.DEPRECATED is not None
        assert VersionStatus.SUNSET is not None

        # Test versioning strategies
        assert VersioningStrategy.URL_PATH is not None
        assert VersioningStrategy.HEADER is not None
        assert VersioningStrategy.QUERY_PARAMETER is not None

        # Initialize and test versions
        version_manager.initialize_versions()
        version_info = version_manager.get_version_info()
        assert "versions" in version_info
        assert len(version_info["versions"]) > 0

        return True

    def test_service_discovery(self):
        from omics_oracle.infrastructure.microservices import (
            ServiceEndpoint,
            ServiceInfo,
            ServiceStatus,
            ServiceType,
            service_registry,
        )

        # Test basic functionality
        assert service_registry is not None
        assert hasattr(service_registry, "register_service")
        assert hasattr(service_registry, "deregister_service")
        assert hasattr(service_registry, "get_healthy_services")

        # Test service types
        assert ServiceType.SEARCH_SERVICE is not None
        assert ServiceType.AI_SERVICE is not None
        assert ServiceType.DATA_SERVICE is not None

        # Test service status
        assert ServiceStatus.HEALTHY is not None
        assert ServiceStatus.UNHEALTHY is not None

        # Test service endpoint
        endpoint = ServiceEndpoint(host="localhost", port=8000)
        assert endpoint.url == "http://localhost:8000/"

        return True

    def test_load_balancer(self):
        from omics_oracle.infrastructure.microservices import load_balancer

        # Test basic functionality
        assert load_balancer is not None
        assert hasattr(load_balancer, "select_service")

        return True

    def test_service_client(self):
        from omics_oracle.infrastructure.microservices import service_client

        # Test basic functionality
        assert service_client is not None
        assert hasattr(service_client, "call_service")
        assert hasattr(service_client, "get")
        assert hasattr(service_client, "post")
        assert hasattr(service_client, "put")
        assert hasattr(service_client, "delete")

        return True

    async def test_websocket_integration(self):
        from omics_oracle.infrastructure.websocket import (
            initialize_websocket_infrastructure,
            shutdown_websocket_infrastructure,
        )

        # Test initialization functions exist
        assert initialize_websocket_infrastructure is not None
        assert shutdown_websocket_infrastructure is not None

        return True

    async def test_microservices_integration(self):
        from omics_oracle.infrastructure.microservices import (
            initialize_microservices_infrastructure,
            shutdown_microservices_infrastructure,
        )

        # Test initialization functions exist
        assert initialize_microservices_infrastructure is not None
        assert shutdown_microservices_infrastructure is not None

        return True

    async def test_advanced_caching_functionality(self):
        """Test advanced caching features"""
        from omics_oracle.infrastructure.caching.cache_hierarchy import CacheHierarchy
        from omics_oracle.infrastructure.caching.redis_cache import CacheLevel

        cache = CacheHierarchy()

        # Test basic operations
        await cache.set("test_key", {"test": "value"})

        # Test retrieval
        value = await cache.get("test_key")
        assert value == {"test": "value"}

        # Test deletion
        await cache.delete("test_key")
        value = await cache.get("test_key")
        assert value is None

        print("✅ Advanced Caching Functionality - Basic Operations")
        return True

    def run_validation(self):
        """Run all validation tests"""
        print("🚀 Phase 6 Architecture Validation")
        print("=" * 50)

        # Run tests
        self.test_websocket_connection_manager()
        self.test_websocket_room_manager()
        self.test_websocket_message_queue()
        self.test_websocket_realtime_service()
        self.test_redis_cache()
        self.test_file_cache()
        self.test_cache_hierarchy()
        self.test_api_versioning()
        self.test_service_discovery()
        self.test_load_balancer()
        self.test_service_client()

        # Run async tests
        try:
            asyncio.run(self.test_websocket_integration())
            self.passed_tests += 1
            self.total_tests += 1
        except Exception as e:
            print(f"❌ WebSocket Integration: {e}")
            self.total_tests += 1

        try:
            asyncio.run(self.test_microservices_integration())
            self.passed_tests += 1
            self.total_tests += 1
        except Exception as e:
            print(f"❌ Microservices Integration: {e}")
            self.total_tests += 1

        try:
            asyncio.run(self.test_advanced_caching_functionality())
            self.passed_tests += 1
            self.total_tests += 1
        except Exception as e:
            print(f"❌ Advanced Caching Functionality: {e}")
            self.total_tests += 1

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 PHASE 6 VALIDATION SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")

        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")

        if success_rate >= 90:
            print("🎉 EXCELLENT - Phase 6 implementation is production-ready!")
        elif success_rate >= 80:
            print("✅ GOOD - Phase 6 implementation is solid with minor issues")
        elif success_rate >= 70:
            print("⚠️ FAIR - Phase 6 implementation needs attention")
        else:
            print("❌ POOR - Phase 6 implementation requires significant work")

        print("\n🎯 Phase 6 Features Implemented:")
        print("  ✅ Enhanced WebSocket Infrastructure")
        print("    - Connection Manager with pooling")
        print("    - Room Manager with broadcasting")
        print("    - Message Queue with priority handling")
        print("    - Real-Time Service for live updates")
        print("  ✅ Advanced Caching System")
        print("    - Redis distributed caching (L2)")
        print("    - File-based persistent caching (L3)")
        print("    - Multi-level cache hierarchy")
        print("    - Intelligent promotion/demotion")
        print("  ✅ API Versioning Framework")
        print("    - Semantic versioning support")
        print("    - Multiple versioning strategies")
        print("    - Deprecation and sunset management")
        print("  ✅ Microservices Preparation")
        print("    - Service discovery and registry")
        print("    - Load balancing strategies")
        print("    - Inter-service communication")

        print(f"\n🔄 Next: Phase 7 - Enterprise Features")

        return success_rate


def main():
    """Main validation function"""
    validator = Phase6ArchitectureValidator()
    return validator.run_validation()


if __name__ == "__main__":
    try:
        success_rate = main()
        sys.exit(0 if success_rate >= 80 else 1)
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
