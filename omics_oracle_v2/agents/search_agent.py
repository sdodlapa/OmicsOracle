"""
Search Agent for GEO dataset searching.

Searches GEO database for relevant datasets using UnifiedGEOClient,
ranks results by relevance, and applies filtering criteria.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import nest_asyncio

from ..core.config import Settings
from ..lib.geo import GEOClient
from ..lib.geo.models import GEOSeriesMetadata
from ..lib.ranking import KeywordRanker
from ..lib.search.advanced import AdvancedSearchConfig, AdvancedSearchPipeline
from .base import Agent
from .context import AgentContext
from .exceptions import AgentExecutionError, AgentValidationError
from .models.search import RankedDataset, SearchInput, SearchOutput

# Allow nested event loops for API contexts (only if not using uvloop)
try:
    nest_asyncio.apply()
except ValueError:
    # uvloop doesn't support nest_asyncio, but we don't need it in API context
    logger = logging.getLogger(__name__)
    logger.debug("nest_asyncio not applied (uvloop detected)")

logger = logging.getLogger(__name__)


class SearchAgent(Agent[SearchInput, SearchOutput]):
    """
    Agent for searching GEO datasets.

    Uses GEOClient to search for datasets, ranks results
    by relevance, and applies user-specified filters.
    """

    def __init__(self, settings: Settings, enable_semantic: bool = False):
        """
        Initialize Search Agent.

        Args:
            settings: Application settings
            enable_semantic: Enable semantic search with AdvancedSearchPipeline
        """
        super().__init__(settings)
        self._geo_client: GEOClient = None
        self._ranker = KeywordRanker(settings.ranking)
        self._enable_semantic = enable_semantic
        self._semantic_pipeline: Optional[AdvancedSearchPipeline] = None
        self._semantic_index_loaded = False

    def _initialize_resources(self) -> None:
        """Initialize the GEO client and optionally semantic search."""
        try:
            logger.info("Initializing GEOClient for SearchAgent")
            self._geo_client = GEOClient(self.settings.geo)
            logger.info("GEOClient initialized successfully")

            # Initialize semantic search if enabled
            if self._enable_semantic:
                logger.info("Initializing AdvancedSearchPipeline for semantic search")
                self._initialize_semantic_search()
        except Exception as e:
            raise AgentExecutionError(f"Failed to initialize resources: {e}") from e

    def _cleanup_resources(self) -> None:
        """Clean up GEO client and semantic search resources."""
        if self._geo_client:
            logger.info("Cleaning up GEO client resources")
            self._geo_client = None

        if self._semantic_pipeline:
            logger.info("Cleaning up semantic search pipeline")
            self._semantic_pipeline = None
            self._semantic_index_loaded = False

    def _run_async(self, coro):
        """
        Run an async coroutine in a sync context.

        Handles both cases:
        - Running inside an async event loop (FastAPI context)
        - Running outside an event loop (standalone scripts)

        Args:
            coro: Coroutine to run

        Returns:
            Result of the coroutine
        """
        import asyncio

        try:
            # Check if there's a running loop
            _ = asyncio.get_running_loop()
            # We're in an async context - create a new thread with its own loop
            import threading

            result = [None]
            exception = [None]

            def run_in_thread():
                try:
                    # Create a new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result[0] = new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()

            if exception[0]:
                raise exception[0]
            return result[0]

        except RuntimeError:
            # No running loop - we can use asyncio.run directly
            return asyncio.run(coro)

    def _validate_input(self, input_data: SearchInput) -> SearchInput:
        """
        Validate search input.

        Args:
            input_data: Search input to validate

        Returns:
            Validated search input

        Raises:
            AgentValidationError: If validation fails
        """
        # Pydantic already validates most constraints
        # Additional custom validation if needed
        if input_data.min_samples and input_data.min_samples < 1:
            raise AgentValidationError("min_samples must be at least 1")

        return input_data

    def _process(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
        """
        Execute GEO dataset search.

        Uses semantic search if enabled and available, otherwise falls back to
        traditional keyword-based GEO search.

        Args:
            input_data: Validated search input
            context: Agent execution context

        Returns:
            Search results with ranked datasets

        Raises:
            AgentExecutionError: If search fails
        """
        try:
            context.set_metric("search_terms_count", len(input_data.search_terms))

            # Try semantic search first if enabled
            if self._enable_semantic and self._semantic_index_loaded:
                logger.info("Using semantic search pipeline")
                query = input_data.original_query or " ".join(input_data.search_terms)
                semantic_results = self._semantic_search(query, input_data, context)

                if semantic_results:
                    # Apply filters to semantic results
                    filtered_results = self._apply_semantic_filters(semantic_results, input_data)
                    context.set_metric("semantic_filtered_count", len(filtered_results))

                    filters_applied = self._get_applied_filters(input_data)
                    filters_applied["search_mode"] = "semantic"

                    return SearchOutput(
                        datasets=filtered_results,
                        total_found=len(semantic_results),
                        search_terms_used=input_data.search_terms,
                        filters_applied=filters_applied,
                    )

            # Fallback to traditional GEO search
            logger.info("Using traditional GEO search")
            context.set_metric("search_mode", "keyword")

            # 1. Execute search with GEO client
            logger.info(f"Searching GEO with {len(input_data.search_terms)} terms")
            search_query = self._build_search_query(input_data)
            context.set_metric("search_query", search_query)

            # Handle async operations properly
            search_result = self._run_async(
                self._geo_client.search(query=search_query, max_results=input_data.max_results)
            )

            context.set_metric("raw_results_count", search_result.total_found)
            logger.info(f"Found {search_result.total_found} initial results")

            # 2. Fetch metadata for the GEO IDs (batch fetch top results)
            top_ids = search_result.geo_ids[: input_data.max_results]
            logger.info(f"Fetching metadata for {len(top_ids)} datasets")

            geo_datasets = []
            for geo_id in top_ids:
                try:
                    metadata = self._run_async(self._geo_client.get_metadata(geo_id))
                    geo_datasets.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to fetch metadata for {geo_id}: {e}")
                    # Continue with other datasets

            context.set_metric("metadata_fetched_count", len(geo_datasets))
            logger.info(f"Successfully fetched {len(geo_datasets)} metadata records")

            # 3. Apply filters
            filtered_datasets = self._apply_filters(geo_datasets, input_data)
            context.set_metric("filtered_results_count", len(filtered_datasets))
            logger.info(f"Filtered to {len(filtered_datasets)} datasets")

            # 4. Rank results by relevance
            ranked_datasets = self._rank_datasets(filtered_datasets, input_data)
            context.set_metric("ranked_results_count", len(ranked_datasets))

            # 5. Track applied filters
            filters_applied = self._get_applied_filters(input_data)
            filters_applied["search_mode"] = "keyword"

            return SearchOutput(
                datasets=ranked_datasets,
                total_found=search_result.total_found,
                search_terms_used=input_data.search_terms,
                filters_applied=filters_applied,
            )

        except Exception as e:
            logger.error(f"Error executing search: {e}")
            raise AgentExecutionError(f"Failed to execute search: {e}") from e

    def _build_search_query(self, input_data: SearchInput) -> str:
        """
        Build GEO search query from search terms.

        Args:
            input_data: Search input with terms

        Returns:
            Formatted search query string
        """
        # Filter out generic/non-specific terms
        generic_terms = {"dataset", "datasets", "data", "study", "studies", "analysis", "profiling"}
        filtered_terms = [term for term in input_data.search_terms if term.lower() not in generic_terms]

        # If we filtered everything out, use original terms
        if not filtered_terms:
            filtered_terms = input_data.search_terms

        query_parts = []

        # Add main search terms
        for term in filtered_terms:
            # Escape special characters and quote multi-word terms
            if " " in term:
                query_parts.append(f'"{term}"')
            else:
                query_parts.append(term)

        # Determine whether to use AND or OR logic
        # Use AND if:
        # 1. Original query contains "and" or "&"
        # 2. We have 2-4 specific biomedical terms (suggests combined requirement)
        use_and_logic = False
        if input_data.original_query:
            query_lower = input_data.original_query.lower()
            if " and " in query_lower or " & " in query_lower:
                use_and_logic = True
            # Also use AND for "joint" or "combined" or "multi"
            elif any(word in query_lower for word in ["joint", "combined", "multi", "integrated"]):
                use_and_logic = True

        # If we have 2-3 specific terms and no clear OR intent, use AND
        if not use_and_logic and 2 <= len(query_parts) <= 3:
            use_and_logic = True

        # Combine with appropriate logic
        if use_and_logic:
            query = " AND ".join(query_parts)
            logger.info(f"Using AND logic for search: {query}")
        else:
            query = " OR ".join(query_parts)
            logger.info(f"Using OR logic for search: {query}")

        # Add organism filter if specified
        if input_data.organism:
            query = f"({query}) AND {input_data.organism}[Organism]"

        # Add study type filter if specified
        if input_data.study_type:
            query = f"({query}) AND {input_data.study_type}[DataSet Type]"

        return query

    def _apply_filters(
        self, datasets: List[GEOSeriesMetadata], input_data: SearchInput
    ) -> List[GEOSeriesMetadata]:
        """
        Apply filtering criteria to datasets.

        Args:
            datasets: Raw GEO datasets
            input_data: Search input with filter criteria

        Returns:
            Filtered list of datasets
        """
        filtered = datasets

        # Filter by minimum samples
        if input_data.min_samples:
            filtered = [d for d in filtered if d.sample_count and d.sample_count >= input_data.min_samples]
            logger.info(f"Filtered by min_samples={input_data.min_samples}: {len(filtered)} remain")

        # Additional filters can be added here
        # e.g., publication date, platform type, etc.

        return filtered

    def _apply_semantic_filters(
        self, datasets: List[RankedDataset], input_data: SearchInput
    ) -> List[RankedDataset]:
        """
        Apply filtering criteria to semantic search results.

        Args:
            datasets: Ranked datasets from semantic search
            input_data: Search input with filter criteria

        Returns:
            Filtered list of datasets
        """
        filtered = datasets

        # Filter by minimum samples
        if input_data.min_samples:
            filtered = [d for d in filtered if d.sample_count and d.sample_count >= input_data.min_samples]
            logger.info(
                f"Filtered semantic results by min_samples={input_data.min_samples}: "
                f"{len(filtered)} remain"
            )

        # Filter by organism if specified
        if input_data.organism:
            organism_lower = input_data.organism.lower()
            filtered = [d for d in filtered if d.organism and organism_lower in d.organism.lower()]
            logger.info(
                f"Filtered semantic results by organism={input_data.organism}: " f"{len(filtered)} remain"
            )

        return filtered

    def _rank_datasets(
        self, datasets: List[GEOSeriesMetadata], input_data: SearchInput
    ) -> List[RankedDataset]:
        """
        Rank datasets by relevance to search terms.

        Args:
            datasets: Filtered GEO datasets
            input_data: Search input with terms

        Returns:
            List of ranked datasets with scores
        """
        ranked = []

        for dataset in datasets:
            score, reasons = self._calculate_relevance(dataset, input_data)
            ranked.append(RankedDataset(dataset=dataset, relevance_score=score, match_reasons=reasons))

        # Sort by relevance score (highest first)
        ranked.sort(key=lambda d: d.relevance_score, reverse=True)

        return ranked

    def _calculate_relevance(
        self, dataset: GEOSeriesMetadata, input_data: SearchInput
    ) -> tuple[float, List[str]]:
        """
        Calculate relevance score for a dataset.

        Args:
            dataset: GEO dataset to score
            input_data: Search input with terms

        Returns:
            Tuple of (score, match_reasons)
        """
        score = 0.0
        reasons = []

        # Normalize search terms for matching
        search_terms_lower = {term.lower() for term in input_data.search_terms}

        # 1. Title matches (highest weight: 0.4)
        title_lower = (dataset.title or "").lower()
        title_matches = sum(1 for term in search_terms_lower if term in title_lower)
        if title_matches > 0:
            title_score = min(0.4, title_matches * 0.2)
            score += title_score
            reasons.append(f"Title matches {title_matches} search term(s)")

        # 2. Summary matches (medium weight: 0.3)
        summary_lower = (dataset.summary or "").lower()
        summary_matches = sum(1 for term in search_terms_lower if term in summary_lower)
        if summary_matches > 0:
            summary_score = min(0.3, summary_matches * 0.15)
            score += summary_score
            reasons.append(f"Summary matches {summary_matches} search term(s)")

        # 3. Organism match (bonus: 0.15)
        if input_data.organism:
            organism_lower = (dataset.organism or "").lower()
            if input_data.organism.lower() in organism_lower:
                score += 0.15
                reasons.append(f"Organism matches: {dataset.organism}")

        # 4. Sample count (bonus for more samples: up to 0.15)
        if dataset.sample_count:
            # Normalize: 0.05 for 10+ samples, 0.10 for 50+, 0.15 for 100+
            if dataset.sample_count >= 100:
                score += 0.15
                reasons.append(f"Large sample size: {dataset.sample_count} samples")
            elif dataset.sample_count >= 50:
                score += 0.10
                reasons.append(f"Good sample size: {dataset.sample_count} samples")
            elif dataset.sample_count >= 10:
                score += 0.05
                reasons.append(f"Adequate sample size: {dataset.sample_count} samples")

        # Normalize score to 0.0-1.0 range
        score = min(1.0, score)

        # Ensure minimum score if any match exists
        if not reasons:
            reasons.append("General database match")
            score = 0.1  # Minimum score for being in results

        return score, reasons

    def _get_applied_filters(self, input_data: SearchInput) -> Dict[str, str]:
        """
        Get dictionary of applied filters.

        Args:
            input_data: Search input

        Returns:
            Dictionary of filter names to values
        """
        filters = {}

        if input_data.organism:
            filters["organism"] = input_data.organism

        if input_data.study_type:
            filters["study_type"] = input_data.study_type

        if input_data.min_samples:
            filters["min_samples"] = str(input_data.min_samples)

        return filters

    def _initialize_semantic_search(self) -> None:
        """
        Initialize semantic search pipeline and load index.

        Loads the GEO dataset vector index if available, otherwise logs a warning.
        """
        try:
            # Create search configuration
            search_config = AdvancedSearchConfig(
                enable_query_expansion=True,
                enable_reranking=True,
                enable_rag=False,  # Disable RAG for SearchAgent (use in QueryAgent instead)
                enable_caching=True,
                top_k=50,  # Get more initial results for reranking
                rerank_top_k=20,  # Return top 20 after reranking
            )

            # Initialize pipeline
            self._semantic_pipeline = AdvancedSearchPipeline(search_config)
            logger.info("AdvancedSearchPipeline initialized")

            # Try to load GEO dataset index
            index_path = Path("data/vector_db/geo_index.faiss")
            if index_path.exists():
                logger.info(f"Loading GEO dataset index from {index_path}")
                self._semantic_pipeline.vector_db.load(str(index_path))
                index_size = self._semantic_pipeline.vector_db.size()
                logger.info(f"Loaded {index_size} GEO dataset embeddings")
                self._semantic_index_loaded = True
            else:
                logger.warning(
                    f"GEO dataset index not found at {index_path}. "
                    "Semantic search will fall back to keyword-only mode. "
                    "Run 'python -m omics_oracle_v2.scripts.embed_geo_datasets' to create index."
                )
                self._semantic_index_loaded = False

        except Exception as e:
            logger.error(f"Failed to initialize semantic search: {e}")
            logger.warning("Semantic search disabled, falling back to keyword search")
            self._enable_semantic = False
            self._semantic_pipeline = None

    def _semantic_search(
        self, query: str, input_data: SearchInput, context: AgentContext
    ) -> List[RankedDataset]:
        """
        Execute semantic search using AdvancedSearchPipeline.

        Args:
            query: Natural language search query
            input_data: Search input with filters
            context: Agent execution context

        Returns:
            List of ranked datasets from semantic search
        """
        if not self._semantic_pipeline or not self._semantic_index_loaded:
            logger.warning("Semantic search not available, using fallback")
            return []

        try:
            logger.info(f"Executing semantic search: {query[:100]}...")

            # Execute semantic search
            result = self._semantic_pipeline.search(
                query=query, top_k=input_data.max_results, return_answer=False
            )

            # Track metrics
            context.set_metric("semantic_search_used", True)
            context.set_metric("semantic_expanded_query", result.expanded_query)
            context.set_metric("semantic_cache_hit", result.cache_hit)
            context.set_metric("semantic_search_time_ms", result.total_time_ms)

            # Convert semantic results to RankedDataset format
            ranked_datasets = []
            results_to_use = result.reranked_results if result.reranked_results else result.results

            for idx, item in enumerate(results_to_use or [], 1):
                metadata = item.get("metadata", {})

                # Create GEOSeriesMetadata-like object
                # Note: Semantic results may have different structure
                ranked_datasets.append(
                    RankedDataset(
                        accession=metadata.get("id", item.get("id", f"SEM{idx}")),
                        title=metadata.get("title", ""),
                        summary=metadata.get("summary", item.get("text", "")[:500]),
                        organism=metadata.get("organism"),
                        sample_count=metadata.get("sample_count"),
                        platform=metadata.get("platform"),
                        pubmed_id=metadata.get("pubmed_id"),
                        submission_date=metadata.get("submission_date"),
                        relevance_score=item.get("score", 0.0),
                        rank=idx,
                        relevance_reasons=[
                            f"Semantic similarity: {item.get('semantic_score', 0.0):.3f}",
                            f"Keyword match: {item.get('keyword_score', 0.0):.3f}",
                            f"Combined score: {item.get('score', 0.0):.3f}",
                        ],
                    )
                )

            logger.info(f"Semantic search returned {len(ranked_datasets)} results")
            return ranked_datasets

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            context.set_metric("semantic_search_error", str(e))
            return []

    def enable_semantic_search(self, enable: bool = True) -> None:
        """
        Enable or disable semantic search at runtime.

        Args:
            enable: Whether to enable semantic search
        """
        was_enabled = self._enable_semantic
        self._enable_semantic = enable

        if enable and not was_enabled:
            # Initialize if enabling for the first time
            if not self._semantic_pipeline:
                logger.info("Enabling semantic search, initializing pipeline...")
                self._initialize_semantic_search()
        elif not enable and was_enabled:
            logger.info("Disabling semantic search")

    def is_semantic_search_available(self) -> bool:
        """
        Check if semantic search is available and ready.

        Returns:
            True if semantic search is enabled and index is loaded
        """
        return self._enable_semantic and self._semantic_index_loaded
