"""Tests for Report Agent."""

import json

import pytest

from omics_oracle_v2.agents import ReportAgent
from omics_oracle_v2.agents.base import AgentState
from omics_oracle_v2.agents.models.data import DataQualityLevel, ProcessedDataset
from omics_oracle_v2.agents.models.report import (
    KeyInsight,
    ReportFormat,
    ReportInput,
    ReportOutput,
    ReportSection,
    ReportType,
)
from omics_oracle_v2.core.config import Settings


class TestReportInput:
    """Test ReportInput model."""

    def test_valid_input(self):
        """Test valid report input."""
        dataset = ProcessedDataset(
            geo_id="GSE123",
            title="Test",
            summary="Summary",
            organism="Homo sapiens",
            sample_count=10,
            platform_count=1,
            has_publication=True,
            has_sra_data=False,
            quality_score=0.8,
            quality_level=DataQualityLevel.GOOD,
            relevance_score=0.9,
            metadata_completeness=0.85,
        )

        report_input = ReportInput(datasets=[dataset])
        assert len(report_input.datasets) == 1
        assert report_input.report_type == ReportType.COMPREHENSIVE

    def test_empty_datasets(self):
        """Test that empty datasets raise error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ReportInput(datasets=[])

    def test_report_type_options(self):
        """Test different report types."""
        dataset = ProcessedDataset(
            geo_id="GSE123",
            title="Test",
            summary="Summary",
            organism="Homo sapiens",
            sample_count=10,
            platform_count=1,
            has_publication=True,
            has_sra_data=False,
            quality_score=0.8,
            quality_level=DataQualityLevel.GOOD,
            relevance_score=0.9,
            metadata_completeness=0.85,
        )

        for report_type in ReportType:
            report_input = ReportInput(datasets=[dataset], report_type=report_type)
            assert report_input.report_type == report_type

    def test_report_format_options(self):
        """Test different report formats."""
        dataset = ProcessedDataset(
            geo_id="GSE123",
            title="Test",
            summary="Summary",
            organism="Homo sapiens",
            sample_count=10,
            platform_count=1,
            has_publication=True,
            has_sra_data=False,
            quality_score=0.8,
            quality_level=DataQualityLevel.GOOD,
            relevance_score=0.9,
            metadata_completeness=0.85,
        )

        for report_format in ReportFormat:
            report_input = ReportInput(datasets=[dataset], report_format=report_format)
            assert report_input.report_format == report_format


class TestReportAgent:
    """Test ReportAgent functionality."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        settings = Settings()
        # Note: AI client may need API key, tests may use fallback mode
        return settings

    @pytest.fixture
    def agent(self, settings):
        """Create ReportAgent instance."""
        return ReportAgent(settings)

    @pytest.fixture
    def sample_datasets(self):
        """Create sample datasets for testing."""
        datasets = []

        # High quality dataset
        datasets.append(
            ProcessedDataset(
                geo_id="GSE1",
                title="Comprehensive breast cancer analysis",
                summary="Large-scale gene expression profiling of breast cancer samples",
                organism="Homo sapiens",
                sample_count=150,
                platform_count=1,
                submission_date="2024-01-01",
                age_days=270,
                pubmed_ids=["12345"],
                has_publication=True,
                has_sra_data=True,
                sra_run_count=150,
                quality_score=0.95,
                quality_level=DataQualityLevel.EXCELLENT,
                quality_strengths=["Large sample size", "Published", "SRA data available"],
                relevance_score=0.9,
                metadata_completeness=0.95,
            )
        )

        # Good quality dataset
        datasets.append(
            ProcessedDataset(
                geo_id="GSE2",
                title="Gene expression in lung cancer",
                summary="Expression profiling of lung cancer tissue samples",
                organism="Homo sapiens",
                sample_count=80,
                platform_count=1,
                submission_date="2023-06-01",
                age_days=480,
                pubmed_ids=["67890"],
                has_publication=True,
                has_sra_data=False,
                quality_score=0.82,
                quality_level=DataQualityLevel.GOOD,
                quality_strengths=["Good sample size", "Published"],
                relevance_score=0.85,
                metadata_completeness=0.80,
            )
        )

        # Fair quality dataset
        datasets.append(
            ProcessedDataset(
                geo_id="GSE3",
                title="Disease gene expression",
                summary="Gene expression study",
                organism="Mus musculus",
                sample_count=20,
                platform_count=1,
                submission_date="2020-01-01",
                age_days=1370,
                has_publication=False,
                has_sra_data=False,
                quality_score=0.55,
                quality_level=DataQualityLevel.FAIR,
                quality_issues=["No publications", "Small sample size"],
                relevance_score=0.6,
                metadata_completeness=0.65,
            )
        )

        return datasets

    def test_agent_initialization(self, agent):
        """Test agent can be initialized."""
        assert agent is not None
        assert agent.state == AgentState.IDLE

    def test_simple_report_generation(self, agent, sample_datasets):
        """Test basic report generation."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output is not None
        assert isinstance(result.output, ReportOutput)
        assert result.output.total_datasets_analyzed == 3

    def test_brief_report_type(self, agent, sample_datasets):
        """Test brief report generation."""
        report_input = ReportInput(datasets=sample_datasets, report_type=ReportType.BRIEF)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output.report_type == ReportType.BRIEF
        # Brief reports should have fewer sections
        assert len(result.output.sections) <= 3

    def test_comprehensive_report_type(self, agent, sample_datasets):
        """Test comprehensive report generation."""
        report_input = ReportInput(datasets=sample_datasets, report_type=ReportType.COMPREHENSIVE)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output.report_type == ReportType.COMPREHENSIVE
        # Comprehensive reports should have more sections
        assert len(result.output.sections) >= 2

    def test_technical_report_type(self, agent, sample_datasets):
        """Test technical report generation."""
        report_input = ReportInput(datasets=sample_datasets, report_type=ReportType.TECHNICAL)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output.report_type == ReportType.TECHNICAL
        # Technical reports should include technical details section
        section_titles = [s.title for s in result.output.sections]
        assert "Technical Details" in section_titles

    def test_markdown_format(self, agent, sample_datasets):
        """Test markdown report format."""
        report_input = ReportInput(datasets=sample_datasets, report_format=ReportFormat.MARKDOWN)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output.report_format == ReportFormat.MARKDOWN
        # Markdown should contain headers
        assert "# " in result.output.full_report or "## " in result.output.full_report

    def test_json_format(self, agent, sample_datasets):
        """Test JSON report format."""
        report_input = ReportInput(datasets=sample_datasets, report_format=ReportFormat.JSON)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output.report_format == ReportFormat.JSON
        # Should be valid JSON
        json.loads(result.output.full_report)

    def test_text_format(self, agent, sample_datasets):
        """Test plain text report format."""
        report_input = ReportInput(datasets=sample_datasets, report_format=ReportFormat.TEXT)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output.report_format == ReportFormat.TEXT
        assert len(result.output.full_report) > 0

    def test_html_format(self, agent, sample_datasets):
        """Test HTML report format."""
        report_input = ReportInput(datasets=sample_datasets, report_format=ReportFormat.HTML)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output.report_format == ReportFormat.HTML
        # HTML should contain tags
        assert "<html>" in result.output.full_report or "<h1>" in result.output.full_report

    def test_query_context_in_title(self, agent, sample_datasets):
        """Test that query context appears in title."""
        report_input = ReportInput(datasets=sample_datasets, query_context="breast cancer TP53")
        result = agent.execute(report_input)

        assert result.success is True
        assert "breast cancer TP53" in result.output.title

    def test_max_datasets_limit(self, agent, sample_datasets):
        """Test limiting number of datasets in report."""
        # Add more datasets
        extended_datasets = sample_datasets * 5  # 15 datasets

        report_input = ReportInput(datasets=extended_datasets, max_datasets=5)
        result = agent.execute(report_input)

        assert result.success is True
        # Should include only top 5
        assert len(result.output.datasets_included) <= 5

    def test_quality_analysis_section(self, agent, sample_datasets):
        """Test quality analysis section generation."""
        report_input = ReportInput(datasets=sample_datasets, include_quality_analysis=True)
        result = agent.execute(report_input)

        assert result.success is True
        # Should have quality analysis section
        section_titles = [s.title for s in result.output.sections]
        assert "Quality Analysis" in section_titles

    def test_recommendations_generation(self, agent, sample_datasets):
        """Test recommendations are generated."""
        report_input = ReportInput(datasets=sample_datasets, include_recommendations=True)
        result = agent.execute(report_input)

        assert result.success is True
        assert len(result.output.recommendations) > 0

    def test_insights_extraction(self, agent, sample_datasets):
        """Test key insights extraction."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        assert len(result.output.key_insights) > 0

    def test_quality_summary_calculation(self, agent, sample_datasets):
        """Test quality summary statistics."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        assert "excellent" in result.output.quality_summary
        assert "good" in result.output.quality_summary
        assert "fair" in result.output.quality_summary
        assert "poor" in result.output.quality_summary

    def test_datasets_included_list(self, agent, sample_datasets):
        """Test list of included dataset IDs."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        assert len(result.output.datasets_included) > 0
        assert "GSE1" in result.output.datasets_included

    def test_generated_timestamp(self, agent, sample_datasets):
        """Test report includes generation timestamp."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        assert result.output.generated_at is not None
        # Should be ISO format timestamp
        assert "T" in result.output.generated_at

    def test_executive_summary(self, agent, sample_datasets):
        """Test executive summary generation."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        assert len(result.output.summary) > 0

    def test_context_metrics(self, agent, sample_datasets):
        """Test that context metrics are recorded."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        assert "execution_time_ms" in result.metadata
        # Check output contains expected data
        assert result.output.total_datasets_analyzed == 3

    def test_no_recommendations_when_disabled(self, agent, sample_datasets):
        """Test recommendations can be disabled."""
        report_input = ReportInput(datasets=sample_datasets, include_recommendations=False)
        result = agent.execute(report_input)

        assert result.success is True
        assert len(result.output.recommendations) == 0

    def test_get_section_by_title(self, agent, sample_datasets):
        """Test retrieving section by title."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        overview = result.output.get_section_by_title("Dataset Overview")
        assert overview is not None
        assert overview.title == "Dataset Overview"

    def test_get_high_confidence_insights(self, agent, sample_datasets):
        """Test filtering high confidence insights."""
        report_input = ReportInput(datasets=sample_datasets)
        result = agent.execute(report_input)

        assert result.success is True
        high_conf = result.output.get_high_confidence_insights(min_confidence=0.8)
        for insight in high_conf:
            assert insight.confidence >= 0.8


class TestReportSection:
    """Test ReportSection model."""

    def test_create_section(self):
        """Test creating a report section."""
        section = ReportSection(title="Overview", content="This is an overview section", order=0)
        assert section.title == "Overview"
        assert section.order == 0


class TestKeyInsight:
    """Test KeyInsight model."""

    def test_create_insight(self):
        """Test creating a key insight."""
        insight = KeyInsight(
            insight="High quality datasets available",
            supporting_datasets=["GSE123", "GSE456"],
            confidence=0.95,
        )
        assert insight.confidence == 0.95
        assert len(insight.supporting_datasets) == 2


class TestReportType:
    """Test ReportType enum."""

    def test_report_types(self):
        """Test report type enum values."""
        assert ReportType.BRIEF.value == "brief"
        assert ReportType.COMPREHENSIVE.value == "comprehensive"
        assert ReportType.TECHNICAL.value == "technical"
        assert ReportType.EXECUTIVE.value == "executive"


class TestReportFormat:
    """Test ReportFormat enum."""

    def test_report_formats(self):
        """Test report format enum values."""
        assert ReportFormat.MARKDOWN.value == "markdown"
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.TEXT.value == "text"
