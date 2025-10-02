"""
Integration tests for Phase 3 Clean Architecture components.

Tests the integration between repositories, use cases, event bus,
and infrastructure components.
"""

import asyncio

# Add project root to Python path
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.omics_oracle.application.dto.search_dto import SearchRequestDTO
from src.omics_oracle.application.use_cases.enhanced_search_datasets import EnhancedSearchDatasetsUseCase
from src.omics_oracle.domain.entities.dataset import Dataset
from src.omics_oracle.domain.value_objects.search_query import SearchType
from src.omics_oracle.infrastructure.caching.memory_cache import MemoryCache
from src.omics_oracle.infrastructure.dependencies.container import Container
from src.omics_oracle.infrastructure.messaging.event_bus import EventBus
from src.omics_oracle.infrastructure.messaging.search_events import (
    SearchCompletedEvent,
    SearchFailedEvent,
    SearchStartedEvent,
)
from src.omics_oracle.infrastructure.repositories.geo_search_repository import GEOSearchRepository
from src.omics_oracle.shared.exceptions.domain_exceptions import ValidationError


class TestPhase3Architecture:
    """Test suite for Phase 3 architecture components."""

    @pytest.fixture
    async def event_bus(self):
        """Create an event bus for testing."""
        return EventBus()

    @pytest.fixture
    async def memory_cache(self):
        """Create a memory cache for testing."""
        return MemoryCache(default_ttl=60)

    @pytest.fixture
    async def mock_geo_client(self):
        """Create a mock GEO client."""
        mock_client = AsyncMock()
        mock_client.search_datasets.return_value = [
            {
                "geo_id": "GSE123456",
                "title": "Test Dataset 1",
                "summary": "A test dataset for cancer research",
                "organism": "Homo sapiens",
                "platform": "GPL570",
                "samples_count": 24,
                "metadata": {"study_type": "expression profiling"},
            },
            {
                "geo_id": "GSE789012",
                "title": "Test Dataset 2",
                "summary": "Another test dataset",
                "organism": "Mus musculus",
                "platform": "GPL96",
                "samples_count": 18,
                "metadata": {"study_type": "genome variation"},
            },
        ]
        return mock_client

    @pytest.fixture
    async def geo_repository(self, mock_geo_client):
        """Create a GEO search repository with mock client."""
        return GEOSearchRepository(mock_geo_client)

    @pytest.fixture
    async def search_use_case(self, geo_repository, event_bus):
        """Create an enhanced search use case."""
        return EnhancedSearchDatasetsUseCase(geo_repository, event_bus)

    @pytest.fixture
    async def container(self, geo_repository, event_bus, memory_cache):
        """Create a dependency injection container."""
        container = Container()
        await container.register_singleton(EventBus, event_bus)
        await container.register_singleton(MemoryCache, memory_cache)
        await container.register_singleton(type(geo_repository), geo_repository)
        return container

    @pytest.mark.asyncio
    async def test_event_bus_basic_functionality(self, event_bus):
        """Test basic event bus publish/subscribe functionality."""
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe to events
        await event_bus.subscribe(SearchStartedEvent, handler)

        # Publish an event
        event = SearchStartedEvent(
            query="test query",
            search_type="all",
            max_results=10,
            timestamp=datetime.now(),
        )
        await event_bus.publish(event)

        # Wait for async processing
        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0].query == "test query"

    async def test_memory_cache_operations(self, memory_cache):
        """Test memory cache set/get/delete operations."""
        # Test basic set/get
        await memory_cache.set("test_key", "test_value")
        value = await memory_cache.get("test_key")
        assert value == "test_value"

        # Test TTL expiration
        await memory_cache.set("ttl_key", "ttl_value", ttl=0.1)
        await asyncio.sleep(0.2)
        value = await memory_cache.get("ttl_key")
        assert value is None

        # Test delete
        await memory_cache.set("delete_key", "delete_value")
        await memory_cache.delete("delete_key")
        value = await memory_cache.get("delete_key")
        assert value is None

    async def test_geo_repository_search(self, geo_repository, mock_geo_client):
        """Test GEO repository search functionality."""
        from src.omics_oracle.domain.value_objects.search_query import SearchQuery

        # Create search query
        query = SearchQuery(
            query_text="cancer",
            max_results=10,
            search_type=SearchType.ALL,
        )

        # Execute search
        datasets = await geo_repository.search(query)

        # Verify results
        assert len(datasets) == 2
        assert all(isinstance(dataset, Dataset) for dataset in datasets)
        assert datasets[0].geo_id == "GSE123456"
        assert datasets[1].geo_id == "GSE789012"

        # Verify mock was called correctly
        mock_geo_client.search_datasets.assert_called_once_with(
            query="cancer",
            max_results=10,
            search_type="all",
        )

    async def test_enhanced_search_use_case_success(self, search_use_case, event_bus):
        """Test successful search execution with event publishing."""
        received_events = []

        async def event_handler(event):
            received_events.append(event)

        # Subscribe to all search events
        await event_bus.subscribe(SearchStartedEvent, event_handler)
        await event_bus.subscribe(SearchCompletedEvent, event_handler)

        # Create search request
        request = SearchRequestDTO(
            query="cancer research",
            max_results=10,
            search_type=SearchType.ALL,
        )

        # Execute search
        response = await search_use_case.execute(request)

        # Wait for async event processing
        await asyncio.sleep(0.1)

        # Verify response
        assert response.query == "cancer research"
        assert response.total_found == 2
        assert len(response.results) == 2
        assert response.search_time > 0

        # Verify events were published
        assert len(received_events) == 2
        assert isinstance(received_events[0], SearchStartedEvent)
        assert isinstance(received_events[1], SearchCompletedEvent)
        assert received_events[0].query == "cancer research"
        assert received_events[1].results_count == 2

    async def test_enhanced_search_use_case_validation_error(self, search_use_case, event_bus):
        """Test search use case with validation error."""
        received_events = []

        async def event_handler(event):
            received_events.append(event)

        # Subscribe to search failed events
        await event_bus.subscribe(SearchFailedEvent, event_handler)

        # Create invalid search request
        request = SearchRequestDTO(
            query="",  # Empty query should cause validation error
            max_results=10,
        )

        # Execute search and expect validation error
        with pytest.raises(ValidationError, match="Search query cannot be empty"):
            await search_use_case.execute(request)

        # Wait for async event processing
        await asyncio.sleep(0.1)

        # Verify error event was published
        assert len(received_events) == 1
        assert isinstance(received_events[0], SearchFailedEvent)
        assert received_events[0].error_type == "ValidationError"

    async def test_dependency_container_operations(self, container):
        """Test dependency injection container functionality."""
        # Test retrieving registered dependencies
        event_bus = await container.get(EventBus)
        assert isinstance(event_bus, EventBus)

        cache = await container.get(MemoryCache)
        assert isinstance(cache, MemoryCache)

        # Test optional retrieval
        non_existent = await container.get_optional(str)
        assert non_existent is None

        # Test registration info
        registered_types = await container.get_registered_types()
        assert "EventBus" in registered_types
        assert "MemoryCache" in registered_types

    async def test_end_to_end_search_workflow(self, container, mock_geo_client):
        """Test complete end-to-end search workflow."""
        # Get dependencies from container
        event_bus = await container.get(EventBus)
        geo_repository = await container.get(GEOSearchRepository)

        # Create use case
        use_case = EnhancedSearchDatasetsUseCase(geo_repository, event_bus)

        # Track all events
        all_events = []

        async def track_events(event):
            all_events.append(event)

        await event_bus.subscribe(SearchStartedEvent, track_events)
        await event_bus.subscribe(SearchCompletedEvent, track_events)
        await event_bus.subscribe(SearchFailedEvent, track_events)

        # Execute search
        request = SearchRequestDTO(
            query="Alzheimer disease",
            max_results=5,
            search_type=SearchType.EXPRESSION,
        )

        response = await use_case.execute(request)

        # Wait for event processing
        await asyncio.sleep(0.1)

        # Verify complete workflow
        assert response.total_found == 2
        assert len(all_events) == 2  # Started + Completed
        assert isinstance(all_events[0], SearchStartedEvent)
        assert isinstance(all_events[1], SearchCompletedEvent)

        # Verify the mock was called with correct parameters
        mock_geo_client.search_datasets.assert_called_once_with(
            query="Alzheimer disease",
            max_results=5,
            search_type="expression",
        )

    async def test_cache_integration(self, memory_cache):
        """Test cache integration scenarios."""
        # Test caching search results
        search_key = "search:cancer:10"
        search_results = [
            {"geo_id": "GSE12345", "title": "Cancer Study 1"},
            {"geo_id": "GSE67890", "title": "Cancer Study 2"},
        ]

        # Cache results
        await memory_cache.set(search_key, search_results, ttl=300)

        # Retrieve from cache
        cached_results = await memory_cache.get(search_key)
        assert cached_results == search_results

        # Test cache statistics
        stats = await memory_cache.get_stats()
        assert stats["total_keys"] >= 1
        assert stats["active_keys"] >= 1

    async def test_error_handling_and_recovery(self, event_bus, mock_geo_client):
        """Test error handling and recovery mechanisms."""
        # Configure mock to raise an exception
        mock_geo_client.search_datasets.side_effect = Exception("API Error")

        # Create repository and use case
        repository = GEOSearchRepository(mock_geo_client)
        use_case = EnhancedSearchDatasetsUseCase(repository, event_bus)

        # Track error events
        error_events = []

        async def track_errors(event):
            error_events.append(event)

        await event_bus.subscribe(SearchFailedEvent, track_errors)

        # Execute search that should fail
        request = SearchRequestDTO(query="test", max_results=10)

        with pytest.raises(Exception, match="API Error"):
            await use_case.execute(request)

        # Wait for event processing
        await asyncio.sleep(0.1)

        # Verify error event was published
        assert len(error_events) == 1
        assert error_events[0].error_message == "GEO search failed: API Error"

    async def test_concurrent_operations(self, search_use_case, event_bus):
        """Test concurrent search operations."""
        # Track events from concurrent searches
        all_events = []

        async def track_all_events(event):
            all_events.append(event)

        await event_bus.subscribe(SearchStartedEvent, track_all_events)
        await event_bus.subscribe(SearchCompletedEvent, track_all_events)

        # Create multiple search requests
        requests = [SearchRequestDTO(query=f"query_{i}", max_results=5) for i in range(3)]

        # Execute searches concurrently
        tasks = [search_use_case.execute(request) for request in requests]
        responses = await asyncio.gather(*tasks)

        # Wait for all events to be processed
        await asyncio.sleep(0.2)

        # Verify all searches completed
        assert len(responses) == 3
        assert all(response.total_found == 2 for response in responses)

        # Verify events were published for all searches
        assert len(all_events) == 6  # 3 started + 3 completed events


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
