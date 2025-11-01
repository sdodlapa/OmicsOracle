# PDF Storage Strategy: GEO-Centric Hybrid Approach

**Date:** October 14, 2024  
**Status:** 🎯 Recommended Architecture  
**Decision:** Hybrid (SQLite metadata + GEO-organized filesystem)

---

## 🎯 Design Goals

1. **GEO-Centric Organization** - All data for GSE12345 in one place
2. **Query Performance** - Fast lookups by GEO ID, PMID, DOI
3. **Storage Efficiency** - Handle 1000+ PDFs without bloat
4. **Data Integrity** - Consistency between DB and files
5. **Easy Access** - Can view PDFs without extraction

---

## 📊 Storage Architecture

### Database Schema (SQLite)

```sql
-- Main publications table (GEO-centric)
CREATE TABLE geo_publications (
    -- Identifiers
    geo_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    doi TEXT,
    
    -- Metadata
    title TEXT,
    authors TEXT,
    journal TEXT,
    year INTEGER,
    
    -- PDF file information
    pdf_path TEXT,              -- Relative: "data/pdfs/by_geo/GSE12345/pmid_12345678.pdf"
    pdf_size_bytes INTEGER,
    pdf_hash_sha256 TEXT,       -- For integrity checking
    pdf_downloaded_at TIMESTAMP,
    pdf_source TEXT,            -- Which URL source worked (PMC, Unpaywall, etc.)
    
    -- Processing status
    extracted_at TIMESTAMP,     -- When content was extracted
    extraction_quality REAL,    -- Quality score (0-1.0)
    extraction_grade TEXT,      -- A/B/C/D/F grade
    
    -- URLs that were tried
    urls_discovered TEXT,       -- JSON array of all URLs found
    urls_tried TEXT,            -- JSON array of URLs that were attempted
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (geo_id, pmid)
);

-- Indexes for fast queries
CREATE INDEX idx_geo_id ON geo_publications(geo_id);
CREATE INDEX idx_pmid ON geo_publications(pmid);
CREATE INDEX idx_doi ON geo_publications(doi);
CREATE INDEX idx_quality ON geo_publications(extraction_quality);
CREATE INDEX idx_downloaded ON geo_publications(pdf_downloaded_at);

-- Extracted content table (GEO-centric)
CREATE TABLE geo_publication_content (
    geo_id TEXT NOT NULL,
    pmid TEXT NOT NULL,
    
    -- Extracted sections (JSON)
    sections_json TEXT,         -- {"abstract": "...", "introduction": "...", ...}
    tables_json TEXT,           -- [{"caption": "...", "rows": [...]}, ...]
    references_json TEXT,       -- [{"doi": "...", "pmid": "...", ...}, ...]
    
    -- Metadata
    page_count INTEGER,
    text_length INTEGER,
    section_count INTEGER,
    table_count INTEGER,
    reference_count INTEGER,
    
    -- ChatGPT formatting
    chatgpt_prompt TEXT,        -- Ready-to-use prompt
    chatgpt_json TEXT,          -- Formatted JSON
    
    -- Timestamps
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (geo_id, pmid),
    FOREIGN KEY (geo_id, pmid) REFERENCES geo_publications(geo_id, pmid)
);

-- GEO dataset metadata
CREATE TABLE geo_datasets (
    geo_id TEXT PRIMARY KEY,
    title TEXT,
    summary TEXT,
    organism TEXT,
    sample_count INTEGER,
    publication_count INTEGER,  -- Count of associated publications
    last_processed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Filesystem Organization (GEO-Centric)

```
data/
├── pdfs/
│   └── by_geo/
│       ├── GSE12345/
│       │   ├── pmid_12345678.pdf
│       │   ├── pmid_87654321.pdf
│       │   ├── pmid_11111111.pdf
│       │   └── .manifest.json          # Quick metadata
│       ├── GSE67890/
│       │   ├── pmid_22222222.pdf
│       │   └── .manifest.json
│       └── GSE11111/
│           └── ...
│
├── enriched/                            # Extracted content (optional backup)
│   └── by_geo/
│       ├── GSE12345/
│       │   ├── pmid_12345678.json      # Enriched content
│       │   ├── pmid_87654321.json
│       │   └── ...
│       └── ...
│
└── database/
    ├── geo_publications.db              # Main SQLite database
    ├── geo_publications.db-wal          # WAL file (write-ahead log)
    └── geo_publications.db-shm          # Shared memory
