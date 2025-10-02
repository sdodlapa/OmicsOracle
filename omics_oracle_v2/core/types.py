"""
Type definitions and protocols for OmicsOracle v2.

Provides common type aliases and protocol classes used across the codebase
for better type safety and code documentation.
"""

from typing import Any, Dict, List, Protocol

# Type aliases for common patterns
JSON = Dict[str, Any]
EntityDict = Dict[str, Any]
MetadataDict = Dict[str, str]


class Summarizer(Protocol):
    """Protocol for summarization services."""

    def summarize(self, text: str) -> str:
        """Generate a summary from text."""
        ...


class EntityExtractor(Protocol):
    """Protocol for entity extraction services."""

    def extract_entities(self, text: str) -> List[Any]:
        """Extract entities from text."""
        ...
