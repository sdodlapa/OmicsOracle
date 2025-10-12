"""Tests for search history management."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from omics_oracle_v2.lib.dashboard.search_history import SearchHistoryManager, SearchRecord, SearchTemplate


@pytest.fixture
def temp_storage():
    """Temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def manager(temp_storage):
    """Search history manager with temp storage."""
    return SearchHistoryManager(storage_dir=temp_storage)


@pytest.fixture
def sample_record():
    """Sample search record."""
    return SearchRecord(
        query="BRCA1 mutations",
        databases=["pubmed", "pmc"],
        year_range=(2020, 2024),
        max_results=100,
        timestamp=datetime.now().isoformat(),
        result_count=42,
        execution_time=1.5,
        use_llm=False,
    )


@pytest.fixture
def sample_template():
    """Sample search template."""
    return SearchTemplate(
        name="Cancer Research",
        description="Standard cancer biomarker search",
        query="cancer biomarkers",
        databases=["pubmed"],
        year_range=(2015, 2024),
        max_results=200,
        use_llm=True,
        tags=["cancer", "biomarkers"],
    )


def test_search_record_creation(sample_record):
    """Test creating a search record."""
    assert sample_record.query == "BRCA1 mutations"
    assert sample_record.databases == ["pubmed", "pmc"]
    assert sample_record.result_count == 42
    assert sample_record.execution_time == 1.5


def test_search_record_serialization(sample_record):
    """Test search record to/from dict."""
    data = sample_record.to_dict()
    assert isinstance(data, dict)
    assert data["query"] == "BRCA1 mutations"

    restored = SearchRecord.from_dict(data)
    assert restored.query == sample_record.query
    assert restored.databases == sample_record.databases


def test_search_template_creation(sample_template):
    """Test creating a search template."""
    assert sample_template.name == "Cancer Research"
    assert sample_template.description == "Standard cancer biomarker search"
    assert sample_template.tags == ["cancer", "biomarkers"]
    assert sample_template.created_at is not None


def test_search_template_serialization(sample_template):
    """Test search template to/from dict."""
    data = sample_template.to_dict()
    assert isinstance(data, dict)
    assert data["name"] == "Cancer Research"

    restored = SearchTemplate.from_dict(data)
    assert restored.name == sample_template.name
    assert restored.tags == sample_template.tags


def test_manager_initialization(temp_storage):
    """Test manager initialization."""
    manager = SearchHistoryManager(storage_dir=temp_storage)
    assert manager.storage_dir == temp_storage
    assert manager.history_file == temp_storage / "search_history.json"
    assert manager.templates_file == temp_storage / "search_templates.json"
    assert manager.storage_dir.exists()


def test_add_and_get_history(manager, sample_record):
    """Test adding and retrieving search history."""
    manager.add_search(sample_record)

    history = manager.get_history()
    assert len(history) == 1
    assert history[0].query == "BRCA1 mutations"


def test_history_limit(manager):
    """Test history retrieval limit."""
    # Add multiple records
    for i in range(20):
        record = SearchRecord(
            query=f"Query {i}",
            databases=["pubmed"],
            year_range=(2020, 2024),
            max_results=100,
            timestamp=datetime.now().isoformat(),
        )
        manager.add_search(record)

    # Get limited history
    history = manager.get_history(limit=10)
    assert len(history) == 10
    # Should be most recent first
    assert history[0].query == "Query 19"


def test_get_recent_queries(manager):
    """Test getting recent unique queries."""
    # Add records with some duplicate queries
    queries = ["Query A", "Query B", "Query A", "Query C", "Query B", "Query D"]
    for query in queries:
        record = SearchRecord(
            query=query,
            databases=["pubmed"],
            year_range=(2020, 2024),
            max_results=100,
            timestamp=datetime.now().isoformat(),
        )
        manager.add_search(record)

    recent = manager.get_recent_queries(limit=10)
    # Should have unique queries only
    assert len(recent) == 4
    # Should be in reverse order of last occurrence
    assert recent == ["Query D", "Query B", "Query C", "Query A"]


def test_search_history_by_query(manager):
    """Test searching history by query text."""
    # Add records with different queries
    for query in ["cancer biomarkers", "diabetes genetics", "cancer treatment"]:
        record = SearchRecord(
            query=query,
            databases=["pubmed"],
            year_range=(2020, 2024),
            max_results=100,
            timestamp=datetime.now().isoformat(),
        )
        manager.add_search(record)

    # Search for "cancer"
    results = manager.search_history(query="cancer")
    assert len(results) == 2
    assert all("cancer" in r.query for r in results)


def test_search_history_by_database(manager):
    """Test searching history by database."""
    # Add records with different databases
    databases_list = [["pubmed"], ["pmc"], ["pubmed", "pmc"]]
    for dbs in databases_list:
        record = SearchRecord(
            query="test query",
            databases=dbs,
            year_range=(2020, 2024),
            max_results=100,
            timestamp=datetime.now().isoformat(),
        )
        manager.add_search(record)

    # Search for pubmed
    results = manager.search_history(database="pubmed")
    assert len(results) == 2


