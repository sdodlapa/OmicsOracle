"""
Analysis client for LLM, Q&A, trends, and network analysis.

This is where the missing 90% of features are exposed!
"""

import logging
from typing import Any, Dict, List

from .base_client import APIClient
from .models import (
    AnalysisRequest,
    AnalysisResponse,
    CitationMetrics,
    NetworkGraph,
    Publication,
    QARequest,
    QAResponse,
    TrendAnalysis,
)

logger = logging.getLogger(__name__)


class AnalysisClient(APIClient):
    """
    Client for advanced analysis operations.

    Features:
    - LLM analysis of search results
    - Q&A over publications
    - Trend analysis over time
    - Citation network graphs
    - Detailed citation metrics

    Usage:
        async with AnalysisClient() as client:
            # LLM analysis
            analysis = await client.analyze_with_llm(
                query="CRISPR",
                results=search_results.results[:10]
            )

            # Ask questions
            answer = await client.ask_question(
                question="What delivery mechanisms are used?",
                context=search_results.results
            )

            # Get trends
            trends = await client.get_trends(search_results.results)

            # Citation network
            network = await client.get_network(search_results.results)
    """

    async def analyze_with_llm(
        self,
        query: str,
        results: List[Publication],
        analysis_type: str = "overview",
    ) -> AnalysisResponse:
        """
        Analyze search results using LLM.

        This was the MISSING feature from the dashboard!
        Backend has this ready at /api/v1/agents/analyze

        Args:
            query: Original search query
            results: Publications to analyze (max 20)
            analysis_type: Type of analysis ("overview", "detailed", "synthesis")

        Returns:
            AnalysisResponse with insights, gaps, recommendations

        Example:
            analysis = await client.analyze_with_llm(
                query="CRISPR gene editing",
                results=search_results.results[:10],
                analysis_type="overview"
            )

            print(analysis.overview)
            print("Key findings:", analysis.key_findings)
            print("Research gaps:", analysis.research_gaps)
        """
        # Build request
        request = AnalysisRequest(
            query=query,
            results=results[:20],  # Limit to 20 for token reasons
            analysis_type=analysis_type,
        )

        logger.info(f"Analyzing {len(results)} results with LLM...")

        # Call API
        response_data = await self.post(
            "/api/agents/analyze",
            json=request.dict(),
        )

        # Parse response
        response = AnalysisResponse(**response_data)

        logger.info(f"Analysis complete (confidence: {response.confidence:.2f})")

        return response

    async def ask_question(
        self,
        question: str,
        context: List[Publication],
    ) -> QAResponse:
        """
        Ask a question about search results (RAG-based Q&A).

        Another MISSING feature! Backend has RAG pipeline ready.

        Args:
            question: User question
            context: Publications to use as context (max 10)

        Returns:
            QAResponse with answer, sources, confidence

        Example:
            answer = await client.ask_question(
                question="What delivery mechanisms are most effective?",
                context=search_results.results
            )

            print(answer.answer)
            print("Sources:", answer.sources)
            print("Follow-up:", answer.follow_up_questions)
        """
        # Build request
        request = QARequest(
            question=question,
            context=context[:10],  # Limit context
        )

        logger.info(f"Q&A: {question}")

        # Call API
        response_data = await self.post(
            "/api/agents/query",
            json=request.dict(),
        )

        # Parse response
        response = QAResponse(**response_data)

        logger.info(f"Answer: {response.answer[:100]}...")

        return response

    async def get_trends(
        self,
        results: List[Publication],
    ) -> TrendAnalysis:
        """
        Analyze publication trends over time.

        Partially implemented in dashboard, but missing:
        - Growth rate
        - Predictions
        - Peak year detection

        Args:
            results: Publications to analyze

        Returns:
            TrendAnalysis with trends, growth, predictions

        Example:
            trends = await client.get_trends(search_results.results)

            print(f"Growth rate: {trends.growth_rate:.1f}% per year")
            print(f"Peak year: {trends.peak_year}")
            print(f"Predicted 5yr: {trends.prediction_5yr} papers")
        """
        logger.info(f"Analyzing trends for {len(results)} publications...")

        # Call API
        response_data = await self.post(
            "/api/predictions/trends",
            json={
                "publications": [pub.dict() for pub in results],
            },
        )

        # Parse response
        trends = TrendAnalysis(**response_data)

        logger.info(f"Trends: {len(trends.trends)} data points, " f"growth={trends.growth_rate:.1f}%")

        return trends

    async def get_network(
        self,
        results: List[Publication],
        min_citations: int = 5,
    ) -> NetworkGraph:
        """
        Build citation network graph.

        Another partially implemented feature!
        Dashboard shows basic network, but missing:
        - Cluster detection
        - Interactive controls
        - Network metrics

        Args:
            results: Publications to include in network
            min_citations: Minimum citations to include node

        Returns:
            NetworkGraph with nodes, edges, clusters

        Example:
            network = await client.get_network(
                results=search_results.results,
                min_citations=10
            )

            print(f"Network: {len(network.nodes)} nodes, {len(network.edges)} edges")
            print(f"Clusters: {len(network.clusters)}")
        """
        logger.info(f"Building citation network for {len(results)} publications...")

        # Call API
        response_data = await self.post(
            "/api/analytics/network",
            json={
                "publications": [pub.dict() for pub in results],
                "min_citations": min_citations,
            },
        )

        # Parse response
        network = NetworkGraph(**response_data)

        logger.info(
            f"Network: {len(network.nodes)} nodes, "
            f"{len(network.edges)} edges, "
            f"{len(network.clusters)} clusters"
        )

        return network

    async def get_citation_analysis(
        self,
        pub_id: str,
    ) -> CitationMetrics:
        """
        Get detailed citation analysis for a publication.

        This exists in backend but not fully displayed!

        Args:
            pub_id: Publication ID

        Returns:
            CitationMetrics with count, velocity, predictions
        """
        logger.info(f"Getting citation analysis for {pub_id}...")

        response_data = await self.get(
            f"/api/analytics/citations/{pub_id}",
            use_cache=True,
        )

        return CitationMetrics(**response_data)

    async def get_biomarker_analysis(
        self,
        results: List[Publication],
    ) -> Dict[str, Any]:
        """
        Get aggregated biomarker analysis.

        Currently only in analytics tab, not per-publication view!

        Args:
            results: Publications to analyze

        Returns:
            Dictionary with biomarker frequencies, co-occurrences, pathways
        """
        logger.info(f"Analyzing biomarkers from {len(results)} publications...")

        response_data = await self.post(
            "/api/analytics/biomarkers",
            json={
                "publications": [pub.dict() for pub in results],
            },
        )

        return response_data

    async def generate_report(
        self,
        query: str,
        results: List[Publication],
        include_analysis: bool = True,
    ) -> str:
        """
        Generate comprehensive analysis report.

        COMPLETELY MISSING from dashboard!
        Backend has report generation ready.

        Args:
            query: Original query
            results: Search results
            include_analysis: Include LLM analysis

        Returns:
            Formatted report (Markdown)
        """
        logger.info("Generating comprehensive report...")

        response_data = await self.post(
            "/api/agents/report",
            json={
                "query": query,
                "publications": [pub.dict() for pub in results],
                "include_analysis": include_analysis,
            },
        )

        return response_data["report"]
