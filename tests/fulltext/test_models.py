"""
Tests for full-text data models.
"""

from lib.fulltext.models import (
    Author,
    ContentType,
    Figure,
    FullTextContent,
    FullTextResult,
    Reference,
    Section,
    SourceType,
    Table,
)


class TestAuthor:
    def test_author_creation(self):
        author = Author(
            surname="Smith",
            given_names="John",
            email="john@example.com",
            orcid="0000-0001-2345-6789",
            affiliations=["University of Science", "Lab of Research"],
        )

        assert author.surname == "Smith"
        assert author.given_names == "John"
        assert author.full_name == "John Smith"
        assert len(author.affiliations) == 2

    def test_author_without_given_name(self):
        author = Author(surname="Doe")
        assert author.full_name == "Doe"

    def test_author_to_dict(self):
        author = Author(surname="Jones", given_names="Alice")
        data = author.to_dict()

        assert data["surname"] == "Jones"
        assert data["given_names"] == "Alice"
        assert data["full_name"] == "Alice Jones"


class TestFigure:
    def test_figure_creation(self):
        fig = Figure(
            id="fig1", label="Figure 1", caption="Distribution of samples", graphic_ref="PMC123_fig1.jpg"
        )

        assert fig.id == "fig1"
        assert fig.label == "Figure 1"
        assert "Distribution" in fig.caption


class TestTable:
    def test_table_creation(self):
        table = Table(
            id="table1",
            label="Table 1",
            caption="Patient demographics",
            table_columns=["Age", "Gender"],
            table_values=[["45", "M"], ["32", "F"]],
        )

        assert table.id == "table1"
        assert len(table.table_columns) == 2
        assert len(table.table_values) == 2


class TestReference:
    def test_reference_creation(self):
        ref = Reference(
            id="ref1",
            authors=["Smith J", "Doe A"],
            title="Important findings",
            source="Nature",
            year="2023",
            doi="10.1234/nature.2023.001",
            pmid="12345678",
        )

        assert ref.id == "ref1"
        assert len(ref.authors) == 2
        assert ref.doi == "10.1234/nature.2023.001"


class TestSection:
    def test_section_creation(self):
        section = Section(
            id="sec1",
            title="Introduction",
            level=1,
            paragraphs=["This is the first paragraph.", "This is the second."],
        )

        assert section.title == "Introduction"
        assert section.level == 1
        assert len(section.paragraphs) == 2

    def test_section_get_full_text(self):
        section = Section(id="sec1", title="Methods", paragraphs=["Para 1", "Para 2"])

        text = section.get_full_text()
        assert "Methods" in text
        assert "Para 1" in text
        assert "Para 2" in text

    def test_nested_sections(self):
        subsection = Section(id="sec1.1", title="Subsection", level=2, paragraphs=["Subsection content"])

        parent = Section(
            id="sec1", title="Parent", level=1, paragraphs=["Parent content"], subsections=[subsection]
        )

        text = parent.get_full_text()
        assert "Parent" in text
        assert "Subsection" in text
        assert "Subsection content" in text


class TestFullTextContent:
    def test_content_creation(self):
        content = FullTextContent(
            title="Test Article",
            abstract="This is a test abstract.",
            keywords=["test", "article"],
            authors=[Author(surname="Smith", given_names="John")],
            pmid="12345678",
            pmc="PMC123456",
        )

        assert content.title == "Test Article"
        assert len(content.keywords) == 2
        assert len(content.authors) == 1
        assert content.pmid == "12345678"

    def test_get_section_by_title(self):
        methods = Section(id="sec1", title="Methods", level=1)
        results = Section(id="sec2", title="Results", level=1)

        content = FullTextContent(title="Test", sections=[methods, results])

        found = content.get_section_by_title("method")
        assert found is not None
        assert found.title == "Methods"

        found_results = content.get_section_by_title("RESULT", case_sensitive=False)
        assert found_results is not None

    def test_get_methods_text(self):
        methods = Section(id="sec1", title="Methods", paragraphs=["We used this method."])

        content = FullTextContent(title="Test", sections=[methods])

        methods_text = content.get_methods_text()
        assert "We used this method" in methods_text

    def test_get_full_text(self):
        section = Section(id="sec1", title="Introduction", paragraphs=["Intro paragraph"])

        content = FullTextContent(title="Test Article", abstract="Test abstract", sections=[section])

        full_text = content.get_full_text()
        assert "Test Article" in full_text
        assert "Test abstract" in full_text
        assert "Introduction" in full_text
        assert "Intro paragraph" in full_text

    def test_to_dict(self):
        content = FullTextContent(title="Test", authors=[Author(surname="Smith")], pmid="123")

        data = content.to_dict()
        assert data["title"] == "Test"
        assert len(data["authors"]) == 1
        assert data["pmid"] == "123"


class TestFullTextResult:
    def test_result_creation(self):
        result = FullTextResult(
            success=True,
            content="This is the full text.",
            content_type=ContentType.XML,
            source=SourceType.PMC,
            source_url="https://example.com",
        )

        assert result.success is True
        assert result.content_type == ContentType.XML
        assert result.source == SourceType.PMC

    def test_quality_score_calculation(self):
        result = FullTextResult(
            success=True,
            content_type=ContentType.XML,
            has_abstract=True,
            has_methods=True,
            has_references=True,
            has_figures=True,
            word_count=3500,
        )

        score = result.calculate_quality_score()

        # XML: 0.3, abstract: 0.2, methods: 0.15, refs: 0.15, figs: 0.1, words: 0.1
        # Total should be 1.0
        assert score >= 0.95  # Allow small floating point error
        assert result.quality_score >= 0.95

    def test_quality_score_partial(self):
        result = FullTextResult(
            success=True, content_type=ContentType.PDF, has_abstract=True, word_count=1500
        )

        score = result.calculate_quality_score()

        # PDF: 0.15, abstract: 0.2, words: 0.05 = 0.4
        assert 0.35 <= score <= 0.45

    def test_to_dict(self):
        result = FullTextResult(success=True, content_type=ContentType.XML, source=SourceType.PMC)

        data = result.to_dict()
        assert data["success"] is True
        assert data["content_type"] == "xml"
        assert data["source"] == "pmc"
