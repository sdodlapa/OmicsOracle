"""
Query Expansion Module

Automatically expand user queries with biomedical synonyms, organism mappings,
and technique abbreviations to improve search recall.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QueryExpansionConfig(BaseModel):
    """Configuration for query expansion."""

    enabled: bool = Field(default=True, description="Enable query expansion")
    max_expansions: int = Field(default=5, description="Maximum number of expansions per term")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for expansion")
    synonym_database: str = Field(
        default="omics_oracle_v2/lib/nlp/synonyms.json",
        description="Path to synonym database",
    )


@dataclass
class ExpandedQuery:
    """Result of query expansion."""

    original: str
    expanded_terms: List[str] = field(default_factory=list)
    organism_mappings: Dict[str, str] = field(default_factory=dict)
    technique_mappings: Dict[str, List[str]] = field(default_factory=dict)
    concept_mappings: Dict[str, List[str]] = field(default_factory=dict)
    all_terms: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate all terms after initialization."""
        if not self.all_terms:
            self.all_terms = self._compute_all_terms()

    def _compute_all_terms(self) -> List[str]:
        """Compute all unique terms including original and expansions."""
        terms = {self.original}
        terms.update(self.expanded_terms)

        for synonyms in self.organism_mappings.values():
            if isinstance(synonyms, str):
                terms.add(synonyms)
            else:
                terms.update(synonyms)

        for synonyms_list in self.technique_mappings.values():
            terms.update(synonyms_list)

        for synonyms_list in self.concept_mappings.values():
            terms.update(synonyms_list)

        return sorted(terms)


