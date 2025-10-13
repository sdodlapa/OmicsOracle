"""
FastAPI Dependency Injection

Provides dependencies for FastAPI endpoints.

Note: get_search_agent() removed - /api/agents/search now uses OmicsSearchPipeline directly.
      SearchAgent is kept only for Orchestrator compatibility.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status

from omics_oracle_v2.agents import DataAgent, Orchestrator, QueryAgent, ReportAgent
from omics_oracle_v2.api.config import APISettings
from omics_oracle_v2.core import Settings

logger = logging.getLogger(__name__)


# Singleton instances
_settings: Optional[Settings] = None
_api_settings: Optional[APISettings] = None
_query_agent: Optional[QueryAgent] = None
_data_agent: Optional[DataAgent] = None
_report_agent: Optional[ReportAgent] = None
_orchestrator: Optional[Orchestrator] = None


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


def get_query_agent(settings: Settings = Depends(get_settings)) -> QueryAgent:
    """Get Query Agent instance (singleton)."""
    global _query_agent
    if _query_agent is None:
        _query_agent = QueryAgent(settings=settings)
    return _query_agent


def get_data_agent(settings: Settings = Depends(get_settings)) -> DataAgent:
    """Get Data Agent instance (singleton)."""
    global _data_agent
    if _data_agent is None:
        _data_agent = DataAgent(settings=settings)
    return _data_agent


def get_report_agent(settings: Settings = Depends(get_settings)) -> ReportAgent:
    """Get Report Agent instance (singleton)."""
    global _report_agent
    if _report_agent is None:
        _report_agent = ReportAgent(settings=settings)
    return _report_agent


def get_orchestrator(settings: Settings = Depends(get_settings)) -> Orchestrator:
    """Get Orchestrator instance (singleton)."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(settings=settings)
    return _orchestrator


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
