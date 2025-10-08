"""
Semantic Ranking Enhancement for OmicsOracle

This module adds OpenAI embedding-based semantic similarity to improve
dataset relevance ranking beyond simple keyword matching.
"""

import logging
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SemanticRanker:
    """
    Semantic similarity ranker using OpenAI embeddings.

    Enhances keyword-based ranking with semantic understanding
    to catch synonyms, related concepts, and biomedical terminology.
    """

    # Common biomedical technique synonyms
    TECHNIQUE_SYNONYMS = {
        "dna methylation": [
            "5mc",
            "5-methylcytosine",
            "bisulfite sequencing",
            "bisulfite-seq",
            "wgbs",
            "whole genome bisulfite sequencing",
            "rrbs",
            "reduced representation bisulfite sequencing",
            "methylc-seq",
            "nome-seq",
            "nucleosome occupancy and methylome sequencing",
        ],
        "chromatin accessibility": [
            "atac-seq",
            "assay for transposase-accessible chromatin",
            "dnase-seq",
            "dnase hypersensitivity",
            "faire-seq",
            "formaldehyde-assisted isolation of regulatory elements",
            "mnase-seq",
            "nome-seq",
        ],
        "hi-c": [
            "3d genome",
            "chromatin conformation",
            "chromosome conformation capture",
            "genome architecture",
            "chromatin architecture",
            "spatial genome organization",
        ],
        "rna-seq": [
            "transcriptome",
            "gene expression profiling",
            "rna sequencing",
            "transcriptomics",
            "mrna-seq",
        ],
        "single-cell": [
            "sc-",
            "single cell",
            "drop-seq",
            "10x genomics",
            "10x",
            "cell-level",
            "single-nucleus",
        ],
        "joint profiling": [
            "multi-omics",
            "multiomics",
            "simultaneous profiling",
            "integrated profiling",
            "coupled assay",
            "combined profiling",
            "co-profiling",
            "nmt-seq",
            "nome-seq",
            "sci-met",
        ],
    }

    def __init__(self, openai_client=None):
        """
        Initialize semantic ranker.

        Args:
            openai_client: OpenAI client instance (optional, will try to create)
        """
        self.client = openai_client
        self.embedding_cache = {}  # Cache embeddings to avoid recomputation

        if not self.client:
            try:
                import os

                from openai import OpenAI

                api_key = os.getenv("OMICS_AI_OPENAI_API_KEY")
                if api_key:
                    self.client = OpenAI(api_key=api_key)
                    logger.info("Semantic ranker initialized with OpenAI")
                else:
                    logger.warning("No OpenAI API key - semantic ranking disabled")
            except ImportError:
                logger.warning("OpenAI library not installed - semantic ranking disabled")

    def expand_query_with_synonyms(self, query: str) -> str:
        """
        Expand query with biomedical synonyms.

        Args:
            query: Original user query

        Returns:
            Expanded query with synonyms
        """
        query_lower = query.lower()
        expanded_terms = [query]

        for technique, synonyms in self.TECHNIQUE_SYNONYMS.items():
            if technique in query_lower:
                # Add a few most common synonyms
                expanded_terms.extend(synonyms[:3])

        return " OR ".join(set(expanded_terms))

    def get_embedding(self, text: str, cache_key: str = None) -> List[float]:
        """
        Get text embedding from OpenAI.

        Args:
            text: Text to embed
            cache_key: Optional cache key to avoid recomputation

        Returns:
            Embedding vector
        """
        if not self.client:
            return None

        # Check cache
        if cache_key and cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        try:
            # Use smaller, cheaper model
            response = self.client.embeddings.create(
                model="text-embedding-3-small",  # $0.02 per 1M tokens
                input=text[:8000],  # Truncate to avoid token limit
            )

            embedding = response.data[0].embedding

            # Cache result
            if cache_key:
                self.embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return None

    def calculate_similarity(self, query: str, dataset_text: str, dataset_id: str = None) -> float:
        """
        Calculate semantic similarity between query and dataset.

        Args:
            query: User query
            dataset_text: Dataset title + summary concatenated
            dataset_id: Dataset ID for caching

        Returns:
            Similarity score (0.0-1.0)
        """
        if not self.client:
            return 0.0

        # Get embeddings
        query_emb = self.get_embedding(query, cache_key=f"query:{query}")
        dataset_emb = self.get_embedding(dataset_text, cache_key=f"dataset:{dataset_id}")

        if query_emb is None or dataset_emb is None:
            return 0.0

        # Calculate cosine similarity
        query_vec = np.array(query_emb)
        dataset_vec = np.array(dataset_emb)

        similarity = np.dot(query_vec, dataset_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(dataset_vec)
        )

        # Normalize to 0-1 range (cosine is -1 to 1)
        normalized = (similarity + 1) / 2

        return float(normalized)

    def enhance_relevance_score(
        self,
        query: str,
        dataset_title: str,
        dataset_summary: str,
        keyword_score: float,
        dataset_id: str = None,
    ) -> Tuple[float, List[str]]:
        """
        Enhance keyword-based relevance with semantic similarity.

        Args:
            query: User query
            dataset_title: Dataset title
            dataset_summary: Dataset summary
            keyword_score: Existing keyword-based score
            dataset_id: Dataset ID

        Returns:
            Tuple of (enhanced_score, explanation)
        """
        explanation = []

        # Combine title and summary for embedding
        dataset_text = f"{dataset_title}. {dataset_summary}"

        # Calculate semantic similarity
        semantic_score = self.calculate_similarity(query, dataset_text, dataset_id)

        if semantic_score > 0:
            explanation.append(f"Semantic similarity: {semantic_score:.2f}")

            # Blend scores: 60% semantic, 40% keyword
            blended_score = 0.6 * semantic_score + 0.4 * keyword_score

            # Boost if both methods agree
            if semantic_score > 0.7 and keyword_score > 0.5:
                blended_score = min(1.0, blended_score * 1.1)
                explanation.append("High confidence match (semantic + keyword)")

            return blended_score, explanation
        else:
            # Fall back to keyword score if semantic fails
            return keyword_score, ["Keyword-based ranking only"]

    def detect_technique_mentions(self, text: str) -> List[str]:
        """
        Detect biomedical techniques mentioned in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected techniques
        """
        text_lower = text.lower()
        detected = []

        for technique, synonyms in self.TECHNIQUE_SYNONYMS.items():
            if technique in text_lower:
                detected.append(technique)
            else:
                for synonym in synonyms:
                    if synonym in text_lower:
                        detected.append(f"{technique} ({synonym})")
                        break

        return detected


