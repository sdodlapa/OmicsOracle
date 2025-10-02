"""
Services Layer for OmicsOracle

This module contains service classes for various operations:

Services:
    - SummarizationService: AI-powered text summarization
    - CostManager: Cost tracking and management
    - Cache: Result caching for performance

Features:
    - NLP processing and query interpretation
    - Ontology mapping and term normalization
    - GEO data retrieval and processing
    - Caching and performance optimization
    - Cost tracking and budget management

Example:
    >>> from omics_oracle.services import SummarizationService
    >>> summarizer = SummarizationService()
    >>> summary = await summarizer.summarize(text)
"""

from .cost_manager import CostManager
from .summarizer import SummarizationService

__version__ = "0.1.0"

__all__ = [
    "SummarizationService",
    "CostManager",
]
