"""
Unit tests for citation managers integration.
"""

import json

import pytest

from omics_oracle.integrations.citation_managers import CitationManagerIntegration, export_geo_references


class TestCitationManagerIntegration:
    """Test suite for citation manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.citation_manager = CitationManagerIntegration()
        self.mock_geo_data = {
            "accession": "GSE12345",
            "title": "Test RNA-seq Dataset",
            "summary": "This is a test RNA sequencing dataset for validation purposes.",
            "submission_date": "2023-01-15",
            "organism": "Homo sapiens",
            "platform": "GPL24676",
        }

    def test_format_geo_reference_basic(self):
        """Test basic GEO reference formatting."""
        reference = self.citation_manager.format_geo_reference(self.mock_geo_data)

        assert reference["id"] == "GSE12345"
        assert reference["type"] == "dataset"
        assert reference["title"] == "Test RNA-seq Dataset"
        assert reference["abstract"] == "This is a test RNA sequencing dataset for validation purposes."
        assert reference["URL"] == "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345"
        assert reference["publisher"] == "Gene Expression Omnibus (GEO)"
        assert reference["source"] == "NCBI GEO"
        assert reference["note"] == "GEO accession: GSE12345"
        assert reference["issued"]["date-parts"] == [["2023"]]

    def test_format_geo_reference_with_papers(self):
        """Test GEO reference formatting with related papers."""
        papers = [
            {
                "pmid": "12345",
                "title": "Related Paper 1",
                "authors": ["Smith, J", "Doe, J"],
                "journal": "Nature",
                "year": "2023",
                "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/12345/",
            },
            {
                "pmid": "67890",
                "title": "Related Paper 2",
                "authors": ["Brown, A"],
                "journal": "Science",
                "year": "2022",
                "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/67890/",
            },
        ]

        reference = self.citation_manager.format_geo_reference(self.mock_geo_data, papers)

        assert "related_papers" in reference
        assert len(reference["related_papers"]) == 2
        assert reference["related_papers"][0]["pmid"] == "12345"
        assert reference["related_papers"][0]["title"] == "Related Paper 1"

    def test_format_geo_reference_invalid_date(self):
        """Test reference formatting with invalid date."""
        geo_data = self.mock_geo_data.copy()
        geo_data["submission_date"] = "invalid-date"

        reference = self.citation_manager.format_geo_reference(geo_data)

        assert reference["issued"]["date-parts"] == [["invalid-date"]]

    def test_to_bibtex_basic(self):
        """Test BibTeX format generation."""
        reference = self.citation_manager.format_geo_reference(self.mock_geo_data)
        bibtex = self.citation_manager.to_bibtex(reference)

        assert "@misc{GSE12345," in bibtex
        assert "title = {Test RNA-seq Dataset}" in bibtex
        assert "publisher = {Gene Expression Omnibus (GEO)}" in bibtex
        assert "url = {https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345}" in bibtex
        assert "year = {2023}" in bibtex
        assert "note = {GEO accession: GSE12345}" in bibtex
        assert bibtex.endswith("}")

    def test_to_bibtex_long_abstract(self):
        """Test BibTeX generation with long abstract."""
        geo_data = self.mock_geo_data.copy()
        geo_data["summary"] = "A" * 600  # Long abstract

        reference = self.citation_manager.format_geo_reference(geo_data)
        bibtex = self.citation_manager.to_bibtex(reference)

        # Should truncate abstract
        assert "abstract = {" + "A" * 500 + "...}" in bibtex

    def test_to_ris_basic(self):
        """Test RIS format generation."""
        reference = self.citation_manager.format_geo_reference(self.mock_geo_data)
        ris = self.citation_manager.to_ris(reference)

        lines = ris.split("\n")
        assert "TY  - DATA" in lines
        assert "TI  - Test RNA-seq Dataset" in lines
        assert "UR  - https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345" in lines
        assert "PB  - Gene Expression Omnibus (GEO)" in lines
        assert "PY  - 2023" in lines
        assert "N1  - GEO accession: GSE12345" in lines
        assert "ER  - " in lines

    def test_to_ris_with_papers(self):
        """Test RIS format with related papers."""
        papers = [
            {"pmid": "12345", "title": "Related Paper 1"},
            {"pmid": "67890", "title": "Related Paper 2"},
            {"pmid": "11111", "title": "Related Paper 3"},
        ]

        reference = self.citation_manager.format_geo_reference(self.mock_geo_data, papers)
        ris = self.citation_manager.to_ris(reference)

        assert "N1  - Related Papers:" in ris
        assert "N1  - PMID:12345 - Related Paper 1" in ris
        assert "N1  - PMID:67890 - Related Paper 2" in ris
        assert "N1  - PMID:11111 - Related Paper 3" in ris

    def test_to_ris_long_abstract(self):
        """Test RIS format with long abstract."""
        geo_data = self.mock_geo_data.copy()
        geo_data["summary"] = "B" * 250  # Long abstract

        reference = self.citation_manager.format_geo_reference(geo_data)
        ris = self.citation_manager.to_ris(reference)

        # Should split abstract into chunks
        assert "AB  - " + "B" * 200 in ris
        assert "AB  - " + "B" * 50 in ris

    def test_to_endnote_xml_basic(self):
        """Test EndNote XML format generation."""
        reference = self.citation_manager.format_geo_reference(self.mock_geo_data)
        xml = self.citation_manager.to_endnote_xml(reference)

        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
        assert '<ref-type name="Dataset">59</ref-type>' in xml
        assert "<title>Test RNA-seq Dataset</title>" in xml
        assert "<year>2023</year>" in xml
        assert "<publisher>Gene Expression Omnibus (GEO)</publisher>" in xml
        assert "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345" in xml

    def test_escape_xml_special_chars(self):
        """Test XML character escaping."""
        text = "Test & <tag> \"quoted\" 'single' > text"
        escaped = self.citation_manager._escape_xml(text)

        assert "&amp;" in escaped
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "&quot;" in escaped
        assert "&apos;" in escaped

    def test_escape_xml_empty_string(self):
        """Test XML escaping with empty string input."""
        escaped = self.citation_manager._escape_xml("")
        assert escaped == ""

    def test_to_csl_json_basic(self):
        """Test CSL-JSON format generation."""
        reference = self.citation_manager.format_geo_reference(self.mock_geo_data)
        csl_json = self.citation_manager.to_csl_json(reference)

        data = json.loads(csl_json)
        assert len(data) == 1

        item = data[0]
        assert item["id"] == "GSE12345"
        assert item["type"] == "dataset"
        assert item["title"] == "Test RNA-seq Dataset"
        assert item["URL"] == "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345"
        assert item["publisher"] == "Gene Expression Omnibus (GEO)"
        assert "issued" in item
        assert "accessed" in item

    def test_export_references_bibtex(self):
        """Test exporting multiple references in BibTeX format."""
        datasets = [
            self.mock_geo_data,
            {
                "accession": "GSE67890",
                "title": "Another Test Dataset",
                "summary": "Another test dataset.",
                "submission_date": "2022-06-20",
            },
        ]

        bibtex = self.citation_manager.export_references(datasets, "bibtex")

        assert "@misc{GSE12345," in bibtex
        assert "@misc{GSE67890," in bibtex
        assert "Test RNA-seq Dataset" in bibtex
        assert "Another Test Dataset" in bibtex

    def test_export_references_csl_json(self):
        """Test exporting multiple references in CSL-JSON format."""
        datasets = [
            self.mock_geo_data,
            {
                "accession": "GSE67890",
                "title": "Another Test Dataset",
                "summary": "Another test dataset.",
                "submission_date": "2022-06-20",
            },
        ]

        csl_json = self.citation_manager.export_references(datasets, "csl-json")

        data = json.loads(csl_json)
        assert len(data) == 2
        assert data[0]["id"] == "GSE12345"
        assert data[1]["id"] == "GSE67890"

    def test_export_references_unsupported_format(self):
        """Test exporting with unsupported format."""
        datasets = [self.mock_geo_data]

        result = self.citation_manager.export_references(datasets, "unsupported")

        # Should return empty string for unsupported format
        assert result == ""


class TestConvenienceFunction:
    """Test the convenience function."""

    def test_export_geo_references(self):
        """Test the convenience function."""
        datasets = [
            {
                "accession": "GSE12345",
                "title": "Test Dataset",
                "summary": "Test summary.",
                "submission_date": "2023-01-01",
            }
        ]

        bibtex = export_geo_references(datasets, "bibtex")

        assert "@misc{GSE12345," in bibtex
        assert "Test Dataset" in bibtex


if __name__ == "__main__":
    pytest.main([__file__])
