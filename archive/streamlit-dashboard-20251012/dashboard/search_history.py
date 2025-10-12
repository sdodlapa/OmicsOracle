"""
Search history and saved search management for dashboard.

Provides functionality to track search history, save search templates,
and enable quick re-execution of previous searches.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SearchRecord:
    """Record of a search execution."""

    query: str
    databases: List[str]
    year_range: tuple
    max_results: int
    timestamp: str
    result_count: int = 0
    execution_time: float = 0.0
    use_llm: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchRecord":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SearchTemplate:
    """Saved search template."""

    name: str
    description: str
    query: str
    databases: List[str]
    year_range: tuple
    max_results: int
    use_llm: bool = False
    tags: List[str] = None
    created_at: str = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchTemplate":
        """Create from dictionary."""
        return cls(**data)


class SearchHistoryManager:
    """Manages search history and saved templates."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize history manager.

        Args:
            storage_dir: Directory for storing history and templates
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".omicsoracle" / "dashboard"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.history_file = self.storage_dir / "search_history.json"
        self.templates_file = self.storage_dir / "search_templates.json"

        self._history: List[SearchRecord] = []
        self._templates: Dict[str, SearchTemplate] = {}

        self._load()

    def _load(self) -> None:
        """Load history and templates from disk."""
        # Load history
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    self._history = [SearchRecord.from_dict(record) for record in data]
            except Exception as e:
                print(f"Error loading search history: {e}")
                self._history = []

        # Load templates
        if self.templates_file.exists():
            try:
                with open(self.templates_file, "r") as f:
                    data = json.load(f)
                    self._templates = {
                        name: SearchTemplate.from_dict(template) for name, template in data.items()
                    }
            except Exception as e:
                print(f"Error loading search templates: {e}")
                self._templates = {}

    def _save(self) -> None:
        """Save history and templates to disk."""
        # Save history (keep last 100 searches)
        try:
            history_data = [record.to_dict() for record in self._history[-100:]]
            with open(self.history_file, "w") as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            print(f"Error saving search history: {e}")

        # Save templates
        try:
            templates_data = {name: template.to_dict() for name, template in self._templates.items()}
            with open(self.templates_file, "w") as f:
                json.dump(templates_data, f, indent=2)
        except Exception as e:
            print(f"Error saving search templates: {e}")

    def add_search(self, record: SearchRecord) -> None:
        """Add search to history.

        Args:
            record: Search record to add
        """
        self._history.append(record)
        self._save()

    def get_history(self, limit: int = 50) -> List[SearchRecord]:
        """Get recent search history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of recent search records
        """
        return list(reversed(self._history[-limit:]))

    def get_recent_queries(self, limit: int = 10) -> List[str]:
        """Get recent unique queries.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of recent unique queries
        """
        seen = set()
        queries = []

        for record in reversed(self._history):
            if record.query not in seen:
                seen.add(record.query)
                queries.append(record.query)

            if len(queries) >= limit:
                break

        return queries

    def search_history(self, query: str = None, database: str = None) -> List[SearchRecord]:
        """Search through history.

        Args:
            query: Filter by query text (substring match)
            database: Filter by database

        Returns:
            Filtered search records
        """
        results = self._history

        if query:
            query_lower = query.lower()
            results = [r for r in results if query_lower in r.query.lower()]

        if database:
            results = [r for r in results if database in r.databases]

        return list(reversed(results))

    def save_template(self, template: SearchTemplate) -> None:
        """Save a search template.

        Args:
            template: Template to save
        """
        self._templates[template.name] = template
        self._save()

    def get_template(self, name: str) -> Optional[SearchTemplate]:
        """Get a saved template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        return self._templates.get(name)

    def get_templates(self, tag: str = None) -> List[SearchTemplate]:
        """Get all templates, optionally filtered by tag.

        Args:
            tag: Filter by tag

        Returns:
            List of templates
        """
        templates = list(self._templates.values())

        if tag:
            templates = [t for t in templates if tag in t.tags]

        return sorted(templates, key=lambda t: t.created_at, reverse=True)

    def delete_template(self, name: str) -> bool:
        """Delete a saved template.

        Args:
            name: Template name

        Returns:
            True if deleted, False if not found
        """
        if name in self._templates:
            del self._templates[name]
            self._save()
            return True
        return False

    def clear_history(self) -> None:
        """Clear all search history."""
        self._history = []
        self._save()

    def get_stats(self) -> Dict[str, Any]:
        """Get search history statistics.

        Returns:
            Dictionary with statistics
        """
        if not self._history:
            return {
                "total_searches": 0,
                "unique_queries": 0,
                "total_results": 0,
                "avg_results": 0,
                "most_searched_query": None,
                "most_used_database": None,
            }

        queries = [r.query for r in self._history]
        databases = [db for r in self._history for db in r.databases]

        from collections import Counter

        query_counts = Counter(queries)
        db_counts = Counter(databases)

        return {
            "total_searches": len(self._history),
            "unique_queries": len(set(queries)),
            "total_results": sum(r.result_count for r in self._history),
            "avg_results": sum(r.result_count for r in self._history) / len(self._history),
            "most_searched_query": query_counts.most_common(1)[0][0] if query_counts else None,
            "most_used_database": db_counts.most_common(1)[0][0] if db_counts else None,
        }
