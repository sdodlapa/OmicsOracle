"""
Publication Search Pipeline - Main orchestration following golden pattern.

This pipeline follows the AdvancedSearchPipeline pattern with:
- Feature toggles for incremental adoption
- Conditional initialization
- Configuration-driven design
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import List

from omics_oracle_v2.lib.cache import AsyncRedisCache
from omics_oracle_v2.lib.citations.clients.openalex import OpenAlexClient, OpenAlexConfig
from omics_oracle_v2.lib.citations.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.citations.clients.semantic_scholar import (
    SemanticScholarClient,
    SemanticScholarConfig,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.clients import CitationFinder
from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.publications.citations.llm_analyzer import LLMCitationAnalyzer
from omics_oracle_v2.lib.publications.clients.institutional_access import (
    InstitutionalAccessManager,
    InstitutionType,
)
from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.deduplication import AdvancedDeduplicator
from omics_oracle_v2.lib.publications.models import Publication, PublicationResult, PublicationSearchResult
from omics_oracle_v2.lib.publications.ranking.ranker import PublicationRanker

# REMOVED: NLP imports (BiomedicalNER, SynonymExpander, EntityType)
# Query preprocessing now handled by OmicsSearchPipeline's QueryOptimizer


logger = logging.getLogger(__name__)


class PublicationSearchPipeline:
    """
    Main pipeline for publication search and analysis.

    This pipeline follows the golden pattern from AdvancedSearchPipeline:
    - Feature toggles in configuration
    - Conditional initialization based on enabled features
    - Conditional execution in search flow

    Week 1-2 Features:
    - PubMed search (enable_pubmed)
    - Basic ranking

    Week 3 Features (TODO):
    - Google Scholar (enable_scholar)
    - Citation analysis (enable_citations)

    Week 4 Features (TODO):
    - PDF download (enable_pdf_download)
    - Full-text extraction (enable_fulltext)

    Example:
        >>> config = PublicationSearchConfig(
        ...     enable_pubmed=True,
        ...     pubmed_config=PubMedConfig(email="user@example.com")
        ... )
        >>> pipeline = PublicationSearchPipeline(config)
        >>> results = pipeline.search("cancer genomics", max_results=50)
    """

    def __init__(self, config: PublicationSearchConfig):
        """
        Initialize pipeline with configuration.

        Args:
            config: Publication search configuration
        """
        self.config = config
        self._initialized = False

        # Conditional initialization based on feature toggles
        # Week 1-2: Only PubMed
        if config.enable_pubmed:
            logger.info("Initializing PubMed client")
            self.pubmed_client = PubMedClient(config.pubmed_config)
        else:
            self.pubmed_client = None

        # OpenAlex (Primary citation source) - NEW
        if config.enable_citations or config.enable_openalex:
            logger.info("Initializing OpenAlex client")
            openalex_config = OpenAlexConfig(
                enable=True,
                email=config.pubmed_config.email
                if config.pubmed_config
                else None,  # Use same email for polite pool
            )
            self.openalex_client = OpenAlexClient(openalex_config)
        else:
            self.openalex_client = None

        # Week 3: Google Scholar (Day 13 - NOW IMPLEMENTED) - Fallback for citations
        if config.enable_scholar:
            logger.info("Initializing Google Scholar client (fallback for citations)")
            self.scholar_client = GoogleScholarClient(config.scholar_config)
        else:
            self.scholar_client = None

        # Semantic Scholar for citation enrichment (FREE alternative to Google Scholar)
        # Always enabled for citation metrics - no blocking/rate limit issues
        logger.info("Initializing Semantic Scholar client for citation enrichment")
        self.semantic_scholar_client = SemanticScholarClient(SemanticScholarConfig(enable=True))

        # Week 3: Citation analysis (Day 16-17 - NOW MULTI-SOURCE)
        if config.enable_citations:
            logger.info("Initializing citation analyzer with multi-source support")

            # Initialize with OpenAlex as primary, Scholar as fallback
            self.citation_finder = CitationFinder(
                openalex_client=self.openalex_client,
                scholar_client=self.scholar_client,
                semantic_scholar_client=self.semantic_scholar_client,
            )

            # Initialize LLM-powered analysis
            logger.info(f"Initializing LLM citation analyzer (provider={config.llm_config.provider})")
            # API keys come from environment variables
            self.llm_client = LLMClient(
                provider=config.llm_config.provider,
                model=config.llm_config.model,
                cache_enabled=config.llm_config.cache_enabled,
                temperature=config.llm_config.temperature,
            )
            self.llm_citation_analyzer = LLMCitationAnalyzer(self.llm_client)
        else:
            self.citation_finder = None
            self.llm_citation_analyzer = None

        # Week 4: Institutional access (NEW) - Initialize FIRST before PDF downloader
        if config.enable_institutional_access:
            logger.info(f"Initializing institutional access: {config.primary_institution}")
            # Primary institution
            primary_inst = (
                InstitutionType.GEORGIA_TECH
                if config.primary_institution.lower() == "gatech"
                else InstitutionType.OLD_DOMINION
            )
            self.institutional_manager = InstitutionalAccessManager(primary_inst)

            # Secondary/fallback institution
            if config.secondary_institution:
                secondary_inst = (
                    InstitutionType.GEORGIA_TECH
                    if config.secondary_institution.lower() == "gatech"
                    else InstitutionType.OLD_DOMINION
                )
                self.institutional_manager_fallback = InstitutionalAccessManager(secondary_inst)
            else:
                self.institutional_manager_fallback = None
        else:
            self.institutional_manager = None
            self.institutional_manager_fallback = None

        # Week 4: PDF processing (after institutional access)
        if config.enable_pdf_download:
            from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager

            logger.info("Initializing PDF download manager (async)")
            # Use new async PDFDownloadManager (replaces old PDFDownloader)
            self.pdf_downloader = PDFDownloadManager(
                max_concurrent=5,
                max_retries=3,
                validate_pdf=True,
            )
        else:
            self.pdf_downloader = None

        # Week 4: Full-text extraction
        if config.enable_fulltext:
            from omics_oracle_v2.lib.publications.pdf_text_extractor import PDFTextExtractor

            logger.info("Initializing PDF text extractor")
            self.pdf_text_extractor = PDFTextExtractor()
        else:
            self.pdf_text_extractor = None

        # Full-text manager for OA source access (NEW - Phase 1 complete)
        if config.enable_fulltext_retrieval:
            import os

            logger.info("Initializing FullTextManager with OA sources")
            fulltext_config = FullTextManagerConfig(
                enable_core=True,
                enable_biorxiv=True,
                enable_arxiv=True,
                enable_crossref=True,
                enable_openalex=True,  # Use OA URLs from OpenAlex metadata
                enable_unpaywall=True,  # ENABLED - 50% coverage improvement
                enable_scihub=True,  # WARNING: ENABLED - additional 25% coverage (use responsibly)
                enable_libgen=True,  # WARNING: ENABLED - additional 5-10% coverage (use responsibly)
                unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
                scihub_use_proxy=False,  # Set to True to use Tor/proxy
                libgen_use_proxy=False,  # Set to True to use Tor/proxy
                core_api_key=os.getenv("CORE_API_KEY"),
                download_pdfs=False,  # Just get URLs for now
                max_concurrent=3,
            )
            self.fulltext_manager = FullTextManager(fulltext_config)
        else:
            self.fulltext_manager = None

        # Week 3 Day 14: Advanced fuzzy deduplication
        if config.fuzzy_dedup_config.enable:
            logger.info("Initializing fuzzy deduplication")
            self.fuzzy_deduplicator = AdvancedDeduplicator(
                title_similarity_threshold=config.fuzzy_dedup_config.title_threshold,
                author_similarity_threshold=config.fuzzy_dedup_config.author_threshold,
                year_tolerance=config.fuzzy_dedup_config.year_tolerance,
                enable_fuzzy_matching=True,
            )
        else:
            self.fuzzy_deduplicator = None

        # Day 26: Redis caching for 10-100x speedup
        if config.enable_cache:
            logger.info(f"Initializing Redis cache: {config.redis_config.host}:{config.redis_config.port}")
            self.cache = AsyncRedisCache(
                host=config.redis_config.host,
                port=config.redis_config.port,
                db=config.redis_config.db,
                password=config.redis_config.password,
                default_ttl=config.redis_config.default_ttl,
            )
        else:
            self.cache = None

        # Core components (always initialized)
        self.ranker = PublicationRanker(config)

        # REMOVED: Query preprocessing (moved to OmicsSearchPipeline's QueryOptimizer)
        # No longer need duplicate NER or SynonymExpander here

        logger.info(
            f"PublicationSearchPipeline initialized with features: "
            f"pubmed={config.enable_pubmed}, "
            f"scholar={config.enable_scholar}, "
            f"citations={config.enable_citations}, "
            f"pdf={config.enable_pdf_download}, "
            f"fulltext={config.enable_fulltext}, "
            f"fuzzy_dedup={config.fuzzy_dedup_config.enable}, "
            f"cache={config.enable_cache}"
        )

    def initialize(self) -> None:
        """Initialize pipeline resources."""
        if self._initialized:
            return

        # Initialize clients that support it
        if self.pubmed_client:
            self.pubmed_client.initialize()

        if self.scholar_client:
            self.scholar_client.initialize()

        self._initialized = True
        logger.info("PublicationSearchPipeline initialized")

    def cleanup(self) -> None:
        """Clean up pipeline resources."""
        if not self._initialized:
            return

        # Cleanup clients
        if self.pubmed_client:
            self.pubmed_client.cleanup()

        if self.scholar_client:
            self.scholar_client.cleanup()

        # Cleanup FullTextManager (async, use asyncio.run)
        if self.fulltext_manager:
            import asyncio

            asyncio.run(self.fulltext_manager.cleanup())
            logger.info("FullTextManager cleaned up")

        # Close cache connection (Day 26)
        # Note: cache.close() is async, call it from async context
        # For sync cleanup, we just set to None (connection will close on garbage collection)
        if self.cache:
            self.cache = None
            logger.info("Redis cache marked for cleanup")

        self._initialized = False
        logger.info("PublicationSearchPipeline cleaned up")

    async def cleanup_async(self) -> None:
        """
        Async cleanup for pipeline resources (Day 26).

        Use this instead of cleanup() when in async context to properly close Redis.
        """
        if not self._initialized:
            return

        # Cleanup clients
        if self.pubmed_client:
            self.pubmed_client.cleanup()

        if self.scholar_client:
            self.scholar_client.cleanup()

        # Cleanup FullTextManager
        if self.fulltext_manager:
            await self.fulltext_manager.cleanup()
            logger.info("FullTextManager cleaned up")

        # Close cache connection properly
        if self.cache:
            await self.cache.close()
            logger.info("Redis cache connection closed")

        self._initialized = False
        logger.info("PublicationSearchPipeline cleaned up")

    # REMOVED: _preprocess_query(), _build_pubmed_query(), _build_openalex_query()
    # Query preprocessing now handled by OmicsSearchPipeline's QueryOptimizer
    # PublicationSearchPipeline will receive pre-optimized queries

    def search(
        self, query: str, max_results: int = 50, min_relevance_score: float = None, **kwargs
    ) -> PublicationResult:
        """
        Search for publications across enabled sources.

        This follows the conditional execution pattern:
        - Check each feature toggle
        - Execute component if enabled
        - Aggregate results
        - Rank and return

        Args:
            query: Search query
            max_results: Maximum total results to return
            min_relevance_score: Minimum relevance score filter
            **kwargs: Additional search parameters

        Returns:
            PublicationResult with ranked publications
        """
        start_time = time.time()

        # Ensure initialized
        if not self._initialized:
            self.initialize()

        logger.info(f"Searching publications for: '{query}'")

        # NOTE: Query preprocessing now handled by OmicsSearchPipeline's QueryOptimizer
        # This pipeline receives the optimized query directly

        # Step 1: Search enabled sources
        all_publications = []
        sources_used = []

        # 1a. PubMed search (conditional execution)
        if self.pubmed_client:
            try:
                logger.info("Searching PubMed...")
                pubmed_results = self.pubmed_client.search(query, max_results=max_results, **kwargs)
                all_publications.extend(pubmed_results)
                sources_used.append("pubmed")
                logger.info(f"PubMed returned {len(pubmed_results)} results")
            except Exception as e:
                logger.error(f"PubMed search failed: {e}")

        # 1b. Google Scholar search (Week 3 - conditional execution)
        if self.scholar_client:
            try:
                logger.info("Searching Google Scholar...")
                scholar_results = self.scholar_client.search(query, max_results)
                all_publications.extend(scholar_results)
                sources_used.append("google_scholar")
                logger.info(f"Scholar returned {len(scholar_results)} results")
            except Exception as e:
                logger.error(f"Google Scholar search failed: {e}")

        # 1c. OpenAlex search (NEW - sustainable alternative to Scholar)
        if self.openalex_client:
            try:
                logger.info("Searching OpenAlex...")
                openalex_results = self.openalex_client.search(query, max_results=max_results, **kwargs)
                all_publications.extend(openalex_results)
                sources_used.append("openalex")
                logger.info(f"OpenAlex returned {len(openalex_results)} results")
            except Exception as e:
                logger.error(f"OpenAlex search failed: {e}")

        # Step 2: Deduplicate (if enabled)
        if self.config.deduplication and len(all_publications) > 0:
            all_publications = self._deduplicate_publications(all_publications)
            logger.info(f"After deduplication: {len(all_publications)} publications")

        # Step 3: Enrich with institutional access info (Week 4 - NEW)
        if self.institutional_manager and len(all_publications) > 0:
            try:
                logger.info("Phase 1: Adding institutional access URLs to metadata...")
                for pub in all_publications:
                    # Check access status
                    access_status = self.institutional_manager.check_access_status(pub)

                    # Try fallback institution if primary doesn't have access
                    if not any(access_status.values()) and self.institutional_manager_fallback:
                        access_status = self.institutional_manager_fallback.check_access_status(pub)

                    # Add to metadata
                    pub.metadata["access_status"] = access_status
                    pub.metadata["has_access"] = any(access_status.values())

                    # Get access URL if available
                    access_url = self.institutional_manager.get_access_url(pub)
                    if not access_url and self.institutional_manager_fallback:
                        access_url = self.institutional_manager_fallback.get_access_url(pub)

                    if access_url:
                        pub.metadata["access_url"] = access_url
                        logger.debug(f"  Added institutional URL for: {pub.title[:50]}...")

            except Exception as e:
                logger.error(f"Institutional access enrichment failed: {e}")

        # Step 3.5: Enrich with full-text URLs (NEW - OA sources)
        if self.fulltext_manager and len(all_publications) > 0:
            try:
                import asyncio

                logger.info(f"Enriching {len(all_publications)} publications with full-text URLs...")

                # Initialize and get full-text (run in asyncio)
                async def enrich_fulltext():
                    if not self.fulltext_manager.initialized:
                        await self.fulltext_manager.initialize()
                    return await self.fulltext_manager.get_fulltext_batch(all_publications)

                # Run async function in event loop
                fulltext_results = asyncio.run(enrich_fulltext())

                # Attach full-text URLs to publications
                for pub, ft_result in zip(all_publications, fulltext_results):
                    if ft_result.success:
                        pub.metadata["fulltext_url"] = ft_result.url
                        pub.metadata["fulltext_source"] = ft_result.source.value
                        if ft_result.metadata:
                            pub.metadata["fulltext_metadata"] = ft_result.metadata

                # Log statistics
                success_count = sum(1 for r in fulltext_results if r.success)
                stats = self.fulltext_manager.get_statistics()
                logger.info(
                    f"Full-text enrichment: {success_count}/{len(all_publications)} "
                    f"publications ({stats['success_rate']} success rate)"
                )
                logger.info(f"Sources used: {stats['by_source']}")

            except Exception as e:
                logger.error(f"Full-text enrichment failed: {e}")

        # Step 4: Rank publications
        ranked_results = self.ranker.rank(all_publications, query, top_k=max_results)

        # Step 5: Citation analysis (Week 3 - conditional execution)
        if self.citation_finder and ranked_results:
            try:
                logger.info("Enriching with citation data...")
                ranked_results = self._enrich_citations(ranked_results)
            except Exception as e:
                logger.error(f"Citation enrichment failed: {e}")

        # Step 5.5: Enrich with Semantic Scholar citations (FREE alternative to Google Scholar)
        if self.semantic_scholar_client and ranked_results:
            try:
                logger.info("Enriching with Semantic Scholar citation data...")
                # Extract publications from ranked results
                publications = [result.publication for result in ranked_results]

                # Enrich with citations (batch processing with rate limiting)
                enriched_pubs = self.semantic_scholar_client.enrich_publications(publications)

                # Update ranked results with enriched publications
                for i, enriched_pub in enumerate(enriched_pubs):
                    ranked_results[i].publication = enriched_pub

                enriched_count = sum(1 for p in enriched_pubs if p.citations > 0)
                logger.info(
                    f"Semantic Scholar enrichment complete: {enriched_count}/{len(enriched_pubs)} publications have citation data"
                )
            except Exception as e:
                logger.error(f"Semantic Scholar enrichment failed: {e}")

        # Step 6: PDF download (Week 4 - conditional execution)
        if self.pdf_downloader and ranked_results:
            try:
                logger.info("Downloading PDFs...")
                self._download_pdfs(ranked_results)
            except Exception as e:
                logger.error(f"PDF download failed: {e}")

        # Step 7: Full-text extraction (Week 4 - conditional execution)
        if self.pdf_text_extractor and ranked_results:
            try:
                logger.info("Extracting full text...")
                ranked_results = self._extract_fulltext(ranked_results)
            except Exception as e:
                logger.error(f"Full-text extraction failed: {e}")

        # Step 8: Filter by minimum score (if specified)
        if min_relevance_score is not None:
            ranked_results = self.ranker.filter_by_score(ranked_results, min_relevance_score)
        elif self.config.min_relevance_score > 0:
            ranked_results = self.ranker.filter_by_score(ranked_results, self.config.min_relevance_score)

        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000

        # Build result
        result = PublicationResult(
            query=query,
            publications=ranked_results,
            total_found=len(all_publications),
            sources_used=sources_used,
            search_time_ms=search_time_ms,
            metadata={
                "config": {
                    "pubmed_enabled": self.config.enable_pubmed,
                    "scholar_enabled": self.config.enable_scholar,
                    "openalex_enabled": self.config.enable_openalex,
                    "citations_enabled": self.config.enable_citations,
                    "pdf_enabled": self.config.enable_pdf_download,
                    "fulltext_enabled": self.config.enable_fulltext,
                    "institutional_access_enabled": self.config.enable_institutional_access,
                    "primary_institution": self.config.primary_institution
                    if self.config.enable_institutional_access
                    else None,
                },
                "ranking_weights": self.config.ranking_weights,
            },
        )

        logger.info(
            f"Search complete: {len(ranked_results)} ranked results "
            f"from {len(all_publications)} total in {search_time_ms:.2f}ms"
        )

        return result

    async def search_async(
        self, query: str, max_results: int = 50, min_relevance_score: float = None, **kwargs
    ) -> PublicationResult:
        """
        Async search with Redis caching for 10-100x speedup (Day 26).

        Cache Strategy:
        - First query: 5-10 seconds (async search + ranking)
        - Cached query: <100ms (Redis lookup only)

        Args:
            query: Search query
            max_results: Maximum total results to return
            min_relevance_score: Minimum relevance score filter
            **kwargs: Additional search parameters

        Returns:
            PublicationResult with ranked publications (cached or fresh)
        """
        start_time = time.time()

        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                "search", query, max_results=max_results, min_score=min_relevance_score, **kwargs
            )

            cached_result = await self.cache.get(cache_key)
            if cached_result:
                cache_time_ms = (time.time() - start_time) * 1000
                logger.info(f"Cache HIT for query '{query}' ({cache_time_ms:.2f}ms)")

                # Add cache metadata
                cached_result.metadata["cached"] = True
                cached_result.metadata["cache_time_ms"] = cache_time_ms
                cached_result.search_time_ms = cache_time_ms

                return cached_result

            logger.info(f"Cache MISS for query '{query}' - performing search...")

        # Cache miss - perform regular search
        # Note: Running sync search in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: self.search(query, max_results, min_relevance_score, **kwargs)
        )

        # Store in cache
        if self.cache:
            ttl = self.config.redis_config.search_ttl
            await self.cache.set(cache_key, result, ttl=ttl)
            logger.info(f"Cached search result for query '{query}' (TTL: {ttl}s)")

        # Add cache metadata
        result.metadata["cached"] = False
        result.metadata["cache_ttl"] = self.config.redis_config.search_ttl if self.cache else None

        return result

    async def get_cache_stats(self) -> dict:
        """
        Get cache statistics (Day 26).

        Returns:
            Dict with hits, misses, and hit rate
        """
        if not self.cache:
            return {
                "enabled": False,
                "message": "Caching is disabled",
            }

        stats = self.cache.get_stats()
        stats["enabled"] = True
        stats["ttl_search"] = self.config.redis_config.search_ttl
        stats["ttl_llm"] = self.config.redis_config.llm_ttl
        return stats

    async def clear_cache(self, pattern: str = None):
        """
        Clear cache (Day 26).

        Args:
            pattern: Pattern to match (e.g., "search:*"). If None, clears all.
        """
        if not self.cache:
            logger.warning("Caching is disabled - nothing to clear")
            return

        if pattern:
            await self.cache.clear_pattern(pattern)
            logger.info(f"Cleared cache pattern: {pattern}")
        else:
            await self.cache.clear_all()
            logger.info("Cleared all cache")

    def _deduplicate_publications(self, publications: List[Publication]) -> List[Publication]:
        """
        Remove duplicate publications using ID-based and fuzzy matching.

        Week 3 Enhancement: Multi-pass deduplication
        - Pass 1: ID-based (PMID, PMCID, DOI) - fast exact matching
        - Pass 2: Fuzzy matching (title, authors, year) - catches variations (Day 14)

        Fuzzy matching handles:
        - Title variations (case, punctuation, typos)
        - Author name differences ("Smith, J." vs "J. Smith")
        - Preprint vs published pairs (year tolerance)

        Args:
            publications: List of publications

        Returns:
            Deduplicated list
        """
        if not publications:
            return []

        # Pass 1: ID-based deduplication (fast, exact)
        seen_pmids = set()
        seen_pmcids = set()
        seen_dois = set()
        unique_pubs = []

        for pub in publications:
            # Check if we've seen this publication by any identifier
            is_duplicate = False

            if pub.pmid and pub.pmid in seen_pmids:
                is_duplicate = True
            if pub.pmcid and pub.pmcid in seen_pmcids:
                is_duplicate = True
            if pub.doi and pub.doi in seen_dois:
                is_duplicate = True

            if not is_duplicate:
                # Add this publication and record its identifiers
                unique_pubs.append(pub)
                if pub.pmid:
                    seen_pmids.add(pub.pmid)
                if pub.pmcid:
                    seen_pmcids.add(pub.pmcid)
                if pub.doi:
                    seen_dois.add(pub.doi)

        id_duplicates_removed = len(publications) - len(unique_pubs)
        if id_duplicates_removed > 0:
            logger.info(f"Pass 1 (ID-based): Removed {id_duplicates_removed} duplicates")

        # Pass 2: Fuzzy deduplication (Day 14)
        if self.fuzzy_deduplicator:
            before_fuzzy = len(unique_pubs)
            unique_pubs = self.fuzzy_deduplicator.deduplicate(unique_pubs)
            fuzzy_duplicates_removed = before_fuzzy - len(unique_pubs)
            if fuzzy_duplicates_removed > 0:
                logger.info(f"Pass 2 (Fuzzy): Removed {fuzzy_duplicates_removed} additional duplicates")

        total_removed = len(publications) - len(unique_pubs)
        if total_removed > 0:
            logger.info(f"Total duplicates removed: {total_removed}/{len(publications)}")

        return unique_pubs

    def _enrich_citations(self, results: List[PublicationSearchResult]) -> List[PublicationSearchResult]:
        """
        Enrich results with citation data (Week 3 Day 16-17).

        Two-phase enrichment:
        1. Extract citing papers using CitationAnalyzer
        2. Analyze citations semantically using LLMCitationAnalyzer

        Args:
            results: Publication results

        Returns:
            Enriched results with citation analysis
        """
        if not self.citation_finder:
            logger.warning("Citation finder not available - skipping enrichment")
            return results

        logger.info(f"Enriching {len(results)} publications with citation data...")
        enriched_results = []

        for result in results:
            try:
                pub = result.publication

                # Phase 1: Get citing papers
                logger.debug(f"Finding citations for: {pub.title[:50]}...")
                citing_papers = self.citation_finder.find_citing_papers(
                    pub, max_results=min(100, self.config.llm_config.batch_size * 10)
                )

                # Store citation count
                pub.metadata["citing_papers_count"] = len(citing_papers)

                # Phase 2: LLM analysis of citations (if available and papers found)
                if self.llm_citation_analyzer and citing_papers:
                    logger.debug(f"Analyzing {len(citing_papers)} citations with LLM...")

                    # Get citation contexts
                    contexts = []
                    for citing_paper in citing_papers[: self.config.llm_config.batch_size * 2]:
                        citation_contexts = self.citation_finder.get_citation_contexts(pub, citing_paper)
                        for ctx in citation_contexts:
                            contexts.append((ctx, pub, citing_paper))

                    # Analyze in batches
                    if contexts:
                        usage_analyses = self.llm_citation_analyzer.analyze_batch(
                            contexts, batch_size=self.config.llm_config.batch_size
                        )

                        # Store analyses
                        pub.metadata["citation_analyses"] = [
                            {
                                "paper_id": a.paper_id,
                                "paper_title": a.paper_title,
                                "dataset_reused": a.dataset_reused,
                                "usage_type": a.usage_type,
                                "confidence": a.confidence,
                                "key_findings": a.key_findings,
                                "novel_biomarkers": a.novel_biomarkers,
                                "clinical_relevance": a.clinical_relevance,
                            }
                            for a in usage_analyses
                        ]

                        # Count dataset reuse
                        reuse_count = sum(1 for a in usage_analyses if a.dataset_reused)
                        pub.metadata["dataset_reuse_count"] = reuse_count

                        logger.info(
                            f"Citation analysis complete: {len(citing_papers)} citations, "
                            f"{reuse_count} dataset reuses detected"
                        )
                else:
                    pub.metadata["citation_analyses"] = []

                enriched_results.append(result)

            except Exception as e:
                logger.error(f"Failed to enrich citations for {result.publication.title[:50]}...: {e}")
                # Add publication anyway without citation enrichment
                enriched_results.append(result)

        logger.info(f"Citation enrichment complete for {len(enriched_results)} publications")
        return enriched_results

    def _download_pdfs(self, results: List[PublicationSearchResult]) -> None:
        """
        Download PDFs and extract full text for publications (Week 4).

        Uses institutional access to get PDFs from paywalled sources,
        downloads them, and extracts full text.

        Args:
            results: Publication results
        """
        if not self.pdf_downloader:
            logger.warning("PDF downloader not initialized - skipping PDF download")
            return

        publications = [result.publication for result in results]

        # Download PDFs in batch
        logger.info(f"Downloading PDFs for {len(publications)} publications...")
        try:
            # PDFDownloadManager.download_batch() is async, need to run in event loop
            # It does NOT accept max_workers parameter
            import asyncio

            pdf_dir = Path("data/pdfs")
            pdf_dir.mkdir(parents=True, exist_ok=True)

            # Run async download in event loop
            download_report = asyncio.run(
                self.pdf_downloader.download_batch(
                    publications=publications, output_dir=pdf_dir, url_field="fulltext_url"
                )
            )
            logger.info(
                f"PDF download complete: {download_report.successful}/{download_report.total} successful"
            )
        except Exception as e:
            logger.error(f"PDF download failed: {e}", exc_info=True)

        # Extract full text if enabled
        if self.pdf_text_extractor and self.config.enable_fulltext:
            pdf_count = len([p for p in publications if p.pdf_path and Path(p.pdf_path).exists()])
            logger.info(f"Extracting full text from {pdf_count} PDFs...")

            for pub in publications:
                if pub.pdf_path and Path(pub.pdf_path).exists():
                    try:
                        from datetime import datetime

                        # Extract text
                        full_text = self.pdf_text_extractor.extract_from_pdf(Path(pub.pdf_path))

                        if full_text:
                            pub.full_text = full_text
                            pub.full_text_source = "pdf"
                            pub.text_length = len(full_text)
                            pub.extraction_date = datetime.now()

                            # Get text stats
                            stats = self.pdf_text_extractor.get_text_stats(full_text)
                            pub.metadata["text_stats"] = stats

                            logger.info(f"Extracted {stats['words']} words from {pub.title[:50]}...")
                        else:
                            logger.warning(f"No text extracted from {pub.title[:50]}...")

                    except Exception as e:
                        logger.error(f"Text extraction failed for {pub.title[:50]}...: {e}")

        # Log download statistics if PDFs were downloaded
        if self.pdf_downloader and download_report.successful > 0:
            stats = self.pdf_downloader.get_download_stats()
            logger.info(
                f"PDF download complete: {stats['total_pdfs']} PDFs, " f"{stats['total_size_mb']} MB total"
            )

    def _extract_fulltext(self, results: List[PublicationSearchResult]) -> List[PublicationSearchResult]:
        """
        Extract full text from PDFs (Week 4).

        Args:
            results: Publication results

        Returns:
            Results with full text
        """
        # TODO: Week 4 implementation
        logger.warning("Full-text extraction not yet implemented (Week 4)")
        return results

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False

    @property
    def is_initialized(self) -> bool:
        """Check if pipeline is initialized."""
        return self._initialized

    def get_enabled_features(self) -> List[str]:
        """
        Get list of enabled features.

        Returns:
            List of feature names
        """
        features = []
        if self.config.enable_pubmed:
            features.append("pubmed")
        if self.config.enable_scholar:
            features.append("google_scholar")
        if self.config.enable_citations:
            features.append("citations")
        if self.config.enable_pdf_download:
            features.append("pdf_download")
        if self.config.enable_fulltext:
            features.append("fulltext_extraction")
        if self.config.enable_institutional_access:
            features.append(f"institutional_access_{self.config.primary_institution}")
        return features

    async def close(self) -> None:
        """Clean up async resources (Week 3 Day 3: Session cleanup)."""
        if hasattr(self, "pdf_downloader") and self.pdf_downloader:
            await self.pdf_downloader.close()
        if hasattr(self, "fulltext_manager") and self.fulltext_manager:
            await self.fulltext_manager.close()
