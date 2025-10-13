"""
Storage module.

This package handles persistent storage of publications, PDFs,
and other downloaded content.

Components:
- pdf/: PDF download and storage management
"""

from omics_oracle_v2.lib.enrichment.fulltext.download_manager import PDFDownloadManager

__all__ = [
    "PDFDownloadManager",
]
