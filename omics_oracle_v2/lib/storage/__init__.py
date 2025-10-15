"""
Storage Module - Unified Database System

GEO-centric storage with SQLite database and filesystem organization.

Quick Start:
    from omics_oracle_v2.lib.storage import (
        UnifiedDatabase,
        UniversalIdentifier,
        GEOStorage,
        DatabaseQueries,
        Analytics
    )

    # Initialize database
    db = UnifiedDatabase("data/database/omics_oracle.db")

    # Initialize storage
    storage = GEOStorage("data")

    # Insert publication
    pub = UniversalIdentifier(
        geo_id="GSE12345",
        pmid="12345678",
        title="Example Paper"
    )
    db.insert_universal_identifier(pub)

    # Save PDF
    pdf_info = storage.save_pdf(
        geo_id="GSE12345",
        pmid="12345678",
        source_path=Path("paper.pdf")
    )

    # Query
    queries = DatabaseQueries()
    pubs = queries.get_geo_publications("GSE12345")

    # Analytics
    analytics = Analytics()
    analytics.export_geo_dataset("GSE12345", "output/")

Legacy:
    PDFDownloadManager from pipelines.pdf_download (will be deprecated)
"""

from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager

from .analytics import Analytics
from .geo_storage import GEOStorage
from .integrity import (IntegrityVerifier, calculate_sha256,
                        verify_file_integrity)
from .models import (CacheMetadata, ContentExtraction, EnrichedContent,
                     GEODataset, PDFAcquisition, ProcessingLog,
                     UniversalIdentifier, URLDiscovery, expires_at_iso,
                     now_iso)
from .queries import DatabaseQueries
from .registry import GEORegistry, get_registry
from .unified_db import UnifiedDatabase

__all__ = [
    # Database
    "UnifiedDatabase",
    # Query & Analytics
    "DatabaseQueries",
    "Analytics",
    # Storage
    "GEOStorage",
    # Registry
    "GEORegistry",
    "get_registry",
    # Models
    "UniversalIdentifier",
    "GEODataset",
    "URLDiscovery",
    "PDFAcquisition",
    "ContentExtraction",
    "EnrichedContent",
    "ProcessingLog",
    "CacheMetadata",
    # Integrity
    "calculate_sha256",
    "verify_file_integrity",
    "IntegrityVerifier",
    # Utilities
    "now_iso",
    "expires_at_iso",
    # Legacy
    "PDFDownloadManager",
]
