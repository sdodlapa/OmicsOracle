"""
AI services library.

Provides AI-powered text summarization using OpenAI GPT models.
Designed for genomics and biomedical dataset analysis with domain-specific prompts.

Key Components:
    - SummarizationClient: Main AI summarization client
    - PromptBuilder: Genomics-specific prompt templates
    - Summary models: Type-safe request/response models
    - Utilities: Token estimation and metadata preparation

Example:
    >>> from omics_oracle_v2.lib.analysis.ai import SummarizationClient, SummaryType
    >>> from omics_oracle_v2.core import Settings
    >>>
    >>> settings = Settings()
    >>> client = SummarizationClient(settings)
    >>>
    >>> # Generate comprehensive summary
    >>> metadata = {
    ...     "title": "RNA-seq analysis of cancer cells",
    ...     "summary": "Gene expression profiling...",
    ...     "organism": "Homo sapiens",
    ...     "platform": "Illumina HiSeq",
    ...     "samples_count": 24
    ... }
    >>> response = client.summarize(
    ...     metadata=metadata,
    ...     summary_type=SummaryType.COMPREHENSIVE
    ... )
    >>> print(response.overview)
    >>> print(response.methodology)
    >>> print(response.significance)
    >>>
    >>> # Batch summarization for search results
    >>> batch_response = client.summarize_batch(
    ...     query="cancer genomics",
    ...     results=[{"id": "GSE123", "metadata": {...}}, ...]
    ... )

Status: Phase 1 Task 5
"""

from .client import SummarizationClient
from .models import (BatchSummaryRequest, BatchSummaryResponse, ModelInfo,
                     SummaryRequest, SummaryResponse, SummaryType)
from .prompts import PromptBuilder

__all__ = [
    # Client
    "SummarizationClient",
    # Models
    "SummaryType",
    "SummaryRequest",
    "SummaryResponse",
    "BatchSummaryRequest",
    "BatchSummaryResponse",
    "ModelInfo",
    # Prompts
    "PromptBuilder",
]
