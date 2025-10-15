"""
Reference Parser

Parses bibliography/references section to extract cited papers.
Basic implementation using pattern matching for common citation formats.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Reference:
    """Represents a parsed reference."""

    number: Optional[int] = None  # Reference number (if numbered)
    authors: Optional[str] = None  # Author list
    title: Optional[str] = None  # Paper title
    journal: Optional[str] = None  # Journal name
    year: Optional[int] = None  # Publication year
    doi: Optional[str] = None  # DOI
    pmid: Optional[str] = None  # PubMed ID
    raw_text: str = ""  # Original citation text


@dataclass
class ReferenceParsingResult:
    """Result of reference parsing."""

    references: List[Reference] = field(default_factory=list)
    reference_count: int = 0
    dois_found: List[str] = field(default_factory=list)
    pmids_found: List[str] = field(default_factory=list)
    method: str = "pattern_matching"


class ReferenceParser:
    """Parses references from bibliography section."""

    # Pattern for DOI
    DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+", re.IGNORECASE)

    # Pattern for PMID
    PMID_PATTERN = re.compile(r"PMID:?\s*(\d{7,8})", re.IGNORECASE)

    # Pattern for year in parentheses or brackets
    YEAR_PATTERN = re.compile(r"[\(\[](\d{4})[\)\]]")

    # Pattern for numbered reference (e.g., "1. Authors...")
    NUMBERED_REF_PATTERN = re.compile(r"^(\d+)\.?\s+(.+)")

    def __init__(self):
        """Initialize reference parser."""
        pass

    def parse_references(self, references_text: str) -> ReferenceParsingResult:
        """
        Parse references from bibliography text.

        Args:
            references_text: Text of references section

        Returns:
            ReferenceParsingResult with parsed references
        """
        try:
            # Split into individual references
            # Heuristic: Split on numbered lines or double newlines
            reference_entries = self._split_references(references_text)

            references = []
            all_dois = []
            all_pmids = []

            for entry_text in reference_entries:
                ref = self._parse_single_reference(entry_text)
                if ref:
                    references.append(ref)

                    if ref.doi:
                        all_dois.append(ref.doi)
                    if ref.pmid:
                        all_pmids.append(ref.pmid)

            return ReferenceParsingResult(
                references=references,
                reference_count=len(references),
                dois_found=all_dois,
                pmids_found=all_pmids,
                method="pattern_matching",
            )

        except Exception as e:
            logger.error(f"Reference parsing failed: {e}")
            return ReferenceParsingResult()

    def _split_references(self, text: str) -> List[str]:
        """Split references text into individual entries."""
        lines = text.split("\n")
        entries = []
        current_entry = []

        for line in lines:
            line_clean = line.strip()

            if not line_clean:
                continue

            # Check if this is start of new numbered reference
            if self.NUMBERED_REF_PATTERN.match(line_clean):
                # Save previous entry
                if current_entry:
                    entries.append("\n".join(current_entry))

                # Start new entry
                current_entry = [line_clean]
            else:
                # Continuation of current entry
                if current_entry:
                    current_entry.append(line_clean)

        # Add last entry
        if current_entry:
            entries.append("\n".join(current_entry))

        return entries

    def _parse_single_reference(self, entry_text: str) -> Optional[Reference]:
        """Parse a single reference entry."""
        if not entry_text.strip():
            return None

        ref = Reference(raw_text=entry_text)

        # Extract reference number
        num_match = self.NUMBERED_REF_PATTERN.match(entry_text)
        if num_match:
            ref.number = int(num_match.group(1))

        # Extract DOI
        doi_match = self.DOI_PATTERN.search(entry_text)
        if doi_match:
            ref.doi = doi_match.group(0)

        # Extract PMID
        pmid_match = self.PMID_PATTERN.search(entry_text)
        if pmid_match:
            ref.pmid = pmid_match.group(1)

        # Extract year
        year_match = self.YEAR_PATTERN.search(entry_text)
        if year_match:
            ref.year = int(year_match.group(1))

        # Extract authors (heuristic: text before year)
        if year_match:
            authors_text = entry_text[: year_match.start()].strip()
            # Remove reference number
            if num_match:
                authors_text = authors_text[len(num_match.group(0)) :].strip()
            ref.authors = authors_text[:200]  # Limit length

        return ref
