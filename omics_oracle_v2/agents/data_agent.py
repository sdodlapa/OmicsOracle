"""
Data Agent for dataset metadata processing and validation.

Processes GEO dataset metadata, validates data quality, extracts
structured information, and prepares datasets for analysis.
"""

import logging
from typing import List, Tuple

from ..core.config import Settings
from .base import Agent
from .context import AgentContext
from .exceptions import AgentExecutionError, AgentValidationError
from .models.data import DataInput, DataOutput, DataQualityLevel, ProcessedDataset

logger = logging.getLogger(__name__)


class DataAgent(Agent[DataInput, DataOutput]):
    """
    Agent for processing and validating dataset metadata.

    Extracts structured information from GEO metadata, assesses
    data quality, and prepares datasets for downstream analysis.
    """

    def __init__(self, settings: Settings):
        """
        Initialize Data Agent.

        Args:
            settings: Application settings
        """
        super().__init__(settings)

    def _initialize_resources(self) -> None:
        """Initialize resources (none needed for DataAgent)."""
        logger.info("DataAgent initialized (no external resources required)")

    def _cleanup_resources(self) -> None:
        """Clean up resources (none to clean)."""
        logger.info("DataAgent cleanup complete")

    def _validate_input(self, input_data: DataInput) -> DataInput:
        """
        Validate data input.

        Args:
            input_data: Data input to validate

        Returns:
            Validated data input

        Raises:
            AgentValidationError: If validation fails
        """
        if not input_data.datasets:
            raise AgentValidationError("No datasets provided for processing")

        # Validate quality score threshold
        if not 0.0 <= input_data.min_quality_score <= 1.0:
            raise AgentValidationError("min_quality_score must be between 0.0 and 1.0")

        return input_data

    def _process(self, input_data: DataInput, context: AgentContext) -> DataOutput:
        """
        Process and validate dataset metadata.

        Args:
            input_data: Validated data input
            context: Agent execution context

        Returns:
            Processed datasets with quality metrics

        Raises:
            AgentExecutionError: If processing fails
        """
        try:
            context.set_metric("total_datasets", len(input_data.datasets))
            logger.info(f"Processing {len(input_data.datasets)} datasets")

            # Process each dataset
            processed_datasets = []
            quality_counts = {level.value: 0 for level in DataQualityLevel}

            for ranked_dataset in input_data.datasets:
                try:
                    processed = self._process_dataset(ranked_dataset, context)

                    # Apply filters
                    if self._passes_filters(processed, input_data):
                        processed_datasets.append(processed)
                        quality_counts[processed.quality_level.value] += 1
                        logger.debug(
                            f"Processed {processed.geo_id}: "
                            f"quality={processed.quality_score:.2f}, "
                            f"level={processed.quality_level.value}"
                        )
                    else:
                        logger.debug(f"Filtered out {processed.geo_id} (failed quality filters)")

                except Exception as e:
                    logger.warning(f"Failed to process dataset: {e}")
                    context.set_metric("processing_errors", context.metrics.get("processing_errors", 0) + 1)

            # Calculate statistics
            total_processed = len(processed_datasets)
            context.set_metric("datasets_processed", total_processed)
            context.set_metric("datasets_filtered", len(input_data.datasets) - total_processed)

            avg_quality = (
                sum(d.quality_score for d in processed_datasets) / total_processed
                if total_processed > 0
                else 0.0
            )

            total_passed = sum(
                1 for d in processed_datasets if d.quality_score >= input_data.min_quality_score
            )

            logger.info(
                f"Processed {total_processed} datasets, "
                f"average quality: {avg_quality:.2f}, "
                f"passed threshold: {total_passed}"
            )

            return DataOutput(
                processed_datasets=processed_datasets,
                total_processed=total_processed,
                total_passed_quality=total_passed,
                average_quality_score=avg_quality,
                quality_distribution=quality_counts,
            )

        except Exception as e:
            logger.error(f"Error processing datasets: {e}")
            raise AgentExecutionError(f"Failed to process datasets: {e}") from e

    def _process_dataset(self, ranked_dataset, context: AgentContext) -> ProcessedDataset:
        """
        Process a single dataset.

        Args:
            ranked_dataset: RankedDataset from search results
            context: Agent execution context

        Returns:
            ProcessedDataset with quality metrics
        """
        metadata = ranked_dataset.dataset

        # Extract basic information
        geo_id = metadata.geo_id
        title = metadata.title or ""
        summary = metadata.summary or ""
        organism = metadata.organism or "Unknown"
        sample_count = metadata.sample_count or 0
        platform_count = metadata.platform_count or 0

        # Extract dates
        submission_date = metadata.submission_date
        publication_date = metadata.publication_date
        age_days = metadata.get_age_days()

        # Extract publications
        pubmed_ids = metadata.pubmed_ids or []
        has_publication = len(pubmed_ids) > 0

        # Extract SRA data
        has_sra_data = metadata.has_sra_data()
        sra_run_count = metadata.sra_info.run_count if metadata.sra_info else 0

        # Calculate quality metrics
        quality_score, quality_issues, quality_strengths = self._calculate_quality_score(metadata)
        quality_level = self._determine_quality_level(quality_score)

        # Calculate metadata completeness
        metadata_completeness = self._calculate_metadata_completeness(metadata)

        context.set_metric(f"quality_{geo_id}", quality_score)

        return ProcessedDataset(
            geo_id=geo_id,
            title=title,
            summary=summary,
            organism=organism,
            sample_count=sample_count,
            platform_count=platform_count,
            submission_date=submission_date,
            publication_date=publication_date,
            age_days=age_days,
            pubmed_ids=pubmed_ids,
            has_publication=has_publication,
            has_sra_data=has_sra_data,
            sra_run_count=sra_run_count,
            quality_score=quality_score,
            quality_level=quality_level,
            quality_issues=quality_issues,
            quality_strengths=quality_strengths,
            relevance_score=ranked_dataset.relevance_score,
            metadata_completeness=metadata_completeness,
        )

    def _calculate_quality_score(self, metadata) -> Tuple[float, List[str], List[str]]:
        """
        Calculate overall quality score for a dataset.

        Args:
            metadata: GEOSeriesMetadata

        Returns:
            Tuple of (quality_score, issues, strengths)
        """
        score = 0.0
        issues = []
        strengths = []

        # 1. Sample count (0-20 points)
        if metadata.sample_count:
            if metadata.sample_count >= 100:
                score += 20
                strengths.append(f"Large sample size: {metadata.sample_count} samples")
            elif metadata.sample_count >= 50:
                score += 15
                strengths.append(f"Good sample size: {metadata.sample_count} samples")
            elif metadata.sample_count >= 10:
                score += 10
                strengths.append(f"Adequate sample size: {metadata.sample_count} samples")
            else:
                score += 5
                issues.append(f"Small sample size: {metadata.sample_count} samples")
        else:
            issues.append("Missing sample count information")

        # 2. Title quality (0-15 points)
        if metadata.title:
            title_len = len(metadata.title)
            if title_len >= 20:
                score += 15
                if title_len >= 50:
                    strengths.append("Descriptive title")
            elif title_len >= 10:
                score += 10
            else:
                score += 5
                issues.append("Very short title")
        else:
            issues.append("Missing title")

        # 3. Summary quality (0-15 points)
        if metadata.summary:
            summary_len = len(metadata.summary)
            if summary_len >= 200:
                score += 15
                strengths.append("Comprehensive summary")
            elif summary_len >= 100:
                score += 10
            elif summary_len >= 50:
                score += 5
            else:
                issues.append("Very short summary")
        else:
            issues.append("Missing summary")

        # 4. Publication (0-20 points)
        if metadata.pubmed_ids and len(metadata.pubmed_ids) > 0:
            score += 20
            strengths.append(f"Published ({len(metadata.pubmed_ids)} publication(s))")
        else:
            issues.append("No associated publications")

        # 5. SRA data (0-10 points)
        if metadata.has_sra_data():
            score += 10
            strengths.append("Raw sequencing data available (SRA)")
        else:
            issues.append("No SRA sequencing data")

        # 6. Recency (0-10 points)
        age_days = metadata.get_age_days()
        if age_days is not None:
            if age_days <= 365:  # Within 1 year
                score += 10
                strengths.append("Recent dataset (< 1 year old)")
            elif age_days <= 1825:  # Within 5 years
                score += 7
            elif age_days <= 3650:  # Within 10 years
                score += 4
            else:
                issues.append(f"Old dataset ({age_days // 365} years)")

        # 7. Metadata completeness (0-10 points)
        completeness = self._calculate_metadata_completeness(metadata)
        score += completeness * 10
        if completeness >= 0.8:
            strengths.append("Complete metadata")
        elif completeness < 0.5:
            issues.append("Incomplete metadata")

        # Normalize to 0.0-1.0
        quality_score = min(1.0, score / 100.0)

        return quality_score, issues, strengths

    def _calculate_metadata_completeness(self, metadata) -> float:
        """
        Calculate metadata completeness score.

        Args:
            metadata: GEOSeriesMetadata

        Returns:
            Completeness score (0.0-1.0)
        """
        required_fields = [
            "geo_id",
            "title",
            "summary",
            "organism",
            "submission_date",
            "sample_count",
        ]

        optional_fields = [
            "publication_date",
            "overall_design",
            "contact_name",
            "platform_count",
            "pubmed_ids",
        ]

        # Check required fields
        required_complete = sum(1 for field in required_fields if getattr(metadata, field, None))
        required_score = required_complete / len(required_fields)

        # Check optional fields
        optional_complete = sum(1 for field in optional_fields if getattr(metadata, field, None))
        optional_score = optional_complete / len(optional_fields)

        # Weighted: 70% required, 30% optional
        completeness = (required_score * 0.7) + (optional_score * 0.3)

        return completeness

    def _determine_quality_level(self, quality_score: float) -> DataQualityLevel:
        """
        Determine quality level from score.

        Args:
            quality_score: Quality score (0.0-1.0)

        Returns:
            DataQualityLevel enum value
        """
        if quality_score >= 0.9:
            return DataQualityLevel.EXCELLENT
        elif quality_score >= 0.75:
            return DataQualityLevel.GOOD
        elif quality_score >= 0.5:
            return DataQualityLevel.FAIR
        else:
            return DataQualityLevel.POOR

    def _passes_filters(self, dataset: ProcessedDataset, input_data: DataInput) -> bool:
        """
        Check if dataset passes quality filters.

        Args:
            dataset: Processed dataset
            input_data: Input with filter criteria

        Returns:
            True if dataset passes all filters
        """
        # Quality score filter
        if dataset.quality_score < input_data.min_quality_score:
            return False

        # Publication filter
        if input_data.require_publication and not dataset.has_publication:
            return False

        # SRA data filter
        if input_data.require_sra and not dataset.has_sra_data:
            return False

        return True
