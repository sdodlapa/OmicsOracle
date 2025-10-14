"""
Pipeline 3: Citation Download
==============================

Downloads PDFs using URLs collected from Pipeline 2.

Features:
- Waterfall strategy (tries URLs in priority order)
- Retry logic with exponential backoff
- Rate limiting and politeness
- Cookie/session management
- Verification and validation

Components:
- download_manager.py: Main download orchestrator
"""

from omics_oracle_v2.lib.pipelines.citation_download.download_manager import PDFDownloadManager

__all__ = ["PDFDownloadManager"]