```

---

## 🔄 Workflow Integration

### Pipeline 3: PDF Acquisition (Updated)

```python
from pathlib import Path
import hashlib
import json
from datetime import datetime

class GeoCentricPDFManager:
    """Manages PDFs with GEO-centric organization."""
    
    def __init__(self, base_dir: Path = Path("data/pdfs/by_geo")):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_pdf_path(self, geo_id: str, pmid: str) -> Path:
        """Get the expected path for a PDF."""
        geo_dir = self.base_dir / geo_id
        return geo_dir / f"pmid_{pmid}.pdf"
    
    def save_pdf(
        self,
        geo_id: str,
        pmid: str,
        pdf_content: bytes,
        source: str,
        urls_tried: list
    ) -> dict:
        """
        Save PDF to GEO-organized directory and return metadata.
        
        Returns:
            dict with pdf_path, pdf_size, pdf_hash, etc.
        """
        # Create GEO directory
        geo_dir = self.base_dir / geo_id
        geo_dir.mkdir(parents=True, exist_ok=True)
        
        # Save PDF
        pdf_path = geo_dir / f"pmid_{pmid}.pdf"
        pdf_path.write_bytes(pdf_content)
        
        # Calculate hash for integrity
        pdf_hash = hashlib.sha256(pdf_content).hexdigest()
        
        # Update manifest
        self._update_manifest(geo_id, pmid, pdf_path, pdf_hash, source)
        
        return {
            "pdf_path": str(pdf_path.relative_to(Path("data"))),
            "pdf_size_bytes": len(pdf_content),
            "pdf_hash_sha256": pdf_hash,
            "pdf_source": source,
            "urls_tried": json.dumps(urls_tried),
            "pdf_downloaded_at": datetime.utcnow().isoformat()
        }
    
    def _update_manifest(self, geo_id: str, pmid: str, pdf_path: Path, 
                         pdf_hash: str, source: str):
        """Update the .manifest.json file in GEO directory."""
        geo_dir = self.base_dir / geo_id
        manifest_path = geo_dir / ".manifest.json"
        
        # Load existing manifest
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
        else:
            manifest = {
                "geo_id": geo_id,
                "pdfs": {},
                "created_at": datetime.utcnow().isoformat()
            }
        
        # Add/update PDF entry
        manifest["pdfs"][pmid] = {
            "filename": pdf_path.name,
            "hash": pdf_hash,
            "source": source,
            "downloaded_at": datetime.utcnow().isoformat()
        }
        manifest["updated_at"] = datetime.utcnow().isoformat()
        manifest["pdf_count"] = len(manifest["pdfs"])
        
        # Save manifest
        manifest_path.write_text(json.dumps(manifest, indent=2))
    
    def verify_integrity(self, geo_id: str, pmid: str, 
                        expected_hash: str) -> bool:
        """Verify PDF integrity using SHA256 hash."""
        pdf_path = self.get_pdf_path(geo_id, pmid)
        
        if not pdf_path.exists():
            return False
        
        actual_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        return actual_hash == expected_hash
    
    def get_geo_stats(self, geo_id: str) -> dict:
        """Get statistics for a GEO dataset."""
        geo_dir = self.base_dir / geo_id
        
        if not geo_dir.exists():
            return {"exists": False}
        
        pdfs = list(geo_dir.glob("pmid_*.pdf"))
        total_size = sum(pdf.stat().st_size for pdf in pdfs)
        
        return {
            "exists": True,
            "geo_id": geo_id,
            "pdf_count": len(pdfs),
            "total_size_mb": total_size / (1024 * 1024),
            "pdfs": [pdf.name for pdf in pdfs]
        }
```

### Database Integration

```python
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

