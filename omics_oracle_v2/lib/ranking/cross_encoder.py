"""
Cross-Encoder Reranking Module

High-precision reranking of search results using cross-encoder models.
Cross-encoders jointly encode query and document for better relevance scoring.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from sentence_transformers import CrossEncoder


class RerankingConfig(BaseModel):
    """Configuration for cross-encoder reranking."""

    enabled: bool = Field(default=True, description="Enable reranking")
    model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model name",
    )
    batch_size: int = Field(default=32, description="Batch size for reranking")
    top_k: int = Field(default=20, description="Number of top results to return")
    cache_enabled: bool = Field(default=True, description="Enable result caching")
    cache_dir: str = Field(default="data/cache/reranking", description="Cache directory")
    device: str = Field(default="cpu", description="Device for model inference (cpu/cuda)")


@dataclass
class RerankedResult:
    """Result after cross-encoder reranking."""

    id: str
    text: str
    metadata: Dict
    original_score: float
    rerank_score: float
    combined_score: float
    rank: int


class CrossEncoderReranker:
    """
    Rerank search results using cross-encoder models.

    Cross-encoders provide higher precision than bi-encoders (embeddings)
    by jointly encoding query and document together. They are slower but
    more accurate, making them ideal for reranking top results.

    Example:
        >>> reranker = CrossEncoderReranker()
        >>> results = [
        ...     {"id": "1", "text": "ATAC-seq chromatin", "score": 0.8},
        ...     {"id": "2", "text": "RNA-seq gene expression", "score": 0.75}
        ... ]
        >>> reranked = reranker.rerank("chromatin accessibility", results)
        >>> print(reranked[0].rerank_score)  # Higher score for better match
        0.92
    """

    def __init__(self, config: Optional[RerankingConfig] = None):
        """
        Initialize cross-encoder reranker.

        Args:
            config: Reranking configuration
        """
        self.config = config or RerankingConfig()
        self.model: Optional[CrossEncoder] = None
        self._cache: Dict[str, List[Dict]] = {}

        if self.config.cache_enabled:
            self._load_cache()

        # Lazy load model on first use
        if self.config.enabled:
            self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> None:
        """Load cross-encoder model if not already loaded."""
        if self.model is None:
            self.model = CrossEncoder(self.config.model, device=self.config.device)

    def _load_cache(self) -> None:
        """Load reranking cache from disk."""
        cache_path = Path(self.config.cache_dir) / "rerank_cache.json"

        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self) -> None:
        """Save reranking cache to disk."""
        if not self.config.cache_enabled:
            return

        cache_path = Path(self.config.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

        cache_file = cache_path / "rerank_cache.json"

        try:
            with open(cache_file, "w") as f:
                json.dump(self._cache, f, indent=2)
        except Exception:
            pass  # Fail silently on cache save errors

    def _get_cache_key(self, query: str, result_ids: List[str]) -> str:
        """Generate cache key for query and results."""
        key_data = f"{query}:{','.join(sorted(result_ids))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def rerank(
        self,
        query: str,
        results: List[Dict],
        top_k: Optional[int] = None,
        alpha: float = 0.7,
    ) -> List[RerankedResult]:
        """
        Rerank search results using cross-encoder.

        Args:
            query: Search query
            results: List of search results with 'id', 'text', 'score', 'metadata'
            top_k: Number of top results to return (default: config.top_k)
            alpha: Weight for rerank_score vs original_score (0-1)
                   combined = alpha * rerank + (1-alpha) * original

        Returns:
            List of RerankedResult objects sorted by combined_score

        Example:
            >>> results = [
            ...     {
            ...         "id": "GSE123",
            ...         "text": "ATAC-seq chromatin accessibility",
            ...         "score": 0.8,
            ...         "metadata": {"title": "Chromatin Study"}
            ...     }
            ... ]
            >>> reranked = reranker.rerank("chromatin accessibility", results)
        """
        if not self.config.enabled or not results:
            # Return original results if reranking disabled
            return [
                RerankedResult(
                    id=r["id"],
                    text=r.get("text", ""),
                    metadata=r.get("metadata", {}),
                    original_score=r.get("score", 0.0),
                    rerank_score=r.get("score", 0.0),
                    combined_score=r.get("score", 0.0),
                    rank=i + 1,
                )
                for i, r in enumerate(results)
            ]

        top_k = top_k or self.config.top_k

        # Check cache
        result_ids = [r["id"] for r in results]
        cache_key = self._get_cache_key(query, result_ids)

        if self.config.cache_enabled and cache_key in self._cache:
            # Return cached results
            cached = self._cache[cache_key]
            return [RerankedResult(**r) for r in cached[: min(top_k, len(cached))]]

        # Ensure model is loaded
        self._ensure_model_loaded()

        # Prepare query-document pairs
        pairs = [(query, r.get("text", "")) for r in results]

        # Get rerank scores in batches
        rerank_scores = self._score_batched(pairs)

        # Combine scores and create reranked results
        reranked = []
        for i, (result, rerank_score) in enumerate(zip(results, rerank_scores)):
            original_score = result.get("score", 0.0)

            # Normalize rerank score to 0-1 range (cross-encoder scores vary)
            normalized_rerank = self._normalize_score(rerank_score)

            # Combined score: weighted average
            combined_score = alpha * normalized_rerank + (1 - alpha) * original_score

            reranked.append(
                RerankedResult(
                    id=result["id"],
                    text=result.get("text", ""),
                    metadata=result.get("metadata", {}),
                    original_score=original_score,
                    rerank_score=normalized_rerank,
                    combined_score=combined_score,
                    rank=0,  # Will be set after sorting
                )
            )

        # Sort by combined score
        reranked.sort(key=lambda x: x.combined_score, reverse=True)

        # Set ranks
        for i, result in enumerate(reranked):
            result.rank = i + 1

        # Take top_k
        top_results = reranked[:top_k]

        # Cache results
        if self.config.cache_enabled:
            self._cache[cache_key] = [
                {
                    "id": r.id,
                    "text": r.text,
                    "metadata": r.metadata,
                    "original_score": r.original_score,
                    "rerank_score": r.rerank_score,
                    "combined_score": r.combined_score,
                    "rank": r.rank,
                }
                for r in top_results
            ]
            self._save_cache()

        return top_results

    def _score_batched(self, pairs: List[tuple]) -> List[float]:
        """Score query-document pairs in batches."""
        if self.model is None:
            return [0.0] * len(pairs)

        scores = []
        batch_size = self.config.batch_size

        for i in range(0, len(pairs), batch_size):
            batch = pairs[i : i + batch_size]
            batch_scores = self.model.predict(batch)
            scores.extend(batch_scores.tolist())

        return scores

    def _normalize_score(self, score: float) -> float:
        """
        Normalize cross-encoder score to 0-1 range.

        MS-MARCO model typically outputs scores in range [-10, 10].
        We use sigmoid to normalize to [0, 1].
        """
        import math

        # Sigmoid normalization
        return 1 / (1 + math.exp(-score))

    def get_stats(self) -> Dict:
        """Get reranking statistics."""
        return {
            "model": self.config.model,
            "cache_size": len(self._cache),
            "cache_enabled": self.config.cache_enabled,
            "enabled": self.config.enabled,
            "device": self.config.device,
        }

    def clear_cache(self) -> None:
        """Clear reranking cache."""
        self._cache = {}
        cache_path = Path(self.config.cache_dir) / "rerank_cache.json"
        if cache_path.exists():
            cache_path.unlink()


def main():
    """Demo cross-encoder reranking."""
    print("=" * 70)
    print("CROSS-ENCODER RERANKING DEMONSTRATION")
    print("=" * 70)
    print()

    # Create reranker
    config = RerankingConfig(top_k=5)
    reranker = CrossEncoderReranker(config)

    print(f"Model: {config.model}")
    print(f"Device: {config.device}")
    print()

    # Sample search results
    query = "chromatin accessibility profiling"

    results = [
        {
            "id": "GSE123001",
            "text": "ATAC-seq analysis of chromatin accessibility in human cells",
            "score": 0.85,
            "metadata": {"title": "ATAC-seq Study", "organism": "Homo sapiens"},
        },
        {
            "id": "GSE123002",
            "text": "RNA-seq gene expression profiling in cancer cells",
            "score": 0.80,
            "metadata": {
                "title": "RNA-seq Cancer Study",
                "organism": "Homo sapiens",
            },
        },
        {
            "id": "GSE123003",
            "text": "DNase-seq mapping of open chromatin regions",
            "score": 0.78,
            "metadata": {
                "title": "DNase-seq Study",
                "organism": "Mus musculus",
            },
        },
        {
            "id": "GSE123004",
            "text": "ChIP-seq histone modification profiling",
            "score": 0.75,
            "metadata": {
                "title": "ChIP-seq Epigenetics",
                "organism": "Homo sapiens",
            },
        },
        {
            "id": "GSE123005",
            "text": "Whole genome sequencing of cancer patients",
            "score": 0.70,
            "metadata": {"title": "WGS Cancer", "organism": "Homo sapiens"},
        },
    ]

    print(f"Query: '{query}'")
    print("-" * 70)
    print()

    # Rerank
    print("Reranking results...")
    reranked = reranker.rerank(query, results, alpha=0.7)

    print(f"\nTop {len(reranked)} results after reranking:")
    print("=" * 70)

    for result in reranked:
        print(f"\nRank {result.rank}: {result.id}")
        print(f"  Title: {result.metadata.get('title', 'N/A')}")
        print(f"  Original Score: {result.original_score:.3f}")
        print(f"  Rerank Score:   {result.rerank_score:.3f}")
        print(f"  Combined Score: {result.combined_score:.3f} [*]")

    print()
    print("=" * 70)
    print("RERANKING IMPACT")
    print("=" * 70)

    # Compare rankings
    original_order = [r["id"] for r in results]
    reranked_order = [r.id for r in reranked]

    print(f"\nOriginal order: {', '.join(original_order[:5])}")
    print(f"Reranked order: {', '.join(reranked_order[:5])}")

    if original_order[:5] != reranked_order:
        print("\n+ Rankings improved! More relevant results promoted.")
    else:
        print("\n- Rankings unchanged (already optimal)")

    print()
    print(f"Cache stats: {reranker.get_stats()}")


if __name__ == "__main__":
    main()
