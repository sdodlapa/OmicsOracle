"""
Full-text content retrieval and extraction for OmicsOracle.

This module provides functionality to fetch and parse full-text articles from
various sources including PubMed Central, Unpaywall, institutional repositories,
and gray-area sources.
"""

from lib.fulltext.content_extractor import ContentExtractor
from lib.fulltext.content_fetcher import ContentFetcher
from lib.fulltext.models import (
    Author,
    ContentType,
    Figure,
    FullTextContent,
    FullTextResult,
    Reference,
    Section,
    SourceType,
    Table,
)
from lib.fulltext.pdf_downloader import PDFDownloader, download_pdf_from_doi

__all__ = [
    "ContentType",
    "SourceType",
    "Author",
    "Figure",
    "Table",
    "Reference",
    "Section",
    "FullTextContent",
    "FullTextResult",
    "ContentFetcher",
    "ContentExtractor",
    "PDFDownloader",
    "download_pdf_from_doi",
]
