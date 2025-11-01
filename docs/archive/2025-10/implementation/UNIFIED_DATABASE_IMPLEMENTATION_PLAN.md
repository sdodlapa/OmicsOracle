# Unified Database System - Technical Implementation Plan

**Date:** October 14, 2024  
**Status:** 🚀 Ready to Implement  
**Architecture:** GEO-Centric Hybrid (SQLite + Filesystem)  
**Based On:** 
- `docs/DATABASE_ARCHITECTURE_CRITICAL_EVALUATION.md` (evaluation & strategy)
- `docs/PDF_STORAGE_STRATEGY.md` (hybrid storage design)

---

## 📋 Executive Summary

**Goal:** Implement a unified, GEO-centric database system that eliminates data fragmentation and provides a single source of truth for all OmicsOracle data.

**Approach:** Hybrid architecture combining:
- **SQLite** for metadata, relationships, and structured content
- **Filesystem** for large binary files (PDFs) organized by GEO ID
- **Unified identifiers** (UniversalIdentifier) as the linking mechanism

**Timeline:** 2-3 days for core implementation + 1 day for testing/validation

---

## 🎯 Design Principles

1. **GEO-Centric First** - All data organized by GEO dataset ID
2. **Single Source of Truth** - One database, one filesystem structure
3. **Universal Identifiers** - Consistent linking across all tables
4. **Performance** - Fast queries, efficient storage
5. **Integrity** - Hash verification, foreign keys, atomic transactions
6. **Maintainability** - Clear schema, good indexes, simple queries

---

## 📊 Database Schema (Complete)

### Core Tables

