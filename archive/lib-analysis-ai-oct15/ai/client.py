"""
AI-powered summarization service for genomics datasets.

Provides intelligent summarization using OpenAI's GPT models with
support for different summary types and batch processing.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from omics_oracle_v2.core.config import AISettings
from omics_oracle_v2.core.exceptions import AIError

if TYPE_CHECKING:
    from omics_oracle_v2.core.config import Settings

from .models import (BatchSummaryResponse, ModelInfo, SummaryResponse,
                     SummaryType)
from .prompts import PromptBuilder
from .utils import (aggregate_batch_statistics, estimate_tokens,
                    extract_technical_details, prepare_metadata)

logger = logging.getLogger(__name__)

# Optional OpenAI dependency
try:
    from openai import OpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI library not available - AI summarization disabled")


class SummarizationClient:
    """
    Client for AI-powered genomics dataset summarization.

    Provides:
    - Multiple summary types (brief, comprehensive, technical)
    - Batch summarization for search results
    - Token estimation and cost tracking
    - Configurable models and parameters
    """

    def __init__(self, settings: Optional[Union[AISettings, "Settings"]] = None):
        """
        Initialize summarization client.

        Args:
            settings: AI configuration settings or full Settings object
        """
        from omics_oracle_v2.core.config import Settings as FullSettings
        from omics_oracle_v2.core.config import get_settings

        if settings is None:
            all_settings = get_settings()
            settings = all_settings.ai
        elif isinstance(settings, FullSettings):
            # Extract AI settings from full Settings object
            settings = settings.ai

        self.settings = settings

        # Initialize OpenAI client
        self.client: Optional[Any] = None
        if HAS_OPENAI and self.settings.openai_api_key:
            try:
                self.client = OpenAI(api_key=self.settings.openai_api_key)
                logger.info(
                    f"OpenAI client initialized with model: {self.settings.model}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            if not HAS_OPENAI:
                logger.warning("OpenAI library not installed")
            else:
                logger.warning("OpenAI API key not configured")

        # Initialize prompt builder
        self.prompt_builder = PromptBuilder()

        logger.info("Summarization client initialized")

    def summarize(
        self,
        metadata: Dict[str, Any],
        query_context: Optional[str] = None,
        summary_type: SummaryType = SummaryType.COMPREHENSIVE,
        dataset_id: Optional[str] = None,
    ) -> Optional[SummaryResponse]:
        """
        Generate AI-powered summary of a genomics dataset.

        Args:
            metadata: Dataset metadata
            query_context: Original user query for context
            summary_type: Type of summary to generate
            dataset_id: Dataset identifier (for response tracking)

        Returns:
            SummaryResponse with generated content or None if unavailable

        Raises:
            AIError: If summarization fails
        """
        if not self.client:
            logger.warning("OpenAI client not available - cannot generate summary")
            return None

        # Prepare metadata
        cleaned_metadata = prepare_metadata(metadata)

        # Extract dataset ID
        actual_dataset_id = (
            dataset_id
            or cleaned_metadata.get("accession")
            or cleaned_metadata.get("id")
            or "unknown"
        )

        logger.info(f"Generating {summary_type.value} summary for {actual_dataset_id}")

        try:
            # Generate summary components based on type
            response = SummaryResponse(
                dataset_id=actual_dataset_id,
                summary_type=summary_type,
                model_used=self.settings.model,
            )

            # Generate different components based on summary type
            if summary_type in [SummaryType.BRIEF, SummaryType.COMPREHENSIVE]:
                response.overview = self._generate_overview(
                    cleaned_metadata, query_context
                )

            if summary_type in [SummaryType.COMPREHENSIVE, SummaryType.TECHNICAL]:
                response.methodology = self._generate_methodology(cleaned_metadata)
                response.significance = self._generate_significance(
                    cleaned_metadata, query_context
                )

            if summary_type == SummaryType.BRIEF:
                response.brief = self._generate_brief(cleaned_metadata, query_context)

            if summary_type == SummaryType.COMPREHENSIVE:
                response.technical_details = extract_technical_details(cleaned_metadata)

            # Estimate total tokens used
            total_text = " ".join(
                filter(
                    None,
                    [
                        response.overview,
                        response.methodology,
                        response.significance,
                        response.technical_details,
                        response.brief,
                    ],
                )
            )
            response.token_usage = estimate_tokens(total_text)

            logger.info(
                f"Generated summary for {actual_dataset_id} "
                f"(~{response.token_usage} tokens)"
            )

            return response if response.has_content() else None

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise AIError(f"Failed to generate summary: {e}") from e

    def _generate_overview(
        self, metadata: Dict[str, Any], query_context: Optional[str] = None
    ) -> Optional[str]:
        """Generate high-level overview summary."""
        prompt = self.prompt_builder.build_overview_prompt(metadata, query_context)
        system_message = self.prompt_builder.get_system_message("overview")

        return self._call_llm(
            prompt, system_message, max_tokens=self.settings.max_tokens
        )

    def _generate_methodology(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Generate methodology summary."""
        prompt = self.prompt_builder.build_methodology_prompt(metadata)
        system_message = self.prompt_builder.get_system_message("methodology")

        return self._call_llm(prompt, system_message, max_tokens=300)

    def _generate_significance(
        self, metadata: Dict[str, Any], query_context: Optional[str] = None
    ) -> Optional[str]:
        """Generate research significance summary."""
        prompt = self.prompt_builder.build_significance_prompt(metadata, query_context)
        system_message = self.prompt_builder.get_system_message("significance")

        return self._call_llm(prompt, system_message, max_tokens=300)

    def _generate_brief(
        self, metadata: Dict[str, Any], query_context: Optional[str] = None
    ) -> Optional[str]:
        """Generate brief one-paragraph summary."""
        prompt = self.prompt_builder.build_overview_prompt(
            metadata, query_context, brief=True
        )
        system_message = self.prompt_builder.get_system_message("brief")

        return self._call_llm(prompt, system_message, max_tokens=200)

    def _call_llm(
        self, prompt: str, system_message: str, max_tokens: int = 500
    ) -> Optional[str]:
        """
        Make LLM API call.

        Args:
            prompt: User prompt
            system_message: System role message
            max_tokens: Maximum tokens in response

        Returns:
            Generated text or None if call fails
        """
        if not self.client:
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.settings.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=self.settings.temperature,
                timeout=self.settings.timeout,
            )

            content = response.choices[0].message.content
            return content.strip() if content and content.strip() else None

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return None

    def summarize_batch(
        self, query: str, results: List[Dict[str, Any]], max_datasets: int = 10
    ) -> BatchSummaryResponse:
        """
        Generate summary of multiple dataset results.

        Args:
            query: Original search query
            results: List of dataset results
            max_datasets: Maximum datasets to include in summary

        Returns:
            BatchSummaryResponse with aggregated statistics
        """
        if not results:
            return BatchSummaryResponse(
                query=query,
                total_datasets=0,
                overview="No datasets found for the given query.",
            )

        # Limit results if needed
        results_subset = results[:max_datasets]

        logger.info(f"Generating batch summary for {len(results_subset)} datasets")

        # Aggregate statistics
        stats = aggregate_batch_statistics(results_subset)

        # Create overview
        overview = (
            f"Found {stats['total_datasets']} datasets with "
            f"{stats['total_samples']} total samples across "
            f"{len(stats['organisms'])} organisms using "
            f"{len(stats['platforms'])} different platforms."
        )

        return BatchSummaryResponse(
            query=query,
            total_datasets=stats["total_datasets"],
            total_samples=stats["total_samples"],
            organisms=stats["organisms"],
            platforms=stats["platforms"],
            study_types=stats["study_types"],
            overview=overview,
        )

    def get_model_info(self) -> ModelInfo:
        """Get information about the configured model."""
        return ModelInfo(
            model_name=self.settings.model,
            provider="openai",
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            available=self.client is not None,
        )
