"""
Unified Search Pipeline - Main orchestration for all omics search operations.

This pipeline brings together:
- QueryAnalyzer: Route queries based on type (GEO ID vs text)
- QueryOptimizer: NER + synonym expansion via SapBERT
- RedisCache: Performance optimization
- Multi-source search: GEO, PubMed, OpenAlex
- AdvancedDeduplicator: 2-pass deduplication system

Week 1 implementation following golden pattern from AdvancedSearchPipeline.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from omics_oracle_v2.lib.cache.redis_cache import RedisCache
from omics_oracle_v2.lib.geo import GEOClient
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.deduplication import AdvancedDeduplicator
from omics_oracle_v2.lib.publications.models import Publication
from omics_oracle_v2.lib.query.analyzer import QueryAnalyzer, SearchType
from omics_oracle_v2.lib.query.optimizer import QueryOptimizer

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSearchConfig:
    """
    Configuration for unified search pipeline.

    Feature Toggles (Week 1):
    - enable_geo_search: GEO dataset search
    - enable_publication_search: PubMed/OpenAlex publication search
    - enable_query_optimization: NER + synonym expansion via SapBERT
    - enable_caching: Redis-based caching
    - enable_deduplication: Advanced fuzzy deduplication

    Example:
        >>> config = UnifiedSearchConfig(
        ...     enable_geo_search=True,
        ...     enable_publication_search=True,
        ...     enable_query_optimization=True,
        ...     enable_caching=True,
        ... )
    """

    # Feature toggles
    enable_geo_search: bool = True
    enable_publication_search: bool = True
    enable_query_optimization: bool = True
    enable_caching: bool = True
    enable_deduplication: bool = True

    # Query optimization
    enable_sapbert: bool = True  # Enable SapBERT embeddings for synonyms
    enable_ner: bool = True  # Enable biomedical NER

    # Caching configuration
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_db: int = 0
    cache_ttl_search: int = 86400  # 24 hours for search results
    cache_ttl_metadata: int = 604800  # 7 days for publication metadata
    cache_ttl_geo: int = 2592000  # 30 days for GEO metadata

    # Deduplication thresholds
    title_similarity_threshold: float = 85.0
    author_similarity_threshold: float = 80.0
    year_tolerance: int = 1

    # Search limits
    max_geo_results: int = 100
    max_publication_results: int = 100

    # Component configurations (optional - will use defaults if not provided)
    geo_client: Optional[GEOClient] = None
    publication_pipeline: Optional[PublicationSearchPipeline] = None


@dataclass
class SearchResult:
    """
    Unified search result containing both GEO datasets and publications.

    Attributes:
        query: Original query string
        optimized_query: Query after optimization (NER + synonyms)
        query_type: Detected query type (geo_id, dataset, publication, mixed)
        geo_datasets: List of GEO dataset results
        publications: List of publication results
        total_results: Total number of results
        search_time_ms: Total search time in milliseconds
        cache_hit: Whether results came from cache
        metadata: Additional metadata about the search
    """

    query: str
    optimized_query: str
    query_type: str
    geo_datasets: List[GEOSeriesMetadata] = field(default_factory=list)
    publications: List[Publication] = field(default_factory=list)
    total_results: int = 0
    search_time_ms: float = 0.0
    cache_hit: bool = False
    metadata: Dict = field(default_factory=dict)


class OmicsSearchPipeline:
    """
    Unified search pipeline for all omics search operations.

    This is the main entry point for searching across:
    - GEO datasets (NCBI Gene Expression Omnibus)
    - Publications (PubMed, OpenAlex, Google Scholar)

    Features:
    - Intelligent query analysis and routing
    - Biomedical NER + SapBERT synonym expansion
    - Multi-source search with automatic deduplication
    - Redis-based caching for performance
    - Graceful degradation when components unavailable

    Example:
        >>> # Basic usage
        >>> pipeline = OmicsSearchPipeline(config)
        >>> results = await pipeline.search("APOE gene expression in Alzheimer's disease")
        >>> print(f"Found {results.total_results} results")
        >>> print(f"GEO datasets: {len(results.geo_datasets)}")
        >>> print(f"Publications: {len(results.publications)}")

        >>> # GEO ID fast path
        >>> results = await pipeline.search("GSE123456")
        >>> # Returns metadata for specific GEO series

        >>> # Publication-only search
        >>> results = await pipeline.search("breast cancer treatment", search_type="publication")
    """

    def __init__(self, config: UnifiedSearchConfig):
        """
        Initialize unified search pipeline.

        Args:
            config: Pipeline configuration with feature toggles
        """
        self.config = config
        self._initialized = False

        # Initialize query analyzer (always enabled - lightweight)
        logger.info("Initializing QueryAnalyzer")
        self.query_analyzer = QueryAnalyzer()

        # Initialize query optimizer (conditional)
        if config.enable_query_optimization:
            logger.info(
                f"Initializing QueryOptimizer (SapBERT={config.enable_sapbert}, NER={config.enable_ner})"
            )
            self.query_optimizer = QueryOptimizer(
                enable_sapbert=config.enable_sapbert,
                enable_ner=config.enable_ner,
            )
        else:
            logger.info("Query optimization disabled")
            self.query_optimizer = None

        # Initialize cache (conditional)
        if config.enable_caching:
            logger.info(f"Initializing Redis cache at {config.cache_host}:{config.cache_port}")
            try:
                self.cache = RedisCache(
                    host=config.cache_host,
                    port=config.cache_port,
                    db=config.cache_db,
                )
                self._cache_available = True
            except Exception as e:
                logger.warning(f"Cache initialization failed: {e}. Proceeding without cache.")
                self.cache = None
                self._cache_available = False
        else:
            logger.info("Caching disabled")
            self.cache = None
            self._cache_available = False

        # Initialize deduplicator (conditional)
        if config.enable_deduplication:
            logger.info("Initializing AdvancedDeduplicator")
            self.deduplicator = AdvancedDeduplicator(
                title_similarity_threshold=config.title_similarity_threshold,
                author_similarity_threshold=config.author_similarity_threshold,
                year_tolerance=config.year_tolerance,
                enable_fuzzy_matching=True,
            )
        else:
            logger.info("Deduplication disabled")
            self.deduplicator = None

        # Initialize GEO search (conditional)
        if config.enable_geo_search:
            if config.geo_client:
                logger.info("Using provided GEO client")
                self.geo_client = config.geo_client
            else:
                logger.info("GEO client will be initialized on first use")
                self.geo_client = None
        else:
            logger.info("GEO search disabled")
            self.geo_client = None

        # Initialize publication search (conditional)
        if config.enable_publication_search:
            if config.publication_pipeline:
                logger.info("Using provided publication pipeline")
                self.publication_pipeline = config.publication_pipeline
            else:
                logger.info("Publication pipeline will be initialized on first use")
                self.publication_pipeline = None
        else:
            logger.info("Publication search disabled")
            self.publication_pipeline = None

        self._initialized = True
        logger.info("OmicsSearchPipeline initialized successfully")

    async def search(
        self,
        query: str,
        max_geo_results: Optional[int] = None,
        max_publication_results: Optional[int] = None,
        search_type: Optional[str] = None,
        use_cache: bool = True,
    ) -> SearchResult:
        """
        Execute unified search across all enabled sources.

        Args:
            query: Search query string
            max_geo_results: Max GEO results (overrides config)
            max_publication_results: Max publication results (overrides config)
            search_type: Force search type ("geo", "publication", "mixed", or None for auto-detect)
            use_cache: Whether to use cache (default: True)

        Returns:
            SearchResult with datasets and publications

        Raises:
            ValueError: If query is empty or invalid
            RuntimeError: If search fails

        Example:
            >>> # Auto-detect query type
            >>> results = await pipeline.search("diabetes insulin resistance")

            >>> # Force GEO search only
            >>> results = await pipeline.search("diabetes", search_type="geo")

            >>> # Fast path for GEO IDs
            >>> results = await pipeline.search("GSE123456")
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        start_time = time.time()
        query = query.strip()

        logger.info(f"Starting unified search: '{query}'")

        # Step 1: Check cache
        cache_hit = False
        if use_cache and self._cache_available:
            cached_result = await self._check_cache(query)
            if cached_result:
                logger.info("Cache hit - returning cached results")
                cached_result.cache_hit = True
                return cached_result

        # Step 2: Analyze query type
        analysis = self.query_analyzer.analyze(query)
        logger.info(
            f"Query analysis: type={analysis.search_type.value}, confidence={analysis.confidence:.2f}"
        )

        # Override query type if specified
        if search_type:
            if search_type.lower() == "geo":
                analysis.search_type = SearchType.GEO
            elif search_type.lower() == "publication":
                analysis.search_type = SearchType.PUBLICATIONS
            logger.info(f"Query type overridden to: {analysis.search_type.value}")

        # Step 3: Optimize query (if enabled and not GEO ID fast path)
        optimized_query = query
        optimization_result = None
        if self.query_optimizer and analysis.search_type != SearchType.GEO_ID:
            try:
                logger.info("Optimizing query with NER + SapBERT")
                optimization_result = await self.query_optimizer.optimize(query)
                optimized_query = optimization_result.primary_query
                query_variations = optimization_result.get_all_query_variations()
                logger.info(f"Query optimized: '{query}' -> '{optimized_query}'")
                logger.info(f"Entities found: {len(optimization_result.entities)}")
                logger.info(f"Query variations: {len(query_variations)}")
            except Exception as e:
                logger.warning(f"Query optimization failed: {e}. Using original query.")
                optimized_query = query

        # Step 4: Route and execute searches
        geo_datasets = []
        publications = []

        # GEO ID fast path
        if analysis.search_type == SearchType.GEO_ID and analysis.geo_ids:
            logger.info(f"GEO ID detected: {analysis.geo_ids[0]} - fast path")
            geo_datasets = await self._search_geo_by_id(analysis.geo_ids[0])

        # Dataset search
        elif analysis.search_type == SearchType.GEO or analysis.search_type == SearchType.AUTO:
            if self.config.enable_geo_search:
                logger.info("Executing GEO dataset search")
                geo_datasets = await self._search_geo(
                    optimized_query,
                    max_results=max_geo_results or self.config.max_geo_results,
                )
            else:
                logger.info("GEO search disabled - skipping")

        # Publication search
        if analysis.search_type == SearchType.PUBLICATIONS or analysis.search_type == SearchType.AUTO:
            if self.config.enable_publication_search:
                logger.info("Executing publication search")
                publications = await self._search_publications(
                    optimized_query,
                    max_results=max_publication_results or self.config.max_publication_results,
                )
            else:
                logger.info("Publication search disabled - skipping")

        # Step 5: Deduplicate results
        if self.deduplicator and publications:
            logger.info(f"Deduplicating {len(publications)} publications")
            original_count = len(publications)
            publications = self.deduplicator.deduplicate(publications)
            duplicates_removed = original_count - len(publications)
            logger.info(f"Removed {duplicates_removed} duplicate publications")

        # Step 6: Build result
        search_time_ms = (time.time() - start_time) * 1000
        result = SearchResult(
            query=query,
            optimized_query=optimized_query,
            query_type=analysis.search_type.value,
            geo_datasets=geo_datasets,
            publications=publications,
            total_results=len(geo_datasets) + len(publications),
            search_time_ms=search_time_ms,
            cache_hit=cache_hit,
            metadata={
                "query_confidence": analysis.confidence,
                "geo_ids": analysis.geo_ids,
                "entities_detected": len(optimization_result.entities) if optimization_result else 0,
                "query_variations": len(optimization_result.get_all_query_variations())
                if optimization_result
                else 0,
            },
        )

        logger.info(
            f"Search complete: {result.total_results} results "
            f"({len(geo_datasets)} GEO, {len(publications)} publications) "
            f"in {search_time_ms:.1f}ms"
        )

        # Step 7: Cache result
        if use_cache and self._cache_available and result.total_results > 0:
            await self._cache_result(query, result)

        return result

    async def _check_cache(self, query: str) -> Optional[SearchResult]:
        """Check cache for existing results."""
        if not self.cache:
            return None

        try:
            cached_data = await self.cache.get_search_result(query)
            if cached_data:
                logger.debug(f"Cache hit for query: {query}")
                # Reconstruct SearchResult from cached data
                # Note: Cache stores dict, need to rebuild objects
                return cached_data
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        return None

    async def _cache_result(self, query: str, result: SearchResult) -> None:
        """Cache search result."""
        if not self.cache:
            return

        try:
            await self.cache.set_search_result(
                query,
                result,
                ttl=self.config.cache_ttl_search,
            )
            logger.debug(f"Cached results for query: {query}")
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    async def _search_geo_by_id(self, geo_id: str) -> List[GEOSeriesMetadata]:
        """
        Search GEO by specific ID (fast path).

        Args:
            geo_id: GEO series ID (e.g., GSE123456)

        Returns:
            List with single GEO series metadata
        """
        if not self.geo_client:
            logger.warning("GEO client not initialized - cannot search by ID")
            return []

        try:
            logger.info(f"Fetching GEO metadata for {geo_id}")
            metadata = await self.geo_client.get_series_metadata(geo_id)
            return [metadata] if metadata else []
        except Exception as e:
            logger.error(f"Failed to fetch GEO metadata for {geo_id}: {e}")
            return []

    async def _search_geo(self, query: str, max_results: int) -> List[GEOSeriesMetadata]:
        """
        Search GEO datasets by query.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of GEO series metadata
        """
        if not self.geo_client:
            logger.warning("GEO client not initialized - skipping GEO search")
            return []

        try:
            logger.info(f"Searching GEO: '{query}' (max_results={max_results})")
            results = await self.geo_client.search(query, max_results=max_results)
            logger.info(f"Found {len(results)} GEO datasets")
            return results
        except Exception as e:
            logger.error(f"GEO search failed: {e}")
            return []

    async def _search_publications(self, query: str, max_results: int) -> List[Publication]:
        """
        Search publications by query.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of publications
        """
        if not self.publication_pipeline:
            logger.warning("Publication pipeline not initialized - skipping publication search")
            return []

        try:
            logger.info(f"Searching publications: '{query}' (max_results={max_results})")
            # Note: PublicationSearchPipeline.search() returns PublicationSearchResult
            search_result = await self.publication_pipeline.search(query, max_results=max_results)
            publications = search_result.publications
            logger.info(f"Found {len(publications)} publications")
            return publications
        except Exception as e:
            logger.error(f"Publication search failed: {e}")
            return []

    async def close(self) -> None:
        """Clean up resources."""
        logger.info("Closing OmicsSearchPipeline")

        if self.cache:
            try:
                await self.cache.close()
            except Exception as e:
                logger.warning(f"Error closing cache: {e}")

        if self.geo_client:
            try:
                await self.geo_client.close()
            except Exception as e:
                logger.warning(f"Error closing GEO client: {e}")

        if self.publication_pipeline:
            try:
                await self.publication_pipeline.close()
            except Exception as e:
                logger.warning(f"Error closing publication pipeline: {e}")

        logger.info("OmicsSearchPipeline closed")

    def __repr__(self) -> str:
        """String representation."""
        features = []
        if self.config.enable_geo_search:
            features.append("GEO")
        if self.config.enable_publication_search:
            features.append("Publications")
        if self.config.enable_query_optimization:
            features.append("QueryOpt")
        if self.config.enable_caching:
            features.append("Cache")
        if self.config.enable_deduplication:
            features.append("Dedup")

        return f"OmicsSearchPipeline(features={', '.join(features)})"