```sql
-- ============================================================================
-- TABLE 1: Universal Identifiers (Central Hub)
-- ============================================================================
CREATE TABLE universal_identifiers (
    -- Primary composite key
    geo_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    
    -- Alternative identifiers
    doi TEXT,
    pmc_id TEXT,
    arxiv_id TEXT,
    
    -- Publication metadata
    title TEXT NOT NULL,
    authors TEXT,
    journal TEXT,
    year INTEGER,
    abstract TEXT,
    
    -- Source tracking
    source TEXT,                    -- Where we discovered this (GEO, PubMed, etc.)
    confidence REAL DEFAULT 1.0,    -- Confidence in identifier mapping (0-1)
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (geo_id, pmid),
    
    -- Ensure at least one alternative identifier
    CHECK (doi IS NOT NULL OR pmc_id IS NOT NULL OR arxiv_id IS NOT NULL 
           OR title IS NOT NULL)
);

-- Indexes for fast lookups
CREATE INDEX idx_ui_geo_id ON universal_identifiers(geo_id);
CREATE INDEX idx_ui_pmid ON universal_identifiers(pmid);
CREATE INDEX idx_ui_doi ON universal_identifiers(doi);
CREATE INDEX idx_ui_pmc_id ON universal_identifiers(pmc_id);
CREATE INDEX idx_ui_year ON universal_identifiers(year);

-- ============================================================================
-- TABLE 2: GEO Datasets
-- ============================================================================
CREATE TABLE geo_datasets (
    geo_id TEXT PRIMARY KEY,
    
    -- GEO metadata
    title TEXT,
    summary TEXT,
    organism TEXT,
    platform TEXT,
    sample_count INTEGER,
    
    -- Processing status
    publication_count INTEGER DEFAULT 0,
    pdfs_downloaded INTEGER DEFAULT 0,
    pdfs_extracted INTEGER DEFAULT 0,
    
    -- Statistics
    avg_extraction_quality REAL,
    total_pdf_size_bytes INTEGER DEFAULT 0,
    
    -- Timestamps
    last_processed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_geo_organism ON geo_datasets(organism);
CREATE INDEX idx_geo_pub_count ON geo_datasets(publication_count);

-- ============================================================================
-- TABLE 3: URL Discovery (Pipeline 2)
-- ============================================================================
CREATE TABLE url_discovery (
    geo_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    
    -- URLs discovered (stored as JSON array)
    urls_json TEXT,                 -- All URLs found: [{"url": "...", "source": "PMC", "priority": 1}, ...]
    
    -- Discovery metadata
    sources_queried TEXT,           -- JSON array: ["PMC", "Unpaywall", "CORE", ...]
    sources_successful TEXT,        -- JSON array: ["PMC", "Unpaywall"]
    url_count INTEGER,
    
    -- Performance tracking
    discovery_duration_ms INTEGER,
    
    -- Timestamps
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (geo_id, pmid),
    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX idx_url_geo_id ON url_discovery(geo_id);

-- ============================================================================
-- TABLE 4: PDF Acquisition (Pipeline 3)
-- ============================================================================
CREATE TABLE pdf_acquisition (
    geo_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    
    -- PDF file information
    pdf_path TEXT,                  -- Relative: "data/pdfs/by_geo/GSE12345/pmid_12345678.pdf"
    pdf_size_bytes INTEGER,
    pdf_hash_sha256 TEXT,           -- For integrity verification
    
    -- Download metadata
    source_url TEXT,                -- The URL that worked
    source_type TEXT,               -- PMC, Unpaywall, CORE, Sci-Hub, etc.
    
    -- Attempt tracking
    urls_tried TEXT,                -- JSON array of URLs attempted
    attempt_count INTEGER,
    
    -- Performance tracking
    download_duration_ms INTEGER,
    
    -- Status
    status TEXT CHECK(status IN ('success', 'failed', 'pending')) DEFAULT 'pending',
    error_message TEXT,
    
    -- Timestamps
    downloaded_at TIMESTAMP,
    last_attempt_at TIMESTAMP,
    
    PRIMARY KEY (geo_id, pmid),
    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX idx_pdf_geo_id ON pdf_acquisition(geo_id);
CREATE INDEX idx_pdf_status ON pdf_acquisition(status);
CREATE INDEX idx_pdf_downloaded ON pdf_acquisition(downloaded_at);

-- ============================================================================
-- TABLE 5: Content Extraction (Pipeline 4 - Basic)
-- ============================================================================
CREATE TABLE content_extraction (
    geo_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    
    -- Basic extraction
    full_text TEXT,
    page_count INTEGER,
    text_length INTEGER,
    
    -- Quality metrics
    extraction_quality REAL,       -- 0-1.0 score
    extraction_grade TEXT,          -- A/B/C/D/F
    
    -- Performance tracking
    extraction_duration_ms INTEGER,
    
    -- Status
    status TEXT CHECK(status IN ('success', 'failed', 'pending')) DEFAULT 'pending',
    error_message TEXT,
    
    -- Timestamps
    extracted_at TIMESTAMP,
    
    PRIMARY KEY (geo_id, pmid),
    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX idx_ce_geo_id ON content_extraction(geo_id);
CREATE INDEX idx_ce_quality ON content_extraction(extraction_quality);
CREATE INDEX idx_ce_grade ON content_extraction(extraction_grade);

-- ============================================================================
-- TABLE 6: Enriched Content (Pipeline 4 - Enrichment)
-- ============================================================================
CREATE TABLE enriched_content (
    geo_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    
    -- Structured content (JSON)
    sections_json TEXT,             -- {"abstract": "...", "introduction": "...", ...}
    section_order TEXT,             -- JSON array: ["abstract", "introduction", ...]
    
    tables_json TEXT,               -- [{"caption": "...", "rows": [...], "confidence": 0.8}, ...]
    table_count INTEGER DEFAULT 0,
    
    references_json TEXT,           -- [{"number": 1, "doi": "...", "pmid": "...", ...}, ...]
    reference_count INTEGER DEFAULT 0,
    
    -- Extracted identifiers
    dois_found TEXT,                -- JSON array of DOIs found in references
    pmids_found TEXT,               -- JSON array of PMIDs found in references
    
    -- ChatGPT formatting
    chatgpt_prompt TEXT,            -- Ready-to-use prompt
    chatgpt_json TEXT,              -- Formatted JSON for API
    
    -- Statistics
    section_count INTEGER DEFAULT 0,
    
    -- Timestamps
    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (geo_id, pmid),
    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX idx_ec_geo_id ON enriched_content(geo_id);
CREATE INDEX idx_ec_table_count ON enriched_content(table_count);
CREATE INDEX idx_ec_ref_count ON enriched_content(reference_count);

-- ============================================================================
-- TABLE 7: Processing Log (Audit Trail)
-- ============================================================================
CREATE TABLE processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    geo_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    
    -- Event information
    pipeline TEXT NOT NULL,         -- 'P1', 'P2', 'P3', 'P4'
    event_type TEXT NOT NULL,       -- 'started', 'completed', 'failed'
    message TEXT,
    
    -- Performance
    duration_ms INTEGER,
    
    -- Metadata
    metadata_json TEXT,             -- Additional context as JSON
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers(geo_id, pmid)
);

CREATE INDEX idx_log_geo_pmid ON processing_log(geo_id, pmid);
CREATE INDEX idx_log_pipeline ON processing_log(pipeline);
CREATE INDEX idx_log_event ON processing_log(event_type);
CREATE INDEX idx_log_created ON processing_log(created_at);

-- ============================================================================
-- TABLE 8: Cache Metadata (Track All Caches)
-- ============================================================================
CREATE TABLE cache_metadata (
    cache_key TEXT PRIMARY KEY,     -- e.g., "url_PMC123456", "parsed_12345678"
    cache_type TEXT NOT NULL,       -- 'url', 'parsed', 'api_response'
    
    geo_id TEXT,
    pmid TEXT,
    
    -- Cache information
    cache_path TEXT,                -- If file-based cache
    cache_size_bytes INTEGER,
    cache_hash TEXT,
    
    -- Expiration
    ttl_days INTEGER,
    expires_at TIMESTAMP,
    
    -- Usage tracking
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_type ON cache_metadata(cache_type);
CREATE INDEX idx_cache_geo_pmid ON cache_metadata(geo_id, pmid);
CREATE INDEX idx_cache_expires ON cache_metadata(expires_at);
```