class QueryExpander:
    """
    Expand queries with biomedical synonyms.

    Enhances search recall by automatically finding:
    - Technique synonyms (ATAC-seq -> chromatin accessibility)
    - Organism mappings (human -> Homo sapiens)
    - Concept expansions (gene expression -> transcription)
    - Disease synonyms (diabetes -> diabetes mellitus)
    """

    def __init__(self, config: Optional[QueryExpansionConfig] = None):
        """
        Initialize query expander.

        Args:
            config: Configuration for query expansion
        """
        self.config = config or QueryExpansionConfig()
        self.synonyms: Dict[str, Dict[str, List[str]]] = {}
        self._load_synonyms()

    def _load_synonyms(self) -> None:
        """Load synonym database from JSON file."""
        synonym_path = Path(self.config.synonym_database)

        if not synonym_path.exists():
            # Try relative to project root
            project_root = Path(__file__).parents[3]
            synonym_path = project_root / self.config.synonym_database

        if not synonym_path.exists():
            raise FileNotFoundError(f"Synonym database not found: {self.config.synonym_database}")

        with open(synonym_path, "r") as f:
            self.synonyms = json.load(f)

    def expand_query(self, query: str) -> ExpandedQuery:
        """
        Expand query with synonyms and mappings.

        Args:
            query: Original search query

        Returns:
            ExpandedQuery with all expansions and mappings

        Example:
            >>> expander = QueryExpander()
            >>> result = expander.expand_query("human ATAC-seq")
            >>> print(result.organism_mappings)
            {'human': 'Homo sapiens'}
            >>> print(result.technique_mappings)
            {'ATAC-seq': ['chromatin accessibility', 'open chromatin', ...]}
        """
        if not self.config.enabled:
            return ExpandedQuery(original=query)

        query_lower = query.lower()

        # Find organism mappings
        organism_mappings = self._find_organisms(query_lower)

        # Find technique mappings
        technique_mappings = self._find_techniques(query_lower)

        # Find concept mappings
        concept_mappings = self._find_concepts(query_lower)

        # Find disease mappings
        disease_mappings = self._find_diseases(query_lower)

        # Find tissue mappings
        tissue_mappings = self._find_tissues(query_lower)

        # Combine all expansions
        expanded_terms = set()
        for mappings in [
            technique_mappings,
            concept_mappings,
            disease_mappings,
            tissue_mappings,
        ]:
            for synonyms in mappings.values():
                expanded_terms.update(synonyms[: self.config.max_expansions])

        # Add organism scientific names
        for org_name in organism_mappings.values():
            if isinstance(org_name, list):
                expanded_terms.update(org_name[: self.config.max_expansions])
            else:
                expanded_terms.add(org_name)

        return ExpandedQuery(
            original=query,
            expanded_terms=sorted(expanded_terms),
            organism_mappings=organism_mappings,
            technique_mappings=technique_mappings,
            concept_mappings={**concept_mappings, **disease_mappings, **tissue_mappings},
        )

    def _find_organisms(self, query: str) -> Dict[str, str]:
        """Find organism names in query and map to scientific names."""
        mappings = {}

        if "organisms" not in self.synonyms:
            return mappings

        for common_name, scientific_names in self.synonyms["organisms"].items():
            # Check if common name appears in query
            if re.search(r"\b" + re.escape(common_name) + r"\b", query, re.IGNORECASE):
                # Use first scientific name (most common)
                mappings[common_name] = scientific_names[0]

        return mappings

    def _find_techniques(self, query: str) -> Dict[str, List[str]]:
        """Find sequencing/analysis techniques in query."""
        mappings = {}

        if "techniques" not in self.synonyms:
            return mappings

        for technique, synonyms in self.synonyms["techniques"].items():
            # Check for exact technique name (case-insensitive)
            if re.search(r"\b" + re.escape(technique) + r"\b", query, re.IGNORECASE):
                mappings[technique] = synonyms

        return mappings

    def _find_concepts(self, query: str) -> Dict[str, List[str]]:
        """Find biological concepts in query."""
        mappings = {}

        if "concepts" not in self.synonyms:
            return mappings

        for concept, synonyms in self.synonyms["concepts"].items():
            # Check for concept (may be multi-word)
            if re.search(r"\b" + re.escape(concept) + r"\b", query, re.IGNORECASE):
                mappings[concept] = synonyms

        return mappings

    def _find_diseases(self, query: str) -> Dict[str, List[str]]:
        """Find disease names in query."""
        mappings = {}

        if "diseases" not in self.synonyms:
            return mappings

        for disease, synonyms in self.synonyms["diseases"].items():
            if re.search(r"\b" + re.escape(disease) + r"\b", query, re.IGNORECASE):
                mappings[disease] = synonyms

        return mappings

    def _find_tissues(self, query: str) -> Dict[str, List[str]]:
        """Find tissue types in query."""
        mappings = {}

        if "tissues" not in self.synonyms:
            return mappings

        for tissue, synonyms in self.synonyms["tissues"].items():
            if re.search(r"\b" + re.escape(tissue) + r"\b", query, re.IGNORECASE):
                mappings[tissue] = synonyms

        return mappings

    def expand_for_search(self, query: str) -> str:
        """
        Expand query and return as search string.

        Combines original query with top expansions into a single string
        suitable for search.

        Args:
            query: Original query

        Returns:
            Expanded query string with synonyms

        Example:
            >>> expander = QueryExpander()
            >>> expanded = expander.expand_for_search("human ATAC-seq")
            >>> print(expanded)
            "human ATAC-seq Homo sapiens chromatin accessibility open chromatin"
        """
        expansion = self.expand_query(query)

        # Start with original
        terms = [expansion.original]

        # Add top expansions (limited to avoid query bloat)
        terms.extend(expansion.expanded_terms[: self.config.max_expansions])

        return " ".join(terms)

    def get_expansion_summary(self, query: str) -> Dict[str, any]:
        """
        Get human-readable summary of query expansion.

        Args:
            query: Original query

        Returns:
            Dictionary with expansion details

        Example:
            >>> expander = QueryExpander()
            >>> summary = expander.get_expansion_summary("human ATAC-seq cancer")
            >>> print(summary)
            {
                'original': 'human ATAC-seq cancer',
                'organisms_found': ['human -> Homo sapiens'],
                'techniques_found': ['ATAC-seq -> chromatin accessibility, ...'],
                'concepts_found': ['cancer -> tumor, malignancy, ...'],
                'total_expansions': 12
            }
        """
        expansion = self.expand_query(query)

        return {
            "original": expansion.original,
            "organisms_found": [f"{k} -> {v}" for k, v in expansion.organism_mappings.items()],
            "techniques_found": [
                f"{k} -> {', '.join(v[:3])}..." if len(v) > 3 else f"{k} -> {', '.join(v)}"
                for k, v in expansion.technique_mappings.items()
            ],
            "concepts_found": [
                f"{k} -> {', '.join(v[:3])}..." if len(v) > 3 else f"{k} -> {', '.join(v)}"
                for k, v in expansion.concept_mappings.items()
            ],
            "total_expansions": len(expansion.all_terms) - 1,  # Exclude original
            "all_terms": expansion.all_terms,
        }


def main():
    """Demo query expansion."""
    expander = QueryExpander()

    test_queries = [
        "human ATAC-seq",
        "mouse RNA-seq cancer",
        "chromatin accessibility diabetes",
        "single cell gene expression heart",
    ]

    print("=" * 70)
    print("QUERY EXPANSION DEMONSTRATION")
    print("=" * 70)
    print()

    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 70)

        summary = expander.get_expansion_summary(query)

        if summary["organisms_found"]:
            print(f"Organisms: {', '.join(summary['organisms_found'])}")

        if summary["techniques_found"]:
            print(f"Techniques: {', '.join(summary['techniques_found'])}")

        if summary["concepts_found"]:
            print(f"Concepts: {', '.join(summary['concepts_found'])}")

        print(f"Total expansions: {summary['total_expansions']}")
        print(f"Expanded query: {expander.expand_for_search(query)}")
        print()


if __name__ == "__main__":
    main()
