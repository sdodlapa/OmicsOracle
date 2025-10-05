"""
Search Agent for GEO dataset searching.

Searches GEO database for relevant datasets using UnifiedGEOClient,
ranks results by relevance, and applies filtering criteria.
"""

import logging
from typing import Dict, List

import nest_asyncio

from ..core.config import Settings
from ..lib.geo import GEOClient
from ..lib.geo.models import GEOSeriesMetadata
from ..lib.ranking import KeywordRanker
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

    def __init__(self, settings: Settings):
        """
        Initialize Search Agent.

        Args:
            settings: Application settings
        """
        super().__init__(settings)
        self._geo_client: GEOClient = None
        self._ranker = KeywordRanker(settings.ranking)

    def _initialize_resources(self) -> None:
        """Initialize the GEO client."""
        try:
            logger.info("Initializing GEOClient for SearchAgent")
            self._geo_client = GEOClient(self.settings.geo)
            logger.info("GEOClient initialized successfully")
        except Exception as e:
            raise AgentExecutionError(f"Failed to initialize GEO client: {e}") from e

    def _cleanup_resources(self) -> None:
        """Clean up GEO client resources."""
        if self._geo_client:
            logger.info("Cleaning up GEO client resources")
            self._geo_client = None

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