# Example usage
if __name__ == "__main__":
    ranker = SemanticRanker()

    # Example query
    query = "joint profiling of chromatin accessibility AND DNA methylation"

    # Example datasets
    datasets = [
        {
            "id": "GSE109262",
            "title": "Joint profiling of chromatin accessibility, DNA methylation and transcription",
            "summary": "We developed a method for simultaneous profiling...",
            "keyword_score": 0.85,
        },
        {
            "id": "GSE200685",
            "title": "Germ-cell specific eIF4E1b [NOMe-seq]",
            "summary": "NOMe-seq enables simultaneous profiling of DNA methylation and chromatin accessibility...",
            "keyword_score": 0.15,  # Low because "NOMe-seq" not recognized by keywords
        },
    ]

    print(f"Query: {query}\n")

    for ds in datasets:
        enhanced_score, reasons = ranker.enhance_relevance_score(
            query=query,
            dataset_title=ds["title"],
            dataset_summary=ds["summary"],
            keyword_score=ds["keyword_score"],
            dataset_id=ds["id"],
        )

        print(f"{ds['id']}: {ds['title'][:60]}...")
        print(f"  Keyword score: {ds['keyword_score']:.2f}")
        print(f"  Enhanced score: {enhanced_score:.2f}")
        print(f"  Reasons: {', '.join(reasons)}")
        print()
