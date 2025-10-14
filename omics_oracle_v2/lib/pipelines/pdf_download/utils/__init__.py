"""
Shared utilities for PDF download pipeline.

This package provides PDF validation and manipulation utilities.
"""

from .pdf_utils import (  # Constants; Validation functions; Utility functions; Backward compatibility
    MAX_PDF_SIZE,
    MIN_PDF_SIZE,
    PDF_EXTENSIONS,
    PDF_MAGIC_BYTES,
    get_pdf_info,
    is_pdf_filename,
    is_pdf_url,
    is_valid_pdf,
    sanitize_pdf_filename,
    validate_pdf_content,
    validate_pdf_file,
)

__all__ = [
    # PDF Constants
    "PDF_MAGIC_BYTES",
    "MIN_PDF_SIZE",
    "MAX_PDF_SIZE",
    "PDF_EXTENSIONS",
    # PDF Validation functions
    "validate_pdf_content",
    "validate_pdf_file",
    "is_pdf_url",
    "is_pdf_filename",
    # PDF Utility functions
    "get_pdf_info",
    "sanitize_pdf_filename",
    # PDF Backward compatibility
    "is_valid_pdf",
]
