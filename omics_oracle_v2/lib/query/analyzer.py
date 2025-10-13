"""
Query Analyzer for OmicsOracle Unified Pipeline

Simple query type detection and routing logic.
Determines whether a query is:
- GEO ID (GSE12345, GPL570, etc.)
- GEO keyword search (dataset, series, etc.)
- Publication search (papers, articles, etc.)
- Auto (determine from context)
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List


class SearchType(Enum):
    """Query search type enumeration."""

    GEO_ID = "geo_id"  # Direct GEO ID lookup
    GEO = "geo"  # GEO dataset keyword search
    PUBLICATIONS = "publications"  # Publication search
    HYBRID = "hybrid"  # Search both GEO and publications
    AUTO = "auto"  # Auto-detect from query


@dataclass
class QueryInfo:
    """
    Query analysis result.

    Attributes:
        original_query: The original user query
        search_type: Detected search type
        geo_ids: Extracted GEO IDs (if any)
        is_geo_id: True if query contains only GEO IDs
        confidence: Confidence score for search type detection (0-1)
    """

    original_query: str
    search_type: SearchType
    geo_ids: List[str]
    is_geo_id: bool
    confidence: float = 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "original_query": self.original_query,
            "search_type": self.search_type.value,
            "geo_ids": self.geo_ids,
            "is_geo_id": self.is_geo_id,
            "confidence": self.confidence,
        }


class QueryAnalyzer:
    """
    Simple query analyzer for routing.

    Uses pattern matching and keyword detection to determine
    query type and route to appropriate search pipeline.

    NO complex NLP or entity extraction (handled by QueryOptimizer).
    """

    # GEO ID patterns
    GEO_ID_PATTERN = re.compile(r"\b(GSE|GPL|GSM|GDS)\d+\b", re.IGNORECASE)

    # Keyword sets for classification
    GEO_KEYWORDS = {
        "dataset",
        "datasets",
        "geo",
        "series",
        "samples",
        "gse",
        "gpl",
        "gsm",
        "gds",
        "microarray",
        "rna-seq",
        "expression data",
        "gene expression",
        "sequencing data",
    }

    PUBLICATION_KEYWORDS = {
        "paper",
        "papers",
        "publication",
        "publications",
        "article",
        "articles",
        "journal",
        "study",
        "studies",
        "pmid",
        "doi",
        "pubmed",
        "research",
        "literature",
    }

    def __init__(self):
        """Initialize query analyzer."""

    def analyze(self, query: str) -> QueryInfo:
        """
        Analyze query and determine search type.

        Logic:
        1. Check for GEO ID patterns (GSE12345, GPL570, etc.)
        2. Check for explicit keywords (dataset, paper, etc.)
        3. Default to AUTO (let pipeline decide)

        Args:
            query: User query string

        Returns:
            QueryInfo with detected search type and metadata
        """
        if not query or not query.strip():
            return QueryInfo(
                original_query=query,
                search_type=SearchType.AUTO,
                geo_ids=[],
                is_geo_id=False,
                confidence=0.0,
            )

        query_cleaned = query.strip()

        # Step 1: Check for GEO IDs
        geo_ids = self._extract_geo_ids(query_cleaned)

        if geo_ids:
            # Check if query ONLY contains GEO IDs (no other text)
            non_id_text = self.GEO_ID_PATTERN.sub("", query_cleaned).strip()
            non_id_text = re.sub(r"[,;\s]+", "", non_id_text)  # Remove separators

            if not non_id_text or len(non_id_text) < 3:
                # Pure GEO ID query
                return QueryInfo(
                    original_query=query,
                    search_type=SearchType.GEO_ID,
                    geo_ids=geo_ids,
                    is_geo_id=True,
                    confidence=1.0,
                )
            else:
                # GEO IDs mixed with keywords - treat as GEO search
                return QueryInfo(
                    original_query=query,
                    search_type=SearchType.GEO,
                    geo_ids=geo_ids,
                    is_geo_id=False,
                    confidence=0.9,
                )

        # Step 2: Check for explicit keywords
        query_lower = query_cleaned.lower()

        # Count keyword matches
        geo_matches = sum(1 for kw in self.GEO_KEYWORDS if kw in query_lower)
        pub_matches = sum(1 for kw in self.PUBLICATION_KEYWORDS if kw in query_lower)

        # Determine search type based on keyword dominance
        if geo_matches > pub_matches and geo_matches > 0:
            confidence = min(0.7 + (geo_matches * 0.1), 1.0)
            return QueryInfo(
                original_query=query,
                search_type=SearchType.GEO,
                geo_ids=[],
                is_geo_id=False,
                confidence=confidence,
            )

        elif pub_matches > geo_matches and pub_matches > 0:
            confidence = min(0.7 + (pub_matches * 0.1), 1.0)
            return QueryInfo(
                original_query=query,
                search_type=SearchType.PUBLICATIONS,
                geo_ids=[],
                is_geo_id=False,
                confidence=confidence,
            )

        else:
            # No clear keywords - auto-detect
            # Default to publications unless query is very short
            if len(query_cleaned.split()) <= 2:
                # Short query - might be a disease/gene name
                search_type = SearchType.AUTO
                confidence = 0.5
            else:
                # Longer query - likely publication search
                search_type = SearchType.PUBLICATIONS
                confidence = 0.6

            return QueryInfo(
                original_query=query,
                search_type=search_type,
                geo_ids=[],
                is_geo_id=False,
                confidence=confidence,
            )

    def _extract_geo_ids(self, query: str) -> List[str]:
        """
        Extract GEO IDs from query.

        Supports:
        - GSE (Series)
        - GPL (Platform)
        - GSM (Sample)
        - GDS (Dataset)

        Args:
            query: Query string

        Returns:
            List of extracted GEO IDs (uppercase)
        """
        matches = self.GEO_ID_PATTERN.findall(query)

        # Reconstruct full IDs (pattern returns prefix separately)
        geo_ids = []
        for match in self.GEO_ID_PATTERN.finditer(query):
            geo_id = match.group(0).upper()
            if geo_id not in geo_ids:
                geo_ids.append(geo_id)

        return geo_ids

    def is_geo_query(self, query: str) -> bool:
        """
        Quick check if query is GEO-related.

        Args:
            query: Query string

        Returns:
            True if query appears to be GEO-related
        """
        info = self.analyze(query)
        return info.search_type in (SearchType.GEO_ID, SearchType.GEO)

    def is_publication_query(self, query: str) -> bool:
        """
        Quick check if query is publication-related.

        Args:
            query: Query string

        Returns:
            True if query appears to be publication-related
        """
        info = self.analyze(query)
        return info.search_type == SearchType.PUBLICATIONS


# Example usage and tests
if __name__ == "__main__":
    analyzer = QueryAnalyzer()

    # Test cases
    test_queries = [
        "GSE12345",
        "GSE12345 GSE67890",
        "breast cancer dataset",
        "alzheimer's disease papers",
        "GSE12345 breast cancer",
        "diabetes",
        "APOE gene expression in alzheimer's disease",
        "recent publications on CRISPR",
    ]

    print("Query Analyzer Test Results:")
    print("=" * 80)

    for query in test_queries:
        result = analyzer.analyze(query)
        print(f"\nQuery: '{query}'")
        print(f"  Type: {result.search_type.value}")
        print(f"  GEO IDs: {result.geo_ids}")
        print(f"  Is GEO ID: {result.is_geo_id}")
        print(f"  Confidence: {result.confidence:.2f}")
