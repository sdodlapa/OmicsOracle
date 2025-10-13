"""
Advanced semantic search pipeline integrating all Phase 1-Full features.

This module provides a complete end-to-end search pipeline that combines:
- Query expansion with biomedical synonyms
- Hybrid search (keyword + semantic)
- Cross-encoder reranking
- RAG-based natural language answers
- Performance optimization (caching, batching)

This is the flagship search interface for OmicsOracle.
"""

import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from omics_oracle_v2.lib.embeddings.service import EmbeddingConfig, EmbeddingService
from omics_oracle_v2.lib.nlp.query_expander import QueryExpander, QueryExpansionConfig
from omics_oracle_v2.lib.performance.cache import CacheConfig
from omics_oracle_v2.lib.performance.optimizer import OptimizationConfig, SearchOptimizer
from omics_oracle_v2.lib.rag.pipeline import LLMProvider, RAGConfig, RAGPipeline
from omics_oracle_v2.lib.ranking.cross_encoder import CrossEncoderReranker, RerankingConfig
from omics_oracle_v2.lib.search.hybrid import HybridSearchEngine, SearchConfig
from omics_oracle_v2.lib.vector_db.faiss_db import FAISSVectorDB

logger = logging.getLogger(__name__)


@dataclass
class AdvancedSearchConfig:
    """Configuration for advanced search pipeline."""

    # Feature toggles
    enable_query_expansion: bool = True
    enable_reranking: bool = True
    enable_rag: bool = True
    enable_caching: bool = True

    # Component configs
    embedding_config: Optional[EmbeddingConfig] = None
    search_config: Optional[SearchConfig] = None
    expansion_config: Optional[QueryExpansionConfig] = None
    reranking_config: Optional[RerankingConfig] = None
    rag_config: Optional[RAGConfig] = None
    cache_config: Optional[CacheConfig] = None

    # Search parameters
    top_k: int = 20
    rerank_top_k: int = 10


