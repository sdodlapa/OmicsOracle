"""
Tests for LLM-powered citation analysis.
"""

import datetime
from unittest.mock import MagicMock, Mock

import pytest

from omics_oracle_v2.lib.citations.models import CitationContext
from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.publications.citations.llm_analyzer import LLMCitationAnalyzer
from omics_oracle_v2.lib.publications.models import Publication


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = Mock(spec=LLMClient)
    return client


@pytest.fixture
def sample_cited_paper():
    """Create sample cited paper (dataset paper)."""
    return Publication(
        title="TCGA: A Comprehensive Cancer Genomics Database",
        authors=["John Doe", "Jane Smith"],
        doi="10.1234/tcga.2015",
        publication_date=datetime.date(2015, 1, 1),
        abstract="A comprehensive database of cancer genomics data across multiple cancer types.",
        journal="Nature",
    )


@pytest.fixture
def sample_citing_paper():
    """Create sample citing paper."""
    return Publication(
        title="Novel Breast Cancer Biomarkers Identified from TCGA Data",
        authors=["Alice Johnson", "Bob Williams"],
        doi="10.5678/breast.2020",
        publication_date=datetime.date(2020, 6, 15),
        abstract="We analyzed TCGA breast cancer data and identified novel prognostic biomarkers using machine learning.",
        journal="Cancer Research",
    )


@pytest.fixture
def sample_citation_context():
    """Create sample citation context."""
    return CitationContext(
        citing_paper_id="10.5678/breast.2020",
        cited_paper_id="10.1234/tcga.2015",
        context_text="We downloaded breast cancer data from TCGA [1] and performed differential expression analysis to identify prognostic biomarkers. The dataset included 1,000 samples with matched clinical data.",
        sentence="We downloaded breast cancer data from TCGA [1] and performed differential expression analysis.",
        paragraph="We downloaded breast cancer data from TCGA [1] and performed differential expression analysis to identify prognostic biomarkers. The dataset included 1,000 samples with matched clinical data. We used machine learning to identify genes associated with survival.",
        section="Methods",
    )


