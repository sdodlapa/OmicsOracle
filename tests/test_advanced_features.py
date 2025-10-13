"""
Tests for Day 18 advanced analysis features.

Tests Q&A system, trend analysis, knowledge graph, and report generation.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from omics_oracle_v2.lib.citations.models import UsageAnalysis
from omics_oracle_v2.lib.publications.analysis import (
    BiomarkerKnowledgeGraph,
    DatasetImpactReportGenerator,
    DatasetQASystem,
    TemporalTrendAnalyzer,
)
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource


@pytest.fixture
def sample_dataset():
    """Create sample dataset publication."""
    return Publication(
        title="The Cancer Genome Atlas",
        doi="10.1038/nature12345",
        abstract="A comprehensive genomic dataset for cancer research.",
        authors=["Smith, J.", "Doe, J."],
        publication_date=datetime(2012, 1, 1),
        source=PublicationSource.PUBMED,
    )


@pytest.fixture
def sample_citation_analyses():
    """Create sample citation analyses."""
    return [
        UsageAnalysis(
            paper_id="paper1",
            paper_title="Biomarker Discovery in Cancer",
            dataset_reused=True,
            usage_type="biomarker_discovery",
            confidence=0.9,
            novel_biomarkers=["GENE1", "GENE2"],
            application_domain="oncology",
            methodology="machine_learning",
            validation_status="validated",
        ),
        UsageAnalysis(
            paper_id="paper2",
            paper_title="Clinical Applications",
            dataset_reused=True,
            usage_type="clinical_validation",
            confidence=0.85,
            novel_biomarkers=["GENE3"],
            application_domain="oncology",
            methodology="statistical_analysis",
            validation_status="validated",
        ),
        UsageAnalysis(
            paper_id="paper3",
            paper_title="Unrelated Study",
            dataset_reused=False,
            usage_type="none",
            confidence=0.95,
        ),
    ]


@pytest.fixture
def sample_citing_papers():
    """Create sample citing papers."""
    return [
        Publication(
            title="Biomarker Discovery in Cancer",
            doi="10.1038/paper1",
            publication_date=datetime(2015, 6, 1),
            source=PublicationSource.PUBMED,
        ),
        Publication(
            title="Clinical Applications",
            doi="10.1038/paper2",
            publication_date=datetime(2016, 3, 1),
            source=PublicationSource.PUBMED,
        ),
        Publication(
            title="Unrelated Study",
            doi="10.1038/paper3",
            publication_date=datetime(2017, 1, 1),
            source=PublicationSource.PUBMED,
        ),
    ]


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = MagicMock()
    client.generate.return_value = {
        "content": "Based on the analyses, GENE1 and GENE2 were discovered as novel biomarkers.",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }
    return client


# ============================================================================
# Q&A System Tests
# ============================================================================


def test_qa_system_initialization(mock_llm_client):
    """Test Q&A system initialization."""
    qa = DatasetQASystem(mock_llm_client)
    assert qa.llm == mock_llm_client


def test_qa_ask_question(mock_llm_client, sample_dataset, sample_citation_analyses):
    """Test asking a question."""
    qa = DatasetQASystem(mock_llm_client)

    result = qa.ask(
        dataset=sample_dataset,
        question="What biomarkers were discovered?",
        citation_analyses=sample_citation_analyses,
    )

    # Check result structure
    assert "answer" in result
    assert "evidence" in result
    assert "question" in result
    assert "dataset_title" in result

    # Verify LLM was called
    assert mock_llm_client.generate.called


def test_qa_batch_questions(mock_llm_client, sample_dataset, sample_citation_analyses):
    """Test asking multiple questions."""
    qa = DatasetQASystem(mock_llm_client)

    questions = [
        "What biomarkers were discovered?",
        "What clinical applications exist?",
    ]

    results = qa.ask_batch(sample_dataset, questions, sample_citation_analyses)

    # Check results
    assert len(results) == 2
    assert all("answer" in r for r in results)


def test_qa_suggest_questions(mock_llm_client, sample_dataset, sample_citation_analyses):
    """Test question suggestions."""
    qa = DatasetQASystem(mock_llm_client)

    suggestions = qa.suggest_questions(sample_dataset, sample_citation_analyses)

    # Should suggest questions based on available data
    assert len(suggestions) > 0
    assert any("biomarker" in q.lower() for q in suggestions)


def test_qa_statistics(mock_llm_client, sample_citation_analyses):
    """Test statistics aggregation."""
    qa = DatasetQASystem(mock_llm_client)

    stats = qa.get_statistics(sample_citation_analyses)

    # Check statistics
    assert stats["total_citations"] == 3
    assert stats["dataset_reused"] == 2
    assert stats["reuse_rate"] == pytest.approx(0.6667, rel=0.01)  # Decimal, not percentage
    assert "oncology" in stats["domains"]
    assert "biomarker_discovery" in stats["usage_types"]


# ============================================================================
# Trend Analysis Tests
# ============================================================================


def test_trend_analyzer_initialization():
    """Test trend analyzer initialization."""
    analyzer = TemporalTrendAnalyzer()
    assert analyzer is not None


def test_analyze_trends(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test trend analysis."""
    analyzer = TemporalTrendAnalyzer()

    trends = analyzer.analyze_trends(
        dataset=sample_dataset,
        citation_analyses=sample_citation_analyses,
        citing_papers=sample_citing_papers,
    )

    # Check trend structure
    assert "citation_timeline" in trends
    assert "usage_type_trends" in trends
    assert "domain_evolution" in trends
    assert "biomarker_timeline" in trends
    assert "impact_trajectory" in trends


