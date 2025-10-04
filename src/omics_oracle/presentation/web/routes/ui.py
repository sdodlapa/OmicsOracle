"""
UI and Dashboard Routes

All user interface and dashboard serving endpoints.
Handles static file serving for various dashboard interfaces.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ui", "dashboards"])

# Get the static directory path
STATIC_DIR = Path(__file__).parent.parent / "static"


# ============================================================================
# MAIN INTERFACE ROUTES
# ============================================================================


@router.get("/", summary="Main Web Interface")
async def root():
    """
    Serve the main web interface.

    Serves the enhanced futuristic interface as the default.
    Falls back to other interfaces if not available.
    """
    # Try enhanced futuristic interface first
    enhanced_path = STATIC_DIR / "futuristic_enhanced.html"
    if enhanced_path.exists():
        return FileResponse(str(enhanced_path))

    # Fallback to research intelligence dashboard
    dashboard_path = STATIC_DIR / "research_intelligence_dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))

    # Final fallback to basic index
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    return {"error": "Web interface not found"}


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================


@router.get("/dashboard/basic", summary="Basic Dashboard")
async def basic_dashboard():
    """Serve the basic dashboard interface."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Basic dashboard not found"}


@router.get("/dashboard/research", summary="Research Dashboard")
async def research_dashboard():
    """Serve the research dashboard interface."""
    dashboard_path = STATIC_DIR / "research_dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"error": "Research dashboard not found"}


@router.get("/dashboard/intelligence", summary="Intelligence Dashboard")
async def intelligence_dashboard():
    """Serve the research intelligence dashboard interface."""
    dashboard_path = STATIC_DIR / "research_intelligence_dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"error": "Research intelligence dashboard not found"}


@router.get("/dashboard/advanced", summary="Advanced Dashboard")
async def advanced_dashboard():
    """Serve the most advanced dashboard interface."""
    dashboard_path = STATIC_DIR / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return {"error": "Advanced dashboard not found"}


@router.get("/futuristic", summary="Futuristic Interface")
async def futuristic_interface():
    """Serve the futuristic next-generation interface."""
    futuristic_path = STATIC_DIR / "futuristic_interface.html"
    if futuristic_path.exists():
        return FileResponse(str(futuristic_path))
    return {"error": "Futuristic interface not found"}


@router.get("/futuristic-enhanced", summary="Enhanced Futuristic Interface")
async def futuristic_enhanced_interface():
    """Serve the enhanced futuristic interface with agent monitoring."""
    enhanced_path = STATIC_DIR / "futuristic_enhanced.html"
    if enhanced_path.exists():
        return FileResponse(str(enhanced_path))
    return {"error": "Enhanced futuristic interface not found"}


@router.get("/enhanced", summary="Enhanced Interface")
async def enhanced_interface():
    """Serve the enhanced futuristic interface (alias)."""
    enhanced_path = STATIC_DIR / "futuristic_enhanced.html"
    if enhanced_path.exists():
        return FileResponse(str(enhanced_path))
    return {"error": "Enhanced futuristic interface not found"}


# ============================================================================
# DASHBOARD DISCOVERY
# ============================================================================


@router.get("/dashboards", summary="List Available Dashboards")
async def list_dashboards() -> Dict[str, Any]:
    """
    List all available dashboard interfaces.

    Returns information about all available dashboards including
    their names, URLs, and availability status.
    """
    dashboards: List[Dict[str, str]] = []

    dashboard_files = {
        "basic": "index.html",
        "research": "research_dashboard.html",
        "intelligence": "research_intelligence_dashboard.html",
        "advanced": "dashboard.html",
        "futuristic": "futuristic_interface.html",
        "futuristic-enhanced": "futuristic_enhanced.html",
    }

    for name, filename in dashboard_files.items():
        file_path = STATIC_DIR / filename
        if file_path.exists():
            if name == "futuristic":
                url = "/futuristic"
            elif name == "futuristic-enhanced":
                url = "/futuristic-enhanced"
            else:
                url = f"/dashboard/{name}"

            dashboards.append(
                {
                    "name": name,
                    "url": url,
                    "description": f"{name.replace('-', ' ').title()} dashboard interface",
                    "available": True,
                }
            )

    return {
        "available_dashboards": dashboards,
        "total": len(dashboards),
        "default": "/",
        "current_default": "futuristic-enhanced",
        "recommended": "/futuristic-enhanced",
    }
