"""
Comprehensive Query Flow Tracer for OmicsOracle

This script traces a query's entire journey through the OmicsOracle system,
from frontend submission to backend processing and result display.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path to import modules
# Import required modules
try:
    from src.omics_oracle.monitoring.query_tracer import QueryTracer
except ImportError:
    logger.error("Failed to import QueryTracer - please run this script from the project root")
    sys.exit(1)

# Try to import other required modules
try:
    from src.omics_oracle.core.config import Config
    from src.omics_oracle.pipeline.pipeline import OmicsOracle
    from src.omics_oracle.search.enhanced_query_handler import QueryParser, perform_multi_strategy_search
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Some functionality may be limited")


# Mock objects for API testing
class MockRequest:
    """Mock request object for API testing."""

    def __init__(self, query, max_results=10):
        self.query = query
        self.max_results = max_results


class MockBackgroundTasks:
    """Mock background tasks for API testing."""

    def add_task(self, func, *args, **kwargs):
        logger.info(f"Added background task: {func.__name__}")


async def trace_query_flow(query: str, max_results: int = 10, output_dir: str = "query_traces"):
    """
    Trace a query's complete flow through the OmicsOracle system.

    Args:
        query: The search query to trace
        max_results: Maximum number of results to return
        output_dir: Directory to save trace files

    Returns:
        Path to the generated trace report
    """
    # Create a unique ID for this trace
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_id = f"trace_{timestamp}"

    # Initialize the QueryTracer
    tracer = QueryTracer(
        query_id=trace_id,
        original_query=query,
        output_dir=output_dir,
        detailed=True,
    )

    pipeline = None

    try:
        # Step 1: Initialize the backend components
        logger.info("Step 1: Initializing backend components")

        with tracer.trace_context("initialization", "config"):
            config = Config()

            # Set NCBI email for Bio.Entrez
            os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"

            # Ensure NCBI email is set in config
            if hasattr(config, "ncbi"):
                if not hasattr(config.ncbi, "email") or not config.ncbi.email:
                    setattr(config.ncbi, "email", "omicsoracle@example.com")

        with tracer.trace_context("initialization", "pipeline"):
            pipeline = OmicsOracle(config)

            # Set a progress callback if available
            if hasattr(pipeline, "set_progress_callback"):

                @tracer.trace_function("progress")
                async def progress_callback(query_id, event):
                    tracer.record_step(
                        "progress",
                        f"pipeline.{event.stage}",
                        {"query_id": query_id, "message": event.message},
                        {
                            "percentage": event.percentage,
                            "detail": event.detail,
                        },
                        status="progress",
                    )

                pipeline.set_progress_callback(progress_callback)

        # Step 2: Parse and analyze the query
        logger.info("Step 2: Parsing and analyzing the query")

        with tracer.trace_context("query_parsing", "query_analyzer"):
            # Parse query into components
            try:
                parser = QueryParser()
                components = parser.parse_query(query)
                tracer.record_step(
                    "query_parsing",
                    "component_extraction",
                    {"query": query},
                    {"components": components},
                )

                # Generate alternative queries if available
                try:
                    alt_queries = parser.generate_alternative_queries(components)
                    tracer.record_step(
                        "query_parsing",
                        "alternative_generation",
                        {"components": components},
                        {"alternative_queries": alt_queries},
                    )
                except Exception as e:
                    tracer.record_step(
                        "query_parsing",
                        "alternative_generation",
                        {"components": components},
                        None,
                        status="error",
                        error=e,
                    )
            except Exception as e:
                tracer.record_step(
                    "query_parsing",
                    "component_extraction",
                    {"query": query},
                    None,
                    status="error",
                    error=e,
                )

        # Step 3: Process the query through the pipeline
        logger.info("Step 3: Processing query through the pipeline")

        with tracer.trace_context("search", "pipeline_processing"):
            # Try enhanced search first
            try:
                logger.info("Using enhanced query handling")
                geo_ids, metadata_info = await perform_multi_strategy_search(
                    pipeline, query, max_results=max_results
                )

                search_strategy = metadata_info.get("search_strategy", "original")
                query_used = metadata_info.get("query_used", query)

                tracer.record_step(
                    "search",
                    "enhanced_search",
                    {"query": query, "max_results": max_results},
                    {"geo_ids": geo_ids, "metadata_info": metadata_info},
                )

                if search_strategy == "alternative":
                    tracer.record_transformation(
                        "search",
                        query,
                        query_used,
                        "query_replacement",
                        "Using alternative query for better results",
                    )

                # Create a result object for downstream processing
                if geo_ids:
                    result = type(
                        "QueryResult",
                        (),
                        {
                            "geo_ids": geo_ids,
                            "metadata": metadata_info.get("metadata", []),
                            "ai_summaries": metadata_info.get("ai_summaries", {}),
                            "intent": f"Find gene expression data related to {components.get('disease', components.get('tissue', 'biomedical conditions'))} in {components.get('organism', 'organisms')}",
                            "duration": 0.0,
                            "status": type("Status", (), {"value": "COMPLETED"}),
                        },
                    )
                else:
                    # Fall back to standard pipeline
                    logger.info("Enhanced search found no results, using standard pipeline")
                    result = await pipeline.process_query(query, max_results=max_results)

                    tracer.record_step(
                        "search",
                        "standard_search",
                        {"query": query, "max_results": max_results},
                        {
                            "geo_ids": result.geo_ids,
                            "metadata_count": len(result.metadata) if hasattr(result, "metadata") else 0,
                            "ai_summaries": bool(result.ai_summaries)
                            if hasattr(result, "ai_summaries")
                            else False,
                        },
                    )
            except ImportError:
                # If enhanced search is not available, use standard pipeline
                logger.info("Enhanced search module not available, using standard pipeline")
                result = await pipeline.process_query(query, max_results=max_results)

                tracer.record_step(
                    "search",
                    "standard_search",
                    {"query": query, "max_results": max_results},
                    {
                        "geo_ids": result.geo_ids,
                        "metadata_count": len(result.metadata) if hasattr(result, "metadata") else 0,
                        "ai_summaries": bool(result.ai_summaries)
                        if hasattr(result, "ai_summaries")
                        else False,
                    },
                )
            except Exception as e:
                tracer.record_step(
                    "search",
                    "pipeline_processing",
                    {"query": query, "max_results": max_results},
                    None,
                    status="error",
                    error=e,
                )
                raise

        # Step 4: Format results for frontend display
        logger.info("Step 4: Formatting results for frontend display")

        with tracer.trace_context("formatting", "frontend_adapter"):
            # Extract and format the results for the frontend
            datasets = []

            # Check if we have GEO IDs
            if hasattr(result, "geo_ids") and result.geo_ids:
                for i, geo_id in enumerate(result.geo_ids[:max_results]):
                    tracer.record_step(
                        "formatting",
                        f"dataset_{i+1}",
                        {"geo_id": geo_id, "index": i},
                        status="processing",
                    )

                    # Get metadata if available
                    metadata = {}
                    if hasattr(result, "metadata") and i < len(result.metadata):
                        metadata = result.metadata[i] or {}

                    # Get AI insights for this dataset
                    ai_insights = None
                    if (
                        hasattr(result, "ai_summaries")
                        and result.ai_summaries
                        and "individual_summaries" in result.ai_summaries
                    ):
                        for summary_item in result.ai_summaries["individual_summaries"]:
                            if summary_item.get("accession") == geo_id:
                                ai_insights = summary_item.get("summary")
                                break

                    # Format the dataset for frontend display
                    dataset_info = {
                        "geo_id": geo_id,
                        "title": metadata.get("title"),
                        "summary": metadata.get("summary"),
                        "organism": metadata.get("organism", "").strip() or None,
                        "sample_count": metadata.get("sample_count"),
                        "platform": metadata.get("platform", "").strip() or None,
                        "publication_date": metadata.get("pubdate"),
                        "study_type": metadata.get("type"),
                        "ai_insights": ai_insights,
                        "relevance_score": metadata.get("relevance_score"),
                        "geo_summary": metadata.get("summary"),
                        "ai_summary": ai_insights,
                    }

                    datasets.append(dataset_info)

                    tracer.record_step(
                        "formatting",
                        f"dataset_{i+1}",
                        {"geo_id": geo_id, "index": i},
                        {"dataset_info": dataset_info},
                        status="success",
                    )

            # Create formatted response
            response_data = {
                "query": query,
                "datasets": datasets,
                "total_found": len(datasets),
                "search_time": getattr(result, "duration", 0) or 0,
                "timestamp": time.time(),
            }

            tracer.record_step(
                "formatting",
                "response_generation",
                {
                    "result_obj": {
                        "has_geo_ids": hasattr(result, "geo_ids"),
                        "geo_id_count": len(result.geo_ids) if hasattr(result, "geo_ids") else 0,
                        "has_metadata": hasattr(result, "metadata"),
                        "metadata_count": len(result.metadata) if hasattr(result, "metadata") else 0,
                        "has_ai_summaries": hasattr(result, "ai_summaries") and bool(result.ai_summaries),
                    }
                },
                {"response": response_data},
            )

        # Step 5: Mock frontend display
        logger.info("Step 5: Simulating frontend display")

        with tracer.trace_context("frontend", "results_rendering"):
            # Sort datasets by relevance score
            sorted_datasets = sorted(
                datasets,
                key=lambda d: (
                    d.get("title") is not None,
                    d.get("summary") is not None,
                    d.get("relevance_score", 0) or 0,
                ),
                reverse=True,
            )

            # Generate AI insights message for the frontend
            datasets_with_metadata = [d for d in datasets if d.get("title") is not None]
            datasets_with_summaries = [d for d in datasets if d.get("summary") is not None]

            ai_insights = f"Found {len(datasets)} biomedical datasets for '{query}'"
            if datasets_with_metadata:
                ai_insights += f" ({len(datasets_with_metadata)} with metadata)"
            if datasets_with_summaries:
                ai_insights += f" including {len(datasets_with_summaries)} with detailed summaries"
            ai_insights += "."

            tracer.record_step(
                "frontend",
                "insights_generation",
                {"datasets": datasets},
                {"ai_insights": ai_insights},
            )

            # Final frontend display data
            frontend_display = {
                "query": query,
                "result_count": len(datasets),
                "ai_insights": ai_insights,
                "search_time": response_data["search_time"],
                "datasets": sorted_datasets[:5],  # Show only top 5 for brevity
            }

            tracer.record_step(
                "frontend",
                "final_display",
                {"response_data": response_data},
                {"frontend_display": frontend_display},
            )

        # Finalize the trace with the complete result
        tracer.finalize(frontend_display, "completed")

        # Return the path to the generated report
        report_path = os.path.join(output_dir, f"{trace_id}_report.md")
        logger.info(f"Query trace completed. Report saved to: {report_path}")

        return report_path

    except Exception as e:
        logger.error(f"Error during query flow tracing: {e}")
        import traceback

        logger.error(traceback.format_exc())

        # Finalize the trace with error
        tracer.finalize({"error": str(e)}, "failed")

        # Return the path to the generated report
        report_path = os.path.join(output_dir, f"{trace_id}_report.md")
        logger.error(f"Query trace failed. Error report saved to: {report_path}")

        return report_path


def main():
    """Run the query flow tracer from the command line."""
    parser = argparse.ArgumentParser(description="Trace a query's flow through OmicsOracle")
    parser.add_argument("query", help="The search query to trace")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results")
    parser.add_argument(
        "--output-dir",
        default="query_traces",
        help="Directory to save trace files",
    )

    args = parser.parse_args()

    # Run the trace
    asyncio.run(trace_query_flow(args.query, args.max_results, args.output_dir))


if __name__ == "__main__":
    main()
