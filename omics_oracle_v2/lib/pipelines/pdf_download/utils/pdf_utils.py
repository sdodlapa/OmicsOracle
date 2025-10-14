"""
Shared PDF utility functions for validation, detection, and manipulation.

This module provides centralized PDF-related utilities used across the codebase,
eliminating duplicate validation logic and ensuring consistency.

Created: October 14, 2025 (Phase 2.1 - Pipeline 2 Cleanup)
"""

import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

# PDF Constants
PDF_MAGIC_BYTES = b"%PDF-"
MIN_PDF_SIZE = 1024  # 1 KB - minimum realistic PDF size
MAX_PDF_SIZE = 100 * 1024 * 1024  # 100 MB - maximum reasonable PDF size

# Common PDF file extensions
PDF_EXTENSIONS = {".pdf", ".PDF"}


def validate_pdf_content(content: bytes) -> bool:
    """
    Validate PDF content using magic bytes and size checks.

    This is the authoritative PDF validation function used throughout the codebase.

    Checks:
    1. Minimum size (1 KB)
    2. Maximum size (100 MB)
    3. Magic bytes (starts with b"%PDF-")

    Args:
        content: PDF file content as bytes

    Returns:
        True if valid PDF, False otherwise

    Example:
        >>> with open('document.pdf', 'rb') as f:
        ...     content = f.read()
        >>> if validate_pdf_content(content):
        ...     print("Valid PDF!")
    """
    if not content:
        logger.debug("PDF validation failed: empty content")
        return False

    # Check size bounds
    if len(content) < MIN_PDF_SIZE:
        logger.debug(f"PDF validation failed: too small ({len(content)} bytes < {MIN_PDF_SIZE} bytes)")
        return False

    if len(content) > MAX_PDF_SIZE:
        logger.warning(f"PDF validation failed: too large ({len(content)} bytes > {MAX_PDF_SIZE} bytes)")
        return False

    # Check magic bytes
    if not content.startswith(PDF_MAGIC_BYTES):
        logger.debug(
            f"PDF validation failed: incorrect magic bytes (expected {PDF_MAGIC_BYTES}, got {content[:5]})"
        )
        return False

    return True


def validate_pdf_file(file_path: Union[str, Path]) -> bool:
    """
    Validate PDF file by reading and checking content.

    Args:
        file_path: Path to PDF file

    Returns:
        True if valid PDF, False otherwise

    Example:
        >>> if validate_pdf_file('document.pdf'):
        ...     print("Valid PDF file!")
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            logger.debug(f"PDF validation failed: file not found ({file_path})")
            return False

        if not file_path.is_file():
            logger.debug(f"PDF validation failed: not a file ({file_path})")
            return False

        # Read and validate content
        content = file_path.read_bytes()
        return validate_pdf_content(content)

    except Exception as e:
        logger.warning(f"PDF validation error for {file_path}: {e}")
        return False


def is_pdf_url(url: str) -> bool:
    """
    Check if URL likely points to a PDF file based on extension.

    Note: This is a heuristic check - the actual content should still be validated.

    Args:
        url: URL to check

    Returns:
        True if URL ends with .pdf (case-insensitive), False otherwise

    Example:
        >>> is_pdf_url('https://example.com/paper.pdf')
        True
        >>> is_pdf_url('https://example.com/paper.html')
        False
    """
    if not url:
        return False

    url_lower = url.lower()

    # Check for .pdf extension
    if url_lower.endswith(".pdf"):
        return True

    # Check for .pdf before query parameters
    if ".pdf?" in url_lower or ".pdf#" in url_lower:
        return True

    return False


def is_pdf_filename(filename: str) -> bool:
    """
    Check if filename has PDF extension.

    Args:
        filename: Filename to check

    Returns:
        True if filename ends with .pdf (case-insensitive), False otherwise

    Example:
        >>> is_pdf_filename('document.pdf')
        True
        >>> is_pdf_filename('document.PDF')
        True
        >>> is_pdf_filename('document.txt')
        False
    """
    if not filename:
        return False

    return Path(filename).suffix.lower() == ".pdf"


def get_pdf_info(content: bytes) -> dict:
    """
    Extract basic information from PDF content.

    Args:
        content: PDF content as bytes

    Returns:
        Dictionary with:
        - valid: bool - whether PDF is valid
        - size: int - size in bytes
        - size_mb: float - size in MB (rounded to 2 decimals)
        - has_magic_bytes: bool - whether starts with %PDF-

    Example:
        >>> with open('document.pdf', 'rb') as f:
        ...     info = get_pdf_info(f.read())
        >>> print(f"Size: {info['size_mb']} MB")
    """
    info = {
        "valid": False,
        "size": len(content) if content else 0,
        "size_mb": round(len(content) / (1024 * 1024), 2) if content else 0,
        "has_magic_bytes": False,
    }

    if content:
        info["has_magic_bytes"] = content.startswith(PDF_MAGIC_BYTES)
        info["valid"] = validate_pdf_content(content)

    return info


def sanitize_pdf_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize filename for PDF saving.

    Removes/replaces problematic characters and ensures .pdf extension.

    Args:
        filename: Original filename
        max_length: Maximum filename length (default: 200)

    Returns:
        Sanitized filename safe for filesystem

    Example:
        >>> sanitize_pdf_filename('My Paper: A Study (2025).pdf')
        'My_Paper_A_Study_2025.pdf'
    """
    if not filename:
        return "document.pdf"

    # Remove path components (keep only filename)
    filename = Path(filename).name

    # Replace problematic characters with underscore
    problematic_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "\n", "\r", "\t"]
    for char in problematic_chars:
        filename = filename.replace(char, "_")

    # Remove multiple underscores
    while "__" in filename:
        filename = filename.replace("__", "_")

    # Trim length (preserve extension)
    if len(filename) > max_length:
        name_part = filename[:-4] if filename.endswith(".pdf") else filename
        name_part = name_part[: max_length - 4]
        filename = f"{name_part}.pdf"

    # Ensure .pdf extension
    if not filename.lower().endswith(".pdf"):
        filename = f"{filename}.pdf"

    return filename


# Backward compatibility aliases
def is_valid_pdf(content: bytes) -> bool:
    """
    Alias for validate_pdf_content() for backward compatibility.

    Deprecated: Use validate_pdf_content() instead.
    """
    return validate_pdf_content(content)
