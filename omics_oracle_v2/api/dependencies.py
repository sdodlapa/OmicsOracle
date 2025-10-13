"""
FastAPI Dependency Injection

Provides dependencies for FastAPI endpoints.

Note: All agent dependencies removed - agents archived to extras/agents/.
      Main search uses SearchOrchestrator directly (lib/search/orchestrator.py).
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status

from omics_oracle_v2.api.config import APISettings
from omics_oracle_v2.core import Settings

logger = logging.getLogger(__name__)


# Singleton instances
_settings: Optional[Settings] = None
_api_settings: Optional[APISettings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_api_settings() -> APISettings:
    """Get API settings (singleton)."""
    global _api_settings
    if _api_settings is None:
        _api_settings = APISettings()
    return _api_settings


# Agent dependencies removed - all agents archived to extras/agents/
# The following functions have been removed:
#   - get_query_agent()
#   - get_data_agent()
#   - get_report_agent()
#   - get_orchestrator()


async def verify_api_settings(
    api_settings: APISettings = Depends(get_api_settings),
) -> APISettings:
    """Verify API settings are properly configured."""
    # Add any validation logic here
    return api_settings


def validate_query_length(query: str, api_settings: APISettings = Depends(get_api_settings)) -> str:
    """Validate query length."""
    if len(query) > api_settings.max_query_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query exceeds maximum length of {api_settings.max_query_length} characters",
        )
    return query


def validate_max_results(max_results: int, api_settings: APISettings = Depends(get_api_settings)) -> int:
    """Validate max results parameter."""
    if max_results > api_settings.max_results_per_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"max_results exceeds limit of {api_settings.max_results_per_request}",
        )
    return max_results
