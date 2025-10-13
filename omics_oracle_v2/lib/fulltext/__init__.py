"""
Full-text retrieval module.

This package handles retrieving full-text content for publications
from various sources including open access repositories, institutional
access, and web scraping.

Components:
- manager: Coordinates full-text retrieval from multiple sources
- sources/: Individual source clients (Sci-Hub, LibGen, etc.)
"""

# Avoid circular imports - use lazy imports
__all__ = [
    "FullTextManager",
]


def __getattr__(name):
    if name == "FullTextManager":
        from omics_oracle_v2.lib.fulltext.manager import FullTextManager

        return FullTextManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
