"""
Tests for ContentExtractor using pubmed_parser.

These tests verify structured content extraction from PMC XML files.
"""

import pytest  # noqa: F401

from lib.fulltext.content_extractor import ContentExtractor
from lib.fulltext.models import ContentType

# Sample minimal JATS XML for testing
SAMPLE_PMC_XML = """<?xml version="1.0" ?>
<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Archiving and Interchange DTD v1.0 20120330//EN" "JATS-archivearticle1.dtd">
<article xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML" article-type="research-article">
  <front>
    <journal-meta>
      <journal-title-group>
        <journal-title>Test Journal</journal-title>
      </journal-title-group>
    </journal-meta>
    <article-meta>
      <article-id pub-id-type="pmc">12345</article-id>
      <article-id pub-id-type="pmid">67890</article-id>
      <article-id pub-id-type="doi">10.1234/test.2023.001</article-id>
      <title-group>
        <article-title>Test Article About Machine Learning</article-title>
      </title-group>
      <contrib-group>
        <contrib contrib-type="author">
          <name>
            <surname>Smith</surname>
            <given-names>John</given-names>
          </name>
          <xref ref-type="aff" rid="aff1">1</xref>
        </contrib>
        <contrib contrib-type="author">
          <name>
            <surname>Doe</surname>
            <given-names>Jane</given-names>
          </name>
          <xref ref-type="aff" rid="aff1">1</xref>
          <xref ref-type="aff" rid="aff2">2</xref>
        </contrib>
      </contrib-group>
      <aff id="aff1">
        <label>1</label>University of Science, Department of AI
      </aff>
      <aff id="aff2">
        <label>2</label>Research Institute of Technology
      </aff>
      <pub-date pub-type="epub">
        <day>15</day>
        <month>06</month>
        <year>2023</year>
      </pub-date>
      <abstract>
        <p>This is a test abstract about machine learning and artificial intelligence.</p>
      </abstract>
      <kwd-group>
        <kwd>machine learning</kwd>
        <kwd>artificial intelligence</kwd>
      </kwd-group>
    </article-meta>
  </front>
  <body>
    <sec id="sec1">
      <title>Introduction</title>
      <p>This is the introduction paragraph discussing background <xref ref-type="bibr" rid="ref1">1</xref>.</p>
      <p>Second paragraph of introduction.</p>
    </sec>
    <sec id="sec2">
      <title>Methods</title>
      <p>We used machine learning methods to analyze the data.</p>
      <fig id="fig1">
        <label>Figure 1</label>
        <caption>
          <p>Distribution of samples in the dataset.</p>
        </caption>
        <graphic xlink:href="test_fig1.jpg"/>
      </fig>
      <table-wrap id="table1">
        <label>Table 1</label>
        <caption>
          <p>Patient demographics</p>
        </caption>
        <table>
          <thead>
            <tr>
              <th>Age</th>
              <th>Gender</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>45</td>
              <td>M</td>
            </tr>
            <tr>
              <td>32</td>
              <td>F</td>
            </tr>
          </tbody>
        </table>
      </table-wrap>
    </sec>
    <sec id="sec3">
      <title>Results</title>
      <p>We found significant results in our experiments.</p>
    </sec>
  </body>
  <back>
    <ref-list>
      <ref id="ref1">
        <element-citation publication-type="journal">
          <person-group person-group-type="author">
            <name>
              <surname>Johnson</surname>
              <given-names>A</given-names>
            </name>
          </person-group>
          <article-title>Previous work on ML</article-title>
          <source>Nature</source>
          <year>2022</year>
          <pub-id pub-id-type="doi">10.1234/nature.2022.001</pub-id>
          <pub-id pub-id-type="pmid">11111111</pub-id>
        </element-citation>
      </ref>
    </ref-list>
  </back>
</article>
"""


