#!/usr/bin/env python3
"""
OmicsOracle Search Enhancer Integration

This script integrates the advanced search features with the OmicsOracle search API.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
# Import the search enhancer
try:
    from src.omics_oracle.search.advanced_search_enhancer import AdvancedSearchEnhancer
except ImportError:
    logger.error("Failed to import AdvancedSearchEnhancer. Make sure the path is correct.")
    sys.exit(1)


class SearchEnhancerIntegration:
    """Integrates advanced search features with the OmicsOracle search API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the search enhancer integration.

        Args:
            base_url: Base URL of the OmicsOracle API
        """
        self.base_url = base_url
        self.search_endpoint = f"{base_url}/api/v1/search"
        self.enhancer = AdvancedSearchEnhancer()

    async def get_base_search_results(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get search results from the base OmicsOracle search API.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            Dictionary with search results
        """
        logger.info(f"Getting base search results for query: {query}")

        params = {"q": query, "limit": limit}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.search_endpoint, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Search API error: {response.status} - {error_text}")
                        return {
                            "error": f"Search API returned status {response.status}",
                            "results": [],
                        }
            except Exception as e:
                logger.error(f"Error fetching search results: {str(e)}")
                return {"error": str(e), "results": []}

    async def get_enhanced_search_results(
        self,
        query: str,
        limit: int = 20,
        apply_semantic_ranking: bool = True,
        apply_clustering: bool = True,
        generate_reformulations: bool = True,
    ) -> Dict[str, Any]:
        """
        Get enhanced search results by combining base search with advanced features.

        Args:
            query: The search query
            limit: Maximum number of results to return
            apply_semantic_ranking: Whether to apply semantic ranking
            apply_clustering: Whether to apply result clustering
            generate_reformulations: Whether to generate query reformulations

        Returns:
            Dictionary with enhanced search results
        """
        # Get base search results
        base_results = await self.get_base_search_results(query, limit)

        # Check for errors in base results
        if "error" in base_results:
            return base_results

        # Apply enhancements
        results = base_results.get("results", [])
        enhanced_results = self.enhancer.enhance_search_results(
            results=results,
            query=query,
            apply_semantic_ranking=apply_semantic_ranking,
            apply_clustering=apply_clustering,
            generate_reformulations=generate_reformulations,
        )

        # Add metadata from base results
        if "metadata" in base_results:
            enhanced_results["metadata"] = base_results["metadata"]

        return enhanced_results

    async def run_demo_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Run a set of demo queries to showcase the enhanced search features.

        Args:
            queries: List of search queries to run

        Returns:
            List of enhanced search results for each query
        """
        logger.info(f"Running {len(queries)} demo queries")

        all_results = []

        for query in queries:
            logger.info(f"Processing query: {query}")

            # Get enhanced search results
            enhanced_results = await self.get_enhanced_search_results(query)
            all_results.append(enhanced_results)

            # Add a small delay between queries
            await asyncio.sleep(1)

        return all_results

    def save_demo_results(
        self, results: List[Dict[str, Any]], output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        Save demo query results to files.

        Args:
            results: List of enhanced search results
            output_dir: Directory to save results (defaults to './demo_results')

        Returns:
            List of paths to saved result files
        """
        if output_dir is None:
            output_dir = Path("demo_results")

        output_dir.mkdir(exist_ok=True)
        saved_files = []

        for i, result in enumerate(results):
            query = result.get("query", f"query_{i}")
            safe_query = "".join(c if c.isalnum() else "_" for c in query)[:30]

            # Save as JSON
            json_path = output_dir / f"enhanced_search_{safe_query}.json"
            with open(json_path, "w") as f:
                json.dump(result, f, indent=2)
            saved_files.append(json_path)

            # Generate and save a summary markdown file
            md_path = output_dir / f"enhanced_search_{safe_query}.md"
            with open(md_path, "w") as f:
                f.write(self._generate_result_summary(result))
            saved_files.append(md_path)

        return saved_files

    def _generate_result_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate a markdown summary of enhanced search results.

        Args:
            result: Enhanced search results

        Returns:
            Markdown formatted summary
        """
        summary = []

        # Header
        summary.append(f"# Enhanced Search Results: '{result.get('query', 'Unknown Query')}'")
        summary.append("")

        # Enhancements applied
        enhancements = result.get("enhancements", [])
        if enhancements:
            summary.append("## Applied Enhancements")
            for enhancement in enhancements:
                summary.append(f"- {enhancement.replace('_', ' ').title()}")
            summary.append("")

        # Query reformulations
        if "query_reformulations" in result and result["query_reformulations"]:
            summary.append("## Suggested Query Reformulations")
            for ref in result["query_reformulations"]:
                summary.append(f"- **{ref['query']}** - {ref['explanation']}")
            summary.append("")

        # Clusters
        if "clusters" in result and result["clusters"]:
            summary.append("## Result Clusters")
            for cluster in result["clusters"]:
                summary.append(f"### {cluster['label']} ({cluster['count']} results)")
                summary.append("")
            summary.append("")

        # Results
        results = result.get("results", [])
        if results:
            summary.append(f"## Search Results ({len(results)} total)")

            for i, item in enumerate(results[:10]):  # Show top 10 results
                title = item.get("title", f"Result {i+1}")
                summary.append(f"### {i+1}. {title}")

                if "semantic_score" in item:
                    summary.append(f"**Semantic Score:** {item['semantic_score']:.2f}")

                if "id" in item:
                    summary.append(f"**ID:** {item['id']}")

                if "metadata" in item and isinstance(item["metadata"], dict):
                    summary.append("**Metadata:**")
                    for key, value in item["metadata"].items():
                        if value:
                            summary.append(f"- {key.replace('_', ' ').title()}: {value}")

                summary.append("")

            if len(results) > 10:
                summary.append(f"*...and {len(results) - 10} more results*")
                summary.append("")

        return "\n".join(summary)


async def main():
    """Main function to run the search enhancer integration."""
    parser = argparse.ArgumentParser(description="OmicsOracle Search Enhancer Integration")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the OmicsOracle API",
    )
    parser.add_argument("--query", help="Single search query to process")
    parser.add_argument("--demo", action="store_true", help="Run a set of demo queries")
    parser.add_argument("--output-dir", default="demo_results", help="Directory to save results")

    args = parser.parse_args()

    integration = SearchEnhancerIntegration(base_url=args.url)
    output_dir = Path(args.output_dir)

    if args.query:
        # Process a single query
        result = await integration.get_enhanced_search_results(args.query)
        integration.save_demo_results([result], output_dir)

        print(f"\n✅ Enhanced search results saved to {output_dir}")

    elif args.demo:
        # Run demo queries
        demo_queries = [
            "human liver cancer RNA-seq",
            "single cell sequencing in lung tissue",
            "diabetes metabolic pathway analysis",
            "methylation patterns in brain tumors",
            "COVID-19 immune response",
        ]

        results = await integration.run_demo_queries(demo_queries)
        saved_files = integration.save_demo_results(results, output_dir)

        print(f"\n✅ Enhanced search demo results saved to {output_dir}")
        print(f"Generated {len(saved_files)} files")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
