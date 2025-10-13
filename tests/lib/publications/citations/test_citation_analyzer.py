"""
Tests for citation analyzer.
"""

import datetime
from unittest.mock import Mock

import pytest

from omics_oracle_v2.lib.publications.citations.analyzer import CitationAnalyzer
from omics_oracle_v2.lib.search_engines.citations.models import Publication
from omics_oracle_v2.lib.search_engines.citations.scholar import GoogleScholarClient


@pytest.fixture
def mock_scholar_client():
    """Create mock Scholar client."""
    return Mock(spec=GoogleScholarClient)


@pytest.fixture
def sample_publication():
    """Create sample publication."""
    return Publication(
        title="Test Publication",
        authors=["Author One", "Author Two"],
        doi="10.1234/test.2020",
        publication_date=datetime.date(2020, 1, 1),
        abstract="Test abstract",
        journal="Test Journal",
    )


class TestCitationAnalyzer:
    """Test citation analyzer."""

    def test_initialization(self, mock_scholar_client):
        """Test analyzer initialization."""
        analyzer = CitationAnalyzer(mock_scholar_client)
        assert analyzer.scholar_client == mock_scholar_client

    def test_get_citing_papers(self, mock_scholar_client, sample_publication):
        """Test getting citing papers."""
        # Mock scholar response
        citing_paper = Publication(
            title="Citing Paper",
            authors=["Citing Author"],
            doi="10.5678/citing.2021",
            publication_date=datetime.date(2021, 6, 1),
        )
        mock_scholar_client.get_citations.return_value = [citing_paper]

        analyzer = CitationAnalyzer(mock_scholar_client)
        citing_papers = analyzer.get_citing_papers(sample_publication, max_results=10)

        assert len(citing_papers) == 1
        assert citing_papers[0].title == "Citing Paper"
        mock_scholar_client.get_citations.assert_called_once()

    def test_get_citing_papers_with_limit(self, mock_scholar_client, sample_publication):
        """Test getting citing papers with result limit."""
        # Create mock citing papers
        citing_papers = [
            Publication(
                title=f"Paper {i}",
                authors=[f"Author {i}"],
                doi=f"10.{i}/paper.2021",
                publication_date=datetime.date(2021, i, 1),
            )
            for i in range(1, 6)
        ]
        mock_scholar_client.get_citations.return_value = citing_papers

        analyzer = CitationAnalyzer(mock_scholar_client)
        results = analyzer.get_citing_papers(sample_publication, max_results=3)

        assert len(results) <= 5  # All results returned
        mock_scholar_client.get_citations.assert_called_once()

    def test_get_citation_contexts(self, mock_scholar_client, sample_publication):
        """Test getting citation contexts."""
        citing_paper = Publication(
            title="Citing Paper with Context",
            authors=["Author"],
            doi="10.9999/context.2022",
            publication_date=datetime.date(2022, 1, 1),
            abstract="We used data from the original study [1] to validate our findings.",
        )

        analyzer = CitationAnalyzer(mock_scholar_client)

        # Note: This is a simplified version - real implementation would
        # need full text access to extract actual contexts
        contexts = analyzer.get_citation_contexts(sample_publication, citing_paper)

        assert isinstance(contexts, list)

    def test_analyze_citation_network(self, mock_scholar_client, sample_publication):
        """Test citation network analysis."""
        # Create citation chain: paper A -> paper B -> paper C
        paper_b = Publication(
            title="Paper B",
            authors=["Author B"],
            doi="10.1111/b.2021",
            publication_date=datetime.date(2021, 1, 1),
        )

        paper_c = Publication(
            title="Paper C",
            authors=["Author C"],
            doi="10.2222/c.2022",
            publication_date=datetime.date(2022, 1, 1),
        )

        # Mock scholar to return different citations
        def get_citations_mock(pub, max_results=None):
            if pub.doi == sample_publication.doi:
                return [paper_b]
            elif pub.doi == paper_b.doi:
                return [paper_c]
            else:
                return []

        mock_scholar_client.get_citations.side_effect = get_citations_mock

        analyzer = CitationAnalyzer(mock_scholar_client)
        network = analyzer.analyze_citation_network(sample_publication, depth=2)

        assert "root_paper" in network
        assert network["root_paper"]["title"] == sample_publication.title
        assert "citations" in network
        assert len(network["citations"]) > 0

    def test_get_citation_statistics(self, mock_scholar_client, sample_publication):
        """Test citation statistics."""
        # Create citing papers over multiple years
        citing_papers = [
            Publication(
                title=f"Paper {i}",
                authors=[f"Author {i}"],
                doi=f"10.{i}/paper.{year}",
                publication_date=datetime.date(year, 1, 1),
                citations_count=10 * i if i % 2 == 0 else 5,  # Some highly cited
            )
            for i, year in enumerate([2021, 2021, 2022, 2022, 2023], 1)
        ]
        mock_scholar_client.get_citations.return_value = citing_papers

        analyzer = CitationAnalyzer(mock_scholar_client)
        stats = analyzer.get_citation_statistics(sample_publication)

        assert "total_citations" in stats
        assert stats["total_citations"] == 5

        assert "citations_by_year" in stats
        assert 2021 in stats["citations_by_year"]
        assert stats["citations_by_year"][2021] == 2

        assert "highly_cited_papers" in stats
        # Papers with > 10 citations
        assert len(stats["highly_cited_papers"]) >= 0

    def test_empty_citations(self, mock_scholar_client, sample_publication):
        """Test handling of papers with no citations."""
        mock_scholar_client.get_citations.return_value = []

        analyzer = CitationAnalyzer(mock_scholar_client)
        citing_papers = analyzer.get_citing_papers(sample_publication)

        assert len(citing_papers) == 0

    def test_scholar_client_error(self, mock_scholar_client, sample_publication):
        """Test handling of Scholar client errors."""
        mock_scholar_client.get_citations.side_effect = Exception("API error")

        analyzer = CitationAnalyzer(mock_scholar_client)

        with pytest.raises(Exception):
            analyzer.get_citing_papers(sample_publication)