---

## 📁 Filesystem Organization

```
data/
├── database/
│   ├── omics_oracle.db              # Main unified database
│   ├── omics_oracle.db-wal          # Write-ahead log
│   └── omics_oracle.db-shm          # Shared memory
│
├── pdfs/
│   └── by_geo/
│       ├── GSE12345/
│       │   ├── pmid_12345678.pdf
│       │   ├── pmid_87654321.pdf
│       │   └── .manifest.json       # Quick reference
│       ├── GSE67890/
│       │   └── ...
│       └── .../
│
├── enriched/                         # Optional: Backup of enriched JSON
│   └── by_geo/
│       ├── GSE12345/
│       │   ├── pmid_12345678.json
│       │   └── ...
│       └── .../
│
└── cache/
    ├── url_cache/                   # URL discovery cache
    ├── parsed_cache/                # Parsed content cache
    └── api_cache/                   # External API response cache
```

---

## 🔧 Implementation Plan

### Phase 1: Core Database Setup (Day 1 - Morning)

**Files to Create:**
1. `omics_oracle_v2/lib/storage/unified_db.py` - Main database class
2. `omics_oracle_v2/lib/storage/models.py` - Data models (dataclasses)
3. `omics_oracle_v2/lib/storage/schema.sql` - Schema definition
4. `omics_oracle_v2/lib/storage/migrations/` - Migration system

**Tasks:**
- ✅ Create database schema
- ✅ Implement connection pooling
- ✅ Add transaction support
- ✅ Create base CRUD operations
- ✅ Add logging and error handling

**Code Example:**
```python
# omics_oracle_v2/lib/storage/unified_db.py

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import contextmanager
from datetime import datetime
import json

class UnifiedDatabase:
    """
    Unified database for all OmicsOracle data.
    GEO-centric architecture with universal identifiers.
    """
    
    def __init__(self, db_path: Path = Path("data/database/omics_oracle.db")):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
    
    @contextmanager
    def transaction(self):
        """Context manager for atomic transactions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _ensure_schema(self):
        """Create schema if it doesn't exist."""
        schema_file = Path(__file__).parent / "schema.sql"
        
        with self.transaction() as conn:
            conn.executescript(schema_file.read_text())
```

---

### Phase 2: GEO-Centric Storage (Day 1 - Afternoon)

**Files to Create:**
1. `omics_oracle_v2/lib/storage/geo_storage.py` - GEO-centric file manager
2. `omics_oracle_v2/lib/storage/integrity.py` - Hash verification utilities

**Tasks:**
- ✅ Implement GEO-organized filesystem
- ✅ Add PDF hash verification
- ✅ Create manifest file management
- ✅ Add integrity checking

**Code Example:**
```python
# omics_oracle_v2/lib/storage/geo_storage.py

from pathlib import Path
import hashlib
import json
from datetime import datetime

class GEOStorage:
    """Manages GEO-centric file storage."""
    
    def __init__(self, base_dir: Path = Path("data/pdfs/by_geo")):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_pdf(self, geo_id: str, pmid: str, pdf_content: bytes,
                 source: str) -> dict:
        """Save PDF to GEO-organized directory."""
        # Create GEO directory
        geo_dir = self.base_dir / geo_id
        geo_dir.mkdir(exist_ok=True)
        
        # Save PDF
        pdf_path = geo_dir / f"pmid_{pmid}.pdf"
        pdf_path.write_bytes(pdf_content)
        
        # Calculate hash
        pdf_hash = hashlib.sha256(pdf_content).hexdigest()
        
        # Update manifest
        self._update_manifest(geo_id, pmid, pdf_path.name, pdf_hash, source)
        
        return {
            "pdf_path": str(pdf_path.relative_to(Path("data"))),
            "pdf_size_bytes": len(pdf_content),
            "pdf_hash_sha256": pdf_hash,
            "source": source
        }
    
    def verify_integrity(self, geo_id: str, pmid: str, 
                        expected_hash: str) -> bool:
        """Verify PDF integrity."""
        pdf_path = self.base_dir / geo_id / f"pmid_{pmid}.pdf"
        
        if not pdf_path.exists():
            return False
        
        actual_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        return actual_hash == expected_hash
```

