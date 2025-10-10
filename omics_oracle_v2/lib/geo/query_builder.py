"""
GEO search query builder and optimizer.

Transforms natural language queries into optimized NCBI E-utilities search syntax
for comprehensive dataset discovery.
"""

import logging
import re
from typing import List, Set

logger = logging.getLogger(__name__)

# Common stop words to remove from queries
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "will",
    "with",
    "data",
    "dataset",
    "datasets",
    "analysis",
    "study",
    "studies",
    "using",
    "based",
    "joint",
    "profiling",
    "integrated",
    "combined",
    "multi",
    "comprehensive",
}

# GEO-specific field mappings
GEO_FIELDS = {
    "title": "[Title]",
    "abstract": "[Description]",
    "organism": "[Organism]",
    "type": "[Entry Type]",
    "platform": "[Platform]",
}

# Common technique synonyms/variants
TECHNIQUE_SYNONYMS = {
    "hic": ["HiC", "Hi-C", "3C", "chromosome conformation"],
    "chip-seq": ["ChIP-seq", "ChIPseq", "ChIP seq", "chromatin immunoprecipitation"],
    "rna-seq": ["RNA-seq", "RNAseq", "RNA seq", "transcriptome"],
    "atac-seq": ["ATAC-seq", "ATACseq", "ATAC seq"],
    "wgbs": ["WGBS", "whole genome bisulfite", "bisulfite sequencing"],
}


