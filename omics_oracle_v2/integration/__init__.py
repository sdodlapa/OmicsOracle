"""
OmicsOracle Integration Layer

This module provides a clean abstraction layer between the backend API
and multiple frontend implementations (Streamlit, React, Vue, mobile apps).

Key Components:
- APIClient: Base client with auth, caching, error handling
- SearchClient: Search functionality abstraction
- AnalysisClient: Analytics, LLM, ML predictions
- MLClient: Machine learning services
- DataTransformer: Format conversion for different frontends

Usage:
    from omics_oracle_v2.integration import SearchClient, AnalysisClient

    search_client = SearchClient(base_url="http://localhost:8000")
    results = await search_client.search(query="CRISPR", max_results=50)

    analysis_client = AnalysisClient(base_url="http://localhost:8000")
    llm_analysis = await analysis_client.analyze_with_llm(query, results)
"""

from .analysis_client import AnalysisClient
from .base_client import APIClient
from .data_transformer import DataTransformer
from .ml_client import MLClient
from .models import (
    AnalysisRequest,
    AnalysisResponse,
    Publication,
    QARequest,
    QAResponse,
    SearchRequest,
    SearchResponse,
)
from .search_client import SearchClient

__all__ = [
    "APIClient",
    "SearchClient",
    "AnalysisClient",
    "MLClient",
    "DataTransformer",
    "SearchRequest",
    "SearchResponse",
    "Publication",
    "AnalysisRequest",
    "AnalysisResponse",
    "QARequest",
    "QAResponse",
]

__version__ = "2.0.0"