class GEOPublicationDatabase:
    """SQLite database for GEO-centric publication management."""
    
    def __init__(self, db_path: Path = Path("data/database/geo_publications.db")):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return dicts instead of tuples
        
        # Create tables (SQL from above)
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS geo_publications (
                geo_id TEXT NOT NULL,
                pmid TEXT NOT NULL,
                doi TEXT,
                title TEXT,
                authors TEXT,
                journal TEXT,
                year INTEGER,
                pdf_path TEXT,
                pdf_size_bytes INTEGER,
                pdf_hash_sha256 TEXT,
                pdf_downloaded_at TIMESTAMP,
                pdf_source TEXT,
                extracted_at TIMESTAMP,
                extraction_quality REAL,
                extraction_grade TEXT,
                urls_discovered TEXT,
                urls_tried TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (geo_id, pmid)
            );
            
            CREATE INDEX IF NOT EXISTS idx_geo_id ON geo_publications(geo_id);
            CREATE INDEX IF NOT EXISTS idx_pmid ON geo_publications(pmid);
            CREATE INDEX IF NOT EXISTS idx_quality ON geo_publications(extraction_quality);
            
            CREATE TABLE IF NOT EXISTS geo_publication_content (
                geo_id TEXT NOT NULL,
                pmid TEXT NOT NULL,
                sections_json TEXT,
                tables_json TEXT,
                references_json TEXT,
                page_count INTEGER,
                text_length INTEGER,
                section_count INTEGER,
                table_count INTEGER,
                reference_count INTEGER,
                chatgpt_prompt TEXT,
                chatgpt_json TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (geo_id, pmid),
                FOREIGN KEY (geo_id, pmid) REFERENCES geo_publications(geo_id, pmid)
            );
            
            CREATE TABLE IF NOT EXISTS geo_datasets (
                geo_id TEXT PRIMARY KEY,
                title TEXT,
                summary TEXT,
                organism TEXT,
                sample_count INTEGER,
                publication_count INTEGER,
                last_processed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
    
    def save_publication(self, geo_id: str, publication: dict, 
                        pdf_metadata: Optional[dict] = None):
        """Save publication metadata."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO geo_publications (
                geo_id, pmid, doi, title, authors, journal, year,
                pdf_path, pdf_size_bytes, pdf_hash_sha256, 
                pdf_downloaded_at, pdf_source, urls_discovered, urls_tried,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            geo_id,
            publication.get("pmid"),
            publication.get("doi"),
            publication.get("title"),
            publication.get("authors"),
            publication.get("journal"),
            publication.get("year"),
            pdf_metadata.get("pdf_path") if pdf_metadata else None,
            pdf_metadata.get("pdf_size_bytes") if pdf_metadata else None,
            pdf_metadata.get("pdf_hash_sha256") if pdf_metadata else None,
            pdf_metadata.get("pdf_downloaded_at") if pdf_metadata else None,
            pdf_metadata.get("pdf_source") if pdf_metadata else None,
            pdf_metadata.get("urls_discovered") if pdf_metadata else None,
            pdf_metadata.get("urls_tried") if pdf_metadata else None,
            datetime.utcnow().isoformat()
        ))
        
        self.conn.commit()
    
    def save_extracted_content(self, geo_id: str, pmid: str, 
                              enriched_content: dict):
        """Save extracted/enriched content."""
        import json
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO geo_publication_content (
                geo_id, pmid, sections_json, tables_json, references_json,
                page_count, text_length, section_count, table_count, reference_count,
                chatgpt_prompt, chatgpt_json, extracted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            geo_id,
            pmid,
            json.dumps(enriched_content.get("sections", {})),
            json.dumps(enriched_content.get("tables", [])),
            json.dumps(enriched_content.get("references", [])),
            enriched_content.get("page_count"),
            enriched_content.get("text_length"),
            enriched_content.get("section_count"),
            enriched_content.get("table_count"),
            enriched_content.get("reference_count"),
            enriched_content.get("chatgpt_prompt"),
            json.dumps(enriched_content.get("chatgpt_json", {})),
            datetime.utcnow().isoformat()
        ))
        
        # Update extraction metadata in main table
        cursor.execute("""
            UPDATE geo_publications
            SET extraction_quality = ?,
                extraction_grade = ?,
                extracted_at = ?
            WHERE geo_id = ? AND pmid = ?
        """, (
            enriched_content.get("quality_score"),
            enriched_content.get("quality_grade"),
            datetime.utcnow().isoformat(),
            geo_id,
            pmid
        ))
        
        self.conn.commit()
    
    def get_publications_for_geo(self, geo_id: str) -> List[Dict]:
        """Get all publications for a GEO dataset."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM geo_publications WHERE geo_id = ?
            ORDER BY pdf_downloaded_at DESC
        """, (geo_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_geo_statistics(self, geo_id: str) -> Dict:
        """Get statistics for a GEO dataset."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_publications,
                COUNT(pdf_path) as pdfs_downloaded,
                COUNT(extracted_at) as pdfs_extracted,
                AVG(extraction_quality) as avg_quality,
                SUM(pdf_size_bytes) as total_pdf_size
            FROM geo_publications
            WHERE geo_id = ?
        """, (geo_id,))
        
        stats = dict(cursor.fetchone())
        stats["geo_id"] = geo_id
        
        return stats
```

---

## 🎯 Complete Example: GEO-Centric Workflow

```python
import asyncio
from pathlib import Path

async def process_geo_dataset_complete(geo_id: str):
    """
    Complete GEO-centric workflow:
    P1 → P2 → P3 (with GEO storage) → P4 (with GEO storage)
    """
    
    # Initialize GEO-centric storage
    pdf_manager = GeoCentricPDFManager()
    db = GEOPublicationDatabase()
    
    # P1: Discover citations
    from omics_oracle_v2.lib.pipelines import GEOCitationCollector
    geo_collector = GEOCitationCollector()
    citations = geo_collector.collect(geo_id=geo_id)
    
    print(f"P1: Found {len(citations['publications'])} publications for {geo_id}")
    
    # Save GEO dataset metadata
    db.conn.execute("""
        INSERT OR REPLACE INTO geo_datasets (geo_id, publication_count, last_processed)
        VALUES (?, ?, ?)
    """, (geo_id, len(citations['publications']), datetime.utcnow().isoformat()))
    db.conn.commit()
    
    # P2: Discover URLs
    from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
    url_manager = FullTextManager()
    await url_manager.initialize()
    
    # P3: Acquire PDFs (GEO-organized)
    from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
    downloader = PDFDownloadManager()
    
    # P4: Extract content
    from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor
    extractor = PDFExtractor(enable_enrichment=True)
    
    for publication in citations["publications"]:
        try:
            # P2: Discover URLs
            urls_result = await url_manager.get_all_fulltext_urls(publication)
            
            if not urls_result.success:
                # Save publication metadata even without PDF
                db.save_publication(geo_id, {
                    "pmid": publication.pmid,
                    "doi": publication.doi,
                    "title": publication.title,
                })
                continue
            
            # P3: Download PDF to GEO-organized location
            pdf_content = await downloader.download_first_successful(
                urls_result.all_urls
            )
            
            if pdf_content:
                # Save to GEO-organized filesystem
                pdf_metadata = pdf_manager.save_pdf(
                    geo_id=geo_id,
                    pmid=publication.pmid,
                    pdf_content=pdf_content,
                    source=urls_result.metadata.get("successful_source"),
                    urls_tried=urls_result.all_urls
                )
                
                # Save to database
                db.save_publication(
                    geo_id=geo_id,
                    publication={
                        "pmid": publication.pmid,
                        "doi": publication.doi,
                        "title": publication.title,
                        "authors": publication.authors,
                        "journal": publication.journal,
                        "year": publication.year,
                    },
                    pdf_metadata=pdf_metadata
                )
                
                # P4: Extract content
                pdf_path = pdf_manager.get_pdf_path(geo_id, publication.pmid)
                enriched = extractor.extract_text(
                    pdf_path=pdf_path,
                    metadata={
                        "pmid": publication.pmid,
                        "doi": publication.doi,
                        "title": publication.title,
                    }
                )
                
                # Save enriched content
                db.save_extracted_content(geo_id, publication.pmid, enriched)
                
                print(f"✅ {publication.pmid}: PDF acquired + content extracted")
            
        except Exception as e:
            print(f"❌ {publication.pmid}: {e}")
            continue
    
    await url_manager.cleanup()
    
    # Print final statistics
    stats = db.get_geo_statistics(geo_id)
    print(f"\n{'='*60}")
    print(f"GEO Dataset: {geo_id}")
    print(f"{'='*60}")
    print(f"Total publications: {stats['total_publications']}")
    print(f"PDFs downloaded: {stats['pdfs_downloaded']}")
    print(f"PDFs extracted: {stats['pdfs_extracted']}")
    print(f"Avg quality: {stats['avg_quality']:.2f}")
    print(f"Total PDF size: {stats['total_pdf_size'] / (1024*1024):.1f} MB")

# Run
asyncio.run(process_geo_dataset_complete("GSE12345"))
```

---

## 📊 Query Examples

### Get all publications for a GEO dataset

```python
db = GEOPublicationDatabase()
pubs = db.get_publications_for_geo("GSE12345")

for pub in pubs:
    print(f"{pub['pmid']}: {pub['title'][:60]}...")
    print(f"  PDF: {pub['pdf_path']}")
    print(f"  Quality: {pub['extraction_grade']} ({pub['extraction_quality']:.2f})")
```

### Get high-quality publications

```python
cursor = db.conn.cursor()
cursor.execute("""
    SELECT geo_id, pmid, title, extraction_quality, extraction_grade
    FROM geo_publications
    WHERE extraction_quality >= 0.7
    ORDER BY extraction_quality DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row['pmid']}: {row['title'][:50]}... (Grade: {row['extraction_grade']})")