@dataclass
class SearchResult:
    """Enhanced search result with all metadata."""

    query: str
    expanded_query: Optional[str] = None
    results: List[Dict[str, Any]] = None
    reranked_results: List[Dict[str, Any]] = None
    answer: Optional[str] = None
    citations: List[Dict[str, Any]] = None
    confidence: float = 0.0
    total_time_ms: float = 0.0
    cache_hit: bool = False
    expansion_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AdvancedSearchPipeline:
    """
    Advanced semantic search pipeline with all Phase 1-Full features.

    This pipeline provides:
    1. Query expansion with biomedical synonyms
    2. Hybrid semantic + keyword search
    3. Cross-encoder reranking for precision
    4. RAG-based natural language answers
    5. Performance optimization (caching)

    Example:
        >>> # Initialize pipeline
        >>> config = AdvancedSearchConfig(
        ...     enable_query_expansion=True,
        ...     enable_reranking=True,
        ...     enable_rag=True
        ... )
        >>> pipeline = AdvancedSearchPipeline(config)
        >>>
        >>> # Add documents
        >>> docs = [
        ...     {"id": "GSE123", "text": "ATAC-seq analysis...", "metadata": {...}},
        ...     {"id": "GSE124", "text": "RNA-seq profiling...", "metadata": {...}}
        ... ]
        >>> pipeline.add_documents(docs)
        >>>
        >>> # Search with natural language
        >>> result = pipeline.search(
        ...     "What is ATAC-seq used for?",
        ...     return_answer=True
        ... )
        >>> print(result.answer)
        >>> print(result.citations)
    """

    def __init__(self, config: Optional[AdvancedSearchConfig] = None):
        """
        Initialize advanced search pipeline.

        Args:
            config: Pipeline configuration (uses defaults if None)
        """
        self.config = config or AdvancedSearchConfig()

        # Initialize components
        logger.info("Initializing advanced search pipeline...")

        # Query expander
        if self.config.enable_query_expansion:
            expansion_config = self.config.expansion_config or QueryExpansionConfig()
            self.query_expander = QueryExpander(expansion_config)
            logger.info("Query expansion enabled")
        else:
            self.query_expander = None

        # Initialize vector database and embedding service
        embedding_config = self.config.embedding_config or EmbeddingConfig()
        self.embedding_service = EmbeddingService(embedding_config)
        self.vector_db = FAISSVectorDB(dimension=self.embedding_service.get_dimension())
        logger.info("Vector database initialized")

        # Hybrid search engine
        search_config = self.config.search_config or SearchConfig()
        self.search_engine = HybridSearchEngine(self.embedding_service, self.vector_db, search_config)
        logger.info("Hybrid search engine initialized")

        # Cross-encoder reranker
        if self.config.enable_reranking:
            reranking_config = self.config.reranking_config or RerankingConfig()
            self.reranker = CrossEncoderReranker(reranking_config)
            logger.info("Cross-encoder reranking enabled")
        else:
            self.reranker = None

        # RAG pipeline
        if self.config.enable_rag:
            rag_config = self.config.rag_config or RAGConfig()
            self.rag_pipeline = RAGPipeline(rag_config)
            logger.info("RAG pipeline enabled")
        else:
            self.rag_pipeline = None

        # Performance optimizer
        if self.config.enable_caching:
            cache_config = self.config.cache_config or CacheConfig()
            opt_config = OptimizationConfig(enable_caching=True, cache_config=cache_config)
            self.optimizer = SearchOptimizer(opt_config)
            logger.info("Performance optimization enabled")
        else:
            self.optimizer = None

        logger.info("Advanced search pipeline ready")

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Add documents to the search index.

        Args:
            documents: List of document dicts with keys:
                - id: Document identifier
                - text: Document text content
                - metadata: Optional metadata dict

        Returns:
            Number of documents added
        """
        self.search_engine.index_documents(documents)
        return len(documents)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        return_answer: bool = False,
        force_refresh: bool = False,
    ) -> SearchResult:
        """
        Execute advanced search with all features.

        Args:
            query: Search query (natural language)
            top_k: Number of results to return (uses config default if None)
            return_answer: Whether to generate RAG answer
            force_refresh: Skip cache and force fresh search

        Returns:
            SearchResult with results, answer, and metadata
        """
        start_time = time.time()
        top_k = top_k or self.config.top_k

        logger.info(f"Starting advanced search: {query[:50]}...")

        # Step 1: Query expansion
        expanded_query = query
        expansion_summary = None

        if self.config.enable_query_expansion and self.query_expander:
            logger.debug("Expanding query...")
            expanded_query = self.query_expander.expand_for_search(query)
            expansion_summary = self.query_expander.get_expansion_summary(query)
            logger.debug(f"Expanded: {len(expansion_summary.get('expanded_terms', []))} terms")

        # Step 2: Hybrid search (with caching if enabled)
        if self.optimizer and not force_refresh:
            # Use optimizer for caching
            def search_fn(q):
                search_results = self.search_engine.search(q)
                # Convert SearchResult objects to dicts for caching
                result_dicts = []
                for r in search_results[:top_k]:
                    metadata = self.vector_db.get_metadata(r.id)
                    result_dicts.append(
                        {
                            "id": r.id,
                            "text": metadata.get("text", "") if metadata else "",
                            "metadata": r.metadata or {},
                            "score": r.combined_score,
                            "keyword_score": r.keyword_score,
                            "semantic_score": r.semantic_score,
                        }
                    )
                return result_dicts

            results = self.optimizer.optimize_query(expanded_query, search_fn, force_refresh=force_refresh)
            cache_hit = self.optimizer.metrics["cache_hits"] > 0
        else:
            search_results = self.search_engine.search(expanded_query)
            # Convert SearchResult objects to dicts
            results = []
            for r in search_results[:top_k]:
                metadata = self.vector_db.get_metadata(r.id)
                results.append(
                    {
                        "id": r.id,
                        "text": metadata.get("text", "") if metadata else "",
                        "metadata": r.metadata or {},
                        "score": r.combined_score,
                        "keyword_score": r.keyword_score,
                        "semantic_score": r.semantic_score,
                    }
                )
            cache_hit = False

        logger.debug(f"Search returned {len(results)} results")

        # Step 3: Reranking
        reranked_results = None
        if self.config.enable_reranking and self.reranker and len(results) > 0:
            logger.debug("Reranking results...")
            reranked = self.reranker.rerank(
                query,  # Use original query for reranking
                results,
                top_k=self.config.rerank_top_k,
            )
            # Convert RerankedResult objects to dicts
            reranked_results = [
                {
                    "id": r.id,
                    "text": r.text,
                    "metadata": r.metadata,
                    "score": r.combined_score,
                    "original_score": r.original_score,
                    "rerank_score": r.rerank_score,
                    "rank": r.rank,
                }
                for r in reranked
            ]
            logger.debug(f"Reranked to top {len(reranked_results)} results")

        # Step 4: RAG answer generation
        answer = None
        citations = None
        confidence = 0.0

        if return_answer and self.config.enable_rag and self.rag_pipeline:
            logger.debug("Generating RAG answer...")
            # Use reranked results if available, otherwise original results
            answer_results = reranked_results if reranked_results else results

            if len(answer_results) > 0:
                rag_response = self.rag_pipeline.generate_answer(query, answer_results)
                answer = rag_response.answer
                citations = [asdict(c) for c in rag_response.citations]
                confidence = rag_response.confidence
                logger.debug(f"Answer generated (confidence: {confidence:.2f})")

        # Calculate total time
        total_time_ms = (time.time() - start_time) * 1000

        # Create result
        result = SearchResult(
            query=query,
            expanded_query=expanded_query if expanded_query != query else None,
            results=results,
            reranked_results=reranked_results,
            answer=answer,
            citations=citations,
            confidence=confidence,
            total_time_ms=total_time_ms,
            cache_hit=cache_hit,
            expansion_summary=expansion_summary,
        )

        logger.info(
            f"Search complete: {len(results)} results, " f"{total_time_ms:.2f}ms, cache_hit={cache_hit}"
        )

        return result

    def batch_search(
        self, queries: List[str], top_k: Optional[int] = None, return_answers: bool = False
    ) -> List[SearchResult]:
        """
        Execute batch search for multiple queries.

        Args:
            queries: List of search queries
            top_k: Number of results per query
            return_answers: Whether to generate answers for each query

        Returns:
            List of SearchResults
        """
        logger.info(f"Starting batch search: {len(queries)} queries")
        results = []

        for query in queries:
            result = self.search(query, top_k=top_k, return_answer=return_answers)
            results.append(result)

        logger.info(f"Batch search complete: {len(results)} queries processed")
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        stats = {"components": {}}

        # Search engine stats
        if hasattr(self.search_engine, "get_stats"):
            stats["components"]["search_engine"] = self.search_engine.get_stats()

        # Reranker stats
        if self.reranker:
            stats["components"]["reranker"] = self.reranker.get_stats()

        # RAG pipeline stats
        if self.rag_pipeline:
            stats["components"]["rag"] = self.rag_pipeline.get_stats()

        # Optimizer stats
        if self.optimizer:
            stats["components"]["optimizer"] = self.optimizer.get_metrics()

        # Configuration
        stats["config"] = {
            "query_expansion": self.config.enable_query_expansion,
            "reranking": self.config.enable_reranking,
            "rag": self.config.enable_rag,
            "caching": self.config.enable_caching,
        }

        return stats

    def clear_cache(self) -> None:
        """Clear all caches."""
        if self.optimizer:
            self.optimizer.clear_cache()
        if self.rag_pipeline:
            self.rag_pipeline.clear_cache()
        logger.info("All caches cleared")


# Demo usage
if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    print("=" * 80)
    print("Advanced Search Pipeline Demo")
    print("=" * 80)

    # Create pipeline with all features enabled (mock embeddings for demo)
    config = AdvancedSearchConfig(
        enable_query_expansion=True,
        enable_reranking=True,
        enable_rag=True,
        enable_caching=True,
        embedding_config=EmbeddingConfig(api_key="dummy-key-for-demo"),  # Dummy key
        rag_config=RAGConfig(llm_provider=LLMProvider.MOCK),
    )

    try:
        pipeline = AdvancedSearchPipeline(config)
    except Exception as e:
        print(f"\n[!] Error initializing pipeline: {e}")
        print("[!] Demo requires OpenAI API key. Set OPENAI_API_KEY environment variable.")
        print("[!] Exiting demo...")
        sys.exit(1)

    print("\n[*] Pipeline initialized")
    print(f"    Query expansion: {config.enable_query_expansion}")
    print(f"    Reranking: {config.enable_reranking}")
    print(f"    RAG: {config.enable_rag}")
    print(f"    Caching: {config.enable_caching}")

    # Add sample documents
    print("\n[*] Adding sample documents...")
    documents = [
        {
            "id": "GSE123001",
            "text": "ATAC-seq analysis of chromatin accessibility in human T cells. "
            "This study reveals dynamic changes in chromatin accessibility during "
            "T cell activation and identifies key regulatory elements controlling "
            "immune response genes.",
            "metadata": {
                "title": "Chromatin dynamics in T cell activation",
                "accession": "GSE123001",
                "organism": "Homo sapiens",
                "technique": "ATAC-seq",
            },
        },
        {
            "id": "GSE123002",
            "text": "RNA-seq profiling of gene expression in cancer cells. "
            "Comprehensive transcriptome analysis reveals novel oncogenes and "
            "therapeutic targets in breast cancer.",
            "metadata": {
                "title": "Cancer transcriptomics",
                "accession": "GSE123002",
                "technique": "RNA-seq",
            },
        },
        {
            "id": "GSE123003",
            "text": "Single-cell ATAC-seq reveals cell-type-specific regulatory landscapes "
            "in the developing brain. This approach identifies distinct chromatin "
            "accessibility patterns across different neural cell types.",
            "metadata": {
                "title": "Single-cell chromatin accessibility",
                "accession": "GSE123003",
                "technique": "scATAC-seq",
            },
        },
    ]

    num_added = pipeline.add_documents(documents)
    print(f"    Added {num_added} documents")

    # Execute search with all features
    print("\n[*] Executing advanced search...")
    query = "What is ATAC-seq used for?"

    result = pipeline.search(query, top_k=10, return_answer=True)

    print("\n" + "=" * 80)
    print(f"Query: {result.query}")
    print("=" * 80)

    # Query expansion
    if result.expanded_query:
        print(f"\nExpanded Query: {result.expanded_query}")
        if result.expansion_summary:
            print("Expansion Summary:")
            for key, value in result.expansion_summary.items():
                if key != "original_query" and value:
                    print(f"  {key}: {value}")

    # Search results
    print(f"\n[*] Search Results ({len(result.results)} found):")
    for i, res in enumerate(result.results[:3], 1):
        print(f"  {i}. {res['id']}: {res.get('metadata', {}).get('title', 'N/A')}")
        print(f"     Score: {res['score']:.3f}")

    # Reranked results
    if result.reranked_results:
        print(f"\n[*] Reranked Results (top {len(result.reranked_results)}):")
        for i, res in enumerate(result.reranked_results[:3], 1):
            print(f"  {i}. {res['id']}: {res.get('metadata', {}).get('title', 'N/A')}")
            print(f"     Combined: {res['score']:.3f}, " f"Rerank: {res['rerank_score']:.3f}")

    # RAG answer
    if result.answer:
        print("\n" + "-" * 80)
        print("Answer:")
        print(result.answer)

        if result.citations:
            print("\nCitations:")
            for citation in result.citations:
                print(f"  [{citation['doc_id']}] {citation['title']}")

        print(f"\nConfidence: {result.confidence:.2f}")

    # Performance metrics
    print("\n" + "-" * 80)
    print("Performance:")
    print(f"  Total time: {result.total_time_ms:.2f}ms")
    print(f"  Cache hit: {result.cache_hit}")

    # Test caching
    print("\n[*] Testing cache...")
    result2 = pipeline.search(query, top_k=10, return_answer=True)
    print(f"    Second search: {result2.total_time_ms:.2f}ms (cached: {result2.cache_hit})")

    # Pipeline stats
    print("\n[*] Pipeline statistics:")
    stats = pipeline.get_stats()
    for component, component_stats in stats.get("components", {}).items():
        print(f"  {component}:")
        for key, value in component_stats.items():
            print(f"    {key}: {value}")

    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)

    sys.exit(0)