---

### Phase 3: Pipeline Integration (Day 2 - Morning)

**Files to Modify:**
1. `omics_oracle_v2/lib/pipelines/citation_discovery/*.py` - Save to unified DB
2. `omics_oracle_v2/lib/pipelines/url_collection/manager.py` - Save URL discovery
3. `omics_oracle_v2/lib/pipelines/pdf_download/*.py` - Use GEO storage
4. `omics_oracle_v2/lib/pipelines/text_enrichment/*.py` - Save enriched content

**Tasks:**
- ✅ Update P1 to save to universal_identifiers table
- ✅ Update P2 to save to url_discovery table
- ✅ Update P3 to use GEO storage + pdf_acquisition table
- ✅ Update P4 to save to content_extraction + enriched_content tables
- ✅ Add processing_log entries for all pipelines

---

### Phase 4: Query Interface (Day 2 - Afternoon)

**Files to Create:**
1. `omics_oracle_v2/lib/storage/queries.py` - Common query patterns
2. `omics_oracle_v2/lib/storage/analytics.py` - Analytics queries

**Tasks:**
- ✅ Create high-level query methods
- ✅ Add aggregation queries
- ✅ Implement GEO-centric views
- ✅ Add export functionality

**Code Example:**
```python
# omics_oracle_v2/lib/storage/queries.py

class DatabaseQueries:
    """High-level query interface."""
    
    def __init__(self, db: UnifiedDatabase):
        self.db = db
    
    def get_geo_publications(self, geo_id: str) -> List[Dict]:
        """Get all publications for a GEO dataset."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    ui.*,
                    pa.pdf_path,
                    pa.status as pdf_status,
                    ce.extraction_quality,
                    ce.extraction_grade
                FROM universal_identifiers ui
                LEFT JOIN pdf_acquisition pa ON ui.geo_id = pa.geo_id AND ui.pmid = pa.pmid
                LEFT JOIN content_extraction ce ON ui.geo_id = ce.geo_id AND ui.pmid = ce.pmid
                WHERE ui.geo_id = ?
                ORDER BY pa.downloaded_at DESC
            """, (geo_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_high_quality_papers(self, min_quality: float = 0.7) -> List[Dict]:
        """Get high-quality extracted papers."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    ui.geo_id,
                    ui.pmid,
                    ui.title,
                    ce.extraction_quality,
                    ce.extraction_grade,
                    ec.table_count,
                    ec.reference_count
                FROM universal_identifiers ui
                JOIN content_extraction ce ON ui.geo_id = ce.geo_id AND ui.pmid = ce.pmid
                LEFT JOIN enriched_content ec ON ui.geo_id = ec.geo_id AND ui.pmid = ec.pmid
                WHERE ce.extraction_quality >= ?
                ORDER BY ce.extraction_quality DESC
            """, (min_quality,))
            
            return [dict(row) for row in cursor.fetchall()]
```

---

### Phase 5: Migration & Testing (Day 3)

**Files to Create:**
1. `scripts/migrate_to_unified_db.py` - Migration script
2. `tests/test_unified_db.py` - Comprehensive tests
3. `docs/UNIFIED_DATABASE_GUIDE.md` - User guide

**Tasks:**
- ✅ Create migration script for existing data
- ✅ Write comprehensive unit tests
- ✅ Write integration tests
- ✅ Validate data integrity
- ✅ Performance benchmarking
- ✅ Documentation

---

## 📊 Data Flow Examples

### Example 1: Complete Pipeline with Unified DB

