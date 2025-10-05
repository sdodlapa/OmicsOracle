"""
Hybrid search engine combining keyword and semantic search.

Implements result fusion with configurable ranking weights.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

import numpy as np

from omics_oracle_v2.lib.embeddings.service import EmbeddingService
from omics_oracle_v2.lib.vector_db.interface import VectorDB


@dataclass
class SearchConfig:
    """
    Configuration for hybrid search.

    Controls how keyword and semantic results are combined.
    """

    # Search weights (must sum to 1.0)
    keyword_weight: float = 0.4
    semantic_weight: float = 0.6

    # Result limits
    max_results: int = 100
    keyword_k: int = 50  # How many keyword results to fetch
    semantic_k: int = 50  # How many semantic results to fetch

    # Minimum scores (0-1 range)
    min_keyword_score: float = 0.0
    min_semantic_score: float = 0.0
    min_combined_score: float = 0.0

    # Deduplication
    deduplicate: bool = True

    def __post_init__(self):
        """Validate configuration."""
        total_weight = self.keyword_weight + self.semantic_weight
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point error
            raise ValueError(f"keyword_weight + semantic_weight must equal 1.0, got {total_weight}")

        if self.keyword_weight < 0 or self.semantic_weight < 0:
            raise ValueError("Weights must be non-negative")

        if self.max_results <= 0:
            raise ValueError(f"max_results must be positive, got {self.max_results}")

        if self.keyword_k <= 0 or self.semantic_k <= 0:
            raise ValueError("keyword_k and semantic_k must be positive")


@dataclass
class SearchResult:
    """
    Single search result with scores.

    Combines keyword and semantic relevance scores.
    """

    id: str
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    combined_score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    rank: int = 0

    def __lt__(self, other):
        """Compare by combined score (for sorting)."""
        return self.combined_score > other.combined_score  # Higher score = better


class HybridSearchEngine:
    """
    Hybrid search combining keyword and semantic similarity.

    Supports:
    - Keyword-based search (BM25-style ranking)
    - Semantic search (vector similarity)
    - Configurable result fusion
    - Score normalization
    - Deduplication
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_db: VectorDB,
        config: Optional[SearchConfig] = None,
    ):
        """
        Initialize hybrid search engine.

        Args:
            embedding_service: Service for generating query embeddings
            vector_db: Vector database for semantic search
            config: Search configuration (uses defaults if None)
        """
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.config = config or SearchConfig()

        # Keyword search state
        self._keyword_index: Dict[str, Dict[str, float]] = {}  # term -> {id: score}
        self._document_ids: Set[str] = set()

    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "text",
        id_field: str = "id",
        metadata_fields: Optional[List[str]] = None,
    ) -> None:
        """
        Index documents for hybrid search.

        Args:
            documents: List of documents to index
            text_field: Field containing text to search
            id_field: Field containing document ID
            metadata_fields: Optional fields to store as metadata

        Raises:
            ValueError: If documents are invalid
        """
        if not documents:
            return

        # Extract texts and IDs
        texts = []
        ids = []
        metadata_list = []

        for doc in documents:
            if text_field not in doc:
                raise ValueError(f"Document missing '{text_field}' field: {doc}")
            if id_field not in doc:
                raise ValueError(f"Document missing '{id_field}' field: {doc}")

            texts.append(doc[text_field])
            ids.append(doc[id_field])

            # Extract metadata
            if metadata_fields:
                metadata = {field: doc.get(field) for field in metadata_fields}
            else:
                metadata = {k: v for k, v in doc.items() if k not in [text_field, id_field]}
            metadata_list.append(metadata)

        # Generate embeddings and index in vector DB
        embeddings = self.embedding_service.embed_batch(texts)
        self.vector_db.add_vectors(np.array(embeddings), ids=ids, metadata=metadata_list)

        # Build keyword index
        self._build_keyword_index(texts, ids)
        self._document_ids.update(ids)

    def _build_keyword_index(self, texts: List[str], ids: List[str]) -> None:
        """
        Build simple keyword index (term -> document scores).

        Uses basic term frequency for scoring.

        Args:
            texts: Document texts
            ids: Document IDs
        """
        for text, doc_id in zip(texts, ids):
            # Simple tokenization (lowercase, split on whitespace)
            terms = text.lower().split()

            # Count term frequencies
            term_counts: Dict[str, int] = {}
            for term in terms:
                term_counts[term] = term_counts.get(term, 0) + 1

            # Normalize by document length
            doc_length = len(terms)
            for term, count in term_counts.items():
                score = count / doc_length if doc_length > 0 else 0.0

                if term not in self._keyword_index:
                    self._keyword_index[term] = {}
                self._keyword_index[term][doc_id] = score

    def search(self, query: str) -> List[SearchResult]:
        """
        Perform hybrid search.

        Args:
            query: Search query text

        Returns:
            List of SearchResult objects, sorted by combined score
        """
        # Get keyword results
        keyword_results = self._keyword_search(query, k=self.config.keyword_k)

        # Get semantic results
        semantic_results = self._semantic_search(query, k=self.config.semantic_k)

        # Normalize scores to [0, 1] range
        keyword_results = self._normalize_scores(keyword_results)
        semantic_results = self._normalize_scores(semantic_results)

        # Combine results
        combined = self._combine_results(keyword_results, semantic_results)

        # Filter by minimum scores
        combined = self._filter_results(combined)

        # Sort by combined score
        combined.sort()

        # Limit results
        combined = combined[: self.config.max_results]

        # Add ranks
        for i, result in enumerate(combined, 1):
            result.rank = i

        return combined

    def _keyword_search(self, query: str, k: int) -> Dict[str, float]:
        """
        Perform keyword-based search.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Dict mapping document ID to keyword score
        """
        if not self._keyword_index:
            return {}

        # Tokenize query
        query_terms = query.lower().split()

        # Aggregate scores across all query terms
        scores: Dict[str, float] = {}
        for term in query_terms:
            if term in self._keyword_index:
                for doc_id, score in self._keyword_index[term].items():
                    scores[doc_id] = scores.get(doc_id, 0.0) + score

        # Get top k
        top_k = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return dict(top_k)

    def _semantic_search(self, query: str, k: int) -> Dict[str, float]:
        """
        Perform semantic search.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Dict mapping document ID to semantic score (similarity)
        """
        if self.vector_db.size() == 0:
            return {}

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Search vector DB
        results = self.vector_db.search(np.array(query_embedding), k=k)

        # Convert distances to similarities (lower distance = higher similarity)
        # Using exponential decay: similarity = exp(-distance)
        scores = {}
        for doc_id, distance in results:
            # Clip distance to avoid overflow
            distance = min(distance, 100.0)
            similarity = np.exp(-distance)
            scores[doc_id] = float(similarity)

        return scores

    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize scores to [0, 1] range using min-max scaling.

        Args:
            scores: Dict of document ID -> score

        Returns:
            Normalized scores
        """
        if not scores:
            return {}

        values = list(scores.values())
        min_score = min(values)
        max_score = max(values)

        if max_score == min_score:
            # All scores are the same
            return {doc_id: 1.0 for doc_id in scores}

        normalized = {}
        for doc_id, score in scores.items():
            normalized[doc_id] = (score - min_score) / (max_score - min_score)

        return normalized

    def _combine_results(
        self, keyword_scores: Dict[str, float], semantic_scores: Dict[str, float]
    ) -> List[SearchResult]:
        """
        Combine keyword and semantic results.

        Args:
            keyword_scores: Normalized keyword scores
            semantic_scores: Normalized semantic scores

        Returns:
            List of SearchResult objects
        """
        # Get all unique document IDs
        all_ids = set(keyword_scores.keys()) | set(semantic_scores.keys())

        results = []
        for doc_id in all_ids:
            keyword_score = keyword_scores.get(doc_id, 0.0)
            semantic_score = semantic_scores.get(doc_id, 0.0)

            # Apply minimum score filters
            if keyword_score < self.config.min_keyword_score:
                keyword_score = 0.0
            if semantic_score < self.config.min_semantic_score:
                semantic_score = 0.0

            # Weighted combination
            combined_score = (
                self.config.keyword_weight * keyword_score + self.config.semantic_weight * semantic_score
            )

            # Get metadata from vector DB
            metadata = self.vector_db.get_metadata(doc_id)

            result = SearchResult(
                id=doc_id,
                keyword_score=keyword_score,
                semantic_score=semantic_score,
                combined_score=combined_score,
                metadata=metadata,
            )
            results.append(result)

        return results

    def _filter_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Filter results by minimum combined score.

        Args:
            results: List of search results

        Returns:
            Filtered results
        """
        return [r for r in results if r.combined_score >= self.config.min_combined_score]

    def clear(self) -> None:
        """Clear all indexed data."""
        self._keyword_index.clear()
        self._document_ids.clear()
        self.vector_db.clear()

    def size(self) -> int:
        """Get number of indexed documents."""
        return len(self._document_ids)

    def get_config(self) -> SearchConfig:
        """Get current search configuration."""
        return self.config

    def update_config(self, **kwargs) -> None:
        """
        Update search configuration.

        Args:
            **kwargs: Configuration parameters to update
        """
        # Create new config with updated values
        config_dict = {
            "keyword_weight": self.config.keyword_weight,
            "semantic_weight": self.config.semantic_weight,
            "max_results": self.config.max_results,
            "keyword_k": self.config.keyword_k,
            "semantic_k": self.config.semantic_k,
            "min_keyword_score": self.config.min_keyword_score,
            "min_semantic_score": self.config.min_semantic_score,
            "min_combined_score": self.config.min_combined_score,
            "deduplicate": self.config.deduplicate,
        }
        config_dict.update(kwargs)
        self.config = SearchConfig(**config_dict)