def test_save_and_get_template(manager, sample_template):
    """Test saving and retrieving templates."""
    manager.save_template(sample_template)

    retrieved = manager.get_template("Cancer Research")
    assert retrieved is not None
    assert retrieved.name == "Cancer Research"
    assert retrieved.query == "cancer biomarkers"


def test_get_templates(manager):
    """Test getting all templates."""
    # Create multiple templates
    for i in range(3):
        template = SearchTemplate(
            name=f"Template {i}",
            description=f"Description {i}",
            query=f"query {i}",
            databases=["pubmed"],
            year_range=(2020, 2024),
            max_results=100,
        )
        manager.save_template(template)

    templates = manager.get_templates()
    assert len(templates) == 3


def test_get_templates_by_tag(manager):
    """Test filtering templates by tag."""
    # Create templates with different tags
    template1 = SearchTemplate(
        name="Template 1",
        description="Description",
        query="query",
        databases=["pubmed"],
        year_range=(2020, 2024),
        max_results=100,
        tags=["cancer"],
    )
    template2 = SearchTemplate(
        name="Template 2",
        description="Description",
        query="query",
        databases=["pubmed"],
        year_range=(2020, 2024),
        max_results=100,
        tags=["diabetes"],
    )
    template3 = SearchTemplate(
        name="Template 3",
        description="Description",
        query="query",
        databases=["pubmed"],
        year_range=(2020, 2024),
        max_results=100,
        tags=["cancer", "genetics"],
    )

    manager.save_template(template1)
    manager.save_template(template2)
    manager.save_template(template3)

    cancer_templates = manager.get_templates(tag="cancer")
    assert len(cancer_templates) == 2


def test_delete_template(manager, sample_template):
    """Test deleting a template."""
    manager.save_template(sample_template)
    assert manager.get_template("Cancer Research") is not None

    result = manager.delete_template("Cancer Research")
    assert result is True
    assert manager.get_template("Cancer Research") is None

    # Try deleting non-existent template
    result = manager.delete_template("Non-existent")
    assert result is False


def test_clear_history(manager, sample_record):
    """Test clearing history."""
    manager.add_search(sample_record)
    assert len(manager.get_history()) == 1

    manager.clear_history()
    assert len(manager.get_history()) == 0


def test_get_stats_empty(manager):
    """Test getting stats with empty history."""
    stats = manager.get_stats()
    assert stats["total_searches"] == 0
    assert stats["unique_queries"] == 0
    assert stats["total_results"] == 0


def test_get_stats_with_data(manager):
    """Test getting stats with data."""
    # Add multiple records
    for i in range(5):
        record = SearchRecord(
            query="Query A" if i < 3 else "Query B",
            databases=["pubmed"],
            year_range=(2020, 2024),
            max_results=100,
            timestamp=datetime.now().isoformat(),
            result_count=10,
        )
        manager.add_search(record)

    stats = manager.get_stats()
    assert stats["total_searches"] == 5
    assert stats["unique_queries"] == 2
    assert stats["total_results"] == 50
    assert stats["avg_results"] == 10.0
    assert stats["most_searched_query"] == "Query A"
    assert stats["most_used_database"] == "pubmed"


def test_persistence(temp_storage, sample_record, sample_template):
    """Test that data persists across manager instances."""
    # Create manager and add data
    manager1 = SearchHistoryManager(storage_dir=temp_storage)
    manager1.add_search(sample_record)
    manager1.save_template(sample_template)

    # Create new manager instance
    manager2 = SearchHistoryManager(storage_dir=temp_storage)

    # Verify data was loaded
    history = manager2.get_history()
    assert len(history) == 1
    assert history[0].query == "BRCA1 mutations"

    template = manager2.get_template("Cancer Research")
    assert template is not None
    assert template.query == "cancer biomarkers"


def test_history_size_limit(temp_storage):
    """Test that history is limited to last 100 searches."""
    manager = SearchHistoryManager(storage_dir=temp_storage)

    # Add 150 records
    for i in range(150):
        record = SearchRecord(
            query=f"Query {i}",
            databases=["pubmed"],
            year_range=(2020, 2024),
            max_results=100,
            timestamp=datetime.now().isoformat(),
        )
        manager.add_search(record)

    # Create new manager to load from disk
    manager2 = SearchHistoryManager(storage_dir=temp_storage)
    history = manager2.get_history(limit=200)

    # Should only have last 100
    assert len(history) <= 100
    # Should have most recent ones
    assert history[0].query == "Query 149"


def test_error_handling_corrupted_history(temp_storage):
    """Test error handling with corrupted history file."""
    manager = SearchHistoryManager(storage_dir=temp_storage)

    # Write corrupted JSON
    with open(manager.history_file, "w") as f:
        f.write("not valid json{{{")

    # Create new manager - should handle error gracefully
    manager2 = SearchHistoryManager(storage_dir=temp_storage)
    assert len(manager2.get_history()) == 0


def test_error_handling_corrupted_templates(temp_storage):
    """Test error handling with corrupted templates file."""
    manager = SearchHistoryManager(storage_dir=temp_storage)

    # Write corrupted JSON
    with open(manager.templates_file, "w") as f:
        f.write("not valid json{{{")

    # Create new manager - should handle error gracefully
    manager2 = SearchHistoryManager(storage_dir=temp_storage)
    assert len(manager2.get_templates()) == 0