```

### Get GEO datasets with most publications

```python
cursor.execute("""
    SELECT geo_id, COUNT(*) as pub_count
    FROM geo_publications
    GROUP BY geo_id
    ORDER BY pub_count DESC
    LIMIT 10
""")
```

---

## 🔧 Maintenance Operations

### Verify integrity of all PDFs for a GEO dataset

```python
def verify_geo_pdfs(geo_id: str):
    """Verify all PDFs for a GEO dataset."""
    db = GEOPublicationDatabase()
    pdf_manager = GeoCentricPDFManager()
    
    pubs = db.get_publications_for_geo(geo_id)
    
    for pub in pubs:
        if pub['pdf_hash_sha256']:
            is_valid = pdf_manager.verify_integrity(
                geo_id, 
                pub['pmid'],
                pub['pdf_hash_sha256']
            )
            
            if not is_valid:
                print(f"❌ CORRUPTED: {pub['pmid']}")
            else:
                print(f"✅ VALID: {pub['pmid']}")
```

### Export all data for a GEO dataset

```python
def export_geo_dataset(geo_id: str, output_dir: Path):
    """Export all PDFs and data for a GEO dataset."""
    db = GEOPublicationDatabase()
    
    # Create export directory
    export_dir = output_dir / geo_id
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all publications
    pubs = db.get_publications_for_geo(geo_id)
    
    # Copy PDFs
    for pub in pubs:
        if pub['pdf_path']:
            src = Path("data") / pub['pdf_path']
            dst = export_dir / f"{pub['pmid']}.pdf"
            shutil.copy(src, dst)
    
    # Export metadata as JSON
    export_file = export_dir / "publications.json"
    export_file.write_text(json.dumps(pubs, indent=2))
    
    print(f"Exported {len(pubs)} publications to {export_dir}")
```

---

## ✅ Advantages of This Approach

1. **GEO-Centric Organization** ✅
   - All data for GSE12345 in one place (filesystem + DB)
   - Easy to query "all publications for this GEO dataset"

2. **Data Integrity** ✅
   - SHA256 hashes for verification
   - Foreign key constraints in DB
   - Manifest files for quick checks

3. **Performance** ✅
   - Fast SQLite queries
   - No BLOB overhead
   - Efficient file access

4. **Maintainability** ✅
   - Can view PDFs directly
   - Easy backups (rsync geo directories)
   - Simple consistency checks

5. **Scalability** ✅
   - Handles 1000+ PDFs easily
   - Database stays reasonable size
   - Can shard by GEO ID if needed

---

## 🚀 Next Steps

1. ✅ Implement `GeoCentricPDFManager` class
2. ✅ Implement `GEOPublicationDatabase` class
3. ✅ Update Pipeline 3 to use GEO-organized storage
4. ✅ Update Pipeline 4 to save to database
5. ✅ Create migration script for existing PDFs
6. ✅ Add integrity verification tools
7. ✅ Document query patterns

**Status:** Ready to implement!
