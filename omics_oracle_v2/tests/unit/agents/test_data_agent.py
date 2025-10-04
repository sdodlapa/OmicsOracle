"""Tests for Data Agent."""

import pytest

from omics_oracle_v2.agents import DataAgent
from omics_oracle_v2.agents.base import AgentState
from omics_oracle_v2.agents.models.data import DataInput, DataOutput, DataQualityLevel, ProcessedDataset
from omics_oracle_v2.agents.models.search import RankedDataset
from omics_oracle_v2.core.config import Settings
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata, SRAInfo


class TestDataInput:
    """Test DataInput model."""

    def test_valid_input(self):
        """Test valid data input."""
        dataset = GEOSeriesMetadata(geo_id="GSE123", title="Test", sample_count=10)
        ranked = RankedDataset(dataset=dataset, relevance_score=0.8, match_reasons=["test"])

        data_input = DataInput(datasets=[ranked])
        assert len(data_input.datasets) == 1
        assert data_input.min_quality_score == 0.0

    def test_empty_datasets(self):
        """Test that empty datasets raise error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DataInput(datasets=[])

    def test_quality_score_validation(self):
        """Test quality score bounds."""
        dataset = GEOSeriesMetadata(geo_id="GSE123", title="Test", sample_count=10)
        ranked = RankedDataset(dataset=dataset, relevance_score=0.8, match_reasons=["test"])

        # Valid scores
        DataInput(datasets=[ranked], min_quality_score=0.5)
        DataInput(datasets=[ranked], min_quality_score=0.0)
        DataInput(datasets=[ranked], min_quality_score=1.0)

        # Invalid scores
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DataInput(datasets=[ranked], min_quality_score=1.5)

    def test_optional_filters(self):
        """Test optional filter parameters."""
        dataset = GEOSeriesMetadata(geo_id="GSE123", title="Test", sample_count=10)
        ranked = RankedDataset(dataset=dataset, relevance_score=0.8, match_reasons=["test"])

        data_input = DataInput(
            datasets=[ranked],
            min_quality_score=0.75,
            require_publication=True,
            require_sra=True,
        )
        assert data_input.min_quality_score == 0.75
        assert data_input.require_publication is True
        assert data_input.require_sra is True


class TestDataAgent:
    """Test DataAgent functionality."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()

    @pytest.fixture
    def agent(self, settings):
        """Create DataAgent instance."""
        return DataAgent(settings)

    @pytest.fixture
    def sample_datasets(self):
        """Create sample datasets for testing."""
        # High quality dataset
        ds1 = GEOSeriesMetadata(
            geo_id="GSE1",
            title="Comprehensive analysis of breast cancer gene expression",
            summary="This study examines gene expression patterns in breast cancer samples " * 3,
            organism="Homo sapiens",
            sample_count=150,
            platform_count=1,
            submission_date="2024-01-01",
            publication_date="2024-03-01",
            pubmed_ids=["12345678", "87654321"],
        )
        ds1.sra_info = SRAInfo(srp_ids=["SRP123"], run_count=150)

        # Medium quality dataset
        ds2 = GEOSeriesMetadata(
            geo_id="GSE2",
            title="Gene expression in disease",
            summary="Study of gene expression in disease samples",
            organism="Mus musculus",
            sample_count=30,
            platform_count=1,
            submission_date="2020-06-01",
        )

        # Low quality dataset
        ds3 = GEOSeriesMetadata(
            geo_id="GSE3",
            title="Test",
            summary="",
            organism="",
            sample_count=5,
            platform_count=1,
            submission_date="2010-01-01",
        )

        return [
            RankedDataset(dataset=ds1, relevance_score=0.9, match_reasons=["High match"]),
            RankedDataset(dataset=ds2, relevance_score=0.7, match_reasons=["Medium match"]),
            RankedDataset(dataset=ds3, relevance_score=0.3, match_reasons=["Low match"]),
        ]

    def test_agent_initialization(self, agent):
        """Test agent can be initialized."""
        assert agent is not None
        assert agent.state == AgentState.IDLE

    def test_simple_processing(self, agent, sample_datasets):
        """Test basic dataset processing."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True
        assert result.output is not None
        assert isinstance(result.output, DataOutput)
        assert len(result.output.processed_datasets) == 3
        assert result.output.total_processed == 3

    def test_quality_scoring(self, agent, sample_datasets):
        """Test quality score calculation."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True
        datasets = result.output.processed_datasets

        # High quality dataset should have high score
        ds1 = next(d for d in datasets if d.geo_id == "GSE1")
        assert ds1.quality_score >= 0.75
        assert ds1.quality_level in [DataQualityLevel.EXCELLENT, DataQualityLevel.GOOD]

        # Low quality dataset should have low score
        ds3 = next(d for d in datasets if d.geo_id == "GSE3")
        assert ds3.quality_score < 0.5
        assert ds3.quality_level in [DataQualityLevel.FAIR, DataQualityLevel.POOR]

    def test_quality_filtering(self, agent, sample_datasets):
        """Test filtering by minimum quality score."""
        data_input = DataInput(datasets=sample_datasets, min_quality_score=0.6)
        result = agent.execute(data_input)

        assert result.success is True
        # Only high/medium quality datasets should pass
        assert result.output.total_processed <= 3
        for dataset in result.output.processed_datasets:
            assert dataset.quality_score >= 0.6

    def test_publication_filter(self, agent, sample_datasets):
        """Test filtering by publication requirement."""
        data_input = DataInput(datasets=sample_datasets, require_publication=True)
        result = agent.execute(data_input)

        assert result.success is True
        # Only datasets with publications should pass
        for dataset in result.output.processed_datasets:
            assert dataset.has_publication is True

    def test_sra_filter(self, agent, sample_datasets):
        """Test filtering by SRA data requirement."""
        data_input = DataInput(datasets=sample_datasets, require_sra=True)
        result = agent.execute(data_input)

        assert result.success is True
        # Only datasets with SRA data should pass
        for dataset in result.output.processed_datasets:
            assert dataset.has_sra_data is True

    def test_quality_distribution(self, agent, sample_datasets):
        """Test quality level distribution calculation."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True
        distribution = result.output.quality_distribution

        # Should have counts for each quality level
        assert isinstance(distribution, dict)
        total_counts = sum(distribution.values())
        assert total_counts == result.output.total_processed

    def test_average_quality_score(self, agent, sample_datasets):
        """Test average quality score calculation."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True
        assert 0.0 <= result.output.average_quality_score <= 1.0

    def test_metadata_extraction(self, agent, sample_datasets):
        """Test complete metadata extraction."""
        data_input = DataInput(datasets=[sample_datasets[0]])  # High quality dataset
        result = agent.execute(data_input)

        assert result.success is True
        dataset = result.output.processed_datasets[0]

        assert dataset.geo_id == "GSE1"
        assert dataset.title != ""
        assert dataset.summary != ""
        assert dataset.organism == "Homo sapiens"
        assert dataset.sample_count == 150
        assert dataset.has_publication is True
        assert len(dataset.pubmed_ids) == 2
        assert dataset.has_sra_data is True

    def test_quality_issues_tracking(self, agent, sample_datasets):
        """Test that quality issues are identified."""
        data_input = DataInput(datasets=[sample_datasets[2]])  # Low quality dataset
        result = agent.execute(data_input)

        assert result.success is True
        dataset = result.output.processed_datasets[0]

        # Should have identified issues
        assert len(dataset.quality_issues) > 0

    def test_quality_strengths_tracking(self, agent, sample_datasets):
        """Test that quality strengths are identified."""
        data_input = DataInput(datasets=[sample_datasets[0]])  # High quality dataset
        result = agent.execute(data_input)

        assert result.success is True
        dataset = result.output.processed_datasets[0]

        # Should have identified strengths
        assert len(dataset.quality_strengths) > 0

    def test_get_high_quality_datasets(self, agent, sample_datasets):
        """Test filtering output for high quality datasets."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True
        high_quality = result.output.get_high_quality_datasets(min_score=0.75)

        # All should have score >= 0.75
        for dataset in high_quality:
            assert dataset.quality_score >= 0.75

    def test_get_by_quality_level(self, agent, sample_datasets):
        """Test filtering by quality level."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True

        excellent = result.output.get_by_quality_level(DataQualityLevel.EXCELLENT)
        for dataset in excellent:
            assert dataset.quality_level == DataQualityLevel.EXCELLENT

    def test_get_with_publications(self, agent, sample_datasets):
        """Test filtering for datasets with publications."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True
        with_pubs = result.output.get_with_publications()

        for dataset in with_pubs:
            assert dataset.has_publication is True
            assert len(dataset.pubmed_ids) > 0

    def test_get_with_sra_data(self, agent, sample_datasets):
        """Test filtering for datasets with SRA data."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True
        with_sra = result.output.get_with_sra_data()

        for dataset in with_sra:
            assert dataset.has_sra_data is True

    def test_metadata_completeness(self, agent, sample_datasets):
        """Test metadata completeness calculation."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True

        for dataset in result.output.processed_datasets:
            assert 0.0 <= dataset.metadata_completeness <= 1.0

        # High quality dataset should have high completeness
        ds1 = next(d for d in result.output.processed_datasets if d.geo_id == "GSE1")
        assert ds1.metadata_completeness >= 0.7

    def test_age_calculation(self, agent, sample_datasets):
        """Test dataset age calculation."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True

        for dataset in result.output.processed_datasets:
            if dataset.age_days is not None:
                assert dataset.age_days >= 0

    def test_context_metrics(self, agent, sample_datasets):
        """Test that context metrics are recorded."""
        data_input = DataInput(datasets=sample_datasets)
        result = agent.execute(data_input)

        assert result.success is True
        assert result.metadata.get("total_datasets") == 3
        assert "datasets_processed" in result.metadata


