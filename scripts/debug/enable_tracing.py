"""
Pipeline Tracer Integration for OmicsOracle

This module integrates the query tracer with the OmicsOracle pipeline
by monkey patching key methods to add tracing.
"""

import asyncio
import functools
import inspect
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path to import modules
# Import QueryTracer
try:
    from src.omics_oracle.monitoring.query_tracer import QueryTracer
except ImportError:
    logger.error("Failed to import QueryTracer - please run this script from the project root")
    sys.exit(1)

# Global trace directory
TRACE_DIR = os.environ.get("OMICS_ORACLE_TRACE_DIR", "query_traces")
os.makedirs(TRACE_DIR, exist_ok=True)


def trace_enabled():
    """Check if tracing is enabled via environment variable."""
    return os.environ.get("OMICS_ORACLE_TRACE_ENABLED", "1") == "1"


def patch_pipeline():
    """
    Patch the OmicsOracle pipeline class to add tracing.
    """
    try:
        from src.omics_oracle.pipeline.pipeline import OmicsOracle

        # Store original methods
        original_process_query = OmicsOracle.process_query

        # Patch process_query method
        @functools.wraps(original_process_query)
        async def traced_process_query(self, query, max_results=10):
            """Traced version of process_query that adds comprehensive logging."""
            if not trace_enabled():
                return await original_process_query(self, query, max_results)

            # Create a query tracer
            tracer = QueryTracer(original_query=query, output_dir=TRACE_DIR, detailed=True)

            try:
                # Log the query processing
                tracer.record_step(
                    "pipeline",
                    "process_query_start",
                    {"query": query, "max_results": max_results},
                    status="started",
                )

                # Call the original method
                start_time = time.time()
                result = await original_process_query(self, query, max_results)
                duration = time.time() - start_time

                # Log the result
                tracer.record_step(
                    "pipeline",
                    "process_query_end",
                    {"query": query, "max_results": max_results},
                    {
                        "geo_ids": result.geo_ids if hasattr(result, "geo_ids") else [],
                        "metadata_count": len(result.metadata) if hasattr(result, "metadata") else 0,
                        "ai_summaries": bool(result.ai_summaries)
                        if hasattr(result, "ai_summaries")
                        else False,
                        "status": result.status.value if hasattr(result, "status") else "UNKNOWN",
                    },
                    duration=duration,
                )

                # Finalize the trace
                tracer.finalize(result, "completed")

                return result
            except Exception as e:
                tracer.record_step(
                    "pipeline",
                    "process_query_error",
                    {"query": query, "max_results": max_results},
                    status="error",
                    error=e,
                )

                # Finalize the trace with error
                tracer.finalize({"error": str(e)}, "failed")

                # Re-raise the exception
                raise

        # Apply the patches
        OmicsOracle.process_query = traced_process_query

        logger.info("Successfully patched OmicsOracle pipeline with tracing")
        return True
    except ImportError as e:
        logger.error(f"Failed to patch OmicsOracle pipeline: {e}")
        return False


def patch_frontend():
    """
    Patch the frontend API to add tracing.
    """
    try:
        # Try to import and patch the futuristic_enhanced interface
        import interfaces.futuristic_enhanced.main as frontend

        # Store original methods
        original_search_datasets = frontend.search_datasets
        original_process_search_query = frontend.process_search_query

        # Patch search_datasets
        @functools.wraps(original_search_datasets)
        async def traced_search_datasets(request, background_tasks):
            """Traced version of search_datasets that adds comprehensive logging."""
            if not trace_enabled():
                return await original_search_datasets(request, background_tasks)

            # Create a query tracer
            tracer = QueryTracer(
                original_query=request.query,
                output_dir=TRACE_DIR,
                detailed=True,
            )

            try:
                # Log the API request
                tracer.record_step(
                    "frontend",
                    "api_request",
                    {
                        "query": request.query,
                        "max_results": request.max_results,
                    },
                    status="received",
                )

                # Call the original method
                start_time = time.time()
                result = await original_search_datasets(request, background_tasks)
                duration = time.time() - start_time

                # Log the API response
                tracer.record_step(
                    "frontend",
                    "api_response",
                    {
                        "query": request.query,
                        "max_results": request.max_results,
                    },
                    {"result": result.dict() if hasattr(result, "dict") else result},
                    duration=duration,
                )

                # Finalize the trace
                tracer.finalize(result, "completed")

                return result
            except Exception as e:
                tracer.record_step(
                    "frontend",
                    "api_error",
                    {
                        "query": request.query,
                        "max_results": request.max_results,
                    },
                    status="error",
                    error=e,
                )

                # Finalize the trace with error
                tracer.finalize({"error": str(e)}, "failed")

                # Re-raise the exception
                raise

        # Patch process_search_query
        @functools.wraps(original_process_search_query)
        async def traced_process_search_query(query, max_results=10):
            """Traced version of process_search_query that adds comprehensive logging."""
            if not trace_enabled():
                return await original_process_search_query(query, max_results)

            # Create a query tracer
            tracer = QueryTracer(original_query=query, output_dir=TRACE_DIR, detailed=True)

            try:
                # Log the query processing
                tracer.record_step(
                    "frontend",
                    "process_query_start",
                    {"query": query, "max_results": max_results},
                    status="started",
                )

                # Call the original method
                start_time = time.time()
                result = await original_process_search_query(query, max_results)
                duration = time.time() - start_time

                # Log the result
                tracer.record_step(
                    "frontend",
                    "process_query_end",
                    {"query": query, "max_results": max_results},
                    {"result": result},
                    duration=duration,
                )

                # Finalize the trace
                tracer.finalize(result, "completed")

                return result
            except Exception as e:
                tracer.record_step(
                    "frontend",
                    "process_query_error",
                    {"query": query, "max_results": max_results},
                    status="error",
                    error=e,
                )

                # Finalize the trace with error
                tracer.finalize({"error": str(e)}, "failed")

                # Re-raise the exception
                raise

        # Apply the patches
        frontend.search_datasets = traced_search_datasets
        frontend.process_search_query = traced_process_search_query

        logger.info("Successfully patched frontend API with tracing")
        return True
    except ImportError as e:
        logger.warning(f"Failed to patch frontend API: {e}")
        return False