class TestLLMCitationAnalyzer:
    """Test LLM citation analyzer."""

    def test_initialization(self, mock_llm_client):
        """Test analyzer initialization."""
        analyzer = LLMCitationAnalyzer(mock_llm_client)
        assert analyzer.llm == mock_llm_client

    def test_analyze_citation_context_success(
        self,
        mock_llm_client,
        sample_citation_context,
        sample_cited_paper,
        sample_citing_paper,
    ):
        """Test successful citation analysis."""
        # Mock LLM response
        mock_llm_client.generate_json.return_value = {
            "dataset_reused": True,
            "usage_type": "novel_application",
            "confidence": 0.9,
            "research_question": "Identify breast cancer prognostic biomarkers",
            "application_domain": "cancer biomarker discovery",
            "methodology": "machine learning - differential expression",
            "sample_info": "1,000 breast cancer samples from TCGA",
            "key_findings": [
                "Identified 15 novel prognostic genes",
                "Validated in independent cohort",
            ],
            "clinical_relevance": "high",
            "clinical_details": "Potential for patient stratification",
            "novel_biomarkers": ["GENE1", "GENE2", "GENE3"],
            "validation_status": "validated",
            "reasoning": "Clear description of dataset reuse with specific applications",
        }

        analyzer = LLMCitationAnalyzer(mock_llm_client)
        analysis = analyzer.analyze_citation_context(
            sample_citation_context, sample_cited_paper, sample_citing_paper
        )

        # Verify LLM was called
        assert mock_llm_client.generate_json.called
        call_args = mock_llm_client.generate_json.call_args

        # Verify prompt contains key information
        prompt = call_args[0][0]
        assert "TCGA" in prompt
        assert "breast cancer" in prompt

        # Verify analysis results
        assert analysis.dataset_reused is True
        assert analysis.usage_type == "novel_application"
        assert analysis.confidence == 0.9
        assert analysis.research_question == "Identify breast cancer prognostic biomarkers"
        assert analysis.application_domain == "cancer biomarker discovery"
        assert len(analysis.key_findings) == 2
        assert len(analysis.novel_biomarkers) == 3
        assert analysis.clinical_relevance == "high"
        assert analysis.validation_status == "validated"

    def test_analyze_citation_context_no_reuse(
        self,
        mock_llm_client,
        sample_citation_context,
        sample_cited_paper,
        sample_citing_paper,
    ):
        """Test analysis when dataset was not reused."""
        mock_llm_client.generate_json.return_value = {
            "dataset_reused": False,
            "usage_type": "citation_only",
            "confidence": 0.95,
            "research_question": "Literature review on cancer databases",
            "application_domain": "database comparison",
            "methodology": "narrative review",
            "reasoning": "TCGA mentioned as example database, no data analysis performed",
        }

        analyzer = LLMCitationAnalyzer(mock_llm_client)
        analysis = analyzer.analyze_citation_context(
            sample_citation_context, sample_cited_paper, sample_citing_paper
        )

        assert analysis.dataset_reused is False
        assert analysis.usage_type == "citation_only"
        assert analysis.confidence == 0.95

    def test_analyze_citation_context_llm_failure(
        self,
        mock_llm_client,
        sample_citation_context,
        sample_cited_paper,
        sample_citing_paper,
    ):
        """Test handling of LLM failure."""
        mock_llm_client.generate_json.side_effect = Exception("API error")

        analyzer = LLMCitationAnalyzer(mock_llm_client)
        analysis = analyzer.analyze_citation_context(
            sample_citation_context, sample_cited_paper, sample_citing_paper
        )

        # Should return default analysis
        assert analysis.dataset_reused is False
        assert analysis.usage_type == "unknown"
        assert analysis.confidence == 0.0
        assert "API error" in analysis.reasoning

    def test_analyze_batch(
        self, mock_llm_client, sample_citation_context, sample_cited_paper, sample_citing_paper
    ):
        """Test batch analysis."""
        mock_llm_client.generate_json.return_value = {
            "dataset_reused": True,
            "usage_type": "validation",
            "confidence": 0.8,
            "research_question": "Validate findings",
            "application_domain": "validation study",
        }

        # Create multiple contexts
        contexts = [
            (sample_citation_context, sample_cited_paper, sample_citing_paper),
            (sample_citation_context, sample_cited_paper, sample_citing_paper),
            (sample_citation_context, sample_cited_paper, sample_citing_paper),
        ]

        analyzer = LLMCitationAnalyzer(mock_llm_client)
        analyses = analyzer.analyze_batch(contexts, batch_size=2)

        assert len(analyses) == 3
        assert all(a.dataset_reused for a in analyses)
        assert mock_llm_client.generate_json.call_count == 3

    def test_synthesize_dataset_impact(self, mock_llm_client, sample_cited_paper):
        """Test dataset impact synthesis."""
        # Create mock usage analyses
        from omics_oracle_v2.lib.citations.models import UsageAnalysis

        usage_analyses = [
            UsageAnalysis(
                paper_id="paper1",
                paper_title="Paper 1",
                dataset_reused=True,
                usage_type="novel_application",
                confidence=0.9,
                research_question="Question 1",
                application_domain="cancer research",
                methodology="machine learning",
                key_findings=["Finding 1", "Finding 2"],
                clinical_relevance="high",
                novel_biomarkers=["GENE1", "GENE2"],
                validation_status="validated",
            ),
            UsageAnalysis(
                paper_id="paper2",
                paper_title="Paper 2",
                dataset_reused=True,
                usage_type="validation",
                confidence=0.85,
                research_question="Question 2",
                application_domain="drug discovery",
                methodology="statistical analysis",
                key_findings=["Finding 3"],
                clinical_relevance="medium",
                novel_biomarkers=["GENE3"],
                validation_status="in_progress",
            ),
            UsageAnalysis(
                paper_id="paper3",
                paper_title="Paper 3",
                dataset_reused=False,
                usage_type="citation_only",
                confidence=0.95,
            ),
        ]

        mock_llm_client.generate.return_value = {"content": "The TCGA dataset has had significant impact..."}

        analyzer = LLMCitationAnalyzer(mock_llm_client)
        report = analyzer.synthesize_dataset_impact(sample_cited_paper, usage_analyses)

        # Verify report structure
        assert report.dataset_title == sample_cited_paper.title
        assert report.total_citations == 3
        assert report.dataset_reuse_count == 2
        assert "novel_application" in report.usage_types
        assert "validation" in report.usage_types
        assert len(report.application_domains) > 0
        assert len(report.novel_biomarkers) == 3  # GENE1, GENE2, GENE3
        assert report.summary is not None

    def test_biomarker_extraction(self, mock_llm_client, sample_cited_paper):
        """Test biomarker extraction from analyses."""
        from omics_oracle_v2.lib.citations.models import UsageAnalysis

        usage_analyses = [
            UsageAnalysis(
                paper_id="paper1",
                paper_title="Paper 1",
                dataset_reused=True,
                usage_type="novel_application",
                confidence=0.9,
                application_domain="cancer research",
                novel_biomarkers=["GENE1", "GENE2"],
                validation_status="validated",
            ),
            UsageAnalysis(
                paper_id="paper2",
                paper_title="Paper 2",
                dataset_reused=True,
                usage_type="validation",
                confidence=0.85,
                application_domain="cancer research",
                novel_biomarkers=["GENE1", "GENE3"],  # GENE1 duplicated
                validation_status="in_progress",
            ),
        ]

        mock_llm_client.generate.return_value = {"content": "Summary"}

        analyzer = LLMCitationAnalyzer(mock_llm_client)
        report = analyzer.synthesize_dataset_impact(sample_cited_paper, usage_analyses)

        # Should have 3 unique biomarkers
        assert len(report.novel_biomarkers) == 3
        biomarker_names = {bm.name for bm in report.novel_biomarkers}
        assert biomarker_names == {"GENE1", "GENE2", "GENE3"}

        # GENE1 should have 2 sources
        gene1 = next(bm for bm in report.novel_biomarkers if bm.name == "GENE1")
        assert len(gene1.sources) == 2

    def test_domain_aggregation(self, mock_llm_client, sample_cited_paper):
        """Test application domain aggregation."""
        from omics_oracle_v2.lib.citations.models import UsageAnalysis

        usage_analyses = [
            UsageAnalysis(
                paper_id=f"paper{i}",
                paper_title=f"Paper {i}",
                dataset_reused=True,
                usage_type="novel_application",
                confidence=0.9,
                application_domain="cancer research" if i % 2 == 0 else "drug discovery",
            )
            for i in range(10)
        ]

        mock_llm_client.generate.return_value = {"content": "Summary"}

        analyzer = LLMCitationAnalyzer(mock_llm_client)
        report = analyzer.synthesize_dataset_impact(sample_cited_paper, usage_analyses)

        # Should have 2 domains
        assert len(report.application_domains) == 2

        # Domains should be sorted by count
        assert report.application_domains[0].paper_count == 5
        assert report.application_domains[1].paper_count == 5


class TestIntegration:
    """Integration tests with real LLM (optional)."""

    @pytest.mark.skip(reason="Requires LLM API credentials")
    def test_real_llm_analysis(self, sample_citation_context, sample_cited_paper, sample_citing_paper):
        """Test with real LLM (optional integration test)."""
        llm_client = LLMClient(provider="openai", temperature=0.1)
        analyzer = LLMCitationAnalyzer(llm_client)

        analysis = analyzer.analyze_citation_context(
            sample_citation_context, sample_cited_paper, sample_citing_paper
        )

        # Verify reasonable results
        assert analysis.confidence > 0.0
        assert analysis.usage_type in [
            "novel_application",
            "validation",
            "comparison",
            "reanalysis",
            "citation_only",
        ]
