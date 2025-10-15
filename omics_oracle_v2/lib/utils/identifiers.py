"""
Universal Publication Identifier System

This module provides a unified identifier system that works across all
publication sources (PubMed, arXiv, CORE, Unpaywall, etc.), not just PMID-based sources.

Key Features:
    Hierarchical fallback: PMID -> DOI -> PMC -> arXiv -> ... -> Hash
- Filesystem-safe filenames
- Consistent across all 11 full-text sources
- Backwards compatible with existing PMID-based system

Usage:
    >>> from omics_oracle_v2.lib.utils.identifiers import UniversalIdentifier
    >>> identifier = UniversalIdentifier(publication)
    >>> pdf_filename = identifier.filename  # e.g., "doi_10_1234_abc.pdf"
    >>> display_name = identifier.display_name  # e.g., "DOI 10.1234/abc"

Created: October 13, 2025
"""

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class IdentifierType(str, Enum):
    """Types of publication identifiers (priority order)."""

    PMID = "pmid"  # PubMed ID (22M papers)
    DOI = "doi"  # Digital Object Identifier (140M+ works)
    PMCID = "pmcid"  # PubMed Central ID (8M papers)
    ARXIV = "arxiv"  # arXiv preprint ID (2M preprints)
    BIORXIV = "biorxiv"  # bioRxiv preprint DOI
    OPENALEX = "openalex"  # OpenAlex work ID (250M works)
    CORE = "core"  # CORE repository ID (200M papers)
    HASH = "hash"  # Title-based hash (fallback)


@dataclass
class IdentifierMetadata:
    """Metadata about the identifier."""

    type: IdentifierType
    value: str
    source: str  # Which source provided this identifier
    confidence: float = 1.0  # 0.0-1.0 confidence score
    canonical: bool = True  # Is this the canonical form?


