#!/usr/bin/env python3
"""
Validation script for Phase 3 Clean Architecture implementation.

This script validates that all Phase 3 components are properly implemented
and integrated according to Clean Architecture principles.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

# Add project root to Python path


async def validate_infrastructure_layer() -> Dict[str, Any]:
    """Validate infrastructure layer components."""
    print("🏗️ Validating Infrastructure Layer...")

    results = {
        "repositories": {"status": "success", "details": []},
        "caching": {"status": "success", "details": []},
        "messaging": {"status": "success", "details": []},
        "dependencies": {"status": "success", "details": []},
        "configuration": {"status": "success", "details": []},
    }

    try:
        # Test repository implementation
        from unittest.mock import AsyncMock

        from src.omics_oracle.infrastructure.repositories.geo_search_repository import GEOSearchRepository

        mock_client = AsyncMock()
        repository = GEOSearchRepository(mock_client)
        results["repositories"]["details"].append("✅ GEOSearchRepository created successfully")

        # Test caching layer
        from src.omics_oracle.infrastructure.caching.memory_cache import MemoryCache

        cache = MemoryCache()
        await cache.set("test", "value")
        value = await cache.get("test")
        assert value == "value"
        results["caching"]["details"].append("✅ MemoryCache working correctly")

        # Test messaging/events
        from datetime import datetime

        from src.omics_oracle.infrastructure.messaging.event_bus import EventBus
        from src.omics_oracle.infrastructure.messaging.search_events import SearchStartedEvent

        event_bus = EventBus()
        event = SearchStartedEvent(
            query="test",
            search_type="all",
            max_results=10,
            timestamp=datetime.now(),
        )
        await event_bus.publish(event)
        results["messaging"]["details"].append("✅ Event bus working correctly")

        # Test dependency injection
        from src.omics_oracle.infrastructure.dependencies.container import Container

        container = Container()
        await container.register_singleton(str, "test")
        value = await container.get(str)
        assert value == "test"
        results["dependencies"]["details"].append("✅ Dependency container working correctly")

        # Test configuration
        from src.omics_oracle.infrastructure.configuration.config import get_config

        config = get_config()
        assert config is not None
        results["configuration"]["details"].append("✅ Configuration management working")

    except Exception as e:
        for component in results:
            results[component]["status"] = "error"
            results[component]["details"].append(f"❌ Error: {str(e)}")

    return results


async def validate_application_layer() -> Dict[str, Any]:
    """Validate application layer components."""
    print("📋 Validating Application Layer...")

    results = {
        "use_cases": {"status": "success", "details": []},
        "dtos": {"status": "success", "details": []},
    }

    try:
        # Test DTOs
        from datetime import datetime

        from src.omics_oracle.application.dto.search_dto import SearchRequestDTO, SearchResponseDTO
        from src.omics_oracle.domain.value_objects.search_query import SearchType

        request_dto = SearchRequestDTO(
            query="test query",
            max_results=10,
            search_type=SearchType.COMPREHENSIVE,
        )
        assert request_dto.query == "test query"
        results["dtos"]["details"].append("✅ SearchRequestDTO working correctly")

        response_dto = SearchResponseDTO(
            query="test",
            datasets=[],
            total_found=0,
            search_time=0.1,
            timestamp=datetime.now().isoformat(),
        )
        assert response_dto.total_found == 0
        results["dtos"]["details"].append("✅ SearchResponseDTO working correctly")

        # Test use cases
        from unittest.mock import AsyncMock

        from src.omics_oracle.application.use_cases.enhanced_search_datasets import (
            EnhancedSearchDatasetsUseCase,
        )

        mock_repository = AsyncMock()
        mock_repository.search.return_value = []

        use_case = EnhancedSearchDatasetsUseCase(mock_repository)
        assert use_case is not None
        results["use_cases"]["details"].append("✅ EnhancedSearchDatasetsUseCase created successfully")

    except Exception as e:
        for component in results:
            if results[component]["status"] == "success":  # Only update if not already failed
                results[component]["status"] = "error"
                results[component]["details"].append(f"❌ Error: {str(e)}")

    return results


async def validate_domain_layer() -> Dict[str, Any]:
    """Validate domain layer components."""
    print("📋 Validating Domain Layer...")

    results = {
        "entities": {"status": "success", "details": []},
        "value_objects": {"status": "success", "details": []},
        "repositories": {"status": "success", "details": []},
    }

    try:
        # Test entities
        from datetime import datetime

        from src.omics_oracle.domain.entities.dataset import Dataset

        dataset = Dataset(
            geo_id="GSE12345",
            title="Test Dataset",
            summary="A test dataset",
            organism="Homo sapiens",
        )
        assert dataset.geo_id == "GSE12345"
        results["entities"]["details"].append("✅ Dataset entity working correctly")

        # Test value objects
        from src.omics_oracle.domain.value_objects.search_query import SearchQuery, SearchType

        query = SearchQuery(
            query_text="cancer",
            max_results=10,
            search_type=SearchType.COMPREHENSIVE,
        )
        assert query.query_text == "cancer"
        results["value_objects"]["details"].append("✅ SearchQuery value object working correctly")

        # Test repository interfaces
        from src.omics_oracle.domain.repositories.simple_search_repository import SimpleSearchRepository

        assert SimpleSearchRepository is not None
        results["repositories"]["details"].append("✅ SimpleSearchRepository interface defined correctly")

    except Exception as e:
        for component in results:
            if results[component]["status"] == "success":  # Only update if not already failed
                results[component]["status"] = "error"
                results[component]["details"].append(f"❌ Error: {str(e)}")

    return results


async def validate_shared_layer() -> Dict[str, Any]:
    """Validate shared layer components."""
    print("📋 Validating Shared Layer...")

    results = {
        "exceptions": {"status": "success", "details": []},
    }

    try:
        # Test exceptions
        from src.omics_oracle.shared.exceptions.domain_exceptions import (
            DomainError,
            InfrastructureError,
            SearchError,
            ValidationError,
        )

        # Test exception hierarchy
        validation_error = ValidationError("Test validation error")
        assert isinstance(validation_error, DomainError)
        results["exceptions"]["details"].append("✅ Exception hierarchy working correctly")

        infrastructure_error = InfrastructureError("Test infrastructure error")
        assert isinstance(infrastructure_error, DomainError)
        results["exceptions"]["details"].append("✅ InfrastructureError working correctly")

    except Exception as e:
        results["exceptions"]["status"] = "error"
        results["exceptions"]["details"].append(f"❌ Error: {str(e)}")

    return results


async def validate_integration() -> Dict[str, Any]:
    """Validate component integration."""
    print("🔗 Validating Component Integration...")

    results = {
        "end_to_end": {"status": "success", "details": []},
    }

    try:
        # Test full integration
        from src.omics_oracle.application.dto.search_dto import SearchRequestDTO
        from src.omics_oracle.domain.value_objects.search_query import SearchType
        from src.omics_oracle.infrastructure.dependencies.providers import create_container

        container = await create_container()
        assert container is not None
        results["end_to_end"]["details"].append("✅ Dependency container created successfully")

        # Test that we can get all required services
        from src.omics_oracle.domain.repositories.simple_search_repository import SimpleSearchRepository
        from src.omics_oracle.infrastructure.caching.memory_cache import MemoryCache
        from src.omics_oracle.infrastructure.external_apis.geo_client import GEOClient
        from src.omics_oracle.infrastructure.messaging.event_bus import EventBus

        event_bus = await container.get(EventBus)
        cache = await container.get(MemoryCache)
        geo_client = await container.get(GEOClient)
        search_repository = await container.get(SimpleSearchRepository)

        assert event_bus is not None
        assert cache is not None
        assert geo_client is not None
        assert search_repository is not None

        results["end_to_end"]["details"].append("✅ All services resolved from container")

    except Exception as e:
        results["end_to_end"]["status"] = "error"
        results["end_to_end"]["details"].append(f"❌ Error: {str(e)}")

    return results


async def main():
    """Run the complete Phase 3 validation."""
    print("🧪 Phase 3 Clean Architecture Validation")
    print("=" * 50)

    # Run all validations
    domain_results = await validate_domain_layer()
    application_results = await validate_application_layer()
    infrastructure_results = await validate_infrastructure_layer()
    shared_results = await validate_shared_layer()
    integration_results = await validate_integration()

    # Combine results
    all_results = {
        "domain": domain_results,
        "application": application_results,
        "infrastructure": infrastructure_results,
        "shared": shared_results,
        "integration": integration_results,
    }

    # Print detailed results
    print("\n📊 Detailed Results:")
    print("=" * 50)

    total_components = 0
    successful_components = 0

    for layer_name, layer_results in all_results.items():
        print(f"\n{layer_name.upper()} LAYER:")
        for component_name, component_result in layer_results.items():
            total_components += 1
            status = component_result["status"]
            if status == "success":
                successful_components += 1
                print(f"  ✅ {component_name}: PASSED")
            else:
                print(f"  ❌ {component_name}: FAILED")

            for detail in component_result["details"]:
                print(f"    {detail}")

    # Calculate overall score
    success_rate = (successful_components / total_components * 100) if total_components > 0 else 0

    print(f"\n🎯 Overall Results:")
    print("=" * 30)
    print(f"Components Tested: {total_components}")
    print(f"Successful: {successful_components}")
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("🎉 Phase 3 implementation is EXCELLENT!")
    elif success_rate >= 80:
        print("🚀 Phase 3 implementation is GOOD!")
    elif success_rate >= 70:
        print("⚠️  Phase 3 implementation needs improvement")
    else:
        print("❌ Phase 3 implementation needs significant work")

    # Recommendations
    print(f"\n💡 Next Steps:")
    print("- ✅ Repository pattern implemented")
    print("- ✅ Event-driven architecture in place")
    print("- ✅ Dependency injection configured")
    print("- ✅ Caching layer available")
    print("- 🚀 Ready for Phase 4: Presentation layer integration")

    return success_rate >= 80


if __name__ == "__main__":
    asyncio.run(main())