def test_timeline_construction(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test timeline construction."""
    analyzer = TemporalTrendAnalyzer()

    trends = analyzer.analyze_trends(sample_dataset, sample_citation_analyses, sample_citing_papers)
    timeline = trends["citation_timeline"]

    # Should have entries for years with citations
    assert len(timeline) > 0
    assert all(isinstance(year, int) for year in timeline.keys())


def test_usage_trends(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test usage trend analysis."""
    analyzer = TemporalTrendAnalyzer()

    trends = analyzer.analyze_trends(sample_dataset, sample_citation_analyses, sample_citing_papers)
    usage_trends = trends["usage_type_trends"]

    # Should have trends for usage types
    assert "time_series" in usage_trends
    assert "biomarker_discovery" in usage_trends["time_series"]
    assert "trend_directions" in usage_trends
    assert "biomarker_discovery" in usage_trends["trend_directions"]


def test_impact_trajectory(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test impact trajectory calculation."""
    analyzer = TemporalTrendAnalyzer()

    trends = analyzer.analyze_trends(sample_dataset, sample_citation_analyses, sample_citing_papers)
    trajectory = trends["impact_trajectory"]

    # Should have trajectory metrics
    assert "yearly_metrics" in trajectory
    assert "overall_growth_rate" in trajectory


def test_generate_summary(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test summary generation."""
    analyzer = TemporalTrendAnalyzer()

    trends = analyzer.analyze_trends(sample_dataset, sample_citation_analyses, sample_citing_papers)
    summary = analyzer.generate_summary(trends)

    # Should be a readable string
    assert isinstance(summary, str)
    assert len(summary) > 0


# ============================================================================
# Knowledge Graph Tests
# ============================================================================


def test_knowledge_graph_initialization():
    """Test knowledge graph initialization."""
    graph = BiomarkerKnowledgeGraph()
    assert len(graph.biomarkers) == 0
    assert len(graph.papers) == 0
    assert len(graph.datasets) == 0


def test_build_graph(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test building knowledge graph."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    # Check graph was built
    assert len(graph.biomarkers) == 3  # GENE1, GENE2, GENE3
    assert len(graph.papers) == 2  # Only papers that reused dataset
    assert len(graph.datasets) == 1


def test_get_biomarkers(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test getting biomarkers."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    biomarkers = graph.get_all_biomarkers()
    assert len(biomarkers) == 3

    # Test getting specific biomarker
    gene1 = graph.get_biomarker("GENE1")
    assert gene1 is not None
    assert gene1.name == "GENE1"


def test_biomarker_connections(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test getting biomarker connections."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    connections = graph.get_biomarker_connections("GENE1")

    # Check connections
    assert "biomarker" in connections
    assert "discovered_in_papers" in connections
    assert "datasets_used" in connections
    assert "diseases" in connections


def test_validated_biomarkers(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test getting validated biomarkers."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    validated = graph.get_validated_biomarkers()

    # All biomarkers in sample data are validated
    assert len(validated) == 3


def test_biomarker_timeline(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test biomarker timeline."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    timeline = graph.get_biomarker_timeline()

    # Should have entries for discovery years
    assert len(timeline) > 0
    assert 2015 in timeline or 2016 in timeline


def test_graph_statistics(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test graph statistics."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    stats = graph.get_statistics()

    # Check statistics
    assert stats["total_biomarkers"] == 3
    assert stats["total_papers"] == 2
    assert stats["total_datasets"] == 1
    assert stats["validated_biomarkers"] == 3


def test_export_graph(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test graph export."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    export = graph.export_to_dict()

    # Check export structure
    assert "biomarkers" in export
    assert "papers" in export
    assert "datasets" in export
    assert "edges" in export


def test_graph_summary(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test graph summary generation."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    summary = graph.generate_summary()

    # Should be a readable string
    assert isinstance(summary, str)
    assert "Biomarker Knowledge Graph" in summary


# ============================================================================
# Report Generation Tests
# ============================================================================


def test_report_generator_initialization():
    """Test report generator initialization."""
    generator = DatasetImpactReportGenerator()
    assert generator is not None


def test_generate_text_report(sample_dataset, sample_citation_analyses):
    """Test generating text report."""
    generator = DatasetImpactReportGenerator()

    report = generator.generate_report(
        dataset=sample_dataset,
        citation_analyses=sample_citation_analyses,
        format="text",
    )

    # Check report structure
    assert "content" in report
    assert "format" in report
    assert report["format"] == "text"
    assert "dataset_title" in report


def test_generate_markdown_report(sample_dataset, sample_citation_analyses):
    """Test generating markdown report."""
    generator = DatasetImpactReportGenerator()

    report = generator.generate_report(
        dataset=sample_dataset,
        citation_analyses=sample_citation_analyses,
        format="markdown",
    )

    # Should have markdown formatting
    assert "# Dataset Impact Report" in report["content"]
    assert "##" in report["content"]


def test_generate_json_report(sample_dataset, sample_citation_analyses):
    """Test generating JSON report."""
    generator = DatasetImpactReportGenerator()

    report = generator.generate_report(
        dataset=sample_dataset,
        citation_analyses=sample_citation_analyses,
        format="json",
    )

    # Should be valid JSON
    assert report["format"] == "json"
    import json

    parsed = json.loads(report["content"])
    assert "executive_summary" in parsed


def test_report_with_trends(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test report with trend analysis."""
    analyzer = TemporalTrendAnalyzer()
    trends = analyzer.analyze_trends(sample_dataset, sample_citation_analyses, sample_citing_papers)

    generator = DatasetImpactReportGenerator()
    report = generator.generate_report(
        dataset=sample_dataset,
        citation_analyses=sample_citation_analyses,
        trends=trends,
        format="text",
    )

    # Should include trends
    assert "TEMPORAL TRENDS" in report["content"]


def test_report_with_graph(sample_dataset, sample_citation_analyses, sample_citing_papers):
    """Test report with knowledge graph."""
    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    generator = DatasetImpactReportGenerator()
    report = generator.generate_report(
        dataset=sample_dataset,
        citation_analyses=sample_citation_analyses,
        graph=graph,
        format="text",
    )

    # Should include biomarkers
    assert "BIOMARKER" in report["content"]


def test_report_sections(sample_dataset, sample_citation_analyses):
    """Test report sections."""
    generator = DatasetImpactReportGenerator()

    report = generator.generate_report(
        dataset=sample_dataset,
        citation_analyses=sample_citation_analyses,
    )

    sections = report["sections"]

    # Check all sections exist
    assert "executive_summary" in sections
    assert "dataset_overview" in sections
    assert "usage_statistics" in sections
    assert "key_findings" in sections


def test_comprehensive_report(
    sample_dataset, sample_citation_analyses, sample_citing_papers, mock_llm_client
):
    """Test comprehensive report with all features."""
    # Build all components
    analyzer = TemporalTrendAnalyzer()
    trends = analyzer.analyze_trends(sample_dataset, sample_citation_analyses, sample_citing_papers)

    graph = BiomarkerKnowledgeGraph()
    graph.build_from_analyses(sample_dataset, sample_citation_analyses, sample_citing_papers)

    qa = DatasetQASystem(mock_llm_client)
    qa_results = qa.ask_batch(
        sample_dataset,
        ["What biomarkers were discovered?"],
        sample_citation_analyses,
    )

    # Generate report
    generator = DatasetImpactReportGenerator()
    report = generator.generate_report(
        dataset=sample_dataset,
        citation_analyses=sample_citation_analyses,
        trends=trends,
        graph=graph,
        qa_results=qa_results,
        format="text",
    )

    # Should have all sections
    content = report["content"]
    assert "EXECUTIVE SUMMARY" in content
    assert "USAGE STATISTICS" in content
    assert "TEMPORAL TRENDS" in content
    assert "BIOMARKER DISCOVERIES" in content
    assert "KEY FINDINGS" in content
    assert "Q&A INSIGHTS" in content
