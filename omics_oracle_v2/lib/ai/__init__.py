"""
AI services library.

Provides AI-powered text summarization and analysis using large language models.
Designed for biomedical and scientific content with domain-specific prompts.

Key Components:
    - SummarizationService: Main summarization engine
    - PromptManager: Domain-specific prompt templates
    - Summary models: Type-safe request/response models

Example:
    >>> from omics_oracle_v2.lib.ai import SummarizationService
    >>> from omics_oracle_v2.lib.ai.models import SummaryRequest, SummaryType
    >>>
    >>> summarizer = SummarizationService()
    >>> request = SummaryRequest(
    ...     text="Long biomedical text...",
    ...     summary_type=SummaryType.CONCISE
    ... )
    >>> response = summarizer.summarize(request)
    >>> print(response.summary)

Status: Phase 1 Task 5 (In Progress)
"""

# Exports will be added as modules are implemented
# from .summarizer import SummarizationService
# from .models import SummaryRequest, SummaryResponse, SummaryType

__all__ = []
