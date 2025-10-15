"""
Section Detector

Detects standard paper sections using pattern matching and heuristics.
Handles common section headers and variations.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Represents a detected section."""

    name: str  # Canonical name (e.g., "methods")
    title: str  # Original header text (e.g., "Materials and Methods")
    content: str  # Section text
    start_pos: int  # Character position in full text
    end_pos: int  # Character position in full text
    confidence: float = 1.0  # Detection confidence (0-1)


@dataclass
class SectionDetectionResult:
    """Result of section detection."""

    sections: Dict[str, Section] = field(default_factory=dict)
    section_order: List[str] = field(default_factory=list)
    abstract: Optional[str] = None
    title: Optional[str] = None
    full_text: str = ""
    method: str = "pattern_matching"


class SectionDetector:
    """Detects paper sections using pattern matching."""

    # Section patterns (canonical_name -> list of regex patterns)
    SECTION_PATTERNS = {
        "abstract": [
            r"^abstract\s*$",
            r"^summary\s*$",
        ],
        "introduction": [
            r"^introduction\s*$",
            r"^background\s*$",
            r"^1\.?\s+introduction",
        ],
        "methods": [
            r"^methods?\s*$",
            r"^materials?\s+and\s+methods?\s*$",
            r"^experimental\s+procedures?\s*$",
            r"^methodology\s*$",
            r"^2\.?\s+methods?",
        ],
        "results": [
            r"^results?\s*$",
            r"^findings?\s*$",
            r"^3\.?\s+results?",
        ],
        "discussion": [
            r"^discussion\s*$",
            r"^results?\s+and\s+discussion\s*$",
            r"^4\.?\s+discussion",
        ],
        "conclusion": [
            r"^conclusions?\s*$",
            r"^concluding\s+remarks?\s*$",
            r"^summary\s+and\s+conclusions?\s*$",
        ],
        "references": [
            r"^references?\s*$",
            r"^bibliography\s*$",
            r"^literature\s+cited\s*$",
        ],
    }

    def __init__(self):
        """Initialize section detector."""
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficiency."""
        compiled = {}
        for section, patterns in self.SECTION_PATTERNS.items():
            compiled[section] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

    def detect_sections(self, text: str, title: Optional[str] = None) -> SectionDetectionResult:
        """
        Detect sections in paper text.

        Args:
            text: Full paper text
            title: Optional paper title

        Returns:
            SectionDetectionResult with detected sections
        """
        try:
            # Split text into lines
            lines = text.split("\n")

            # Find section headers
            section_headers = self._find_section_headers(lines)

            if not section_headers:
                logger.warning("No section headers detected - using full text")
                return SectionDetectionResult(
                    full_text=text,
                    title=title,
                    sections={"full_text": Section("full_text", "Full Text", text, 0, len(text))},
                    section_order=["full_text"],
                )

            # Extract section content
            sections = self._extract_section_content(text, lines, section_headers)

            # Try to extract abstract
            abstract = self._extract_abstract(sections, text)

            return SectionDetectionResult(
                sections=sections,
                section_order=list(sections.keys()),
                abstract=abstract,
                title=title,
                full_text=text,
                method="pattern_matching",
            )

        except Exception as e:
            logger.error(f"Section detection failed: {e}")
            # Fallback: return full text as single section
            return SectionDetectionResult(
                full_text=text,
                title=title,
                sections={"full_text": Section("full_text", "Full Text", text, 0, len(text))},
                section_order=["full_text"],
            )

    def _find_section_headers(self, lines: List[str]) -> List[Tuple[int, str, str]]:
        """
        Find section headers in text.

        Returns:
            List of (line_number, canonical_name, header_text) tuples
        """
        headers = []

        for i, line in enumerate(lines):
            line_clean = line.strip()

            # Skip empty lines and very long lines (probably not headers)
            if not line_clean or len(line_clean) > 100:
                continue

            # Check against all patterns
            for section_name, patterns in self.compiled_patterns.items():
                for pattern in patterns:
                    if pattern.match(line_clean):
                        headers.append((i, section_name, line_clean))
                        break

        return headers

    def _extract_section_content(
        self, full_text: str, lines: List[str], headers: List[Tuple[int, str, str]]
    ) -> Dict[str, Section]:
        """Extract content between section headers."""
        sections = {}

        for i, (line_num, section_name, header_text) in enumerate(headers):
            # Determine section boundaries
            start_line = line_num + 1  # Start after header
            end_line = headers[i + 1][0] if i + 1 < len(headers) else len(lines)

            # Extract content
            content_lines = lines[start_line:end_line]
            content = "\n".join(content_lines).strip()

            # Calculate character positions
            start_pos = len("\n".join(lines[:start_line]))
            end_pos = start_pos + len(content)

            # Create section
            section = Section(
                name=section_name,
                title=header_text,
                content=content,
                start_pos=start_pos,
                end_pos=end_pos,
                confidence=1.0,
            )

            # Store (handle duplicates by appending to existing)
            if section_name in sections:
                # Multiple sections with same name - merge content
                sections[section_name].content += f"\n\n{content}"
                sections[section_name].end_pos = end_pos
            else:
                sections[section_name] = section

        return sections

    def _extract_abstract(self, sections: Dict[str, Section], full_text: str) -> Optional[str]:
        """Extract abstract from sections or try to find it in text."""
        # Check if abstract section was detected
        if "abstract" in sections:
            return sections["abstract"].content

        # Try to find abstract at start of paper (before introduction)
        if "introduction" in sections:
            intro_start = sections["introduction"].start_pos
            potential_abstract = full_text[:intro_start].strip()

            # Abstract should be substantial but not too long
            if 100 < len(potential_abstract) < 3000:
                return potential_abstract

        return None
