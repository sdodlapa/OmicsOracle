"""
Content extractor for parsing full-text articles.

This module uses pubmed_parser library to extract structured content from
scientific articles in various formats (primarily JATS XML from PMC).
"""

import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pubmed_parser as pp
from bs4 import BeautifulSoup

from lib.fulltext.models import Author, ContentType, Figure, FullTextContent, Reference, Section, Table

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts structured content from scientific articles.

    Uses pubmed_parser for PMC XML parsing, providing:
    - Author extraction with affiliations
    - Reference extraction with DOI/PMID
    - Figure and table extraction
    - Section-based paragraph extraction
    """

    def __init__(self):
        """Initialize content extractor."""
        logger.info("ContentExtractor initialized with pubmed_parser")

    def extract_structured_content(
        self, xml_content: str, source_path: Optional[str] = None
    ) -> Optional[FullTextContent]:
        """
        Extract structured content from XML using pubmed_parser.

        Args:
            xml_content: XML content string
            source_path: Optional path to XML file (for pubmed_parser)

        Returns:
            FullTextContent object or None if extraction fails
        """
        try:
            # pubmed_parser requires a file path, so create temp file if needed
            if source_path and Path(source_path).exists():
                xml_path = source_path
                cleanup = False
            else:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".nxml", delete=False, encoding="utf-8"
                )
                temp_file.write(xml_content)
                temp_file.close()
                xml_path = temp_file.name
                cleanup = True

            try:
                # Parse main article metadata
                article = pp.parse_pubmed_xml(xml_path)

                # Parse references
                references = pp.parse_pubmed_references(xml_path)

                # Parse figures
                figures = pp.parse_pubmed_caption(xml_path)

                # Parse tables
                tables = pp.parse_pubmed_table(xml_path, return_xml=True)

                # Parse paragraphs by section
                paragraphs = pp.parse_pubmed_paragraph(xml_path, all_paragraph=True)

                # Transform to our data models
                content = FullTextContent(
                    title=article.get("full_title", ""),
                    abstract=article.get("abstract", ""),
                    keywords=self._parse_keywords(article.get("subjects", "")),
                    authors=self._transform_authors(
                        article.get("author_list", []), article.get("affiliation_list", [])
                    ),
                    sections=self._transform_paragraphs_to_sections(paragraphs),
                    figures=self._transform_figures(figures),
                    tables=self._transform_tables(tables),
                    references=self._transform_references(references),
                    journal=article.get("journal", ""),
                    publication_year=article.get("publication_year", ""),
                    doi=article.get("doi", ""),
                    pmid=article.get("pmid", ""),
                    pmc=article.get("pmc", ""),
                )

                logger.info(
                    f"Extracted structured content: {len(content.authors)} authors, "
                    f"{len(content.sections)} sections, {len(content.references)} refs"
                )
                return content

            finally:
                # Cleanup temp file
                if cleanup:
                    try:
                        Path(xml_path).unlink()
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Structured extraction failed: {e}", exc_info=True)
            return None

    def _parse_keywords(self, subjects: str) -> List[str]:
        """Parse keywords from semicolon-separated subjects string."""
        if not subjects:
            return []
        return [kw.strip() for kw in subjects.split(";") if kw.strip()]

    def _transform_authors(
        self, author_list: List[List[str]], affiliation_list: List[List[str]]
    ) -> List[Author]:
        """
        Transform pubmed_parser author format to our Author model.

        Args:
            author_list: [['surname', 'given_names', 'aff_key'], ...]
            affiliation_list: [['aff_key', 'affiliation_text'], ...]

        Returns:
            List of Author objects
        """
        # Build affiliation lookup
        aff_dict = {aff[0]: aff[1] for aff in affiliation_list if len(aff) >= 2}

        # Group authors by unique name (same author may have multiple affiliations)
        author_dict: Dict[tuple, Author] = {}

        for author_entry in author_list:
            if len(author_entry) < 2:
                continue

            surname = author_entry[0]
            given_names = author_entry[1] if len(author_entry) > 1 else None
            aff_key = author_entry[2] if len(author_entry) > 2 else None

            # Create unique key
            key = (surname, given_names)

            if key not in author_dict:
                author_dict[key] = Author(surname=surname, given_names=given_names, affiliations=[])

            # Add affiliation if available
            if aff_key and aff_key in aff_dict:
                aff_text = aff_dict[aff_key]
                if aff_text not in author_dict[key].affiliations:
                    author_dict[key].affiliations.append(aff_text)

        return list(author_dict.values())

    def _transform_figures(self, figures: List[Dict[str, Any]]) -> List[Figure]:
        """
        Transform pubmed_parser figures to our Figure model.

        Args:
            figures: List of dicts with fig_caption, fig_label, graphic_ref, etc.

        Returns:
            List of Figure objects
        """
        if not figures:  # Handle None or empty list
            return []

        result = []
        for i, fig in enumerate(figures):
            figure = Figure(
                id=fig.get("fig_id", f"fig{i+1}"),
                label=fig.get("fig_label", ""),
                caption=fig.get("fig_caption", ""),
                graphic_ref=fig.get("graphic_ref", ""),
            )
            result.append(figure)

        return result

    def _transform_tables(self, tables: List[Dict[str, Any]]) -> List[Table]:
        """
        Transform pubmed_parser tables to our Table model.

        Args:
            tables: List of dicts with caption, label, table_columns, table_values, etc.

        Returns:
            List of Table objects
        """
        if not tables:  # Handle None or empty list
            return []

        result = []
        for i, tbl in enumerate(tables):
            table = Table(
                id=f"table{i+1}",
                label=tbl.get("label", ""),
                caption=tbl.get("caption", ""),
                html_content=tbl.get("table_xml", ""),
                table_columns=tbl.get("table_columns", []),
                table_values=tbl.get("table_values", []),
            )
            result.append(table)

        return result

    def _transform_references(self, references: List[Dict[str, Any]]) -> List[Reference]:
        """
        Transform pubmed_parser references to our Reference model.

        Args:
            references: List of dicts with pmid_cited, doi_cited, article_title, etc.

        Returns:
            List of Reference objects
        """
        if not references:  # Handle None or empty list
            return []

        result = []
        for i, ref in enumerate(references):
            reference = Reference(
                id=f"ref{i+1}",
                title=ref.get("article_title", ""),
                source=ref.get("journal", ""),
                year=ref.get("year", ""),
                doi=ref.get("doi_cited", ""),
                pmid=ref.get("pmid_cited", ""),
            )
            result.append(reference)

        return result

    def _transform_paragraphs_to_sections(self, paragraphs: List[Dict[str, Any]]) -> List[Section]:
        """
        Transform pubmed_parser paragraphs to hierarchical Section model.

        Args:
            paragraphs: List of dicts with text, section, reference_ids

        Returns:
            List of Section objects
        """
        # Group paragraphs by section
        section_dict: Dict[str, List[Dict[str, Any]]] = {}

        for para in paragraphs:
            section_name = para.get("section", "Body")
            if section_name not in section_dict:
                section_dict[section_name] = []
            section_dict[section_name].append(para)

        # Create Section objects
        sections = []
        for i, (section_name, paras) in enumerate(section_dict.items()):
            # Collect all paragraphs and reference IDs
            paragraph_texts = [p.get("text", "") for p in paras if p.get("text")]
            all_ref_ids = []
            for p in paras:
                ref_ids = p.get("reference_ids", [])
                if isinstance(ref_ids, list):
                    all_ref_ids.extend(ref_ids)

            section = Section(
                id=f"sec{i+1}",
                title=section_name,
                level=1,  # pubmed_parser doesn't provide nesting info
                paragraphs=paragraph_texts,
                reference_ids=list(set(all_ref_ids)),  # Remove duplicates
            )
            sections.append(section)

        return sections

    def extract_text(self, xml_content: str) -> str:
        """
        Extract plain text from XML (fallback method).

        Args:
            xml_content: XML content string

        Returns:
            Plain text content
        """
        try:
            soup = BeautifulSoup(xml_content, "lxml-xml")

            # Try to get body text
            body = soup.find("body")
            if body:
                return body.get_text(separator="\n", strip=True)

            # Fallback to all text
            return soup.get_text(separator="\n", strip=True)

        except Exception as e:
            logger.error(f"Plain text extraction failed: {e}")
            return ""

    def extract_metadata(self, xml_content: str) -> Dict[str, Any]:
        """
        Extract basic metadata from XML.

        Args:
            xml_content: XML content string

        Returns:
            Dictionary with title, abstract, keywords
        """
        try:
            soup = BeautifulSoup(xml_content, "lxml-xml")

            metadata = {}

            # Title
            title = soup.find("article-title")
            if title:
                metadata["title"] = title.get_text(strip=True)

            # Abstract
            abstract = soup.find("abstract")
            if abstract:
                metadata["abstract"] = abstract.get_text(separator=" ", strip=True)

            # Keywords
            keywords = []
            for kwd in soup.find_all("kwd"):
                keywords.append(kwd.get_text(strip=True))
            metadata["keywords"] = keywords

            return metadata

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {}

    def calculate_quality_score(
        self, content: Optional[str], structured_content: Optional[FullTextContent], content_type: ContentType
    ) -> Dict[str, Any]:
        """
        Calculate quality indicators for extracted content.

        Args:
            content: Raw text content
            structured_content: Structured content object
            content_type: Type of content

        Returns:
            Dictionary with quality indicators
        """
        indicators = {
            "has_abstract": False,
            "has_methods": False,
            "has_references": False,
            "has_figures": False,
            "word_count": 0,
        }

        if structured_content:
            indicators["has_abstract"] = bool(structured_content.abstract)
            indicators["has_methods"] = bool(structured_content.get_methods_text())
            indicators["has_references"] = len(structured_content.references) > 0
            indicators["has_figures"] = len(structured_content.figures) > 0

            # Count words in full text
            full_text = structured_content.get_full_text()
            indicators["word_count"] = len(full_text.split())

        elif content:
            # Basic text analysis
            indicators["word_count"] = len(content.split())
            indicators["has_abstract"] = "abstract" in content.lower()[:1000]
            indicators["has_methods"] = "method" in content.lower()
            indicators["has_references"] = "reference" in content.lower()

        return indicators