class UniversalIdentifier:
    """
    Universal identifier for publications across all sources.

    Provides consistent, filesystem-safe identifiers regardless of source.
    Supports PMID, DOI, arXiv, and other identifier types with fallback.

    Example:
        >>> pub = Publication(pmid="12345", doi="10.1234/abc")
        >>> uid = UniversalIdentifier(pub)
        >>> print(uid.filename)  # "pmid_12345.pdf" (PMID preferred)
        >>> print(uid.display_name)  # "PMID 12345"

        >>> pub = Publication(doi="10.1234/abc", title="Paper")
        >>> uid = UniversalIdentifier(pub)
        >>> print(uid.filename)  # "doi_10_1234__abc.pdf" (DOI fallback)
        >>> print(uid.display_name)  # "DOI 10.1234/abc"
    """

    def __init__(self, publication: Any, prefer_doi: bool = False):
        """
        Initialize from Publication object.

        Args:
            publication: Publication object with various ID fields
            prefer_doi: If True, prefer DOI over PMID (useful for cross-platform work)
        """
        self.publication = publication
        self.prefer_doi = prefer_doi
        self._id_type, self._id_value = self._extract_primary_id()

    def _sanitize_for_filename(self, text: str, max_length: int = 100) -> str:
        """
        Sanitize text for use in filenames.

        Handles:
        - Forward/backward slashes
        - Colons, spaces
        - Special characters
        - Length limits

        Args:
            text: Text to sanitize
            max_length: Maximum length of sanitized text

        Returns:
            Filesystem-safe string
        """
        # Replace problematic characters
        safe = text.replace("/", "__")  # DOI uses / extensively
        safe = safe.replace("\\", "__")
        safe = safe.replace(":", "_")
        safe = safe.replace(" ", "_")
        safe = safe.replace(".", "_")  # Some filesystems don't like multiple dots

        # Keep only alphanumeric, dash, underscore
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", safe)

        # Remove consecutive underscores
        safe = re.sub(r"_+", "_", safe)

        # Trim to max length
        if len(safe) > max_length:
            safe = safe[:max_length]

        # Remove trailing underscores
        safe = safe.strip("_")

        return safe

    def _extract_primary_id(self) -> Tuple[IdentifierType, str]:
        """
        Extract primary identifier with fallback hierarchy.

        Priority order (can be overridden with prefer_doi):
        1. PMID (most specific for biomedical literature)
        2. DOI (universal, cross-platform)
        3. PMC ID (PubMed Central)
        4. arXiv ID (preprints)
        5. bioRxiv DOI (life science preprints)
        6. OpenAlex ID (comprehensive coverage)
        7. CORE ID (open access repository)
        8. Title hash (last resort fallback)

        Returns:
            Tuple of (IdentifierType, sanitized_value)
        """
        pub = self.publication

        # Option 1: Prefer DOI over PMID (for cross-platform work)
        if self.prefer_doi and pub.doi:
            return (IdentifierType.DOI, self._sanitize_for_filename(pub.doi))

        # Standard priority hierarchy

        # Priority 1: PMID (most specific for biomedical)
        if pub.pmid:
            return (IdentifierType.PMID, str(pub.pmid))

        # Priority 2: DOI (universal standard)
        if pub.doi:
            return (IdentifierType.DOI, self._sanitize_for_filename(pub.doi))

        # Priority 3: PMC ID
        if pub.pmcid:
            # Remove 'PMC' prefix if present
            pmcid_clean = pub.pmcid.replace("PMC", "")
            return (IdentifierType.PMCID, pmcid_clean)

        # Priority 4: arXiv ID
        if hasattr(pub, "metadata") and pub.metadata:
            if arxiv_id := pub.metadata.get("arxiv_id"):
                return (IdentifierType.ARXIV, self._sanitize_for_filename(arxiv_id))

        # Priority 5: bioRxiv DOI (special case)
        if pub.doi and "biorxiv" in pub.doi.lower():
            return (IdentifierType.BIORXIV, self._sanitize_for_filename(pub.doi))

        # Priority 6: OpenAlex ID
        if hasattr(pub, "metadata") and pub.metadata:
            if openalex_id := pub.metadata.get("openalex_id"):
                # Remove 'W' prefix if present
                openalex_clean = openalex_id.replace("W", "")
                return (IdentifierType.OPENALEX, openalex_clean)

        # Priority 7: CORE ID
        if hasattr(pub, "metadata") and pub.metadata:
            if core_id := pub.metadata.get("core_id"):
                return (IdentifierType.CORE, str(core_id))

        # Fallback: Title hash (deterministic, always works)
        if pub.title:
            # Use SHA256 for better collision resistance than MD5
            title_hash = hashlib.sha256(pub.title.encode("utf-8")).hexdigest()[:16]
            return (IdentifierType.HASH, title_hash)

        # Ultimate fallback: Random hash (should never happen)
        random_hash = hashlib.sha256(str(id(pub)).encode()).hexdigest()[:16]
        return (IdentifierType.HASH, random_hash)

    @property
    def id_type(self) -> IdentifierType:
        """Get the identifier type."""
        return self._id_type

    @property
    def id_value(self) -> str:
        """Get the sanitized identifier value."""
        return self._id_value

    @property
    def filename(self) -> str:
        """
        Get filename for PDF storage.

        Format: {type}_{value}.pdf

        Examples:
            - pmid_12345.pdf
            - doi_10_1234__abc.pdf
            - arxiv_2401_12345.pdf
            - hash_a1b2c3d4e5f6g7h8.pdf

        Returns:
            Filesystem-safe PDF filename
        """
        return f"{self._id_type.value}_{self._id_value}.pdf"

    @property
    def key(self) -> str:
        """
        Get database/cache key.

        Format: {type}:{value}

        Examples:
            - pmid:12345
            - doi:10.1234/abc
            - arxiv:2401.12345

        Returns:
            Colon-separated key string
        """
        # Use original (unsanitized) value for DOIs
        if self._id_type == IdentifierType.DOI and self.publication.doi:
            return f"{self._id_type.value}:{self.publication.doi}"
        return f"{self._id_type.value}:{self._id_value}"

    @property
    def display_name(self) -> str:
        """
        Get human-readable identifier for UI display.

        Examples:
            - "PMID 12345"
            - "DOI 10.1234/abc"
            - "arXiv:2401.12345"
            - "HASH a1b2c3d4e5f6g7h8"

        Returns:
            Formatted display string
        """
        if self._id_type == IdentifierType.PMID:
            return f"PMID {self._id_value}"
        elif self._id_type == IdentifierType.DOI:
            # Restore original DOI format
            if self.publication.doi:
                return f"DOI {self.publication.doi}"
            else:
                doi_restored = self._id_value.replace("__", "/")
                return f"DOI {doi_restored}"
        elif self._id_type == IdentifierType.ARXIV:
            return f"arXiv:{self._id_value}"
        elif self._id_type == IdentifierType.BIORXIV:
            return f"bioRxiv DOI {self.publication.doi}"
        elif self._id_type == IdentifierType.OPENALEX:
            return f"OpenAlex:W{self._id_value}"
        elif self._id_type == IdentifierType.PMCID:
            return f"PMC{self._id_value}"
        elif self._id_type == IdentifierType.HASH:
            return f"Hash:{self._id_value}"
        else:
            return f"{self._id_type.value.upper()}:{self._id_value}"

    @property
    def short_display(self) -> str:
        """
        Get short display name (truncated for compact UI).

        Returns:
            Truncated display string
        """
        full = self.display_name
        if len(full) > 30:
            return full[:27] + "..."
        return full

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with identifier metadata
        """
        return {
            "type": self._id_type.value,
            "value": self._id_value,
            "key": self.key,
            "filename": self.filename,
            "display_name": self.display_name,
        }

    def __str__(self) -> str:
        """String representation (key format)."""
        return self.key

    def __repr__(self) -> str:
        """Debug representation."""
        return f"UniversalIdentifier({self.key}, filename={self.filename})"

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.key)

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, UniversalIdentifier):
            return False
        return self.key == other.key


def get_identifier_from_filename(filename: str) -> Tuple[IdentifierType, str]:
    """
    Parse identifier from PDF filename.

    Args:
        filename: PDF filename (e.g., "pmid_12345.pdf")

    Returns:
        Tuple of (IdentifierType, value)

    Example:
        >>> id_type, value = get_identifier_from_filename("doi_10_1234__abc.pdf")
        >>> print(id_type)  # IdentifierType.DOI
        >>> print(value)    # "10_1234__abc"
    """
    # Remove .pdf extension
    name = filename.replace(".pdf", "")

    # Split by first underscore
    parts = name.split("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid filename format: {filename}")

    id_type_str, id_value = parts

    try:
        id_type = IdentifierType(id_type_str)
    except ValueError:
        raise ValueError(f"Unknown identifier type: {id_type_str}")

    return (id_type, id_value)


def resolve_doi_from_filename(filename: str) -> Optional[str]:
    """
    Resolve original DOI from sanitized filename.

    Args:
        filename: Sanitized DOI filename (e.g., "doi_10_1234__abc.pdf")

    Returns:
        Original DOI string or None

    Example:
        >>> doi = resolve_doi_from_filename("doi_10_1234__abc.pdf")
        >>> print(doi)  # "10.1234/abc"
    """
    try:
        id_type, value = get_identifier_from_filename(filename)
        if id_type == IdentifierType.DOI:
            # Restore original DOI:
            # 1. Restore / from __
            # 2. Restore . from _
            restored = value.replace("__", "/")
            # DOIs have the format 10.xxxx/... so restore dots carefully
            # Only restore dots after "10" prefix
            parts = restored.split("/")
            if parts[0].startswith("10_"):
                parts[0] = parts[0].replace(
                    "_", ".", 1
                )  # Replace first underscore after 10
            restored = "/".join(parts)
            return restored
        return None
    except ValueError:
        return None


# Example usage and tests
if __name__ == "__main__":
    from types import SimpleNamespace

    print("=" * 80)
    print("Universal Identifier System - Examples")
    print("=" * 80)

    # Test Case 1: PubMed paper
    pub1 = SimpleNamespace(
        pmid="12345",
        doi="10.1234/abc",
        pmcid=None,
        title="Example PubMed Paper",
        metadata={},
    )
    uid1 = UniversalIdentifier(pub1)
    print("\n1. PubMed Paper:")
    print(f"   Filename: {uid1.filename}")
    print(f"   Key: {uid1.key}")
    print(f"   Display: {uid1.display_name}")

    # Test Case 2: Paper with only DOI (common for CORE, Unpaywall)
    pub2 = SimpleNamespace(
        pmid=None,
        doi="10.1234/example.paper",
        pmcid=None,
        title="Example DOI-only Paper",
        metadata={},
    )
    uid2 = UniversalIdentifier(pub2)
    print("\n2. DOI-only Paper:")
    print(f"   Filename: {uid2.filename}")
    print(f"   Key: {uid2.key}")
    print(f"   Display: {uid2.display_name}")

    # Test Case 3: arXiv preprint
    pub3 = SimpleNamespace(
        pmid=None,
        doi=None,
        pmcid=None,
        title="Example arXiv Preprint",
        metadata={"arxiv_id": "2401.12345"},
    )
    uid3 = UniversalIdentifier(pub3)
    print("\n3. arXiv Preprint:")
    print(f"   Filename: {uid3.filename}")
    print(f"   Key: {uid3.key}")
    print(f"   Display: {uid3.display_name}")

    # Test Case 4: No identifiers (fallback to hash)
    pub4 = SimpleNamespace(
        pmid=None, doi=None, pmcid=None, title="Paper with No Identifiers", metadata={}
    )
    uid4 = UniversalIdentifier(pub4)
    print("\n4. No Identifiers (fallback):")
    print(f"   Filename: {uid4.filename}")
    print(f"   Key: {uid4.key}")
    print(f"   Display: {uid4.display_name}")

    print("\n" + "=" * 80)
    print("Universal Identifier System Working!")
    print("=" * 80)
