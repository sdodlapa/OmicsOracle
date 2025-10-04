"""
Data models for Data Agent.

Defines input/output data structures for dataset metadata processing,
validation, and quality assessment.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .search import RankedDataset


class DataQualityLevel(str, Enum):
    """Data quality assessment levels."""

    EXCELLENT = "excellent"  # 90-100% quality score
    GOOD = "good"  # 75-89% quality score
    FAIR = "fair"  # 50-74% quality score
    POOR = "poor"  # Below 50% quality score


class DataInput(BaseModel):
    """Input for data processing operations."""

    datasets: List[RankedDataset] = Field(
        ..., description="Datasets to process from search results", min_length=1
    )
    min_quality_score: float = Field(
        default=0.0, description="Minimum quality score threshold", ge=0.0, le=1.0
    )
    require_publication: bool = Field(default=False, description="Whether to require PubMed publications")
    require_sra: bool = Field(default=False, description="Whether to require SRA data")

    @field_validator("datasets")
    @classmethod
    def validate_datasets(cls, v: List[RankedDataset]) -> List[RankedDataset]:
        """Validate datasets list is not empty."""
        if not v:
            raise ValueError("datasets cannot be empty")
        return v


class ProcessedDataset(BaseModel):
    """Processed and validated dataset with quality metrics."""

    geo_id: str = Field(..., description="GEO series ID")
    title: str = Field(..., description="Dataset title")
    summary: str = Field(..., description="Dataset summary")
    organism: str = Field(..., description="Organism studied")
    sample_count: int = Field(..., description="Number of samples", ge=0)
    platform_count: int = Field(..., description="Number of platforms", ge=0)

    # Dates
    submission_date: Optional[str] = Field(None, description="Submission date")
    publication_date: Optional[str] = Field(None, description="Publication date")
    age_days: Optional[int] = Field(None, description="Days since submission", ge=0)

    # Publications
    pubmed_ids: List[str] = Field(default_factory=list, description="PubMed IDs")
    has_publication: bool = Field(..., description="Whether dataset has publications")

    # SRA data
    has_sra_data: bool = Field(..., description="Whether SRA sequencing data is available")
    sra_run_count: int = Field(default=0, description="Number of SRA runs", ge=0)

    # Quality metrics
    quality_score: float = Field(..., description="Overall quality score (0.0-1.0)", ge=0.0, le=1.0)
    quality_level: DataQualityLevel = Field(..., description="Quality assessment level")
    quality_issues: List[str] = Field(default_factory=list, description="Identified quality issues")
    quality_strengths: List[str] = Field(default_factory=list, description="Dataset strengths")

    # Search relevance
    relevance_score: float = Field(..., description="Search relevance score (0.0-1.0)", ge=0.0, le=1.0)

    # Metadata completeness
    metadata_completeness: float = Field(..., description="Metadata completeness (0.0-1.0)", ge=0.0, le=1.0)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class DataOutput(BaseModel):
    """Output from data processing operations."""

    processed_datasets: List[ProcessedDataset] = Field(
        default_factory=list, description="Processed and validated datasets"
    )
    total_processed: int = Field(..., description="Total datasets processed", ge=0)
    total_passed_quality: int = Field(..., description="Datasets passing quality threshold", ge=0)
    average_quality_score: float = Field(..., description="Average quality score", ge=0.0, le=1.0)
    quality_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Distribution of quality levels"
    )

    def get_high_quality_datasets(self, min_score: float = 0.75) -> List[ProcessedDataset]:
        """
        Get datasets with quality score above threshold.

        Args:
            min_score: Minimum quality score threshold

        Returns:
            List of high-quality datasets
        """
        return [d for d in self.processed_datasets if d.quality_score >= min_score]

    def get_by_quality_level(self, level: DataQualityLevel) -> List[ProcessedDataset]:
        """
        Get datasets by quality level.

        Args:
            level: Quality level to filter by

        Returns:
            List of datasets at specified quality level
        """
        return [d for d in self.processed_datasets if d.quality_level == level]

    def get_with_publications(self) -> List[ProcessedDataset]:
        """
        Get datasets that have publications.

        Returns:
            List of datasets with PubMed publications
        """
        return [d for d in self.processed_datasets if d.has_publication]

    def get_with_sra_data(self) -> List[ProcessedDataset]:
        """
        Get datasets that have SRA sequencing data.

        Returns:
            List of datasets with SRA data
        """
        return [d for d in self.processed_datasets if d.has_sra_data]

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


__all__ = ["DataQualityLevel", "DataInput", "DataOutput", "ProcessedDataset"]
