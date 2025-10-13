"""
Citations module.

This package handles citation discovery and analysis for publications.

Components:
- discovery/: Citation discovery logic
- clients/: Citation API clients (OpenAlex, Semantic Scholar, Google Scholar)
"""

# Lazy imports to avoid circular dependencies
__all__ = [
    "CitationFinder",
]


def __getattr__(name):
    if name == "CitationFinder":
        from omics_oracle_v2.lib.citations.discovery.finder import CitationFinder

        return CitationFinder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
