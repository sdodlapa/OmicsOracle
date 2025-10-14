"""
Storage module.

This package handles persistent storage of publications, PDFs,
and other downloaded content.

Components:
- pdf/: PDF download and storage management
"""

from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager

__all__ = [
    "PDFDownloadManager",
]