class GEOQueryBuilder:
    """
    Build optimized GEO search queries from natural language.

    Features:
    - Extracts key scientific terms
    - Removes stop words
    - Adds technique synonyms
    - Optimizes for GEO database structure
    - Balances precision vs recall
    """

    def __init__(self):
        self.stop_words = STOP_WORDS
        self.technique_synonyms = TECHNIQUE_SYNONYMS

    def build_query(
        self, query: str, mode: str = "balanced", add_synonyms: bool = True, organism: str = None
    ) -> str:
        """
        Build optimized GEO search query.

        Args:
            query: Natural language query
            mode: Search mode - 'precise', 'balanced', or 'broad'
            add_synonyms: Whether to add technique synonyms
            organism: Optional organism filter (e.g., 'human', 'mouse')

        Returns:
            Optimized NCBI E-utilities query string

        Examples:
            >>> builder = GEOQueryBuilder()
            >>> builder.build_query("Joint profiling of DNA methylation and HiC data")
            'DNA methylation AND (HiC OR Hi-C OR "chromosome conformation")'

            >>> builder.build_query("breast cancer RNA-seq", organism='human')
            'breast cancer AND (RNA-seq OR RNAseq OR transcriptome) AND Homo sapiens[Organism]'
        """
        # Step 1: Extract keywords
        keywords = self._extract_keywords(query)

        if not keywords:
            logger.warning(f"No keywords extracted from query: {query}")
            return query  # Return original if extraction fails

        # Step 2: Build core query based on mode
        if mode == "precise":
            core_query = self._build_precise_query(keywords)
        elif mode == "broad":
            core_query = self._build_broad_query(keywords)
        else:  # balanced (default)
            core_query = self._build_balanced_query(keywords, add_synonyms)

        # Step 3: Add organism filter if specified
        if organism:
            organism_name = self._map_organism(organism)
            core_query = f"({core_query}) AND {organism_name}[Organism]"

        logger.info(f"Query optimization: '{query}' -> '{core_query}'")
        return core_query

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from query.

        Removes stop words, preserves scientific terms, handles hyphenated terms.
        """
        # Normalize whitespace
        query = re.sub(r"\s+", " ", query.strip())

        # Tokenize while preserving hyphenated terms
        tokens = re.findall(r"\b[\w-]+\b", query.lower())

        # Filter stop words (but keep if part of compound term)
        keywords = []
        for i, token in enumerate(tokens):
            # Keep hyphenated terms (RNA-seq, Hi-C, etc.)
            if "-" in token:
                keywords.append(token)
                continue

            # Skip stop words
            if token in self.stop_words:
                continue

            # Keep scientific terms (usually longer)
            if len(token) >= 3:
                keywords.append(token)

        return keywords

    def _build_precise_query(self, keywords: List[str]) -> str:
        """
        Build precise query requiring all keywords (high precision, low recall).

        Example: 'DNA AND methylation AND HiC AND chromatin'
        """
        return " AND ".join(keywords)

    def _build_broad_query(self, keywords: List[str]) -> str:
        """
        Build broad query accepting any keyword (low precision, high recall).

        Example: 'DNA OR methylation OR HiC OR chromatin'
        """
        return " OR ".join(keywords)

    def _build_balanced_query(self, keywords: List[str], add_synonyms: bool = True) -> str:
        """
        Build balanced query grouping related terms (balanced precision/recall).

        Strategy:
        - Extract core concepts (nouns, techniques)
        - Group technique synonyms with OR
        - Connect concept groups with AND
        - Prefer Title field for highest relevance

        Example Input: ['dna', 'methylation', 'hic']
        Example Output: '"DNA methylation"[Title] AND (HiC[Title] OR Hi-C[Title] OR "chromosome conformation"[Title])'

        This gives ~10-50 highly relevant results vs 1 (too strict) or 100+ (too broad)
        """
        # Identify techniques in keywords
        technique_groups = []
        regular_keywords = []
        used_keywords = set()

        for keyword in keywords:
            if keyword in used_keywords:
                continue

            # Check if this is a known technique
            is_technique = False
            if add_synonyms:
                for tech_name, synonyms in self.technique_synonyms.items():
                    if keyword in tech_name or any(keyword in syn.lower() for syn in synonyms):
                        # Create OR group with synonyms, restricted to Title field
                        synonym_list = [keyword] + [s for s in synonyms if s.lower() != keyword]
                        # Apply field restriction to each synonym
                        field_synonyms = [
                            f"{syn}[Title]" if " " not in syn else f'"{syn}"[Title]' for syn in synonym_list
                        ]
                        technique_groups.append(f"({' OR '.join(field_synonyms)})")
                        used_keywords.add(keyword)
                        is_technique = True
                        break

            if not is_technique:
                regular_keywords.append(keyword)
                used_keywords.add(keyword)

        # Group regular keywords into concepts (e.g., "DNA methylation")
        # Look for adjacent scientific terms and group them
        concept_groups = []
        i = 0
        while i < len(regular_keywords):
            # Check if we can form a multi-word concept
            if i + 1 < len(regular_keywords):
                two_word = f"{regular_keywords[i]} {regular_keywords[i+1]}"
                # Check if this forms a known scientific term
                if self._is_scientific_concept(two_word):
                    concept_groups.append(f'"{two_word}"[Title]')
                    i += 2
                    continue

            # Single word concept
            if len(regular_keywords[i]) > 2:  # Skip very short words
                concept_groups.append(f"{regular_keywords[i]}[Title]")
            i += 1

        # Combine into query with AND logic
        query_parts = concept_groups + technique_groups

        if len(query_parts) == 1:
            return query_parts[0]
        elif len(query_parts) == 0:
            # Fallback: use original keywords without field restriction
            return " AND ".join(keywords)
        else:
            return " AND ".join(query_parts)

    def _is_scientific_concept(self, phrase: str) -> bool:
        """
        Check if a two-word phrase forms a common scientific concept.

        Common patterns:
        - DNA/RNA + term (DNA methylation, RNA sequencing)
        - Technique + data (ChIP data, ATAC data)
        - Biological + process (cell differentiation, gene expression)
        """
        scientific_concepts = {
            "dna methylation",
            "rna sequencing",
            "gene expression",
            "chromatin accessibility",
            "histone modification",
            "transcription factor",
            "cell differentiation",
            "genome organization",
            "protein binding",
            "dna binding",
            "epigenetic regulation",
            "chromosome conformation",
            "chromatin structure",
        }

        return phrase.lower() in scientific_concepts

    def _map_organism(self, organism: str) -> str:
        """
        Map common organism names to NCBI taxonomy names.
        """
        organism_map = {
            "human": "Homo sapiens",
            "mouse": "Mus musculus",
            "rat": "Rattus norvegicus",
            "fly": "Drosophila melanogaster",
            "worm": "Caenorhabditis elegans",
            "yeast": "Saccharomyces cerevisiae",
            "zebrafish": "Danio rerio",
        }

        return organism_map.get(organism.lower(), organism)

    def suggest_alternatives(self, query: str) -> List[str]:
        """
        Suggest alternative query formulations.

        Returns list of alternative queries with different modes/settings.
        """
        alternatives = []

        # Original query
        alternatives.append(("Original", query))

        # Balanced (default)
        balanced = self.build_query(query, mode="balanced")
        alternatives.append(("Balanced (recommended)", balanced))

        # Broad
        broad = self.build_query(query, mode="broad")
        alternatives.append(("Broad search", broad))

        # Precise
        precise = self.build_query(query, mode="precise")
        alternatives.append(("Precise search", precise))

        # Without synonyms
        no_syn = self.build_query(query, mode="balanced", add_synonyms=False)
        alternatives.append(("Without synonyms", no_syn))

        return alternatives


def optimize_geo_query(query: str, mode: str = "balanced") -> str:
    """
    Convenience function to optimize a GEO query.

    Args:
        query: Natural language query
        mode: Search mode ('precise', 'balanced', 'broad')

    Returns:
        Optimized query string
    """
    builder = GEOQueryBuilder()
    return builder.build_query(query, mode=mode)
