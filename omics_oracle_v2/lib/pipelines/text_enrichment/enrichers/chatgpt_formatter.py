"""
ChatGPT Formatter

Formats enriched content for optimal ChatGPT consumption.
Creates structured JSON with metadata, sections, and context.
"""

import json
import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FormattedContent:
    """ChatGPT-optimized content format."""

    # Paper metadata
    title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None

    # Content structure
    abstract: Optional[str] = None
    sections: Dict[str, str] = None
    section_order: List[str] = None

    # Extracted elements
    tables: List[Dict[str, Any]] = None
    references: List[Dict[str, Any]] = None

    # Statistics
    stats: Dict[str, Any] = None

    # Context
    context: Optional[str] = None  # Optional context about paper usage

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class ChatGPTFormatter:
    """Formats enriched content for ChatGPT."""

    def __init__(self):
        """Initialize formatter."""
        pass

    def format(
        self,
        text: str,
        title: Optional[str] = None,
        sections: Optional[Dict[str, Any]] = None,
        tables: Optional[List[Any]] = None,
        references: Optional[List[Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
    ) -> FormattedContent:
        """
        Format content for ChatGPT.

        Args:
            text: Full paper text
            title: Paper title
            sections: Detected sections (dict of section_name -> Section object)
            tables: Extracted tables
            references: Parsed references
            metadata: Additional metadata (doi, pmid, authors, etc.)
            context: Optional context about how this paper is being used

        Returns:
            FormattedContent optimized for ChatGPT
        """
        formatted = FormattedContent()

        # Add metadata
        if metadata:
            formatted.title = metadata.get("title") or title
            formatted.authors = metadata.get("authors")
            formatted.journal = metadata.get("journal")
            formatted.year = metadata.get("year")
            formatted.doi = metadata.get("doi")
            formatted.pmid = metadata.get("pmid")
        else:
            formatted.title = title

        # Add sections
        if sections:
            formatted.sections = {}
            formatted.section_order = []

            for section_name, section_obj in sections.items():
                # Extract content from Section object
                if hasattr(section_obj, "content"):
                    content = section_obj.content
                else:
                    content = str(section_obj)

                formatted.sections[section_name] = content
                formatted.section_order.append(section_name)

                # Special handling for abstract
                if section_name == "abstract":
                    formatted.abstract = content

        # Add tables
        if tables:
            formatted.tables = []
            for table in tables:
                if hasattr(table, "to_dict"):
                    formatted.tables.append(table.to_dict())
                elif isinstance(table, dict):
                    formatted.tables.append(table)
                else:
                    formatted.tables.append({"raw": str(table)})

        # Add references
        if references:
            formatted.references = []
            for ref in references:
                if hasattr(ref, "to_dict"):
                    formatted.references.append(ref.to_dict())
                elif isinstance(ref, dict):
                    formatted.references.append(ref)
                else:
                    formatted.references.append({"raw": str(ref)})

        # Add statistics
        formatted.stats = self._calculate_stats(text, sections, tables, references)

        # Add context
        if context:
            formatted.context = context

        return formatted

    def _calculate_stats(
        self,
        text: str,
        sections: Optional[Dict] = None,
        tables: Optional[List] = None,
        references: Optional[List] = None,
    ) -> Dict[str, Any]:
        """Calculate content statistics."""
        stats = {
            "total_chars": len(text),
            "total_words": len(text.split()),
        }

        if sections:
            stats["section_count"] = len(sections)
            stats["sections"] = list(sections.keys())

        if tables:
            stats["table_count"] = len(tables)

        if references:
            stats["reference_count"] = len(references)

        return stats

    def format_for_prompt(self, formatted: FormattedContent, max_length: int = 100000) -> str:
        """
        Create ChatGPT prompt-ready text.

        Args:
            formatted: FormattedContent object
            max_length: Maximum character length for prompt

        Returns:
            Formatted text ready for ChatGPT prompt
        """
        parts = []

        # Add title
        if formatted.title:
            parts.append(f"# {formatted.title}\n")

        # Add metadata
        if formatted.authors or formatted.journal or formatted.year:
            meta_parts = []
            if formatted.authors:
                meta_parts.append(f"Authors: {formatted.authors}")
            if formatted.journal:
                meta_parts.append(f"Journal: {formatted.journal}")
            if formatted.year:
                meta_parts.append(f"Year: {formatted.year}")
            parts.append(" | ".join(meta_parts) + "\n")

        # Add DOI/PMID
        if formatted.doi or formatted.pmid:
            id_parts = []
            if formatted.doi:
                id_parts.append(f"DOI: {formatted.doi}")
            if formatted.pmid:
                id_parts.append(f"PMID: {formatted.pmid}")
            parts.append(" | ".join(id_parts) + "\n")

        parts.append("\n")

        # Add abstract
        if formatted.abstract:
            parts.append("## Abstract\n\n")
            parts.append(formatted.abstract + "\n\n")

        # Add sections in order
        if formatted.sections and formatted.section_order:
            for section_name in formatted.section_order:
                if section_name == "abstract":
                    continue  # Already added

                content = formatted.sections[section_name]
                parts.append(f"## {section_name.replace('_', ' ').title()}\n\n")
                parts.append(content + "\n\n")

        # Add context if provided
        if formatted.context:
            parts.append("---\n\n")
            parts.append(f"**Context**: {formatted.context}\n")

        # Join and truncate if needed
        full_text = "".join(parts)

        if len(full_text) > max_length:
            logger.warning(f"Truncating formatted content from {len(full_text)} to {max_length} chars")
            full_text = full_text[:max_length] + "\n\n[... content truncated ...]"

        return full_text