```python
async def process_geo_with_unified_db(geo_id: str):
    """Process GEO dataset using unified database."""
    
    # Initialize
    db = UnifiedDatabase()
    geo_storage = GEOStorage()
    queries = DatabaseQueries(db)
    
    # P1: Citation Discovery
    from omics_oracle_v2.lib.pipelines import GEOCitationCollector
    collector = GEOCitationCollector()
    citations = collector.collect(geo_id=geo_id)
    
    # Save GEO dataset metadata
    with db.transaction() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO geo_datasets (geo_id, publication_count)
            VALUES (?, ?)
        """, (geo_id, len(citations['publications'])))
        
        # Save universal identifiers
        for pub in citations['publications']:
            conn.execute("""
                INSERT OR REPLACE INTO universal_identifiers
                (geo_id, pmid, doi, title, authors, journal, year, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'GEO')
            """, (geo_id, pub.pmid, pub.doi, pub.title, pub.authors, 
                  pub.journal, pub.year))
    
    # P2: URL Discovery
    from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
    url_manager = FullTextManager()
    await url_manager.initialize()
    
    for pub in citations['publications']:
        urls_result = await url_manager.get_all_fulltext_urls(pub)
        
        if urls_result.success:
            # Save URL discovery
            with db.transaction() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO url_discovery
                    (geo_id, pmid, urls_json, url_count, discovered_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (geo_id, pub.pmid, json.dumps(urls_result.all_urls),
                      len(urls_result.all_urls), datetime.utcnow().isoformat()))
            
            # P3: PDF Acquisition
            from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
            pdf_manager = PDFDownloadManager()
            
            pdf_content = await pdf_manager.download_first_successful(
                urls_result.all_urls
            )
            
            if pdf_content:
                # Save to GEO storage
                pdf_metadata = geo_storage.save_pdf(
                    geo_id, pub.pmid, pdf_content,
                    source=urls_result.metadata.get('successful_source')
                )
                
                # Save to database
                with db.transaction() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO pdf_acquisition
                        (geo_id, pmid, pdf_path, pdf_size_bytes, pdf_hash_sha256,
                         source_type, status, downloaded_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'success', ?)
                    """, (geo_id, pub.pmid, pdf_metadata['pdf_path'],
                          pdf_metadata['pdf_size_bytes'], pdf_metadata['pdf_hash_sha256'],
                          pdf_metadata['source'], datetime.utcnow().isoformat()))
                
                # P4: Content Extraction
                from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor
                extractor = PDFExtractor(enable_enrichment=True)
                
                pdf_path = Path("data") / pdf_metadata['pdf_path']
                enriched = extractor.extract_text(pdf_path, metadata={
                    "pmid": pub.pmid,
                    "doi": pub.doi,
                    "title": pub.title
                })
                
                # Save extraction
                with db.transaction() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO content_extraction
                        (geo_id, pmid, full_text, page_count, text_length,
                         extraction_quality, extraction_grade, status, extracted_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'success', ?)
                    """, (geo_id, pub.pmid, enriched.get('full_text'),
                          enriched['page_count'], enriched['text_length'],
                          enriched['quality_score'], enriched.get('quality_grade', 'N/A'),
                          datetime.utcnow().isoformat()))
                    
                    # Save enriched content
                    conn.execute("""
                        INSERT OR REPLACE INTO enriched_content
                        (geo_id, pmid, sections_json, tables_json, references_json,
                         table_count, reference_count, chatgpt_prompt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (geo_id, pub.pmid,
                          json.dumps(enriched.get('sections', {})),
                          json.dumps(enriched.get('tables', [])),
                          json.dumps(enriched.get('references', [])),
                          enriched.get('table_count', 0),
                          enriched.get('reference_count', 0),
                          enriched.get('chatgpt_prompt')))
    
    await url_manager.cleanup()
    
    # Get final statistics
    stats = queries.get_geo_statistics(geo_id)
    print(json.dumps(stats, indent=2))
```

---

## 🎯 Success Criteria

### Performance Targets
- ✅ Query response: <50ms for single GEO dataset
- ✅ Insertion: <10ms per record
- ✅ Full pipeline: <5s per publication (with parallel processing)
- ✅ Database size: <100 MB for 1000 publications

### Data Integrity
- ✅ 100% consistency between filesystem and database
- ✅ SHA256 verification for all PDFs
- ✅ Foreign key constraints enforced
- ✅ Transaction rollback on errors

### Usability
- ✅ Simple query API
- ✅ GEO-centric views
- ✅ Export functionality
- ✅ Migration from old system

---

## 📝 Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Start Phase 1** - Create core database classes
3. **Implement incrementally** - Test each phase before moving forward
4. **Migrate existing data** - Convert current PDFs and metadata
5. **Validate with 100-paper test** - Prove it works at scale

---

## ✅ Archive Status

**Completed:**
- ✅ `deprecated_20251010/` - Old fulltext modules
- ✅ `deprecated_20251012/` - Redundant code
- ✅ `deprecated_20251014_citations_discovery/` - Old citation code
- ✅ `deprecated_20251014_fulltext_old/` - Old fulltext implementation
- ✅ `orphaned_integration_20251011/` - Orphaned integration code

**All old code archived! Ready to implement new system!** 🎉

---

**Ready to proceed?** Let's start with Phase 1! 🚀
