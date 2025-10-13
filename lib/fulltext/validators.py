"""
Validation module for full-text downloads (XML and PDF).

This module provides validation functionality to ensure downloaded content
is correct, complete, and properly formatted before saving to disk.

Features:
- XML structure validation (JATS/PMC XML)
- PDF integrity validation
- Content quality scoring
- Metadata extraction and verification
"""

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class XMLValidator:
    """
    Validates PMC XML files for correctness and completeness.

    Checks:
    - Well-formed XML
    - Required elements present (article-title, journal, etc.)
    - Minimum content length
    - JATS/PMC XML structure
    """

    def __init__(
        self,
        min_xml_size: int = 1000,  # 1KB minimum
        required_elements: Optional[list] = None,
    ):
        """
        Initialize XML validator.

        Args:
            min_xml_size: Minimum valid XML size in bytes
            required_elements: List of required XML elements
        """
        self.min_xml_size = min_xml_size

        # Default required elements for PMC XML
        if required_elements is None:
            self.required_elements = [
                "article-title",
                "journal-title",
                "abstract",
            ]
        else:
            self.required_elements = required_elements

    def validate(self, xml_content: str, identifier: str) -> Tuple[bool, Dict, Optional[str]]:
        """
        Validate XML content.

        Args:
            xml_content: XML string to validate
            identifier: Article identifier (PMC ID, etc.)

        Returns:
            Tuple of (is_valid, metadata, error_message)
        """
        metadata = {"identifier": identifier, "size": len(xml_content)}

        # Check size
        if len(xml_content) < self.min_xml_size:
            error = f"XML too small: {len(xml_content)} bytes (min: {self.min_xml_size})"
            logger.warning(f"{identifier}: {error}")
            return False, metadata, error

        # Check XML declaration
        if not xml_content.strip().startswith("<?xml"):
            error = "Missing XML declaration"
            logger.warning(f"{identifier}: {error}")
            return False, metadata, error

        # Try to parse XML
        try:
            root = ET.fromstring(xml_content)
            metadata["root_tag"] = root.tag
        except ET.ParseError as e:
            error = f"XML parse error: {e}"
            logger.warning(f"{identifier}: {error}")
            return False, metadata, error

        # Check for required elements
        missing_elements = []
        found_elements = {}

        for element in self.required_elements:
            # Search for element (case-insensitive, handles namespaces)
            found = root.find(f".//{element}") or root.find(f".//{{*}}{element}")

            if found is not None:
                text = found.text or ""
                found_elements[element] = text[:100]  # First 100 chars
            else:
                missing_elements.append(element)

        metadata["found_elements"] = found_elements
        metadata["missing_elements"] = missing_elements

        # Calculate quality score
        quality = self._calculate_quality(xml_content, found_elements, missing_elements)
        metadata["quality_score"] = quality

        # Validation passes if we have at least article-title
        if "article-title" not in found_elements:
            error = "Missing required element: article-title"
            logger.warning(f"{identifier}: {error}")
            return False, metadata, error

        logger.info(
            f"{identifier}: XML validation passed "
            f"(quality: {quality:.2f}, found: {len(found_elements)}/{len(self.required_elements)})"
        )
        return True, metadata, None

    def _calculate_quality(self, xml_content: str, found_elements: Dict, missing_elements: list) -> float:
        """
        Calculate XML quality score (0-1).

        Args:
            xml_content: XML content string
            found_elements: Dict of found required elements
            missing_elements: List of missing required elements

        Returns:
            Quality score between 0 and 1
        """
        score = 0.0

        # Size score (up to 0.2)
        if len(xml_content) > 50000:  # > 50KB
            score += 0.2
        elif len(xml_content) > 10000:  # > 10KB
            score += 0.1

        # Required elements score (up to 0.6)
        elements_score = len(found_elements) / len(self.required_elements)
        score += elements_score * 0.6

        # Content richness score (up to 0.2)
        # Check for figures, tables, references
        richness = 0
        if "<fig " in xml_content or "<fig>" in xml_content:
            richness += 1
        if "<table-wrap" in xml_content:
            richness += 1
        if "<ref " in xml_content or "<ref>" in xml_content:
            richness += 1

        score += (richness / 3) * 0.2

        return min(score, 1.0)