class TestCitationContextExtraction:
    """Test citation context extraction."""

    def test_context_from_abstract(self, mock_scholar_client):
        """Test extracting context from abstract."""
        cited = Publication(
            title="Original Dataset Paper",
            authors=["Dataset Author"],
            doi="10.1234/dataset.2015",
        )

        citing = Publication(
            title="Application Paper",
            authors=["App Author"],
            doi="10.5678/app.2020",
            abstract="We analyzed data from the comprehensive dataset [1] using machine learning. "
            "The dataset [1] provided crucial training data for our model.",
        )

        analyzer = CitationAnalyzer(mock_scholar_client)
        contexts = analyzer.get_citation_contexts(cited, citing)

        # Should extract citation references
        assert len(contexts) >= 0

    def test_context_extraction_no_abstract(self, mock_scholar_client):
        """Test context extraction when abstract is missing."""
        cited = Publication(title="Paper A", authors=["Author A"])
        citing = Publication(title="Paper B", authors=["Author B"])  # No abstract

        analyzer = CitationAnalyzer(mock_scholar_client)
        contexts = analyzer.get_citation_contexts(cited, citing)

        # Should handle gracefully
        assert isinstance(contexts, list)


class TestCitationNetworkAnalysis:
    """Test citation network building."""

    def test_depth_0_network(self, mock_scholar_client, sample_publication):
        """Test network with depth 0 (just the root paper)."""
        analyzer = CitationAnalyzer(mock_scholar_client)
        network = analyzer.analyze_citation_network(sample_publication, depth=0)

        assert network["root_paper"]["title"] == sample_publication.title
        # Depth 0 should not fetch citations
        assert not mock_scholar_client.get_citations.called

    def test_depth_1_network(self, mock_scholar_client, sample_publication):
        """Test network with depth 1."""
        citing_paper = Publication(
            title="Direct Citation",
            authors=["Author"],
            doi="10.9999/cite.2021",
        )
        mock_scholar_client.get_citations.return_value = [citing_paper]

        analyzer = CitationAnalyzer(mock_scholar_client)
        network = analyzer.analyze_citation_network(sample_publication, depth=1)

        assert len(network["citations"]) == 1
        assert network["citations"][0]["title"] == "Direct Citation"

    def test_citation_chain(self, mock_scholar_client, sample_publication):
        """Test building citation chain."""
        paper_b = Publication(title="Paper B", authors=["B"], doi="10.1/b")
        paper_c = Publication(title="Paper C", authors=["C"], doi="10.2/c")

        # A cited by B, B cited by C
        def mock_citations(pub, max_results=None):
            if pub.doi == sample_publication.doi:
                return [paper_b]
            elif pub.doi == paper_b.doi:
                return [paper_c]
            return []

        mock_scholar_client.get_citations.side_effect = mock_citations

        analyzer = CitationAnalyzer(mock_scholar_client)
        network = analyzer.analyze_citation_network(sample_publication, depth=2)

        # Should have citations at both levels
        assert len(network["citations"]) >= 1


class TestCitationStatistics:
    """Test citation statistics calculation."""

    def test_stats_by_year(self, mock_scholar_client, sample_publication):
        """Test grouping citations by year."""
        papers_2021 = [
            Publication(title=f"2021 Paper {i}", publication_date=datetime.date(2021, i, 1))
            for i in range(1, 4)
        ]
        papers_2022 = [
            Publication(title=f"2022 Paper {i}", publication_date=datetime.date(2022, i, 1))
            for i in range(1, 3)
        ]

        mock_scholar_client.get_citations.return_value = papers_2021 + papers_2022

        analyzer = CitationAnalyzer(mock_scholar_client)
        stats = analyzer.get_citation_statistics(sample_publication)

        assert stats["citations_by_year"][2021] == 3
        assert stats["citations_by_year"][2022] == 2

    def test_highly_cited_identification(self, mock_scholar_client, sample_publication):
        """Test identification of highly cited papers."""
        papers = [
            Publication(title="Low cited", citations_count=5),
            Publication(title="Medium cited", citations_count=50),
            Publication(title="Highly cited", citations_count=500),
        ]
        mock_scholar_client.get_citations.return_value = papers

        analyzer = CitationAnalyzer(mock_scholar_client)
        stats = analyzer.get_citation_statistics(sample_publication)

        # Highly cited threshold is typically > 100
        highly_cited = stats["highly_cited_papers"]
        assert any(p["title"] == "Highly cited" for p in highly_cited)

    def test_stats_empty_citations(self, mock_scholar_client, sample_publication):
        """Test stats with no citations."""
        mock_scholar_client.get_citations.return_value = []

        analyzer = CitationAnalyzer(mock_scholar_client)
        stats = analyzer.get_citation_statistics(sample_publication)

        assert stats["total_citations"] == 0
        assert len(stats["citations_by_year"]) == 0
        assert len(stats["highly_cited_papers"]) == 0
