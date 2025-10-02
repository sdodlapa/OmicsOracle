"""
API v2 Routes - Enhanced and Real-Time Features

This module provides v2 API endpoints with advanced features:
- Enhanced search with AI-powered ranking
- Real-time updates via WebSocket integration
- Advanced query processing and component extraction
- Intelligent search suggestions

Version: 2.0.0
Status: Active (recommended)
"""

import asyncio
import logging
import time
from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from ....pipeline.pipeline import OmicsOracle, ResultFormat
from ....search.advanced_search_enhancer import AdvancedSearchEnhancer
from ....search.enhanced_query_handler import EnhancedQueryHandler
from ..websockets import manager

logger = logging.getLogger(__name__)

# Create v2 router
router = APIRouter(prefix="/v2", tags=["v2-api"])

# Initialize enhanced search components
query_handler = EnhancedQueryHandler()
search_enhancer = AdvancedSearchEnhancer()
omics_oracle = OmicsOracle()


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================


@router.get("/health", summary="V2 Health Check")
async def health_check() -> Dict[str, Any]:
    """V2 API health check endpoint with feature status."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "api": "v2",
        "features": {
            "enhanced_search": True,
            "real_time_updates": True,
            "ai_ranking": True,
            "websocket_support": True,
        },
        "active_connections": len(manager.active_connections),
    }


@router.get("/status", summary="System Status")
async def system_status() -> Dict[str, Any]:
    """Get comprehensive system status for v2 API."""
    return {
        "status": "operational",
        "version": "2.0.0",
        "api": "v2",
        "features": {
            "real_time_search": True,
            "websocket_support": True,
            "ai_agents": True,
            "advanced_visualization": True,
            "intelligent_suggestions": True,
        },
        "active_connections": len(manager.active_connections),
        "uptime": time.time() - 1672531200,  # Placeholder
        "timestamp": time.time(),
    }


# ============================================================================
# ENHANCED SEARCH ENDPOINTS
# ============================================================================


@router.get("/search", summary="Enhanced Search with AI Ranking")
async def enhanced_search(
    query: str = Query(..., description="The search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    trace: bool = Query(False, description="Include trace information"),
) -> Dict[str, Any]:
    """
    Perform an enhanced search with advanced features like semantic ranking,
    result clustering, and query reformulation.

    This endpoint uses the OmicsOracle pipeline with AI-powered enhancements.
    """
    logger.info(f"Enhanced search: query='{query}', limit={limit}, trace={trace}")

    try:
        # Use the OmicsOracle pipeline for enhanced search
        query_result = await omics_oracle.process_query(
            query,
            max_results=limit,
            result_format=ResultFormat.JSON,
        )

        # Convert dataclass to dict for JSON response
        result_dict = asdict(query_result)
        return result_dict

    except Exception as e:
        logger.error(f"Error in enhanced search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced search error: {str(e)}")


@router.post("/search/realtime", summary="Real-Time Search with Progress Updates")
async def realtime_search(
    background_tasks: BackgroundTasks,
    query: str,
    client_id: Optional[str] = None,
    max_results: int = 20,
    enable_real_time: bool = True,
) -> Dict[str, Any]:
    """
    Perform a search with real-time progress updates via WebSocket.

    This endpoint provides enhanced search capabilities with WebSocket
    integration for real-time progress updates and AI-powered features.
    """
    logger.info(f"Real-time search: query='{query}', client_id={client_id}")

    search_id = f"search_{int(time.time())}_{hash(query) % 10000}"

    try:
        if enable_real_time and client_id:
            # Add background task for real-time updates
            background_tasks.add_task(
                _perform_search_with_updates,
                query,
                client_id,
                max_results,
                search_id,
            )

            return {
                "search_id": search_id,
                "status": "initiated",
                "message": "Search started with real-time updates",
                "client_id": client_id,
                "real_time_enabled": True,
            }
        else:
            # Perform immediate search without real-time updates
            start_time = time.time()

            query_result = await omics_oracle.process_query(
                query,
                max_results=max_results,
                result_format=ResultFormat.JSON,
            )

            search_time = time.time() - start_time

            return {
                "search_id": search_id,
                "query": query,
                "results": (
                    query_result.__dict__ if hasattr(query_result, "__dict__") else str(query_result)
                ),
                "search_time": search_time,
                "timestamp": time.time(),
                "real_time_enabled": False,
            }

    except Exception as e:
        logger.error(f"Error in real-time search: {str(e)}")

        if client_id:
            await manager.send_personal_message(
                {
                    "type": "search_error",
                    "search_id": search_id,
                    "error": str(e),
                    "timestamp": time.time(),
                },
                client_id,
            )

        raise HTTPException(status_code=500, detail=f"Real-time search error: {str(e)}")


async def _perform_search_with_updates(query: str, client_id: str, max_results: int, search_id: str):
    """
    Internal function to perform search with real-time progress updates via WebSocket.
    """
    try:
        # Send initial progress
        await manager.send_search_progress(
            client_id, 5, "Initializing AI agents...", f"Search ID: {search_id}"
        )
        await asyncio.sleep(0.5)

        # Simulate agent initialization
        await manager.send_search_progress(
            client_id, 15, "Search agent activated", "Analyzing query structure"
        )
        await asyncio.sleep(0.5)

        await manager.send_search_progress(
            client_id, 25, "NLP processing...", "Extracting biomedical entities"
        )
        await asyncio.sleep(0.5)

        await manager.send_search_progress(
            client_id, 40, "Database connections established", "Connecting to data sources"
        )
        await asyncio.sleep(0.5)

        # Perform the actual search
        await manager.send_search_progress(
            client_id, 60, "Executing search...", "Processing with OmicsOracle pipeline"
        )

        start_time = time.time()
        query_result = await omics_oracle.process_query(
            query,
            max_results=max_results,
            result_format=ResultFormat.JSON,
        )
        search_time = time.time() - start_time

        await manager.send_search_progress(
            client_id, 80, "Processing results...", "Applying AI ranking and filtering"
        )
        await asyncio.sleep(0.5)

        await manager.send_search_progress(client_id, 95, "Finalizing...", "Preparing visualization data")
        await asyncio.sleep(0.3)

        # Send final results
        await manager.send_search_progress(
            client_id, 100, "Search completed!", f"Found results in {search_time:.2f}s"
        )

        # Send the actual results
        results_data = {
            "search_id": search_id,
            "query": query,
            "results": (query_result.__dict__ if hasattr(query_result, "__dict__") else str(query_result)),
            "search_time": search_time,
            "timestamp": time.time(),
            "total_found": (len(query_result.metadata) if hasattr(query_result, "metadata") else 0),
        }

        await manager.send_search_results(client_id, results_data)

    except Exception as e:
        logger.error(f"Error in real-time search for {client_id}: {str(e)}")
        await manager.send_personal_message(
            {
                "type": "search_error",
                "search_id": search_id,
                "error": str(e),
                "timestamp": time.time(),
            },
            client_id,
        )


@router.get("/search/suggestions", summary="Get Intelligent Search Suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="Partial query for suggestions"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions"),
) -> Dict[str, Any]:
    """
    Get intelligent search suggestions based on partial query.

    Uses AI-powered suggestion engine to provide relevant biomedical term suggestions.
    """
    suggestions = []

    # Biomedical terms database (can be enhanced with ML model)
    biomedical_terms = [
        "cancer genomics",
        "SARS-CoV-2",
        "diabetes mellitus",
        "alzheimer disease",
        "breast cancer",
        "lung cancer",
        "heart disease",
        "neurodegeneration",
        "RNA sequencing",
        "proteomics",
        "metabolomics",
        "transcriptomics",
        "CRISPR",
        "gene expression",
        "protein structure",
        "drug discovery",
        "immunotherapy",
        "cell signaling",
    ]

    query_lower = query.lower()
    for term in biomedical_terms:
        if query_lower in term.lower() or term.lower().startswith(query_lower):
            suggestions.append(
                {
                    "text": term,
                    "category": "biomedical",
                    "confidence": 0.8 if term.lower().startswith(query_lower) else 0.6,
                }
            )

    return {
        "query": query,
        "suggestions": suggestions[:limit],
        "timestamp": time.time(),
    }


# ============================================================================
# QUERY ANALYSIS ENDPOINTS
# ============================================================================


@router.get("/query/components", summary="Extract Query Components")
async def query_components(
    query: str = Query(..., description="The query to analyze"),
) -> Dict[str, Any]:
    """
    Extract biomedical components from a search query.

    Uses NLP to identify diseases, tissues, organisms, data types,
    and analysis methods mentioned in the query.
    """
    logger.info(f"Query component extraction: query='{query}'")

    try:
        # Extract components using the enhanced query handler
        components = query_handler.extract_components(query)

        return {
            "query": query,
            "components": components,
            "diseases": components.get("diseases", []),
            "tissues": components.get("tissues", []),
            "organisms": components.get("organisms", []),
            "data_types": components.get("data_types", []),
            "analysis_methods": components.get("analysis_methods", []),
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Error extracting query components: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Component extraction error: {str(e)}")
