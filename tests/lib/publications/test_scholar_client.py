"""
Unit tests for Google Scholar client.

Note: These tests use mocked responses since Google Scholar blocks scrapers.
Live tests would require proxy configuration (ScraperAPI, Tor, etc.)
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from omics_oracle_v2.core.exceptions import PublicationSearchError
from omics_oracle_v2.lib.publications.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.publications.config import GoogleScholarConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource


@pytest.fixture
def scholar_config():
    """Create test Scholar configuration."""
    return GoogleScholarConfig(
        enable=True, max_results=50, rate_limit_seconds=0.5, use_proxy=False  # Minimum allowed
    )


@pytest.fixture
def mock_scholar_result():
    """Create mock Scholar search result."""
    return {
        "bib": {
            "title": "CRISPR-Cas9 gene editing for cancer therapy",
            "abstract": "Novel approach using CRISPR for targeted cancer treatment",
            "author": ["Smith J", "Johnson A", "Williams B"],
            "venue": "Nature Medicine",
            "pub_year": "2020",
        },
        "doi": "10.1038/nm.4567",
        "num_citations": 150,
        "scholar_id": "abc123",
        "pub_url": "https://scholar.google.com/scholar?...",
        "eprint_url": "https://example.com/paper.pdf",
        "num_versions": 3,
    }


class TestScholarClientInitialization:
    """Test Scholar client initialization."""

    def test_init_with_valid_config(self, scholar_config):
        """Test initialization with valid configuration."""
        client = GoogleScholarClient(scholar_config)

        assert client.config == scholar_config
        assert client.source_name == "google_scholar"
        assert client.config.rate_limit_seconds == 0.5

    def test_init_without_scholarly_library(self, scholar_config, monkeypatch):
        """Test initialization fails without scholarly library."""
        # Simulate scholarly not installed
        monkeypatch.setattr("omics_oracle_v2.lib.publications.clients.scholar.SCHOLARLY_AVAILABLE", False)

        with pytest.raises(ImportError, match="scholarly library is required"):
            GoogleScholarClient(scholar_config)


class TestScholarSearch:
    """Test Google Scholar search functionality."""

    @patch("omics_oracle_v2.lib.publications.clients.scholar.scholarly")
    def test_search_basic(self, mock_scholarly, scholar_config, mock_scholar_result):
        """Test basic search returns publications."""
        # Mock scholarly.search_pubs to return iterator with one result
        mock_scholarly.search_pubs.return_value = iter([mock_scholar_result])

        client = GoogleScholarClient(scholar_config)
        results = client.search("CRISPR cancer", max_results=10)

        assert len(results) == 1
        assert isinstance(results[0], Publication)
        assert results[0].title == "CRISPR-Cas9 gene editing for cancer therapy"
        assert results[0].citations == 150
        assert results[0].source == PublicationSource.GOOGLE_SCHOLAR

    @patch("omics_oracle_v2.lib.publications.clients.scholar.scholarly")
    def test_search_with_year_range(self, mock_scholarly, scholar_config, mock_scholar_result):
        """Test search with year range filter."""
        mock_scholarly.search_pubs.return_value = iter([mock_scholar_result])

        client = GoogleScholarClient(scholar_config)
        results = client.search("genomics", max_results=5, year_from=2020, year_to=2024)

        # Verify year range was passed to scholarly
        mock_scholarly.search_pubs.assert_called_once()
        call_kwargs = mock_scholarly.search_pubs.call_args[1]
        assert call_kwargs["year_low"] == 2020
        assert call_kwargs["year_high"] == 2024

    @patch("omics_oracle_v2.lib.publications.clients.scholar.scholarly")
    def test_search_respects_max_results(self, mock_scholarly, scholar_config, mock_scholar_result):
        """Test search respects max_results parameter."""
        # Create 10 mock results
        mock_results = [mock_scholar_result.copy() for _ in range(10)]
        mock_scholarly.search_pubs.return_value = iter(mock_results)

        client = GoogleScholarClient(scholar_config)
        results = client.search("CRISPR", max_results=5)

        assert len(results) == 5  # Should stop at max_results

    @patch("omics_oracle_v2.lib.publications.clients.scholar.scholarly")
    def test_search_handles_errors(self, mock_scholarly, scholar_config):
        """Test search handles errors gracefully."""
        mock_scholarly.search_pubs.side_effect = Exception("Network error")

        client = GoogleScholarClient(scholar_config)

        with pytest.raises(PublicationSearchError, match="Google Scholar search failed"):
            client.search("test query")

    @patch("omics_oracle_v2.lib.publications.clients.scholar.scholarly")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.time.sleep")
    def test_search_applies_rate_limiting(
        self, mock_sleep, mock_scholarly, scholar_config, mock_scholar_result
    ):
        """Test rate limiting between results."""
        # Return 3 results
        mock_results = [mock_scholar_result.copy() for _ in range(3)]
        mock_scholarly.search_pubs.return_value = iter(mock_results)

        client = GoogleScholarClient(scholar_config)
        results = client.search("test", max_results=3)

        # Should sleep 2 times (not after last result)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(scholar_config.rate_limit_seconds)


class TestScholarFetch:
    """Test fetching publications by identifier."""

    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_fetch_by_doi(self, mock_search, scholar_config):
        """Test fetching publication by DOI."""
        mock_pub = Publication(
            title="Test publication", doi="10.1234/test", source=PublicationSource.GOOGLE_SCHOLAR
        )
        mock_search.return_value = [mock_pub]

        client = GoogleScholarClient(scholar_config)
        result = client.fetch_by_doi("10.1234/test")

        assert result is not None
        assert result.doi == "10.1234/test"
        mock_search.assert_called_once_with("doi:10.1234/test", max_results=1)

    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_fetch_by_doi_not_found(self, mock_search, scholar_config):
        """Test fetch returns None when DOI not found."""
        mock_search.return_value = []

        client = GoogleScholarClient(scholar_config)
        result = client.fetch_by_doi("10.1234/notfound")

        assert result is None

    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.fetch_by_doi")
    def test_fetch_by_id_with_doi(self, mock_fetch_doi, scholar_config):
        """Test fetch_by_id with DOI identifier."""
        mock_pub = Publication(title="Test", doi="10.1234/test", source=PublicationSource.GOOGLE_SCHOLAR)
        mock_fetch_doi.return_value = mock_pub

        client = GoogleScholarClient(scholar_config)
        result = client.fetch_by_id("10.1234/test")

        assert result.doi == "10.1234/test"
        mock_fetch_doi.assert_called_once()


class TestScholarCitations:
    """Test citation retrieval."""

    @patch("omics_oracle_v2.lib.publications.clients.scholar.scholarly")
    def test_get_citations_with_scholar_id(self, mock_scholarly, scholar_config):
        """Test getting citations using Scholar ID."""
        mock_result = {"num_citations": 250}
        mock_scholarly.search_pubs.return_value = iter([mock_result])

        pub = Publication(
            title="Test", source=PublicationSource.GOOGLE_SCHOLAR, metadata={"scholar_id": "xyz789"}
        )

        client = GoogleScholarClient(scholar_config)
        citations = client.get_citations(pub)

        assert citations == 250

    @patch("omics_oracle_v2.lib.publications.clients.scholar.scholarly")
    def test_get_citations_by_title(self, mock_scholarly, scholar_config):
        """Test getting citations by searching title."""
        mock_result = {"num_citations": 100}
        mock_scholarly.search_pubs.return_value = iter([mock_result])

        pub = Publication(title="CRISPR gene editing", source=PublicationSource.PUBMED)

        client = GoogleScholarClient(scholar_config)
        citations = client.get_citations(pub)

        assert citations == 100
        # Verify search with quoted title
        mock_scholarly.search_pubs.assert_called_with('"CRISPR gene editing"')

    @patch("omics_oracle_v2.lib.publications.clients.scholar.scholarly")
    def test_get_citations_handles_errors(self, mock_scholarly, scholar_config):
        """Test citation retrieval handles errors."""
        mock_scholarly.search_pubs.side_effect = Exception("Error")

        pub = Publication(title="Test", source=PublicationSource.PUBMED)

        client = GoogleScholarClient(scholar_config)
        citations = client.get_citations(pub)

        assert citations == 0  # Returns 0 on error


class TestScholarResultParsing:
    """Test parsing of Scholar results into Publication model."""

    def test_parse_complete_result(self, scholar_config, mock_scholar_result):
        """Test parsing complete Scholar result."""
        client = GoogleScholarClient(scholar_config)
        pub = client._parse_scholar_result(mock_scholar_result)

        assert pub.title == "CRISPR-Cas9 gene editing for cancer therapy"
        assert pub.abstract == "Novel approach using CRISPR for targeted cancer treatment"
        assert pub.authors == ["Smith J", "Johnson A", "Williams B"]
        assert pub.journal == "Nature Medicine"
        assert pub.publication_date == datetime(2020, 1, 1)
        assert pub.doi == "10.1038/nm.4567"
        assert pub.citations == 150
        assert pub.source == PublicationSource.GOOGLE_SCHOLAR

        # Check metadata
        assert pub.metadata["scholar_id"] == "abc123"
        assert pub.metadata["pdf_url"] == "https://example.com/paper.pdf"

    def test_parse_minimal_result(self, scholar_config):
        """Test parsing minimal Scholar result."""
        minimal_result = {
            "bib": {"title": "Test Title"},
        }

        client = GoogleScholarClient(scholar_config)
        pub = client._parse_scholar_result(minimal_result)

        assert pub.title == "Test Title"
        assert pub.abstract == ""
        assert pub.authors == []
        assert pub.citations == 0

    def test_parse_authors_list(self, scholar_config):
        """Test parsing authors as list."""
        result = {"bib": {"title": "Test", "author": ["Author A", "Author B"]}}

        client = GoogleScholarClient(scholar_config)
        pub = client._parse_scholar_result(result)

        assert pub.authors == ["Author A", "Author B"]

    def test_parse_authors_string(self, scholar_config):
        """Test parsing authors as string."""
        result = {"bib": {"title": "Test", "author": "Author A, Author B, Author C"}}

        client = GoogleScholarClient(scholar_config)
        pub = client._parse_scholar_result(result)

        assert pub.authors == ["Author A", "Author B", "Author C"]

    def test_parse_date(self, scholar_config):
        """Test date parsing."""
        client = GoogleScholarClient(scholar_config)

        # Valid year
        assert client._parse_date("2020") == datetime(2020, 1, 1)
        assert client._parse_date(2020) == datetime(2020, 1, 1)

        # Invalid
        assert client._parse_date("invalid") is None
        assert client._parse_date(None) is None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
