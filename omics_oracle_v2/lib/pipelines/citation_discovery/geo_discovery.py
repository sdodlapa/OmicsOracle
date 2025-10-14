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
    PubMedConfig,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.openalex import (
    OpenAlexClient,
    OpenAlexConfig,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import (
    PubMedClient,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.semantic_scholar import (
    SemanticScholarClient,
    SemanticScholarConfig,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.deduplication import (
    DeduplicationConfig,
    SmartDeduplicator,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.error_handling import (
    FallbackChain,
    retry_with_backoff,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.relevance_scoring import (
    RelevanceScorer,
    ScoringWeights,
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


class GEOCitationDiscovery:
    """
    Discover papers citing GEO datasets.

    Strategies:
    1. OpenAlex: Papers citing original publication
    2. Semantic Scholar: Papers citing original publication (NEW!)
    3. PubMed: Papers mentioning GEO ID
    """

    def __init__(
        self,
        openalex_client: Optional[OpenAlexClient] = None,
        pubmed_client: Optional[PubMedClient] = None,
        semantic_scholar_client: Optional[SemanticScholarClient] = None,
        cache: Optional[DiscoveryCache] = None,
        use_strategy_a: bool = True,  # Citation-based (OpenAlex + Semantic Scholar)
        use_strategy_b: bool = True,  # Mention-based (PubMed)
        enable_cache: bool = True,
    ):
        # Initialize OpenAlex client if not provided
        if openalex_client is None:
            openalex_config = OpenAlexConfig(
                email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"), enable=True
            )
            self.openalex = OpenAlexClient(config=openalex_config)
            logger.info("Initialized OpenAlex client for citation discovery")
        else:
            self.openalex = openalex_client

        # Initialize Semantic Scholar client if not provided
        if semantic_scholar_client is None:
            s2_config = SemanticScholarConfig(
                api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY")  # Optional
            )
            self.semantic_scholar = SemanticScholarClient(config=s2_config)
            logger.info("Initialized Semantic Scholar client for citation discovery")
        else:
            self.semantic_scholar = semantic_scholar_client

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
            keyword_match=0.30,      # 30% - SECONDARY: direct keyword matches
            recency=0.20,            # 20% - TEMPORAL: recent papers (5yr cutoff)
            citation_count=0.10,     # 10% - IMPACT: citation count
        )
        self.scorer = RelevanceScorer(scoring_weights)
        logger.info("Initialized relevance scorer: content=40%, keywords=30%, recency=20%, citations=10%")

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
                
                # Reconstruct result from cached papers
                original_pmid = geo_metadata.pubmed_ids[0] if geo_metadata.pubmed_ids else None
                return CitationDiscoveryResult(
                    geo_id=geo_metadata.geo_id,
                    original_pmid=original_pmid,
                    citing_papers=ranked_papers[:max_results],
                    strategy_breakdown={"cached": True},
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
                logger.info(
                    f"  {i}. Score={score.total:.3f}: "
                    f"{score.publication.title[:60]}..."
                )

        # Cache the result (ranked papers)
        if self.enable_cache and self.cache:
            self.cache.set(geo_metadata.geo_id, ranked_papers, strategy_key="all")
            logger.debug(f"Cached {len(ranked_papers)} ranked papers for {geo_metadata.geo_id}")

        return CitationDiscoveryResult(
            geo_id=geo_metadata.geo_id,
            original_pmid=original_pmid,
            citing_papers=ranked_papers[:max_results],  # Return top N by relevance
            strategy_breakdown=strategy_breakdown,
        )

    def _find_via_citation(self, pmid: str, max_results: int) -> List[Publication]:
        """
        Strategy A: Find papers citing the original publication

        Uses both OpenAlex and Semantic Scholar with:
        - Retry logic for transient failures
        - Fallback if one source fails
        - Graceful degradation
        """
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

            # Source 1: OpenAlex (DOI-based) with retry
            if self.openalex and self.openalex.config.enable and original_pub.doi:
                @retry_with_backoff(max_retries=2, base_delay=1.0)
                def fetch_openalex():
                    return self.openalex.get_citing_papers(
                        doi=original_pub.doi, max_results=max_results
                    )

                try:
                    openalex_citations = fetch_openalex()
                    all_citing_papers.extend(openalex_citations)
                    logger.info(f"  ✓ OpenAlex: {len(openalex_citations)} citing papers")
                except Exception as e:
                    logger.warning(f"  ✗ OpenAlex failed (will try Semantic Scholar): {e}")

            # Source 2: Semantic Scholar (PMID-based) with retry
            if self.semantic_scholar:
                @retry_with_backoff(max_retries=2, base_delay=1.0)
                def fetch_semantic_scholar():
                    return self.semantic_scholar.get_citing_papers(pmid=pmid, limit=max_results)

                try:
                    s2_citations = fetch_semantic_scholar()
                    all_citing_papers.extend(s2_citations)
                    logger.info(f"  ✓ Semantic Scholar: {len(s2_citations)} total papers")
                except Exception as e:
                    logger.warning(f"  ✗ Semantic Scholar failed: {e}")

            # If both sources failed, return empty (graceful degradation)
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