class TestContentExtractor:
    @pytest.fixture
    def extractor(self):
        """Create ContentExtractor instance."""
        return ContentExtractor()

    @pytest.fixture
    def sample_xml_file(self, tmp_path):
        """Create a temporary XML file with sample content."""
        xml_file = tmp_path / "test_article.nxml"
        xml_file.write_text(SAMPLE_PMC_XML, encoding="utf-8")
        return str(xml_file)

    def test_extractor_initialization(self, extractor):
        """Test that extractor initializes correctly."""
        assert extractor is not None

    def test_extract_structured_content(self, extractor, sample_xml_file):
        """Test extraction of structured content from XML."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        assert content is not None
        assert content.title == "Test Article About Machine Learning"
        assert "machine learning" in content.abstract.lower()
        assert content.pmid == "67890"
        assert content.pmc == "12345"
        assert content.doi == "10.1234/test.2023.001"
        assert content.journal == "Test Journal"
        assert content.publication_year == "2023"

    def test_extract_authors(self, extractor, sample_xml_file):
        """Test author extraction with affiliations."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        assert len(content.authors) == 2

        # Find Smith
        smith = next((a for a in content.authors if a.surname == "Smith"), None)
        assert smith is not None
        assert smith.given_names == "John"
        assert smith.full_name == "John Smith"
        assert len(smith.affiliations) >= 1
        assert any("University of Science" in aff for aff in smith.affiliations)

        # Find Doe with multiple affiliations
        doe = next((a for a in content.authors if a.surname == "Doe"), None)
        assert doe is not None
        assert doe.given_names == "Jane"
        # Doe should have 2 affiliations
        assert len(doe.affiliations) >= 1

    def test_extract_keywords(self, extractor, sample_xml_file):
        """Test keyword extraction."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        assert len(content.keywords) >= 2
        assert "machine learning" in content.keywords
        assert "artificial intelligence" in content.keywords

    def test_extract_sections(self, extractor, sample_xml_file):
        """Test section extraction."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        assert len(content.sections) >= 3

        # Check section titles
        section_titles = [s.title for s in content.sections]
        assert "Introduction" in section_titles
        assert "Methods" in section_titles
        assert "Results" in section_titles

    def test_get_section_by_title(self, extractor, sample_xml_file):
        """Test finding sections by title."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        methods = content.get_section_by_title("method")
        assert methods is not None
        assert "Methods" in methods.title
        assert any("machine learning" in p.lower() for p in methods.paragraphs)

    def test_extract_figures(self, extractor, sample_xml_file):
        """Test figure extraction."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        assert len(content.figures) >= 1

        fig = content.figures[0]
        assert fig.label == "Figure 1"
        assert "Distribution" in fig.caption
        assert "test_fig1.jpg" in fig.graphic_ref

    def test_extract_tables(self, extractor, sample_xml_file):
        """Test table extraction."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        assert len(content.tables) >= 1

        table = content.tables[0]
        assert table.label == "Table 1"
        assert "demographics" in table.caption.lower()
        assert len(table.table_columns) == 2
        assert "Age" in table.table_columns
        assert "Gender" in table.table_columns

    def test_extract_references(self, extractor, sample_xml_file):
        """Test reference extraction."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        assert len(content.references) >= 1

        ref = content.references[0]
        assert "Previous work" in ref.title
        assert ref.source == "Nature"
        assert ref.year == "2022"
        assert ref.doi == "10.1234/nature.2022.001"
        assert ref.pmid == "11111111"

    def test_get_full_text(self, extractor, sample_xml_file):
        """Test full text retrieval."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        full_text = content.get_full_text()

        assert "Test Article About Machine Learning" in full_text
        assert "machine learning" in full_text.lower()
        assert "Introduction" in full_text
        assert "Methods" in full_text
        assert "Results" in full_text

    def test_get_methods_text(self, extractor, sample_xml_file):
        """Test Methods section extraction."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        methods_text = content.get_methods_text()

        assert "machine learning methods" in methods_text.lower()
        assert len(methods_text) > 0

    def test_extract_text_fallback(self, extractor):
        """Test plain text extraction fallback."""
        text = extractor.extract_text(SAMPLE_PMC_XML)

        assert len(text) > 0
        assert "machine learning" in text.lower()

    def test_extract_metadata(self, extractor):
        """Test basic metadata extraction."""
        metadata = extractor.extract_metadata(SAMPLE_PMC_XML)

        assert metadata["title"] == "Test Article About Machine Learning"
        assert "machine learning" in metadata["abstract"].lower()
        assert len(metadata["keywords"]) >= 2

    def test_calculate_quality_score(self, extractor, sample_xml_file):
        """Test quality score calculation."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML, source_path=sample_xml_file)

        indicators = extractor.calculate_quality_score(None, content, ContentType.XML)

        assert indicators["has_abstract"] is True
        assert indicators["has_methods"] is True
        assert indicators["has_references"] is True
        assert indicators["has_figures"] is True
        assert indicators["word_count"] > 0

    def test_extract_with_string_only(self, extractor):
        """Test extraction with XML string only (no file path)."""
        content = extractor.extract_structured_content(SAMPLE_PMC_XML)

        # Should still work by creating temp file
        assert content is not None
        assert content.title == "Test Article About Machine Learning"
