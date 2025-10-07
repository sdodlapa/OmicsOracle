"""
Week 3 Integration Tests - Simplified Version

Tests the complete Week 3 implementation focusing on key integration points.
"""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from omics_oracle_v2.lib.publications.analysis import (
    BiomarkerKnowledgeGraph,
    DatasetImpactReportGenerator,
    DatasetQASystem,
    TemporalTrendAnalyzer,
)
from omics_oracle_v2.lib.publications.citations.models import UsageAnalysis
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline


class TestWeek3Integration:
    """Integration tests for Week 3 features."""

    @pytest.fixture
    def sample_dataset(self):
        """Create a sample dataset publication."""
        return Publication(
            title="TCGA Breast Cancer Dataset",
            doi="10.1038/nature11412",
            abstract="Comprehensive breast cancer genomics dataset",
            authors=["Network, TCGA"],
            publication_date=datetime(2012, 9, 23),
            source=PublicationSource.PUBMED,
        )

    @pytest.fixture
    def sample_analyses(self):
        """Create sample usage analyses."""
        return [
            UsageAnalysis(
                paper_id="paper1",
                paper_title="Biomarker Discovery",
                dataset_reused=True,
                usage_type="biomarker_discovery",
                confidence=0.9,
                novel_biomarkers=["BRCA1", "TP53"],
                application_domain="oncology",
                methodology="machine_learning",
                validation_status="validated",
            ),
            UsageAnalysis(
                paper_id="paper2",
                paper_title="Clinical Validation",
                dataset_reused=True,
                usage_type="clinical_validation",
                confidence=0.85,
                novel_biomarkers=["EGFR"],
                application_domain="oncology",
                methodology="statistical_analysis",
                validation_status="validated",
            ),
            UsageAnalysis(
                paper_id="paper3",
                paper_title="Trend Analysis",
                dataset_reused=True,
                usage_type="trend_analysis",
                confidence=0.8,
                novel_biomarkers=["KRAS"],
                application_domain="oncology",
                methodology="statistical_analysis",
                validation_status="in_progress",
            ),
        ]

    @pytest.fixture
    def sample_papers(self):
        """Create sample citing papers."""
        return [
            Publication(
                title="Biomarker Discovery",
                doi="10.1038/paper1",
                publication_date=datetime(2015, 1, 1),
                source=PublicationSource.PUBMED,
                citation_count=100,
            ),
            Publication(
                title="Clinical Validation",
                doi="10.1038/paper2",
                publication_date=datetime(2016, 1, 1),
                source=PublicationSource.PUBMED,
                citation_count=150,
            ),
            Publication(
                title="Trend Analysis",
                doi="10.1038/paper3",
                publication_date=datetime(2017, 1, 1),
                source=PublicationSource.PUBMED,
                citation_count=75,
            ),
        ]

    def test_complete_workflow(self, sample_dataset, sample_analyses, sample_papers):
        """Test complete workflow from analysis to report."""

        # Step 1: Q&A System
        mock_llm = Mock()
        mock_llm.generate.return_value = {
            "content": "The dataset has been used for biomarker discovery and clinical validation."
        }

        qa_system = DatasetQASystem(mock_llm)
        qa_result = qa_system.ask(sample_dataset, "How has this dataset been used?", sample_analyses)

        assert qa_result["answer"] is not None
        assert qa_result["dataset_title"] == sample_dataset.title
        assert len(qa_result["evidence"]) > 0

        # Step 2: Trend Analysis
        trend_analyzer = TemporalTrendAnalyzer()
        trends = trend_analyzer.analyze_trends(sample_dataset, sample_analyses, sample_papers)

        assert "citation_timeline" in trends
        assert "usage_type_trends" in trends
        assert len(trends["citation_timeline"]) > 0

        # Step 3: Knowledge Graph
        graph = BiomarkerKnowledgeGraph()
        graph.build_from_analyses(sample_dataset, sample_analyses, sample_papers)

        biomarkers = graph.get_all_biomarkers()
        assert len(biomarkers) >= 3  # BRCA1, TP53, EGFR, KRAS

        # Step 4: Report Generation
        report_gen = DatasetImpactReportGenerator()

        # Text report
        text_report = report_gen.generate_report(
            sample_dataset, sample_analyses, trends=trends, graph=graph, qa_results=[qa_result], format="text"
        )

        # Report is a dictionary with 'content' key
        assert "content" in text_report
        assert len(text_report["content"]) > 100
        assert sample_dataset.title in text_report["content"]

        # JSON report
        json_report = report_gen.generate_report(
            sample_dataset, sample_analyses, trends=trends, graph=graph, format="json"
        )

        # JSON report is also a dictionary with 'content' key containing JSON string
        assert "content" in json_report
        assert "sections" in json_report  # Also has sections dict
        assert "dataset_title" in json_report

    def test_multi_source_search_simulation(self):
        """Simulate multi-source search workflow."""
        config = PublicationSearchConfig(enable_pubmed=True, enable_scholar=True, enable_citations=False)

        pipeline = PublicationSearchPipeline(config)

        with patch.object(pipeline.pubmed_client, "search") as mock_pubmed, patch.object(
            pipeline.scholar_client, "search"
        ) as mock_scholar:
            # PubMed results
            pubmed_pubs = [
                Publication(
                    title=f"PubMed Paper {i}",
                    authors=["Author, A."],
                    pmid=f"{10000000 + i}",
                    publication_date=datetime(2023, 1, 1),
                    source=PublicationSource.PUBMED,
                )
                for i in range(15)
            ]

            # Scholar results (some overlap)
            scholar_pubs = [
                Publication(
                    title=f"PubMed Paper {i}",  # Duplicate
                    authors=["Author, A."],
                    doi=f"10.1234/paper{i}",
                    publication_date=datetime(2023, 1, 1),
                    citation_count=50 + i,
                    source=PublicationSource.GOOGLE_SCHOLAR,
                )
                for i in range(10, 15)
            ] + [
                Publication(
                    title=f"Scholar Paper {i}",  # Unique
                    authors=["Author, B."],
                    doi=f"10.1101/2023.{i:02d}.01.123456",
                    publication_date=datetime(2023, 1, 1),
                    citation_count=25 + i,
                    source=PublicationSource.GOOGLE_SCHOLAR,
                )
                for i in range(5)
            ]

            mock_pubmed.return_value = {"publications": pubmed_pubs, "total_found": 15}

            mock_scholar.return_value = {"publications": scholar_pubs, "total_found": 10}

            result = pipeline.search("genomics", max_results=20)

            # Should deduplicate the 5 overlapping papers
            assert len(result.publications) == 20  # 15 + 10 - 5 duplicates

            # Verify metadata
            assert "pubmed" in result.metadata.get("sources_used", [])
            assert "scholar" in result.metadata.get("sources_used", [])
            assert result.metadata.get("duplicates_removed", 0) == 5

    def test_performance_benchmarks(self, sample_dataset, sample_analyses, sample_papers):
        """Basic performance benchmarks."""

        # Trend Analysis
        trend_analyzer = TemporalTrendAnalyzer()
        start = time.time()
        trends = trend_analyzer.analyze_trends(sample_dataset, sample_analyses, sample_papers)
        trend_time = time.time() - start

        assert trend_time < 1.0  # Should be fast
        print(f"\n  Trend Analysis: {trend_time:.3f}s")

        # Knowledge Graph
        graph = BiomarkerKnowledgeGraph()
        start = time.time()
        graph.build_from_analyses(sample_dataset, sample_analyses, sample_papers)
        graph_time = time.time() - start

        assert graph_time < 1.0
        print(f"  Knowledge Graph: {graph_time:.3f}s")

        # Report Generation
        report_gen = DatasetImpactReportGenerator()
        start = time.time()
        report = report_gen.generate_report(
            sample_dataset, sample_analyses, trends=trends, graph=graph, format="text"
        )
        report_time = time.time() - start

        assert report_time < 1.0
        print(f"  Report Generation: {report_time:.3f}s")
        print(f"  Total: {trend_time + graph_time + report_time:.3f}s")

        # Use report to avoid unused variable warning
        assert len(report["content"]) > 100

    def test_coverage_improvement(self):
        """Verify Scholar adds coverage beyond PubMed."""
        config_pubmed_only = PublicationSearchConfig(enable_pubmed=True, enable_scholar=False)

        config_multi_source = PublicationSearchConfig(enable_pubmed=True, enable_scholar=True)

        pipeline_pubmed = PublicationSearchPipeline(config_pubmed_only)
        pipeline_multi = PublicationSearchPipeline(config_multi_source)

        with patch.object(pipeline_pubmed.pubmed_client, "search") as mock_pubmed1, patch.object(
            pipeline_multi.pubmed_client, "search"
        ) as mock_pubmed2, patch.object(pipeline_multi.scholar_client, "search") as mock_scholar:
            # PubMed results (same for both)
            pubmed_pubs = [
                Publication(
                    title=f"Published Paper {i}",
                    pmid=f"{10000000 + i}",
                    publication_date=datetime(2023, 1, 1),
                    source=PublicationSource.PUBMED,
                )
                for i in range(10)
            ]

            # Scholar adds preprints
            scholar_pubs = [
                Publication(
                    title=f"Preprint Paper {i}",
                    doi=f"10.1101/2024.{i:02d}.01.123456",
                    publication_date=datetime(2024, 1, 1),
                    source=PublicationSource.GOOGLE_SCHOLAR,
                )
                for i in range(5)
            ]

            mock_pubmed1.return_value = {"publications": pubmed_pubs, "total_found": 10}
            mock_pubmed2.return_value = {"publications": pubmed_pubs, "total_found": 10}
            mock_scholar.return_value = {"publications": scholar_pubs, "total_found": 5}

            result_pubmed = pipeline_pubmed.search("genomics", max_results=20)
            result_multi = pipeline_multi.search("genomics", max_results=20)

            # Multi-source should find more
            assert len(result_multi.publications) > len(result_pubmed.publications)
            assert len(result_multi.publications) == 15  # 10 + 5
            assert len(result_pubmed.publications) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
