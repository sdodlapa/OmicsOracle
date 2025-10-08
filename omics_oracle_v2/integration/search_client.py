"""
Search client for OmicsOracle API.

Provides high-level interface for search operations.
"""

import logging
from typing import Any, Dict, List, Optional

from .adapters import adapt_search_response
from .base_client import APIClient
from .models import Publication, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)


class SearchClient(APIClient):
    """
    Client for search operations.

    Features:
    - Multi-database search
    - Hybrid search modes (keyword, semantic, hybrid)
    - Result enrichment (citations, quality, biomarkers)
    - Search history
    - Query suggestions

    Usage:
        async with SearchClient() as client:
            # Basic search
            response = await client.search("CRISPR gene editing")

            # Advanced search
            response = await client.search(
                query="cancer immunotherapy",
                databases=["pubmed", "google_scholar"],
                max_results=100,
                search_mode="hybrid",
                filters={"year_min": 2020}
            )

            # Get suggestions
            suggestions = await client.get_suggestions("CRIS")
    """

    async def search(
        self,
        query: str,
        databases: Optional[List[str]] = None,
        max_results: int = 100,
        search_mode: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
        enable_enrichment: bool = True,
    ) -> SearchResponse:
        """
        Execute a search query with filters.

        Args:
            query: Search query string
            databases: List of databases to search (pubmed, google_scholar, semantic_scholar)
            max_results: Maximum number of results
            filters: Additional search filters
            **kwargs: Additional parameters

        Returns:
            SearchResponse: Search results with metadata

        Example:
            ```python
            results = await client.search(
                "CRISPR gene therapy",
                databases=["pubmed", "semantic_scholar"],
                max_results=50
            )
            ```
        """
        # Transform user-friendly request to backend format
        # Backend expects: {search_terms: [str], max_results: int, enable_semantic: bool}
        search_terms = query.split() if isinstance(query, str) else query
        enable_semantic = "semantic_scholar" in (databases or [])

        backend_request = {
            "search_terms": search_terms,
            "max_results": max_results,
            "enable_semantic": enable_semantic,
            "filters": filters or {},
        }

        response = await self.post("/api/agents/search", json=backend_request)

        # Transform backend response to integration layer format
        return adapt_search_response(response)
        # Build request
        request = SearchRequest(
            query=query,
            databases=databases or ["pubmed", "google_scholar"],
            max_results=max_results,
            search_mode=search_mode,
            filters=filters,
            enable_enrichment=enable_enrichment,
        )

        logger.info(f"Searching: '{query}' (mode={search_mode}, max={max_results})")

        # Execute search
        response_data = await self.post(
            "/workflows/search",
            json=request.dict(exclude_none=True),
        )

        # Parse response
        response = SearchResponse(**response_data)

        logger.info(
            f"Search complete: {response.metadata.total_results} results in "
            f"{response.metadata.query_time:.2f}s"
        )

        return response

    async def get_publication(self, pub_id: str) -> Publication:
        """
        Get detailed information about a specific publication.

        Args:
            pub_id: Publication ID (PMID, DOI, etc.)

        Returns:
            Publication with full metadata
        """
        response_data = await self.get(f"/publications/{pub_id}", use_cache=True)
        return Publication(**response_data)

    async def get_suggestions(self, partial_query: str) -> List[str]:
        """
        Get query suggestions based on partial input.

        Args:
            partial_query: Partial query string

        Returns:
            List of suggested completions

        Example:
            suggestions = await client.get_suggestions("CRIS")
            # Returns: ["CRISPR", "CRISPR Cas9", "CRISPR gene editing", ...]
        """
        response = await self.get(
            "/search/suggestions",
            params={"q": partial_query},
            use_cache=True,
        )
        return response.get("suggestions", [])

    async def get_search_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent search history.

        Args:
            limit: Maximum number of history items

        Returns:
            List of recent searches with metadata
        """
        response = await self.get(
            "/search/history",
            params={"limit": limit},
            use_cache=False,
        )
        return response.get("history", [])

    async def save_search(
        self,
        query: str,
        results: SearchResponse,
        name: Optional[str] = None,
    ) -> str:
        """
        Save search results for later retrieval.

        Args:
            query: Original query
            results: Search response
            name: Optional name for saved search

        Returns:
            Saved search ID
        """
        response = await self.post(
            "/search/save",
            json={
                "query": query,
                "results": results.dict(),
                "name": name,
            },
        )
        return response["search_id"]

    async def get_saved_search(self, search_id: str) -> SearchResponse:
        """
        Retrieve a saved search.

        Args:
            search_id: Saved search ID

        Returns:
            Original search response
        """
        response = await self.get(f"/search/saved/{search_id}", use_cache=True)
        return SearchResponse(**response)

    async def export_results(
        self,
        results: SearchResponse,
        format: str = "csv",
    ) -> str:
        """
        Export search results to various formats.

        Args:
            results: Search response to export
            format: Export format ("csv", "json", "bibtex", "ris")

        Returns:
            Exported data as string
        """
        response = await self.post(
            "/search/export",
            json={
                "results": results.dict(),
                "format": format,
            },
        )
        return response["data"]

    async def get_related_publications(
        self,
        pub_id: str,
        count: int = 10,
    ) -> List[Publication]:
        """
        Get publications related to a specific paper.

        Args:
            pub_id: Publication ID
            count: Number of related papers

        Returns:
            List of related publications
        """
        response = await self.get(
            f"/publications/{pub_id}/related",
            params={"count": count},
            use_cache=True,
        )
        return [Publication(**pub) for pub in response["related"]]
