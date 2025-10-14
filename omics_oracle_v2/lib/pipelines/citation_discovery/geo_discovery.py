"""
GEO Citation Discovery

Finds papers that cite GEO datasets using two strategies:
1. Papers citing the original publication (via PMID)
2. Papers mentioning the GEO ID in their text

No LLM analysis - pure citation discovery.
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Set

from omics_oracle_v2.lib.pipelines.citation_discovery.cache import DiscoveryCache
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import (
    EuropePMCConfig,
    OpenCitationsConfig,
    PubMedConfig,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.europepmc import EuropePMCClient
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.openalex import OpenAlexClient, OpenAlexConfig
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.opencitations import OpenCitationsClient
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.semantic_scholar import (
    SemanticScholarClient,
    SemanticScholarConfig,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.deduplication import (
    DeduplicationConfig,
    SmartDeduplicator,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.error_handling import retry_with_backoff
from omics_oracle_v2.lib.pipelines.citation_discovery.metrics_logger import MetricsLogger
from omics_oracle_v2.lib.pipelines.citation_discovery.quality_validation import (
    QualityAssessment,
    QualityConfig,
    QualityLevel,
    QualityValidator,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.relevance_scoring import RelevanceScorer, ScoringWeights
from omics_oracle_v2.lib.pipelines.citation_discovery.source_metrics import (
    SourceManager,
    SourceManagerConfig,
    SourcePriority,
)
from omics_oracle_v2.lib.search_engines.citations.models import Publication
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata

logger = logging.getLogger(__name__)


@dataclass
class CitationDiscoveryResult:
    """Results from citation discovery"""

    geo_id: str
    original_pmid: Optional[str]
    citing_papers: List[Publication]
    strategy_breakdown: dict  # Which papers came from which strategy
    source_metrics: Optional[dict] = None  # Performance metrics per source
    quality_assessments: Optional[List[QualityAssessment]] = None  # Quality validation results (Phase 8)
    quality_summary: Optional[dict] = None  # Quality distribution summary


class GEOCitationDiscovery:
    """
    Discover papers citing GEO datasets.

    Strategies:
    1. OpenAlex: Papers citing original publication
    2. Semantic Scholar: Papers citing original publication
    3. Europe PMC: Papers citing original publication
    4. OpenCitations: Papers citing original publication (Crossref data) (NEW!)
    5. PubMed: Papers mentioning GEO ID
    """

    def __init__(
        self,
        openalex_client: Optional[OpenAlexClient] = None,
        pubmed_client: Optional[PubMedClient] = None,
        semantic_scholar_client: Optional[SemanticScholarClient] = None,
        europepmc_client: Optional[EuropePMCClient] = None,
        opencitations_client: Optional[OpenCitationsClient] = None,
        cache: Optional[DiscoveryCache] = None,
        use_strategy_a: bool = True,  # Citation-based (OpenAlex + S2 + Europe PMC + OpenCitations)
        use_strategy_b: bool = True,  # Mention-based (PubMed)
        enable_cache: bool = True,
        enable_quality_validation: bool = True,  # Enable quality validation (Phase 8)
        quality_config: Optional[QualityConfig] = None,  # Custom quality configuration
        quality_filter_level: Optional[QualityLevel] = None,  # Minimum quality level (None = no filtering)
        enable_metrics_logging: bool = True,  # Enable metrics logging (Phase 10)
        metrics_logger: Optional[MetricsLogger] = None,  # Custom metrics logger
    ):
        # Initialize OpenAlex client if not provided
        if openalex_client is None:
            openalex_config = OpenAlexConfig(email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"), enable=True)
            self.openalex = OpenAlexClient(config=openalex_config)
            logger.info("Initialized OpenAlex client for citation discovery")
        else:
            self.openalex = openalex_client

        # Initialize Semantic Scholar client if not provided
        if semantic_scholar_client is None:
            s2_config = SemanticScholarConfig(api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY"))  # Optional
            self.semantic_scholar = SemanticScholarClient(config=s2_config)
            logger.info("Initialized Semantic Scholar client for citation discovery")
        else:
            self.semantic_scholar = semantic_scholar_client

        # Initialize Europe PMC client if not provided
        if europepmc_client is None:
            europepmc_config = EuropePMCConfig()
            self.europepmc = EuropePMCClient(config=europepmc_config)
            logger.info("Initialized Europe PMC client for citation discovery")
        else:
            self.europepmc = europepmc_client

        # Initialize OpenCitations client if not provided
        if opencitations_client is None:
            opencitations_config = OpenCitationsConfig()
            self.opencitations = OpenCitationsClient(config=opencitations_config)
            logger.info("✓ Initialized OpenCitations client for citation discovery")
        else:
            self.opencitations = opencitations_client

        # Initialize PubMed client if not provided
        if pubmed_client is None:
            pubmed_config = PubMedConfig(
                email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
                api_key=os.getenv("NCBI_API_KEY"),
                max_results=100,
            )
            self.pubmed_client = PubMedClient(pubmed_config)
        else:
            self.pubmed_client = pubmed_client

        # Initialize cache
        self.enable_cache = enable_cache
        if enable_cache:
            if cache is None:
                self.cache = DiscoveryCache(ttl_seconds=604800)  # 1 week default
                logger.info("Initialized citation discovery cache (TTL: 1 week)")
            else:
                self.cache = cache
        else:
            self.cache = None
            logger.info("Cache disabled for citation discovery")

        # Initialize smart deduplicator
        dedup_config = DeduplicationConfig(
            title_similarity_threshold=0.85,
            author_match_threshold=0.7,
            use_doi=True,
            use_pmid=True,
            use_title=True,
            use_authors=True,
            use_year=True,
        )
        self.deduplicator = SmartDeduplicator(dedup_config)
        logger.info("Initialized smart deduplicator (title≥85%, authors≥70%)")

        # Initialize relevance scorer with simplified 4-factor model
        scoring_weights = ScoringWeights(
            content_similarity=0.40,  # 40% - PRIMARY: what the paper discusses
            keyword_match=0.30,  # 30% - SECONDARY: direct keyword matches
            recency=0.20,  # 20% - TEMPORAL: recent papers (5yr cutoff)
            citation_count=0.10,  # 10% - IMPACT: citation count
        )
        self.scorer = RelevanceScorer(scoring_weights)
        logger.info("Initialized relevance scorer: content=40%, keywords=30%, recency=20%, citations=10%")

        # Initialize source manager for metrics and prioritization
        source_config = SourceManagerConfig(
            max_total_time=120.0,  # 2 minutes max for all sources
            per_source_timeout=60.0,  # 1 minute per source
            enable_adaptive_priority=True,
            enable_early_termination=False,  # Get all sources for comprehensive results
            save_metrics=True,
        )
        self.source_manager = SourceManager(source_config)

        # Register all sources with priorities and capabilities
        self.source_manager.register_source(
            "OpenAlex",
            priority=SourcePriority.CRITICAL,  # Fast, comprehensive, reliable
            rate_limit=10.0,  # 10 req/s with polite pool
            supports_batch=False,
            max_batch_size=1,
        )

        self.source_manager.register_source(
            "Semantic Scholar",
            priority=SourcePriority.HIGH,  # Good coverage, reliable
            rate_limit=10.0,  # 10 req/s (100 req/s with API key)
            supports_batch=False,
            max_batch_size=1,
        )

        self.source_manager.register_source(
            "Europe PMC",
            priority=SourcePriority.HIGH,  # Specialized biomedical focus
            rate_limit=3.0,  # 3 req/s
            supports_batch=False,
            max_batch_size=1,
        )

        self.source_manager.register_source(
            "OpenCitations",
            priority=SourcePriority.MEDIUM,  # Good data but slower
            rate_limit=1.0,  # 1 req/s
            supports_batch=True,  # Batch metadata fetching!
            max_batch_size=10,  # 10 DOIs per batch
        )

        self.source_manager.register_source(
            "PubMed",
            priority=SourcePriority.HIGH,  # Now supports citations via elink!
            rate_limit=3.0,  # 3 req/s (10 with API key)
            supports_batch=True,  # Batch fetching of details
            max_batch_size=100,  # Can fetch 100 papers at once
        )

        logger.info("✓ Initialized source manager with 5 sources")

        # Initialize quality validator (Phase 8)
        self.enable_quality_validation = enable_quality_validation
        self.quality_filter_level = quality_filter_level

        if enable_quality_validation:
            self.quality_validator = QualityValidator(config=quality_config or QualityConfig())
            filter_info = (
                f" (filtering: {quality_filter_level.value}+)" if quality_filter_level else " (no filtering)"
            )
            logger.info(f"✓ Initialized quality validator{filter_info}")
        else:
            self.quality_validator = None
            logger.info("Quality validation disabled")

        # Initialize metrics logger (Phase 10)
        self.enable_metrics_logging = enable_metrics_logging
        if enable_metrics_logging:
            self.metrics_logger = metrics_logger or MetricsLogger()
            logger.info("✓ Initialized metrics logger")
        else:
            self.metrics_logger = None
            logger.info("Metrics logging disabled")

        self.use_strategy_a = use_strategy_a
        self.use_strategy_b = use_strategy_b

    async def find_citing_papers(
        self, geo_metadata: GEOSeriesMetadata, max_results: int = 100
    ) -> CitationDiscoveryResult:
        """
        Find all papers citing this GEO dataset.

        Args:
            geo_metadata: GEO dataset metadata
            max_results: Maximum papers to return

        Returns:
            CitationDiscoveryResult with citing papers
        """
        logger.info(f"Finding papers citing {geo_metadata.geo_id}")

        # Check cache first
        if self.enable_cache and self.cache:
            cached_result = self.cache.get(geo_metadata.geo_id, strategy_key="all")
            if cached_result:
                logger.info(f"✓ Cache HIT for {geo_metadata.geo_id} ({len(cached_result)} papers)")

                # ALWAYS re-score cached papers (scores may have changed with weight updates)
                scored_papers = self.scorer.score_publications(cached_result, geo_metadata)
                scored_papers.sort(key=lambda x: x.total, reverse=True)

                # Attach scores to publications
                for score in scored_papers:
                    score.publication._relevance_score = score

                ranked_papers = [score.publication for score in scored_papers]

                # Apply quality validation to cached results (if enabled)
                quality_assessments = None
                quality_summary = None
                final_papers = ranked_papers[:max_results]

                if self.enable_quality_validation and self.quality_validator:
                    logger.info(f"Validating quality of {len(ranked_papers)} cached papers...")
                    quality_assessments = self.quality_validator.validate_publications(ranked_papers)

                    level_counts = {}
                    for level in QualityLevel:
                        level_counts[level.value] = sum(
                            1 for a in quality_assessments if a.quality_level == level
                        )

                    quality_summary = {
                        "total_assessed": len(quality_assessments),
                        "distribution": level_counts,
                        "average_score": sum(a.quality_score for a in quality_assessments)
                        / len(quality_assessments)
                        if quality_assessments
                        else 0,
                    }

                    if self.quality_filter_level:
                        level_order = {
                            QualityLevel.EXCELLENT: 5,
                            QualityLevel.GOOD: 4,
                            QualityLevel.ACCEPTABLE: 3,
                            QualityLevel.POOR: 2,
                            QualityLevel.REJECTED: 1,
                        }
                        min_order = level_order[self.quality_filter_level]
                        pre_filter_count = len(final_papers)
                        final_papers = [
                            a.publication
                            for a in quality_assessments
                            if level_order[a.quality_level] >= min_order and a.recommended_action != "exclude"
                        ][:max_results]

                        quality_summary["filter_level"] = self.quality_filter_level.value
                        quality_summary["pre_filter_count"] = pre_filter_count
                        quality_summary["post_filter_count"] = len(final_papers)
                        quality_summary["filtered_count"] = pre_filter_count - len(final_papers)

                        logger.info(
                            f"Quality filtering (cached, min_level={self.quality_filter_level.value}): "
                            f"{pre_filter_count} → {len(final_papers)} papers"
                        )

                # Log metrics for cached result (Phase 10)
                if self.enable_metrics_logging and self.metrics_logger:
                    source_metrics_data = {}  # No source metrics for cached results
                    dedup_data = {"total_raw": 0, "total_unique": len(ranked_papers), "duplicate_rate": 0}
                    quality_data = None
                    if quality_summary:
                        quality_data = {
                            "enabled": True,
                            "excellent": quality_summary.get("distribution", {}).get("excellent", 0),
                            "good": quality_summary.get("distribution", {}).get("good", 0),
                            "acceptable": quality_summary.get("distribution", {}).get("acceptable", 0),
                            "poor": quality_summary.get("distribution", {}).get("poor", 0),
                            "rejected": quality_summary.get("distribution", {}).get("rejected", 0),
                            "avg_score": quality_summary.get("average_score", 0),
                        }
                        if self.quality_filter_level:
                            quality_data["filter_applied"] = self.quality_filter_level.value
                            quality_data["pre_filter_count"] = quality_summary.get("pre_filter_count", 0)
                            quality_data["post_filter_count"] = quality_summary.get("post_filter_count", 0)

                    cache_data = {"hit": True, "strategy": "cached"}

                    self.metrics_logger.log_discovery_session(
                        geo_id=geo_metadata.geo_id,
                        sources=source_metrics_data,
                        deduplication=dedup_data,
                        quality_validation=quality_data,
                        cache=cache_data,
                        errors=[],
                    )

                # Reconstruct result from cached papers
                original_pmid = geo_metadata.pubmed_ids[0] if geo_metadata.pubmed_ids else None
                return CitationDiscoveryResult(
                    geo_id=geo_metadata.geo_id,
                    original_pmid=original_pmid,
                    citing_papers=final_papers,
                    strategy_breakdown={"cached": True},
                    quality_assessments=quality_assessments,
                    quality_summary=quality_summary,
                )

        all_papers: Set[Publication] = set()
        strategy_breakdown = {"strategy_a": [], "strategy_b": []}

        # Strategy A: Papers citing original publication
        # Get first PMID if available
        original_pmid = geo_metadata.pubmed_ids[0] if geo_metadata.pubmed_ids else None

        if self.use_strategy_a and original_pmid:
            logger.info(f"Strategy A: Finding papers citing PMID {original_pmid}")
            citing_via_pmid = self._find_via_citation(pmid=original_pmid, max_results=max_results)
            for paper in citing_via_pmid:
                all_papers.add(paper)
                strategy_breakdown["strategy_a"].append(paper.pmid or paper.doi)
            logger.info(f"  Found {len(citing_via_pmid)} papers via citation")

        # Strategy B: Papers mentioning GEO ID
        if self.use_strategy_b:
            logger.info(f"Strategy B: Finding papers mentioning {geo_metadata.geo_id}")
            mentioning_geo = self._find_via_geo_mention(geo_id=geo_metadata.geo_id, max_results=max_results)
            for paper in mentioning_geo:
                if paper not in all_papers:
                    all_papers.add(paper)
                    strategy_breakdown["strategy_b"].append(paper.pmid or paper.doi)
            logger.info(f"  Found {len(mentioning_geo)} papers mentioning GEO ID")

        # Convert set to list and apply final deduplication
        all_papers_list = list(all_papers)
        unique_papers = self.deduplicator.deduplicate(all_papers_list)
        dedup_stats = self.deduplicator.get_stats()

        logger.info(
            f"Final deduplication: {len(all_papers_list)} → {len(unique_papers)} unique papers "
            f"({dedup_stats.duplicates_removed} duplicates removed)"
        )

        # Reset deduplicator
        self.deduplicator.reset()

        # Score papers by relevance
        scored_papers = self.scorer.score_publications(unique_papers, geo_metadata)

        # Sort by relevance score (highest first)
        scored_papers.sort(key=lambda x: x.total, reverse=True)

        # Attach scores to publications for transparency
        for score in scored_papers:
            score.publication._relevance_score = score

        # Extract just the publications in ranked order
        ranked_papers = [score.publication for score in scored_papers]

        # Log top scores
        if scored_papers:
            top_5 = scored_papers[:5]
            logger.info("Top 5 papers by relevance:")
            for i, score in enumerate(top_5, 1):
                logger.info(f"  {i}. Score={score.total:.3f}: " f"{score.publication.title[:60]}...")

        # Cache the result (ranked papers)
        if self.enable_cache and self.cache:
            self.cache.set(geo_metadata.geo_id, ranked_papers, strategy_key="all")
            logger.debug(f"Cached {len(ranked_papers)} ranked papers for {geo_metadata.geo_id}")

        # Get source metrics summary
        metrics_summary = self.source_manager.get_summary()

        # Print metrics summary
        self.source_manager.print_summary()

        # Apply quality validation (Phase 8)
        quality_assessments = None
        quality_summary = None
        final_papers = ranked_papers[:max_results]  # Default: top N by relevance

        if self.enable_quality_validation and self.quality_validator:
            logger.info(f"Validating quality of {len(ranked_papers)} papers...")

            # Validate all papers
            quality_assessments = self.quality_validator.validate_publications(ranked_papers)

            # Create quality summary
            level_counts = {}
            for level in QualityLevel:
                level_counts[level.value] = sum(1 for a in quality_assessments if a.quality_level == level)

            quality_summary = {
                "total_assessed": len(quality_assessments),
                "distribution": level_counts,
                "average_score": sum(a.quality_score for a in quality_assessments) / len(quality_assessments)
                if quality_assessments
                else 0,
            }

            # Apply filtering if level specified
            if self.quality_filter_level:
                # Define quality level order
                level_order = {
                    QualityLevel.EXCELLENT: 5,
                    QualityLevel.GOOD: 4,
                    QualityLevel.ACCEPTABLE: 3,
                    QualityLevel.POOR: 2,
                    QualityLevel.REJECTED: 1,
                }

                min_order = level_order[self.quality_filter_level]

                # Filter papers by quality level
                pre_filter_count = len(final_papers)
                final_papers = [
                    a.publication
                    for a in quality_assessments
                    if level_order[a.quality_level] >= min_order and a.recommended_action != "exclude"
                ][:max_results]

                quality_summary["filter_level"] = self.quality_filter_level.value
                quality_summary["pre_filter_count"] = pre_filter_count
                quality_summary["post_filter_count"] = len(final_papers)
                quality_summary["filtered_count"] = pre_filter_count - len(final_papers)

                logger.info(
                    f"Quality filtering (min_level={self.quality_filter_level.value}): "
                    f"{pre_filter_count} → {len(final_papers)} papers "
                    f"({quality_summary['filtered_count']} filtered)"
                )
            else:
                logger.info("Quality validation complete (no filtering applied)")

        # Log metrics for this discovery session (Phase 10)
        if self.enable_metrics_logging and self.metrics_logger:
            # Build source metrics from source manager
            source_metrics_data = {}
            for source_name, metrics in metrics_summary.get("sources", {}).items():
                source_metrics_data[source_name] = {
                    "success": metrics.get("success_rate", "0%") != "0.00%",
                    "response_time": float(metrics.get("avg_response_time", "0s").rstrip("s")),
                    "papers_found": metrics.get("total_papers_found", 0),
                    "unique_papers": metrics.get("unique_papers_contributed", 0),
                }

            # Build deduplication stats
            dedup_data = {
                "total_raw": len(all_papers) if 'all_papers' in locals() else 0,
                "total_unique": len(unique_papers) if 'unique_papers' in locals() else 0,
                "duplicate_rate": (
                    (len(all_papers) - len(unique_papers)) / len(all_papers)
                    if 'all_papers' in locals() and len(all_papers) > 0
                    else 0
                ),
            }

            # Build quality validation data
            quality_data = None
            if quality_summary:
                quality_data = {
                    "enabled": True,
                    "excellent": quality_summary.get("distribution", {}).get("excellent", 0),
                    "good": quality_summary.get("distribution", {}).get("good", 0),
                    "acceptable": quality_summary.get("distribution", {}).get("acceptable", 0),
                    "poor": quality_summary.get("distribution", {}).get("poor", 0),
                    "rejected": quality_summary.get("distribution", {}).get("rejected", 0),
                    "avg_score": quality_summary.get("average_score", 0),
                }
                if self.quality_filter_level:
                    quality_data["filter_applied"] = self.quality_filter_level.value
                    quality_data["pre_filter_count"] = quality_summary.get("pre_filter_count", 0)
                    quality_data["post_filter_count"] = quality_summary.get("post_filter_count", 0)

            # Build cache info
            cache_data = {
                "hit": cached_result is not None if 'cached_result' in locals() else False,
                "strategy": "cached" if 'cached_result' in locals() and cached_result else "fresh",
            }

            # Log the session
            self.metrics_logger.log_discovery_session(
                geo_id=geo_metadata.geo_id,
                sources=source_metrics_data,
                deduplication=dedup_data,
                quality_validation=quality_data,
                cache=cache_data,
                errors=[],  # Could track errors if we enhance error handling
            )

        return CitationDiscoveryResult(
            geo_id=geo_metadata.geo_id,
            original_pmid=original_pmid,
            citing_papers=final_papers,
            strategy_breakdown=strategy_breakdown,
            source_metrics=metrics_summary,
            quality_assessments=quality_assessments,
            quality_summary=quality_summary,
        )

    def _find_via_citation(self, pmid: str, max_results: int) -> List[Publication]:
        """
        Strategy A: Find papers citing the original publication

        Uses OpenAlex, Semantic Scholar, Europe PMC, and OpenCitations with:
        - PARALLEL execution (all sources queried simultaneously!)
        - Retry logic for transient failures
        - Fallback if one source fails
        - Graceful degradation
        """
        import concurrent.futures

        all_citing_papers = []

        try:
            # Fetch original publication details from PubMed (with retry)
            @retry_with_backoff(max_retries=2, base_delay=1.0)
            def fetch_original():
                logger.info(f"Fetching full publication details for PMID {pmid}")
                return self.pubmed_client.fetch_by_id(pmid)

            original_pub = fetch_original()

            if not original_pub:
                logger.warning(f"Could not fetch details for PMID {pmid}")
                return []

            logger.info(
                f"Found original paper: {original_pub.title[:50]}... "
                f"DOI: {original_pub.doi}, PMID: {pmid}"
            )

            # PARALLEL EXECUTION: Define all fetch functions with metrics tracking
            def fetch_openalex():
                import time

                source_name = "OpenAlex"
                metrics = self.source_manager.get_source(source_name)

                if not self.source_manager.should_execute_source(source_name, len(all_citing_papers)):
                    return (source_name, [])

                if self.openalex and self.openalex.config.enable and original_pub.doi:
                    start_time = time.time()
                    try:

                        @retry_with_backoff(max_retries=2, base_delay=1.0)
                        def _fetch():
                            return self.openalex.get_citing_papers(
                                doi=original_pub.doi, max_results=max_results
                            )

                        papers = _fetch()
                        elapsed = time.time() - start_time
                        metrics.record_request(success=True, response_time=elapsed, papers_found=len(papers))
                        return (source_name, papers)
                    except Exception as e:
                        elapsed = time.time() - start_time
                        metrics.record_request(success=False, response_time=elapsed, error=str(e))
                        logger.warning(f"  ✗ {source_name} failed: {e}")
                        return (source_name, [])
                return (source_name, [])

            def fetch_semantic_scholar():
                import time

                source_name = "Semantic Scholar"
                metrics = self.source_manager.get_source(source_name)

                if not self.source_manager.should_execute_source(source_name, len(all_citing_papers)):
                    return (source_name, [])

                if self.semantic_scholar:
                    start_time = time.time()
                    try:

                        @retry_with_backoff(max_retries=2, base_delay=1.0)
                        def _fetch():
                            return self.semantic_scholar.get_citing_papers(pmid=pmid, limit=max_results)

                        papers = _fetch()
                        elapsed = time.time() - start_time
                        metrics.record_request(success=True, response_time=elapsed, papers_found=len(papers))
                        return (source_name, papers)
                    except Exception as e:
                        elapsed = time.time() - start_time
                        metrics.record_request(success=False, response_time=elapsed, error=str(e))
                        logger.warning(f"  ✗ {source_name} failed: {e}")
                        return (source_name, [])
                return (source_name, [])

            def fetch_europepmc():
                import time

                source_name = "Europe PMC"
                metrics = self.source_manager.get_source(source_name)

                if not self.source_manager.should_execute_source(source_name, len(all_citing_papers)):
                    return (source_name, [])

                if self.europepmc:
                    start_time = time.time()
                    try:

                        @retry_with_backoff(max_retries=2, base_delay=1.0)
                        def _fetch():
                            return self.europepmc.get_citing_papers(pmid=pmid, max_results=max_results)

                        papers = _fetch()
                        elapsed = time.time() - start_time
                        metrics.record_request(success=True, response_time=elapsed, papers_found=len(papers))
                        return (source_name, papers)
                    except Exception as e:
                        elapsed = time.time() - start_time
                        metrics.record_request(success=False, response_time=elapsed, error=str(e))
                        logger.warning(f"  ✗ {source_name} failed: {e}")
                        return (source_name, [])
                return (source_name, [])

            def fetch_opencitations():
                import time

                source_name = "OpenCitations"
                metrics = self.source_manager.get_source(source_name)

                if not self.source_manager.should_execute_source(source_name, len(all_citing_papers)):
                    return (source_name, [])

                if self.opencitations and original_pub.doi:
                    start_time = time.time()
                    try:

                        @retry_with_backoff(max_retries=2, base_delay=1.0)
                        def _fetch():
                            return self.opencitations.get_citing_papers(
                                doi=original_pub.doi, limit=max_results
                            )

                        papers = _fetch()
                        elapsed = time.time() - start_time
                        metrics.record_request(success=True, response_time=elapsed, papers_found=len(papers))
                        return (source_name, papers)
                    except Exception as e:
                        elapsed = time.time() - start_time
                        metrics.record_request(success=False, response_time=elapsed, error=str(e))
                        logger.warning(f"  ✗ {source_name} failed: {e}")
                        return (source_name, [])
                return (source_name, [])

            def fetch_pubmed_citations():
                import time

                source_name = "PubMed"
                metrics = self.source_manager.get_source(source_name)

                if not self.source_manager.should_execute_source(source_name, len(all_citing_papers)):
                    return (source_name, [])

                if self.pubmed_client:
                    start_time = time.time()
                    try:

                        @retry_with_backoff(max_retries=2, base_delay=1.0)
                        def _fetch():
                            return self.pubmed_client.get_citing_papers(pmid=pmid, max_results=max_results)

                        papers = _fetch()
                        elapsed = time.time() - start_time
                        metrics.record_request(success=True, response_time=elapsed, papers_found=len(papers))
                        return (source_name, papers)
                    except Exception as e:
                        elapsed = time.time() - start_time
                        metrics.record_request(success=False, response_time=elapsed, error=str(e))
                        logger.warning(f"  ✗ {source_name} failed: {e}")
                        return (source_name, [])
                return (source_name, [])

            # Execute all sources in parallel using ThreadPoolExecutor
            source_contributions = {}  # Track which papers came from which source

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(fetch_openalex),
                    executor.submit(fetch_semantic_scholar),
                    executor.submit(fetch_europepmc),
                    executor.submit(fetch_opencitations),
                    executor.submit(fetch_pubmed_citations),
                ]

                # Collect results as they complete
                for future in concurrent.futures.as_completed(futures):
                    try:
                        source_name, papers = future.result()
                        all_citing_papers.extend(papers)
                        # Track paper IDs from this source
                        source_contributions[source_name] = [p.doi or p.pmid or p.title for p in papers]
                        logger.info(f"  ✓ {source_name}: {len(papers)} citing papers")
                    except Exception as e:
                        logger.warning(f"  ✗ Source failed: {e}")

            # If all sources failed, return empty (graceful degradation)
            if not all_citing_papers:
                logger.error(
                    f"All citation sources failed for PMID {pmid}. "
                    "This may be a transient issue - try again later."
                )
                return []

            # Smart deduplication (fuzzy matching, title similarity, author overlap)
            initial_count = len(all_citing_papers)
            unique_papers = self.deduplicator.deduplicate(all_citing_papers)
            dedup_stats = self.deduplicator.get_stats()

            logger.info(
                f"Smart deduplication: {initial_count} → {len(unique_papers)} papers "
                f"({dedup_stats.duplicates_removed} duplicates removed)"
            )
            logger.debug(f"Dedup breakdown: {dedup_stats.to_dict()}")

            # Track which unique papers came from which source (after deduplication)
            unique_paper_ids = {p.doi or p.pmid or p.title for p in unique_papers}
            unique_source_contributions = {}
            for source_name, paper_ids in source_contributions.items():
                # Find which of this source's papers survived deduplication
                unique_from_source = [pid for pid in paper_ids if pid in unique_paper_ids]
                unique_source_contributions[source_name] = unique_from_source

            # Record deduplication metrics
            self.source_manager.record_deduplication(unique_source_contributions)

            # Reset deduplicator for next use
            self.deduplicator.reset()

            return unique_papers

        except Exception as e:
            logger.error(f"Citation search failed for PMID {pmid}: {e}")
            return []

    def _find_via_geo_mention(self, geo_id: str, max_results: int) -> List[Publication]:
        """
        Strategy B: Find papers mentioning GEO ID

        Uses PubMed with retry logic for reliability
        """
        papers = []

        # Search PubMed for GEO ID mentions (with retry)
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def search_pubmed():
            query = f"{geo_id}[All Fields]"
            return self.pubmed_client.search(query=query, max_results=max_results)

        try:
            pubmed_results = search_pubmed()
            papers.extend(pubmed_results)
            logger.info(f"  ✓ PubMed: {len(pubmed_results)} papers mentioning {geo_id}")
        except Exception as e:
            logger.error(f"  ✗ PubMed search failed for {geo_id} (after retries): {e}")

        return papers