class TestProcessedDataset:
    """Test ProcessedDataset model."""

    def test_create_processed_dataset(self):
        """Test creating a processed dataset."""
        dataset = ProcessedDataset(
            geo_id="GSE123",
            title="Test Dataset",
            summary="Test summary",
            organism="Homo sapiens",
            sample_count=100,
            platform_count=1,
            has_publication=True,
            has_sra_data=True,
            quality_score=0.85,
            quality_level=DataQualityLevel.GOOD,
            relevance_score=0.9,
            metadata_completeness=0.95,
        )

        assert dataset.geo_id == "GSE123"
        assert dataset.quality_score == 0.85
        assert dataset.quality_level == DataQualityLevel.GOOD


class TestDataOutput:
    """Test DataOutput model."""

    def test_create_data_output(self):
        """Test creating data output."""
        dataset1 = ProcessedDataset(
            geo_id="GSE1",
            title="Dataset 1",
            summary="Summary 1",
            organism="Homo sapiens",
            sample_count=100,
            platform_count=1,
            has_publication=True,
            has_sra_data=True,
            quality_score=0.9,
            quality_level=DataQualityLevel.EXCELLENT,
            relevance_score=0.85,
            metadata_completeness=0.95,
        )

        output = DataOutput(
            processed_datasets=[dataset1],
            total_processed=1,
            total_passed_quality=1,
            average_quality_score=0.9,
            quality_distribution={
                "excellent": 1,
                "good": 0,
                "fair": 0,
                "poor": 0,
            },
        )

        assert len(output.processed_datasets) == 1
        assert output.total_processed == 1
        assert output.average_quality_score == 0.9


class TestDataQualityLevel:
    """Test DataQualityLevel enum."""

    def test_quality_levels(self):
        """Test quality level enum values."""
        assert DataQualityLevel.EXCELLENT.value == "excellent"
        assert DataQualityLevel.GOOD.value == "good"
        assert DataQualityLevel.FAIR.value == "fair"
        assert DataQualityLevel.POOR.value == "poor"
