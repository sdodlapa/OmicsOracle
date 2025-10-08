"""
Unit tests for PubMed integration.
"""

import xml.etree.ElementTree as ET
from unittest.mock import AsyncMock, Mock, patch

import pytest

from omics_oracle.integrations.pubmed import PubMedIntegration, search_pubmed_for_geo


class TestPubMedIntegration:
    """Test suite for PubMed integration functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pubmed = PubMedIntegration(email="test@example.com")

    def test_init_with_params(self):
        """Test initialization with parameters."""
        pubmed = PubMedIntegration(email="test@example.com", api_key="test_key")
        assert pubmed.email == "test@example.com"
        assert pubmed.api_key == "test_key"
        assert pubmed.session is None

    def test_build_params_basic(self):
        """Test parameter building with basic params."""
        params = self.pubmed._build_params()

        assert params["tool"] == "OmicsOracle"
        assert params["retmode"] == "xml"
        assert params["email"] == "test@example.com"

    def test_build_params_with_api_key(self):
        """Test parameter building with API key."""
        pubmed = PubMedIntegration(email="test@example.com", api_key="test_key")
        params = pubmed._build_params()

        assert params["api_key"] == "test_key"

    def test_build_params_with_kwargs(self):
        """Test parameter building with additional kwargs."""
        params = self.pubmed._build_params(db="pubmed", term="test")

        assert params["db"] == "pubmed"
        assert params["term"] == "test"

    @patch("aiohttp.ClientSession")
    @patch("aiohttp.TCPConnector")
    async def test_context_manager(self, mock_connector, mock_session):
        """Test async context manager."""
        mock_session_instance = AsyncMock()
        mock_session.return_value = mock_session_instance

        async with self.pubmed as pubmed_ctx:
            assert pubmed_ctx.session is not None
            mock_session.assert_called_once()

        mock_session_instance.close.assert_called_once()

    def test_extract_paper_info_complete(self):
        """Test paper info extraction with complete data."""
        # Create mock XML element
        xml_data = """
        <PubmedArticle>
            <MedlineCitation>
                <PMID>12345678</PMID>
                <Article>
                    <ArticleTitle>Test Article Title</ArticleTitle>
                    <AuthorList>
                        <Author>
                            <LastName>Smith</LastName>
                            <ForeName>John</ForeName>
                        </Author>
                        <Author>
                            <LastName>Doe</LastName>
                            <ForeName>Jane</ForeName>
                        </Author>
                    </AuthorList>
                    <Journal>
                        <Title>Test Journal</Title>
                    </Journal>
                    <PubDate>
                        <Year>2023</Year>
                    </PubDate>
                    <Abstract>
                        <AbstractText>This is a test abstract.</AbstractText>
                    </Abstract>
                </Article>
            </MedlineCitation>
        </PubmedArticle>
        """

        root = ET.fromstring(xml_data)
        paper_info = self.pubmed._extract_paper_info(root)

        assert paper_info is not None
        assert paper_info["pmid"] == "12345678"
        assert paper_info["title"] == "Test Article Title"
        assert len(paper_info["authors"]) == 2
        assert "Smith, John" in paper_info["authors"]
        assert "Doe, Jane" in paper_info["authors"]
        assert paper_info["journal"] == "Test Journal"
        assert paper_info["year"] == "2023"
        assert paper_info["abstract"] == "This is a test abstract."
        assert paper_info["pubmed_url"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"

    def test_extract_paper_info_minimal(self):
        """Test paper info extraction with minimal data."""
        xml_data = """
        <PubmedArticle>
            <MedlineCitation>
                <PMID>87654321</PMID>
                <Article>
                    <ArticleTitle>Minimal Article</ArticleTitle>
                </Article>
            </MedlineCitation>
        </PubmedArticle>
        """

        root = ET.fromstring(xml_data)
        paper_info = self.pubmed._extract_paper_info(root)

        assert paper_info is not None
        assert paper_info["pmid"] == "87654321"
        assert paper_info["title"] == "Minimal Article"
        assert paper_info["authors"] == []
        assert paper_info["journal"] == "Unknown journal"
        assert paper_info["year"] is None
        assert paper_info["abstract"] is None

    def test_extract_paper_info_invalid(self):
        """Test paper info extraction with invalid XML."""
        xml_data = "<invalid>Invalid XML</invalid>"

        root = ET.fromstring(xml_data)
        paper_info = self.pubmed._extract_paper_info(root)

        assert paper_info is None

    @pytest.mark.asyncio
    async def test_search_papers_no_session(self):
        """Test search papers without initialized session."""
        with pytest.raises(RuntimeError, match="Session not initialized"):
            await self.pubmed.search_papers("GSE12345")

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_search_papers_success(self, mock_get):
        """Test successful paper search."""
        # Mock response XML
        mock_xml = """
        <eSearchResult>
            <IdList>
                <Id>12345678</Id>
                <Id>87654321</Id>
            </IdList>
        </eSearchResult>
        """

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.text = AsyncMock(return_value=mock_xml)
        mock_get.return_value.__aenter__.return_value = mock_response

        self.pubmed.session = AsyncMock()

        pmids = await self.pubmed.search_papers("GSE12345", max_results=10)

        assert len(pmids) == 2
        assert "12345678" in pmids
        assert "87654321" in pmids

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_search_papers_no_results(self, mock_get):
        """Test paper search with no results."""
        mock_xml = """
        <eSearchResult>
            <IdList></IdList>
        </eSearchResult>
        """

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.text = AsyncMock(return_value=mock_xml)
        mock_get.return_value.__aenter__.return_value = mock_response

        self.pubmed.session = AsyncMock()

        pmids = await self.pubmed.search_papers("NONEXISTENT")

        assert pmids == []

    @pytest.mark.asyncio
    async def test_fetch_paper_details_empty(self):
        """Test fetching details with empty PMID list."""
        self.pubmed.session = AsyncMock()

        papers = await self.pubmed.fetch_paper_details([])

        assert papers == []

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_paper_details_success(self, mock_get):
        """Test successful paper details fetching."""
        mock_xml = """
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test Article</ArticleTitle>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>
        """

        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.text = AsyncMock(return_value=mock_xml)
        mock_get.return_value.__aenter__.return_value = mock_response

        self.pubmed.session = AsyncMock()

        papers = await self.pubmed.fetch_paper_details(["12345678"])

        assert len(papers) == 1
        assert papers[0]["pmid"] == "12345678"
        assert papers[0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_get_related_papers_integration(self):
        """Test complete workflow of getting related papers."""
        with patch.object(self.pubmed, "search_papers") as mock_search, patch.object(
            self.pubmed, "fetch_paper_details"
        ) as mock_fetch:
            mock_search.return_value = ["12345678", "87654321"]
            mock_fetch.return_value = [
                {"pmid": "12345678", "title": "Paper 1"},
                {"pmid": "87654321", "title": "Paper 2"},
            ]

            papers = await self.pubmed.get_related_papers("GSE12345", "Test Dataset")

            assert len(papers) == 2
            mock_search.assert_called_once_with("GSE12345", "Test Dataset", 10)
            mock_fetch.assert_called_once_with(["12345678", "87654321"])


class TestConvenienceFunction:
    """Test the convenience function."""

    @pytest.mark.asyncio
    @patch("omics_oracle.integrations.pubmed.PubMedIntegration")
    async def test_search_pubmed_for_geo(self, mock_pubmed_class):
        """Test the convenience function."""
        mock_pubmed = AsyncMock()
        mock_pubmed.get_related_papers.return_value = [{"pmid": "12345", "title": "Test"}]
        mock_pubmed_class.return_value.__aenter__.return_value = mock_pubmed

        papers = await search_pubmed_for_geo("GSE12345", email="test@example.com")

        assert len(papers) == 1
        assert papers[0]["pmid"] == "12345"
        mock_pubmed_class.assert_called_once_with(email="test@example.com")
        mock_pubmed.get_related_papers.assert_called_once_with("GSE12345", None, 10)


if __name__ == "__main__":
    pytest.main([__file__])
