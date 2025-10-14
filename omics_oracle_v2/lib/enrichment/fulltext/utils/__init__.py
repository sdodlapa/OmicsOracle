"""
Shared utilities for fulltext enrichment.

This package provides common utilities used across fulltext enrichment components:
- PDF validation and manipulation (pdf_utils)
- Standardized logging with visual indicators (logging_utils)
"""

from .logging_utils import (  # Visual indicators; Logging functions
    FAILURE,
    INFO,
    SUCCESS,
    WARNING,
    grep_pattern,
    log_source_debug,
    log_source_error,
    log_source_failure,
    log_source_info,
    log_source_success,
    log_source_warning,
)
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
    # Logging visual indicators
    "SUCCESS",
    "FAILURE",
    "WARNING",
    "INFO",
    # Logging functions
    "log_source_success",
    "log_source_failure",
    "log_source_warning",
    "log_source_info",
    "log_source_debug",
    "log_source_error",
    "grep_pattern",
]