def patch_enhanced_search():
    """
    Patch the enhanced search handler to add tracing.
    """
    try:
        from src.omics_oracle.search.enhanced_query_handler import perform_multi_strategy_search

        # Store original method
        original_perform_multi_strategy_search = perform_multi_strategy_search

        # Patch perform_multi_strategy_search
        @functools.wraps(original_perform_multi_strategy_search)
        async def traced_perform_multi_strategy_search(pipeline, query, max_results=10):
            """Traced version of perform_multi_strategy_search that adds comprehensive logging."""
            if not trace_enabled():
                return await original_perform_multi_strategy_search(pipeline, query, max_results)

            # Create a query tracer
            tracer = QueryTracer(original_query=query, output_dir=TRACE_DIR, detailed=True)

            try:
                # Log the search start
                tracer.record_step(
                    "enhanced_search",
                    "multi_strategy_start",
                    {"query": query, "max_results": max_results},
                    status="started",
                )

                # Call the original method
                start_time = time.time()
                (
                    geo_ids,
                    metadata,
                ) = await original_perform_multi_strategy_search(pipeline, query, max_results)
                duration = time.time() - start_time

                # Log the search result
                tracer.record_step(
                    "enhanced_search",
                    "multi_strategy_end",
                    {"query": query, "max_results": max_results},
                    {"geo_ids": geo_ids, "metadata": metadata},
                    duration=duration,
                )

                # Log query transformation if alternative query was used
                if metadata.get("search_strategy") == "alternative":
                    tracer.record_transformation(
                        "enhanced_search",
                        query,
                        metadata.get("query_used", query),
                        "query_replacement",
                        "Using alternative query for better results",
                    )

                # Finalize the trace
                tracer.finalize((geo_ids, metadata), "completed")

                return geo_ids, metadata
            except Exception as e:
                tracer.record_step(
                    "enhanced_search",
                    "multi_strategy_error",
                    {"query": query, "max_results": max_results},
                    status="error",
                    error=e,
                )

                # Finalize the trace with error
                tracer.finalize({"error": str(e)}, "failed")

                # Re-raise the exception
                raise

        # Apply the patch
        sys.modules[
            "src.omics_oracle.search.enhanced_query_handler"
        ].perform_multi_strategy_search = traced_perform_multi_strategy_search

        logger.info("Successfully patched enhanced search handler with tracing")
        return True
    except ImportError as e:
        logger.warning(f"Failed to patch enhanced search handler: {e}")
        return False


def apply_all_patches():
    """Apply all available patches to enable comprehensive tracing."""
    results = {
        "pipeline": patch_pipeline(),
        "frontend": patch_frontend(),
        "enhanced_search": patch_enhanced_search(),
    }

    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)

    logger.info(f"Applied {success_count}/{total_count} patches for tracing")

    # Enable tracing
    os.environ["OMICS_ORACLE_TRACE_ENABLED"] = "1"

    return results


def main():
    """Apply all patches and report status."""
    results = apply_all_patches()

    print("\n=== OmicsOracle Tracing Integration ===")
    print(f"Trace directory: {TRACE_DIR}")
    print("\nPatching results:")
    for component, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {component:20} {status}")

    print("\nTracing is now ENABLED. Set OMICS_ORACLE_TRACE_ENABLED=0 to disable.")
    print("Trace reports will be saved to:", TRACE_DIR)


if __name__ == "__main__":
    main()
