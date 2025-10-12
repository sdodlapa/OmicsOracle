"""
Data models for full-text content extraction.

These models represent structured information extracted from scientific articles
including authors, figures, tables, references, and hierarchical sections.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(Enum):
    """Type of content format."""

    XML = "xml"
    HTML = "html"
    PDF = "pdf"
    TEXT = "text"


class SourceType(Enum):
    """Source of the full-text content."""

    PMC = "pmc"
    UNPAYWALL = "unpaywall"
    INSTITUTIONAL = "institutional"
    CORE = "core"
    ARXIV = "arxiv"
    BIORXIV = "biorxiv"
    SCIHUB = "scihub"
    LIBGEN = "libgen"
    PUBLISHER = "publisher"


@dataclass
class Author:
    """Represents an author with affiliations."""

    surname: str
    given_names: Optional[str] = None
    email: Optional[str] = None
    orcid: Optional[str] = None
    affiliations: List[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        """Get full name in 'Given Surname' format."""
        if self.given_names:
            return f"{self.given_names} {self.surname}"
        return self.surname

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "surname": self.surname,
            "given_names": self.given_names,
            "email": self.email,
            "orcid": self.orcid,
            "affiliations": self.affiliations,
            "full_name": self.full_name,
        }


@dataclass
class Figure:
    """Represents a figure in the article."""

    id: str
    label: Optional[str] = None
    caption: Optional[str] = None
    image_path: Optional[str] = None  # Local path if downloaded
    graphic_ref: Optional[str] = None  # Original reference (e.g., filename in XML)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "label": self.label,
            "caption": self.caption,
            "image_path": self.image_path,
            "graphic_ref": self.graphic_ref,
        }


@dataclass
class Table:
    """Represents a table in the article."""

    id: str
    label: Optional[str] = None
    caption: Optional[str] = None
    html_content: Optional[str] = None  # HTML representation
    csv_data: Optional[str] = None  # CSV representation if converted
    table_columns: List[str] = field(default_factory=list)
    table_values: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "label": self.label,
            "caption": self.caption,
            "html_content": self.html_content,
            "csv_data": self.csv_data,
            "table_columns": self.table_columns,
            "table_values": self.table_values,
        }


@dataclass
class Reference:
    """Represents a bibliographic reference."""

    id: str
    authors: List[str] = field(default_factory=list)
    title: Optional[str] = None
    source: Optional[str] = None  # Journal name
    year: Optional[str] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "authors": self.authors,
            "title": self.title,
            "source": self.source,
            "year": self.year,
            "volume": self.volume,
            "pages": self.pages,
            "doi": self.doi,
            "pmid": self.pmid,
        }


@dataclass
class Section:
    """Represents a hierarchical section in the article."""

    id: str
    title: Optional[str] = None
    level: int = 1  # Nesting level (1 = top-level)
    paragraphs: List[str] = field(default_factory=list)
    subsections: List["Section"] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    reference_ids: List[str] = field(default_factory=list)  # Citation callouts

    def get_full_text(self) -> str:
        """Get all text from this section and subsections."""
        text_parts = []
        if self.title:
            text_parts.append(self.title)
        text_parts.extend(self.paragraphs)
        for subsection in self.subsections:
            text_parts.append(subsection.get_full_text())
        return "\n\n".join(text_parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "level": self.level,
            "paragraphs": self.paragraphs,
            "subsections": [s.to_dict() for s in self.subsections],
            "figures": [f.to_dict() for f in self.figures],
            "tables": [t.to_dict() for t in self.tables],
            "reference_ids": self.reference_ids,
        }


@dataclass
class FullTextContent:
    """
    Comprehensive structured representation of an article's full text.

    This model captures the complete hierarchical structure including metadata,
    authors, sections, figures, tables, and references.
    """

    title: str
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    authors: List[Author] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)

    # Metadata
    journal: Optional[str] = None
    publication_year: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmc: Optional[str] = None

    def get_section_by_title(self, pattern: str, case_sensitive: bool = False) -> Optional[Section]:
        """
        Find a section by title pattern (e.g., 'methods', 'introduction').

        Args:
            pattern: String to search for in section titles
            case_sensitive: Whether to match case

        Returns:
            First matching section or None
        """
        search_pattern = pattern if case_sensitive else pattern.lower()

        def search_sections(sections: List[Section]) -> Optional[Section]:
            for section in sections:
                title = section.title or ""
                search_title = title if case_sensitive else title.lower()

                if search_pattern in search_title:
                    return section

                # Recursively search subsections
                result = search_sections(section.subsections)
                if result:
                    return result
            return None

        return search_sections(self.sections)

    def get_methods_text(self) -> str:
        """Get text from Methods section."""
        methods = self.get_section_by_title("method")
        return methods.get_full_text() if methods else ""

    def get_results_text(self) -> str:
        """Get text from Results section."""
        results = self.get_section_by_title("result")
        return results.get_full_text() if results else ""

    def get_full_text(self) -> str:
        """Get all text content concatenated."""
        text_parts = [self.title]
        if self.abstract:
            text_parts.append(self.abstract)
        for section in self.sections:
            text_parts.append(section.get_full_text())
        return "\n\n".join(text_parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "authors": [a.to_dict() for a in self.authors],
            "sections": [s.to_dict() for s in self.sections],
            "figures": [f.to_dict() for f in self.figures],
            "tables": [t.to_dict() for t in self.tables],
            "references": [r.to_dict() for r in self.references],
            "journal": self.journal,
            "publication_year": self.publication_year,
            "doi": self.doi,
            "pmid": self.pmid,
            "pmc": self.pmc,
        }


@dataclass
class FullTextResult:
    """
    Result of a full-text retrieval attempt.

    Contains the retrieved content, metadata about the source and quality,
    and optional structured content.
    """

    success: bool
    content: Optional[str] = None  # Raw text content
    structured_content: Optional[FullTextContent] = None  # Structured parsed content
    content_type: Optional[ContentType] = None
    source: Optional[SourceType] = None
    source_url: Optional[str] = None
    error_message: Optional[str] = None
    quality_score: float = 0.0  # 0-1, based on completeness and format
    retrieved_at: datetime = field(default_factory=datetime.now)

    # Quality indicators
    has_abstract: bool = False
    has_methods: bool = False
    has_references: bool = False
    has_figures: bool = False
    word_count: int = 0

    def calculate_quality_score(self) -> float:
        """
        Calculate quality score based on completeness.

        Score components:
        - Content type: XML (0.3), HTML (0.2), PDF (0.15), TEXT (0.1)
        - Has abstract: 0.2
        - Has methods: 0.15
        - Has references: 0.15
        - Has figures: 0.1
        - Word count: min(word_count / 3000, 0.1)
        """
        score = 0.0

        # Content type quality
        type_scores = {
            ContentType.XML: 0.3,
            ContentType.HTML: 0.2,
            ContentType.PDF: 0.15,
            ContentType.TEXT: 0.1,
        }
        if self.content_type:
            score += type_scores.get(self.content_type, 0.0)

        # Structural completeness
        if self.has_abstract:
            score += 0.2
        if self.has_methods:
            score += 0.15
        if self.has_references:
            score += 0.15
        if self.has_figures:
            score += 0.1

        # Content length (up to 0.1 for 3000+ words)
        score += min(self.word_count / 3000, 0.1)

        self.quality_score = min(score, 1.0)
        return self.quality_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "success": self.success,
            "content_type": self.content_type.value if self.content_type else None,
            "source": self.source.value if self.source else None,
            "source_url": self.source_url,
            "error_message": self.error_message,
            "quality_score": self.quality_score,
            "retrieved_at": self.retrieved_at.isoformat(),
            "has_abstract": self.has_abstract,
            "has_methods": self.has_methods,
            "has_references": self.has_references,
            "has_figures": self.has_figures,
            "word_count": self.word_count,
            "structured_content": self.structured_content.to_dict() if self.structured_content else None,
        }