class PDFValidator:
    """
    Validates PDF files for integrity and completeness.

    Checks:
    - PDF signature (%PDF)
    - EOF marker
    - File size constraints
    - Basic PDF structure
    """

    def __init__(
        self,
        min_pdf_size: int = 10240,  # 10KB minimum
        max_pdf_size: int = 104857600,  # 100MB maximum
    ):
        """
        Initialize PDF validator.

        Args:
            min_pdf_size: Minimum valid PDF size in bytes
            max_pdf_size: Maximum PDF size to accept
        """
        self.min_pdf_size = min_pdf_size
        self.max_pdf_size = max_pdf_size

    def validate(self, pdf_content: bytes, identifier: str) -> Tuple[bool, Dict, Optional[str]]:
        """
        Validate PDF content.

        Args:
            pdf_content: PDF file bytes
            identifier: Article identifier

        Returns:
            Tuple of (is_valid, metadata, error_message)
        """
        metadata = {
            "identifier": identifier,
            "size": len(pdf_content),
            "sha256": hashlib.sha256(pdf_content).hexdigest(),
        }

        # Check size
        if len(pdf_content) < self.min_pdf_size:
            error = f"PDF too small: {len(pdf_content)} bytes"
            logger.warning(f"{identifier}: {error}")
            return False, metadata, error

        if len(pdf_content) > self.max_pdf_size:
            error = f"PDF too large: {len(pdf_content)} bytes"
            logger.warning(f"{identifier}: {error}")
            return False, metadata, error

        # Check PDF signature
        if not pdf_content.startswith(b"%PDF"):
            error = "Not a valid PDF file (missing %PDF header)"
            logger.warning(f"{identifier}: {error}")
            return False, metadata, error

        # Extract PDF version
        version_match = re.match(rb"%PDF-(\d+\.\d+)", pdf_content[:20])
        if version_match:
            metadata["pdf_version"] = version_match.group(1).decode("ascii")

        # Check for EOF marker
        if b"%%EOF" not in pdf_content[-1024:]:
            error = "PDF appears truncated (missing %%EOF marker)"
            logger.warning(f"{identifier}: {error}")
            return False, metadata, error

        # Check for encryption (optional warning)
        if b"/Encrypt" in pdf_content[:10000]:
            logger.warning(f"{identifier}: PDF appears to be encrypted")
            metadata["encrypted"] = True
        else:
            metadata["encrypted"] = False

        logger.info(
            f"{identifier}: PDF validation passed "
            f"({len(pdf_content)/1024:.0f}KB, version: {metadata.get('pdf_version', 'unknown')})"
        )
        return True, metadata, None


class ContentValidator:
    """
    High-level validator for all content types.

    Combines XML and PDF validators with unified interface.
    """

    def __init__(
        self,
        min_xml_size: int = 1000,
        min_pdf_size: int = 10240,
        max_pdf_size: int = 104857600,
    ):
        """
        Initialize content validator with configurable settings.

        Args:
            min_xml_size: Minimum XML size in bytes
            min_pdf_size: Minimum PDF size in bytes
            max_pdf_size: Maximum PDF size in bytes
        """
        self.xml_validator = XMLValidator(min_xml_size=min_xml_size)
        self.pdf_validator = PDFValidator(min_pdf_size=min_pdf_size, max_pdf_size=max_pdf_size)

    def validate_xml(self, xml_content: str, identifier: str) -> Tuple[bool, Dict, Optional[str]]:
        """
        Validate XML content.

        Args:
            xml_content: XML string
            identifier: Article identifier

        Returns:
            Tuple of (is_valid, metadata, error_message)
        """
        return self.xml_validator.validate(xml_content, identifier)

    def validate_pdf(self, pdf_content: bytes, identifier: str) -> Tuple[bool, Dict, Optional[str]]:
        """
        Validate PDF content.

        Args:
            pdf_content: PDF bytes
            identifier: Article identifier

        Returns:
            Tuple of (is_valid, metadata, error_message)
        """
        return self.pdf_validator.validate(pdf_content, identifier)

    def validate_and_report(self, content: bytes, content_type: str, identifier: str) -> Tuple[bool, Dict]:
        """
        Validate content and return detailed report.

        Args:
            content: Content bytes
            content_type: 'xml' or 'pdf'
            identifier: Article identifier

        Returns:
            Tuple of (is_valid, report_dict)
        """
        report = {
            "identifier": identifier,
            "content_type": content_type,
            "size": len(content),
        }

        if content_type.lower() == "xml":
            # Decode bytes to string for XML
            try:
                xml_content = content.decode("utf-8")
            except UnicodeDecodeError:
                report["valid"] = False
                report["error"] = "Failed to decode XML as UTF-8"
                return False, report

            is_valid, metadata, error = self.validate_xml(xml_content, identifier)

        elif content_type.lower() == "pdf":
            is_valid, metadata, error = self.validate_pdf(content, identifier)

        else:
            report["valid"] = False
            report["error"] = f"Unknown content type: {content_type}"
            return False, report

        report["valid"] = is_valid
        report.update(metadata)
        if error:
            report["error"] = error

        return is_valid, report


# Convenience functions


def validate_xml_file(xml_path: Path, min_xml_size: int = 1000) -> Tuple[bool, Dict]:
    """
    Validate XML file.

    Args:
        xml_path: Path to XML file
        min_xml_size: Minimum XML size in bytes

    Returns:
        Tuple of (is_valid, report)
    """
    validator = XMLValidator(min_xml_size=min_xml_size)
    identifier = xml_path.stem

    with open(xml_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    is_valid, metadata, error = validator.validate(xml_content, identifier)

    report = {"file": str(xml_path), **metadata}
    if error:
        report["error"] = error

    return is_valid, report


def validate_pdf_file(pdf_path: Path) -> Tuple[bool, Dict]:
    """
    Validate PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Tuple of (is_valid, report)
    """
    validator = PDFValidator()
    identifier = pdf_path.stem

    with open(pdf_path, "rb") as f:
        pdf_content = f.read()

    is_valid, metadata, error = validator.validate(pdf_content, identifier)

    report = {"file": str(pdf_path), **metadata}
    if error:
        report["error"] = error

    return is_valid, report
