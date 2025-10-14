"""
SearchOrchestrator - Flat search architecture with no nested pipelines.

This replaces the nested OmicsSearchPipeline -> PublicationSearchPipeline architecture
with a single flat orchestrator that calls all clients directly in parallel.

Key improvements:
- True parallel execution (was sequential nested calls)
- Simpler architecture (1 layer instead of 3)
- Easier to test and maintain
- ~60% less code (600 LOC vs 1,800 LOC)
"""

import asyncio
import logging
import time
from typing import List, Optional

from omics_oracle_v2.lib.infrastructure.cache.redis_cache import RedisCache
from omics_oracle_v2.lib.query_processing.optimization.analyzer import QueryAnalyzer, SearchType
from omics_oracle_v2.lib.query_processing.optimization.optimizer import QueryOptimizer
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationResult
from omics_oracle_v2.lib.search_engines.citations.openalex import OpenAlexClient, OpenAlexConfig
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient
from omics_oracle_v2.lib.search_engines.citations.scholar import GoogleScholarClient, GoogleScholarConfig
from omics_oracle_v2.lib.search_engines.geo import GEOClient
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.search_engines.geo.query_builder import GEOQueryBuilder
from omics_oracle_v2.lib.search_orchestration.config import SearchConfig
from omics_oracle_v2.lib.search_orchestration.models import SearchResult

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """
    Flat search orchestrator that coordinates all search operations.

    Replaces the nested pipeline architecture with direct client calls.
    All searches execute in parallel for maximum performance.

    Example:
        >>> config = SearchConfig(
        ...     enable_geo=True,
        ...     enable_pubmed=True,
        ...     enable_openalex=True,
        ... )
        >>> orchestrator = SearchOrchestrator(config)
        >>> result = await orchestrator.search("diabetes")
    """

    def __init__(self, config: SearchConfig):
        """
        Initialize search orchestrator.

        Args:
            config: Search configuration
        """
        self.config = config

        # Stage 2: Query processing
        logger.info("Initializing query analyzer")
        self.query_analyzer = QueryAnalyzer()

        if config.enable_query_optimization:
            logger.info("Initializing query optimizer (NER + SapBERT)")
            self.query_optimizer = QueryOptimizer(
                enable_ner=config.enable_ner,
                enable_sapbert=config.enable_sapbert,
            )
        else:
            self.query_optimizer = None

        # Stage 4: Direct client access (no nested pipelines!)
        if config.enable_geo:
            logger.info("Initializing GEO client")
            self.geo_client = GEOClient()
            self.geo_query_builder = GEOQueryBuilder()
        else:
            self.geo_client = None
            self.geo_query_builder = None

        if config.enable_pubmed:
            logger.info("Initializing PubMed client")
            self.pubmed_client = PubMedClient(config.pubmed_config)
        else:
            self.pubmed_client = None

        if config.enable_openalex:
            logger.info("Initializing OpenAlex client")
            openalex_config = OpenAlexConfig(
                enable=True,
                email=config.openalex_email or config.pubmed_config.email,
            )
            self.openalex_client = OpenAlexClient(openalex_config)
        else:
            self.openalex_client = None

        if config.enable_scholar:
            logger.info("Initializing Google Scholar client")
            self.scholar_client = GoogleScholarClient(GoogleScholarConfig(enable=True))
        else:
            self.scholar_client = None

        # Stage 7: Caching
        if config.enable_cache:
            logger.info(f"Initializing Redis cache ({config.cache_host}:{config.cache_port})")
            try:
                self.cache = RedisCache(
                    host=config.cache_host,
                    port=config.cache_port,
                    db=config.cache_db,
                    default_ttl=config.cache_ttl,
                )
            except Exception as e:
                logger.warning(f"Cache initialization failed: {e}. Continuing without cache.")
                self.cache = None
        else:
            self.cache = None

        logger.info("SearchOrchestrator initialized successfully")

    async def search(
        self,
        query: str,
        search_type: Optional[str] = None,
        max_geo_results: Optional[int] = None,
        max_publication_results: Optional[int] = None,
        use_cache: bool = True,
    ) -> SearchResult:
        """
        Execute search across all enabled sources.

        Args:
            query: Search query
            search_type: Force search type (geo, publication, hybrid, auto)
            max_geo_results: Maximum GEO results
            max_publication_results: Maximum publication results
            use_cache: Whether to use cache

        Returns:
            SearchResult with datasets and publications
        """
        start_time = time.time()

        # Apply defaults
        max_geo_results = max_geo_results or self.config.max_geo_results
        max_publication_results = max_publication_results or self.config.max_publication_results

        logger.info(f"🔍 Search request: '{query}' (type={search_type})")

        # Step 1: Check cache
        cache_hit = False
        if use_cache and self.cache:
            try:
                cache_search_type = search_type or "auto"
                cache_key = f"{query}:{cache_search_type}"
                cached = await self.cache.get_search_result(cache_key, search_type=cache_search_type)
                if cached:
                    logger.info("✅ Cache hit - returning cached results")
                    cached_result = SearchResult(**cached)
                    cached_result.cache_hit = True
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache check failed: {e}")

        # Step 2: Analyze query type
        analysis = self.query_analyzer.analyze(query)
        logger.info(
            f"📊 Query analysis: type={analysis.search_type.value}, confidence={analysis.confidence:.2f}"
        )

        # Default to HYBRID for maximum recall
        if analysis.search_type == SearchType.AUTO:
            logger.info("AUTO mode: Enabling HYBRID search (GEO + Publications)")
            analysis.search_type = SearchType.HYBRID
        elif analysis.search_type == SearchType.PUBLICATIONS:
            logger.info("PUBLICATIONS mode: Enabling HYBRID to also find linked datasets")
            analysis.search_type = SearchType.HYBRID

        # Override if specified
        if search_type:
            if search_type.lower() == "geo":
                analysis.search_type = SearchType.GEO
            elif search_type.lower() == "publication":
                analysis.search_type = SearchType.PUBLICATIONS
            elif search_type.lower() == "hybrid":
                analysis.search_type = SearchType.HYBRID
            logger.info(f"🎯 Query type overridden to: {analysis.search_type.value}")

        # Step 3: Optimize query (if enabled and not GEO ID fast path)
        optimized_query = query
        if self.query_optimizer and analysis.search_type != SearchType.GEO_ID:
            try:
                logger.info("🔄 Optimizing query with NER + SapBERT")
                optimization_result = await self.query_optimizer.optimize(query)
                optimized_query = optimization_result.primary_query
                logger.info(f"✨ Query optimized: '{query}' -> '{optimized_query}'")
                logger.info(f"📝 Entities found: {len(optimization_result.entities)}")
            except Exception as e:
                logger.warning(f"Query optimization failed: {e}. Using original query.")
                optimized_query = query

        # Step 4: Execute searches based on type
        geo_datasets = []
        publications = []

        # GEO ID fast path
        if analysis.search_type == SearchType.GEO_ID and analysis.geo_ids:
            logger.info(f"⚡ GEO ID detected: {analysis.geo_ids[0]} - fast path")
            geo_datasets = await self._search_geo_by_id(analysis.geo_ids[0])

        # HYBRID: Run all searches in parallel
        elif analysis.search_type == SearchType.HYBRID:
            logger.info("🔄 HYBRID search: Running all sources in parallel")
            geo_datasets, publications = await self._search_parallel(
                optimized_query, max_geo_results, max_publication_results
            )

        # GEO only
        elif analysis.search_type == SearchType.GEO:
            logger.info("📊 GEO-only search")
            geo_datasets = await self._search_geo(optimized_query, max_geo_results)

        # Publications only
        elif analysis.search_type == SearchType.PUBLICATIONS:
            logger.info("📄 Publications-only search")
            publications = await self._search_publications(optimized_query, max_publication_results)

        # Step 5: Deduplicate GEO results (GEO IDs are unique)
        geo_datasets = self._deduplicate_geo(geo_datasets)

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
                "geo_count": len(geo_datasets),
                "publication_count": len(publications),
                "query_confidence": analysis.confidence,
            },
        )

        logger.info(f"✅ Search complete: {result.total_results} results in {search_time_ms:.1f}ms")

        # Step 7: Cache result
        if use_cache and self.cache and not cache_hit:
            try:
                cache_search_type = search_type or "auto"
                cache_key = f"{query}:{cache_search_type}"
                # Fixed: search_type should be 2nd positional arg, not keyword arg
                await self.cache.set_search_result(cache_key, cache_search_type, result.to_dict())
                logger.info("💾 Results cached")
            except Exception as e:
                logger.warning(f"Cache set failed: {e}")

        return result

    async def _search_parallel(
        self,
        query: str,
        max_geo_results: int,
        max_publication_results: int,
    ) -> tuple[List[GEOSeriesMetadata], List[Publication]]:
        """
        Execute all searches in parallel.

        This is the key improvement over the nested pipeline architecture.
        """
        tasks = []

        # GEO search task
        if self.geo_client:
            geo_task = self._search_geo(query, max_geo_results)
            tasks.append(("geo", geo_task))

        # Publication search tasks (run all in parallel)
        pub_tasks = []

        if self.pubmed_client:
            pubmed_task = self._search_pubmed(query, max_publication_results)
            pub_tasks.append(("pubmed", pubmed_task))

        if self.openalex_client:
            openalex_task = self._search_openalex(query, max_publication_results)
            pub_tasks.append(("openalex", openalex_task))

        if self.scholar_client:
            scholar_task = self._search_scholar(query, max_publication_results)
            pub_tasks.append(("scholar", scholar_task))

        # Execute all in parallel
        all_tasks = [t[1] for t in tasks] + [t[1] for t in pub_tasks]

        logger.info(f"⚡ Executing {len(all_tasks)} searches in parallel...")
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Parse results
        geo_datasets = []
        publications = []

        # GEO results
        if tasks:
            geo_result = results[0]
            if isinstance(geo_result, list):
                geo_datasets = geo_result
            elif isinstance(geo_result, Exception):
                logger.error(f"GEO search failed: {geo_result}")

        # Publication results
        pub_results = results[len(tasks) :]
        for i, result in enumerate(pub_results):
            source = pub_tasks[i][0]
            if isinstance(result, list):
                publications.extend(result)
                logger.info(f"📄 {source}: {len(result)} results")
            elif isinstance(result, Exception):
                logger.error(f"{source} search failed: {result}")

        return geo_datasets, publications

    async def _search_geo(self, query: str, max_results: int) -> List[GEOSeriesMetadata]:
        """
        Search GEO datasets with per-item caching for 10-50x speedup.

        Strategy:
        1. Get GEO IDs from search (fast, lightweight)
        2. Check cache for full metadata (batch operation)
        3. Fetch only uncached datasets from GEO
        4. Cache newly fetched datasets for future queries
        """
        if not self.geo_client:
            return []

        try:
            # Step 1: Build GEO-optimized query
            logger.info(f"[GEO] Original query: '{query}'")
            geo_query = self.geo_query_builder.build_query(query, mode="balanced")
            if geo_query != query:
                logger.info(f"[GEO] Query optimized: '{query}' -> '{geo_query}'")
            else:
                logger.info("[GEO] Query used as-is (no optimization)")

            logger.info(f"[GEO] Executing search with query: '{geo_query}'")

            # Step 2: Get GEO IDs from search (lightweight, returns IDs only)
            search_result = await self.geo_client.search(geo_query, max_results=max_results)

            if not search_result.geo_ids:
                logger.info("[GEO] No datasets found")
                return []

            geo_ids = search_result.geo_ids
            logger.info(f"[GEO] Found {len(geo_ids)} dataset IDs")

            # Step 3: Check cache for full metadata (batch operation - FAST!)
            cached_datasets = {}
            if self.cache:
                logger.info(f"[GEO] Checking cache for {len(geo_ids)} datasets (batch operation)...")
                cached_datasets = await self.cache.get_geo_datasets_batch(geo_ids)

            # Step 4: Identify what needs fetching
            cached_ids = [gse_id for gse_id, data in cached_datasets.items() if data is not None]
            missing_ids = [gse_id for gse_id in geo_ids if gse_id not in cached_ids]

            cache_hit_rate = (len(cached_ids) / len(geo_ids) * 100) if geo_ids else 0
            logger.info(
                f"[GEO] Cache: {len(cached_ids)}/{len(geo_ids)} datasets cached "
                f"({cache_hit_rate:.1f}% hit rate) - fetching {len(missing_ids)} from GEO"
            )

            # Step 5: Build result list starting with cached datasets
            datasets = []
            newly_fetched = {}

            # Add cached datasets first (instant!)
            for gse_id in cached_ids:
                try:
                    # Reconstruct GEOSeriesMetadata from cached dict
                    metadata = GEOSeriesMetadata(**cached_datasets[gse_id])
                    datasets.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached dataset {gse_id}: {e}")
                    missing_ids.append(gse_id)  # Re-fetch if cache corrupt

            # Step 6: Fetch missing datasets from GEO
            if missing_ids:
                logger.info(f"[GEO] Fetching {len(missing_ids)} uncached datasets from GEO...")
                for geo_id in missing_ids:
                    try:
                        metadata = await self.geo_client.get_metadata(geo_id)
                        if metadata:
                            datasets.append(metadata)
                            newly_fetched[geo_id] = metadata
                    except Exception as e:
                        logger.warning(f"Failed to fetch metadata for {geo_id}: {e}")
                        continue

                # Step 7: Cache newly fetched datasets (batch operation)
                if newly_fetched and self.cache:
                    cached_count = await self.cache.set_geo_datasets_batch(newly_fetched)
                    logger.info(f"[GEO] Cached {cached_count} newly fetched datasets")

            logger.info(
                f"[GEO] ✅ Retrieved {len(datasets)}/{len(geo_ids)} datasets "
                f"({len(cached_ids)} from cache, {len(newly_fetched)} from GEO)"
            )
            return datasets

        except Exception as e:
            logger.error(f"GEO search failed: {e}", exc_info=True)
            return []

    async def _search_geo_by_id(self, geo_id: str) -> List[GEOSeriesMetadata]:
        """
        Fast path for GEO ID lookup with caching.

        This is the fastest possible path - single dataset by ID.
        """
        if not self.geo_client:
            return []

        try:
            logger.info(f"⚡ Fetching GEO {geo_id} directly")

            # Check cache first
            if self.cache:
                cached = await self.cache.get_geo_metadata(geo_id)
                if cached:
                    logger.info(f"⚡ Cache HIT for {geo_id} - instant return!")
                    metadata = GEOSeriesMetadata(**cached)
                    return [metadata]

            # Fetch from GEO if not cached
            metadata = await self.geo_client.get_metadata(geo_id)

            # Cache for future lookups
            if metadata and self.cache:
                await self.cache.set_geo_metadata(geo_id, metadata)

            return [metadata] if metadata else []
        except Exception as e:
            logger.error(f"GEO ID lookup failed: {e}")
            return []

    async def _search_publications(self, query: str, max_results: int) -> List[Publication]:
        """Search all publication sources in parallel."""
        tasks = []

        if self.pubmed_client:
            tasks.append(("pubmed", self._search_pubmed(query, max_results)))

        if self.openalex_client:
            tasks.append(("openalex", self._search_openalex(query, max_results)))

        if self.scholar_client:
            tasks.append(("scholar", self._search_scholar(query, max_results)))

        if not tasks:
            return []

        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        publications = []
        for i, result in enumerate(results):
            source = tasks[i][0]
            if isinstance(result, list):
                publications.extend(result)
                logger.info(f"📄 {source}: {len(result)} results")
            elif isinstance(result, Exception):
                logger.error(f"{source} search failed: {result}")

        return publications

    async def _search_pubmed(self, query: str, max_results: int) -> List[Publication]:
        """Search PubMed."""
        if not self.pubmed_client:
            return []

        try:
            logger.info(f"🔍 Searching PubMed: '{query}'")
            results = await self.pubmed_client.search(query, max_results=max_results)
            # Extract Publication objects from PublicationResult wrappers
            publications = [r.publication for r in results if isinstance(r, PublicationResult)]
            logger.info(f"📄 PubMed: {len(publications)} publications")
            return publications
        except Exception as e:
            logger.error(f"PubMed search failed: {e}", exc_info=True)
            return []

    async def _search_openalex(self, query: str, max_results: int) -> List[Publication]:
        """Search OpenAlex."""
        if not self.openalex_client:
            return []

        try:
            logger.info(f"🔍 Searching OpenAlex: '{query}'")
            results = await self.openalex_client.search_publications(query, max_results=max_results)
            publications = [r.publication for r in results if isinstance(r, PublicationResult)]
            logger.info(f"📄 OpenAlex: {len(publications)} publications")
            return publications
        except Exception as e:
            logger.error(f"OpenAlex search failed: {e}", exc_info=True)
            return []

    async def _search_scholar(self, query: str, max_results: int) -> List[Publication]:
        """Search Google Scholar."""
        if not self.scholar_client:
            return []

        try:
            logger.info(f"🔍 Searching Google Scholar: '{query}'")
            results = await self.scholar_client.search(query, max_results=max_results)
            publications = [r.publication for r in results if isinstance(r, PublicationResult)]
            logger.info(f"📄 Scholar: {len(publications)} publications")
            return publications
        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}", exc_info=True)
            return []

    def _deduplicate_geo(self, datasets: List[GEOSeriesMetadata]) -> List[GEOSeriesMetadata]:
        """Remove duplicate GEO datasets by geo_id."""
        seen_ids = set()
        unique = []

        for dataset in datasets:
            geo_id = dataset.geo_id
            if geo_id not in seen_ids:
                seen_ids.add(geo_id)
                unique.append(dataset)
            else:
                logger.debug(f"Skipping duplicate: {geo_id}")

        if len(unique) < len(datasets):
            logger.info(f"🔄 Deduplicated {len(datasets)} -> {len(unique)} GEO datasets")

        return unique

    async def close(self):
        """Clean up resources.

        Week 3 Day 3: Added GEO client cleanup to cascade close() calls.
        """
        logger.info("Closing SearchOrchestrator")

        # Close GEO client (Week 3 Day 3)
        if self.geo_client:
            try:
                await self.geo_client.close()
                logger.debug("GEO client closed")
            except Exception as e:
                logger.warning(f"GEO client close failed: {e}")

        # Close cache
        if self.cache:
            try:
                await self.cache.close()
                logger.debug("Cache closed")
            except Exception as e:
                logger.warning(f"Cache close failed: {e}")

        logger.info("SearchOrchestrator closed")
