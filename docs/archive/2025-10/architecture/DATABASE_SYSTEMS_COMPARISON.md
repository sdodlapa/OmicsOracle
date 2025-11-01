# Database Systems Comparison & Integration Analysis

**Date:** October 15, 2025  
**Issue:** Two overlapping database systems need architectural decision

---

## Executive Summary

OmicsOracle currently has **TWO database systems** that appear to duplicate functionality:

1. **UnifiedDatabase** (via PipelineCoordinator) - `data/database/omics_oracle.db`
2. **GEORegistry** - `data/omics_oracle.db`

Both are GEO-centric, but serve **fundamentally different purposes**. This document analyzes whether to merge them, keep both, or redesign the architecture.

---

## System 1: UnifiedDatabase (PipelineCoordinator)

### **Location**
- Code: `omics_oracle_v2/lib/pipelines/storage/unified_db.py`
- Schema: `omics_oracle_v2/lib/pipelines/storage/schema.sql`
- Database: `data/database/omics_oracle.db`
- Used by: `PipelineCoordinator`, batch processing scripts

### **Tables (6 tables)**

```sql
1. universal_identifiers  -- GEO-PMID central hub
   PRIMARY KEY (geo_id, pmid)
   Columns: doi, pmc_id, arxiv_id, title, authors, journal, year

2. geo_datasets          -- GEO metadata + statistics
   PRIMARY KEY (geo_id)
   Columns: title, organism, platform, publication_count, 
            pdfs_downloaded, pdfs_extracted, status

3. url_discovery         -- P2: URL collection results
   Columns: geo_id, pmid, urls_json (ALL URLs), sources_queried,
            url_count, has_pdf_url, best_url_type

4. pdf_acquisition       -- P3: PDF download results
   Columns: geo_id, pmid, pdf_path, pdf_hash, pdf_size,
            source_url, download_method, status

5. content_extraction    -- P4: Basic text extraction
   Columns: geo_id, pmid, full_text, word_count,
            extraction_quality, extraction_grade

6. event_log            -- Pipeline events & timing
   Columns: geo_id, pmid, pipeline (P1/P2/P3/P4), event_type,
            message, duration_ms, error_traceback
```

### **Design Philosophy**
- **Pipeline-centric**: Tracks P1 → P2 → P3 → P4 progression
- **Audit trail**: event_log captures every pipeline step
- **Data lineage**: Can trace URL → PDF → Extraction chain
- **Quality tracking**: Extraction quality, grades, errors
- **Batch processing**: Designed for offline pipeline runs

### **Access Patterns**
```python
# PipelineCoordinator usage
coordinator = PipelineCoordinator()

# Record each pipeline step
coordinator.save_citation_discovery(geo_id, pmid, citation_data)  # P1
coordinator.save_url_discovery(geo_id, pmid, urls, sources)       # P2
coordinator.save_pdf_acquisition(geo_id, pmid, pdf_path, ...)     # P3
coordinator.save_content_extraction(geo_id, pmid, content, ...)   # P4

# Query by GEO
pubs = coordinator.db.get_publications_by_geo("GSE12345")
```

### **Strengths**
✅ Complete pipeline tracking  
✅ Detailed event logging with timing  
✅ Data lineage & audit trail  
✅ Quality metrics for extraction  
✅ Transaction support  
✅ Type-safe models (Pydantic)  

### **Weaknesses**
❌ No single-query GEO lookup (need multiple JOINs)  
❌ URLs stored as JSON blob (hard to query)  
❌ No relationship types (original vs citing papers)  
❌ No download retry mechanism  
❌ Not optimized for frontend O(1) lookup  
❌ Complex for simple "get all GEO data" queries  

---

## System 2: GEORegistry

### **Location**
- Code: `omics_oracle_v2/lib/pipelines/storage/registry/geo_registry.py`
- Database: `data/omics_oracle.db`
- Used by: API endpoints (`/enrich-fulltext`), frontend data access

### **Tables (4 tables)**

```sql
1. geo_datasets          -- GEO metadata
   PRIMARY KEY (geo_id)
   Columns: title, organism, platform, sample_count,
            metadata (JSON), relevance_score

2. publications          -- Publications metadata
   PRIMARY KEY (id), UNIQUE (pmid)
   Columns: pmid, doi, pmc_id, title, authors, journal, year,
            metadata (JSON), urls (JSON - ALL URLs for retry)

3. geo_publications      -- GEO ↔ Publication relationships
   PRIMARY KEY (geo_id, publication_id)
   Columns: relationship_type ('original' | 'citing'),
            citation_strategy ('strategy_a' | 'strategy_b')

4. download_history      -- Download attempts & results
   Columns: publication_id, url, source, status ('success' | 'failed'),
            file_path, file_size, error_message, attempt_number
```

### **Design Philosophy**
- **GEO-centric queries**: Frontend needs "show me everything for GSE12345"
- **Relationship tracking**: Original vs citing papers
- **Retry capability**: All URLs stored, can retry failed downloads
- **O(1) lookup**: Single query returns complete GEO data
- **Frontend-optimized**: Matches UI data needs exactly

### **Access Patterns**
```python
# GEORegistry usage
registry = get_registry()

# Register data (simpler API)
registry.register_geo_dataset(geo_id, metadata)
registry.register_publication(pmid, metadata, urls=[...])
registry.link_geo_to_publication(geo_id, pmid, relationship_type="citing")
registry.record_download_attempt(pmid, url, status="failed", error="...")

# Frontend: Get EVERYTHING in ONE query!
data = registry.get_complete_geo_data("GSE12345")
# Returns: {
#   "geo": {...},
#   "papers": {
#     "original": [{pmid, title, urls: [...]}],
#     "citing": [{pmid, title, urls: [...]}]
#   },
#   "statistics": {total: 10, downloaded: 7, failed: 3}
# }

# Retry failed downloads
urls = registry.get_urls_for_retry(pmid)
```

### **Strengths**
✅ O(1) GEO lookup (single query)  
✅ Relationship tracking (original/citing)  
✅ All URLs stored for retry  
✅ Download history tracking  
✅ Frontend-optimized data structure  
✅ Simple API (fewer methods)  
✅ Citation strategy tracking  

### **Weaknesses**
❌ No pipeline event logging  
❌ No extraction quality metrics  
❌ No data lineage tracking  
❌ URLs still in JSON (not fully normalized)  
❌ Limited audit capabilities  

---

## Data Overlap Analysis

### **What's Duplicated**

| Data Type | UnifiedDatabase | GEORegistry | Overlap |
|-----------|----------------|-------------|---------|
| GEO metadata | ✅ geo_datasets | ✅ geo_datasets | **100%** |
| PMID linkage | ✅ universal_identifiers | ✅ publications | **100%** |
| URLs | ✅ url_discovery (JSON) | ✅ publications.urls (JSON) | **100%** |
| PDF paths | ✅ pdf_acquisition | ✅ download_history.file_path | **Partial** |
| Download status | ✅ pdf_acquisition.status | ✅ download_history.status | **Partial** |

### **What's Unique to UnifiedDatabase**

- ✅ Pipeline event logging (event_log)
- ✅ Content extraction results (full_text, word_count, quality)
- ✅ Enriched content (sections, tables, references)
- ✅ Data lineage (P1→P2→P3→P4 chain)
- ✅ Timing metrics (duration_ms per pipeline)

### **What's Unique to GEORegistry**

- ✅ Relationship types (original vs citing papers)
- ✅ Citation strategies (strategy_a vs strategy_b)
- ✅ Multiple download attempts per URL
- ✅ O(1) complete GEO data query
- ✅ Relevance scores

---

## Critical Architectural Question

### **Are Both Centered Around GEO ID?**

**YES - But with Different Perspectives:**

**UnifiedDatabase:**
```
GEO ID → [Pipeline Event Stream]
  ├─ P1: Citations discovered
  ├─ P2: URLs collected (what sources? how many?)
  ├─ P3: PDFs downloaded (from which URL? what size?)
  └─ P4: Content extracted (what quality? what grade?)
```
**Perspective:** GEO as **processing workflow** (pipeline stages)

**GEORegistry:**
```
GEO ID → [Complete Dataset View]
  ├─ GEO metadata
  ├─ Original papers [PMID1, PMID2]
  │   └─ URLs: [pmc, unpaywall, scihub, ...]
  └─ Citing papers [PMID3, PMID4, PMID5]
      └─ URLs: [pmc, unpaywall, scihub, ...]
```
**Perspective:** GEO as **data entity** (relationships & content)

---

## Integration Options

### **Option 1: Merge into Single Database ⚠️**

**Approach:** Add GEORegistry features to UnifiedDatabase

**Implementation:**
```sql
-- Add to universal_identifiers
ALTER TABLE universal_identifiers ADD COLUMN relationship_type TEXT;
ALTER TABLE universal_identifiers ADD COLUMN citation_strategy TEXT;

-- Enhance url_discovery
-- Convert urls_json to separate url_collection table
CREATE TABLE url_collection (
    id INTEGER PRIMARY KEY,
    geo_id TEXT,
    pmid TEXT,
    url TEXT,
    source TEXT,
    priority INTEGER,
    url_type TEXT,
    FOREIGN KEY (geo_id, pmid) REFERENCES universal_identifiers
);

-- Add download_attempts to pdf_acquisition
ALTER TABLE pdf_acquisition ADD COLUMN attempt_number INTEGER DEFAULT 1;
```

**New Query Method:**
```python
# UnifiedDatabase with GEORegistry capabilities
def get_complete_geo_data(self, geo_id: str) -> Dict:
    """
    Single query to get everything (like GEORegistry).
    Requires complex SQL with multiple JOINs.
    """
    sql = """
        SELECT 
            g.*,
            u.pmid, u.relationship_type,
            GROUP_CONCAT(urls) as all_urls,
            p.pdf_path, p.status as pdf_status
        FROM geo_datasets g
        LEFT JOIN universal_identifiers u ON g.geo_id = u.geo_id
        LEFT JOIN url_discovery ud ON u.geo_id = ud.geo_id AND u.pmid = ud.pmid
        LEFT JOIN pdf_acquisition p ON u.geo_id = p.geo_id AND u.pmid = p.pmid
        WHERE g.geo_id = ?
        GROUP BY u.pmid
    """
    # ... complex result processing ...
```

**Pros:**
✅ Single source of truth  
✅ No data duplication  
✅ Unified transaction model  

**Cons:**
❌ Complex queries (performance impact)  
❌ Schema migration required  
❌ Breaks existing PipelineCoordinator API  
❌ Loss of GEORegistry's simple O(1) query  
❌ 3-5 days of refactoring work  

**Verdict:** ⚠️ **High risk, high effort, marginal benefit**

---

### **Option 2: Keep Both (Complementary Systems) ✅**

**Approach:** Recognize they serve different purposes

**Division of Responsibilities:**

```
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Batch Pipelines          │      API Endpoints          │
│  (Background Jobs)        │      (Real-time Queries)    │
│         ↓                 │              ↓              │
│  PipelineCoordinator      │      GEORegistry           │
│         ↓                 │              ↓              │
│  UnifiedDatabase          │      GEORegistry DB         │
│  (Pipeline Tracking)      │      (Frontend Data)        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Usage Pattern:**

**For Batch Processing:**
```python
# Use PipelineCoordinator
coordinator = PipelineCoordinator()

# Process 1000 GEO datasets
for geo_id in geo_ids:
    coordinator.save_citation_discovery(...)  # P1
    coordinator.save_url_discovery(...)       # P2
    coordinator.save_pdf_acquisition(...)     # P3
    coordinator.save_content_extraction(...)  # P4

# Audit the pipeline
errors = coordinator.db.get_failed_events()
stats = coordinator.db.get_pipeline_statistics()
```

**For API Endpoints:**
```python
# Use GEORegistry
registry = get_registry()

# Frontend clicks "Download Papers"
@router.post("/enrich-fulltext")
async def enrich(datasets):
    # ... download PDFs ...
    
    # Store for frontend O(1) access
    registry.register_geo_dataset(geo_id, metadata)
    registry.register_publication(pmid, metadata, urls)
    registry.link_geo_to_publication(geo_id, pmid, "citing")
    
    return enriched_datasets

# Frontend needs data
@router.get("/geo/{geo_id}")
async def get_geo_data(geo_id):
    # Single query - instant response
    return registry.get_complete_geo_data(geo_id)
```

**Synchronization Strategy:**
```python
# Optional: Sync critical data from Coordinator → Registry
def sync_to_frontend_registry(geo_id: str):
    """
    After batch pipeline completes, populate GEORegistry
    so frontend can access the data.
    """
    # Get data from UnifiedDatabase
    pubs = coordinator.db.get_publications_by_geo(geo_id)
    
    # Sync to GEORegistry
    for pub in pubs:
        registry.register_publication(pub.pmid, pub.to_dict())
        registry.link_geo_to_publication(geo_id, pub.pmid, "original")
```

**Pros:**
✅ Each system optimized for its use case  
✅ No breaking changes to existing code  
✅ Clear separation of concerns  
✅ Can sync data when needed  
✅ No performance tradeoffs  
✅ Zero refactoring required  

**Cons:**
⚠️ Some data duplication (acceptable)  
⚠️ Need documentation on which to use when  
⚠️ Two databases to maintain  

**Verdict:** ✅ **Recommended - Pragmatic & Low Risk**

---

### **Option 3: Hybrid Integration (Best of Both) 🎯**

**Approach:** Merge databases but keep separate query interfaces

**Architecture:**
```
Single Database: omics_oracle.db
├── UnifiedDatabase tables (pipeline tracking)
│   ├── universal_identifiers
│   ├── url_discovery  
│   ├── pdf_acquisition
│   ├── content_extraction
│   └── event_log
│
├── GEORegistry tables (frontend data)
│   ├── geo_datasets (SHARED with UnifiedDB)
│   ├── publications (links to universal_identifiers)
│   ├── geo_publications (relationship tracking)
│   └── download_history (links to pdf_acquisition)
│
└── Shared Tables
    └── geo_datasets (single source of GEO metadata)
```

**Implementation:**

1. **Merge databases** (file-level consolidation):
```bash
# Keep one database file
mv data/database/omics_oracle.db data/omics_oracle.db
```

2. **Share geo_datasets table:**
```python
class UnifiedDatabase:
    def __init__(self):
        self.db_path = "data/omics_oracle.db"  # Shared DB

class GEORegistry:
    def __init__(self):
        self.db_path = "data/omics_oracle.db"  # Same DB!
```

3. **Add foreign key constraints:**
```sql
-- Link GEORegistry publications to UnifiedDatabase identifiers
ALTER TABLE publications 
ADD FOREIGN KEY (pmid) 
REFERENCES universal_identifiers(pmid);

-- Link download_history to pdf_acquisition
ALTER TABLE download_history
ADD COLUMN pdf_acquisition_id INTEGER
REFERENCES pdf_acquisition(id);
```

4. **Keep separate APIs** (no code changes):
```python
# PipelineCoordinator keeps its interface
coordinator = PipelineCoordinator()
coordinator.save_citation_discovery(...)

# GEORegistry keeps its interface  
registry = get_registry()
registry.get_complete_geo_data(...)
```

**Pros:**
✅ Single database (easier backups)  
✅ Foreign key integrity  
✅ Can query across both systems  
✅ No API changes (backward compatible)  
✅ Eliminate file-level duplication  
✅ Optional cross-system queries  

**Cons:**
⚠️ Some schema changes needed  
⚠️ Need migration script  
⚠️ 1-2 days implementation  

**Verdict:** 🎯 **Best Long-term Solution**

---

## Detailed Comparison: How They Work

### **Scenario: Download Papers for GSE12345**

**Using PipelineCoordinator:**
```python
# Step 1: P1 - Citation Discovery
coordinator.save_citation_discovery(
    geo_id="GSE12345",
    pmid="24385618",
    citation_data={"title": "...", "doi": "..."}
)
# → Inserts into: universal_identifiers
# → Logs event: event_log (P1, success, 150ms)

# Step 2: P2 - URL Discovery  
coordinator.save_url_discovery(
    geo_id="GSE12345",
    pmid="24385618",
    urls=[{"url": "...", "source": "pmc"}, ...],
    sources=["pmc", "unpaywall", "scihub"]
)
# → Inserts into: url_discovery (urls as JSON blob)
# → Logs event: event_log (P2, success, 2500ms)

# Step 3: P3 - PDF Download
coordinator.save_pdf_acquisition(
    geo_id="GSE12345",
    pmid="24385618",
    pdf_path="data/pdfs/GSE12345/24385618.pdf",
    source_url="https://pmc.../",
    source_type="pmc"
)
# → Inserts into: pdf_acquisition
# → Logs event: event_log (P3, success, 5000ms)

# Step 4: P4 - Content Extraction
coordinator.save_content_extraction(
    geo_id="GSE12345",
    pmid="24385618",
    extraction_data={"full_text": "...", "quality": 0.95}
)
# → Inserts into: content_extraction
# → Logs event: event_log (P4, success, 3000ms)

# Query: Get pipeline progress
events = coordinator.db.get_events("GSE12345", "24385618")
# Returns: [P1: 150ms, P2: 2500ms, P3: 5000ms, P4: 3000ms]
```

**Using GEORegistry:**
```python
# Step 1: Register GEO
registry.register_geo_dataset("GSE12345", {
    "title": "Study of X",
    "organism": "Homo sapiens"
})
# → Inserts into: geo_datasets

# Step 2: Register Publication with ALL URLs
registry.register_publication(
    pmid="24385618",
    metadata={"title": "...", "authors": [...]},
    urls=[
        {"url": "https://pmc.../", "source": "pmc", "priority": 1},
        {"url": "https://unpaywall.../", "source": "unpaywall", "priority": 2},
        {"url": "https://scihub.../", "source": "scihub", "priority": 3}
    ]
)
# → Inserts into: publications (urls as JSON array)

# Step 3: Link GEO ↔ Publication
registry.link_geo_to_publication(
    geo_id="GSE12345",
    pmid="24385618",
    relationship_type="citing",
    citation_strategy="strategy_a"
)
# → Inserts into: geo_publications

# Step 4: Record Download Attempt
registry.record_download_attempt(
    pmid="24385618",
    url="https://pmc.../",
    source="pmc",
    status="success",
    file_path="data/pdfs/GSE12345/24385618.pdf"
)
# → Inserts into: download_history

# Query: Get everything for frontend
data = registry.get_complete_geo_data("GSE12345")
# Single query with JOINs:
# SELECT * FROM geo_datasets g
# LEFT JOIN geo_publications gp ON g.geo_id = gp.geo_id
# LEFT JOIN publications p ON gp.publication_id = p.id
# LEFT JOIN download_history dh ON p.id = dh.publication_id
# WHERE g.geo_id = 'GSE12345'
```

---

## Performance Analysis

### **Query Performance**

**Task:** Get all data for GSE12345 with 10 publications

**UnifiedDatabase (without optimization):**
```python
# Multiple queries required
geo = db.get_geo_dataset("GSE12345")           # Query 1
pubs = db.get_publications_by_geo("GSE12345")  # Query 2
for pub in pubs:
    urls = db.get_url_discovery("GSE12345", pub.pmid)  # Query 3-12
    pdf = db.get_pdf_acquisition("GSE12345", pub.pmid) # Query 13-22
    
# Total: 22 queries
# Execution time: ~50-100ms
```

**GEORegistry:**
```python
data = registry.get_complete_geo_data("GSE12345")

# Single query with JOINs
# Total: 1 query
# Execution time: ~5-10ms
```

**Winner:** GEORegistry (10x faster for frontend queries)

---

### **Storage Efficiency**

**Same GEO dataset (GSE12345, 10 publications):**

**UnifiedDatabase:**
```
geo_datasets:          1 row   (~500 bytes)
universal_identifiers: 10 rows (~5 KB)
url_discovery:         10 rows (~20 KB - JSON URLs)
pdf_acquisition:       10 rows (~3 KB)
content_extraction:    10 rows (~500 KB - full text)
event_log:             40 rows (~10 KB - 4 events × 10 pubs)
────────────────────────────────────────
Total:                 ~540 KB
```

**GEORegistry:**
```
geo_datasets:     1 row   (~500 bytes)
publications:     10 rows (~15 KB - includes URLs JSON)
geo_publications: 10 rows (~1 KB)
download_history: 30 rows (~5 KB - 3 attempts avg)
────────────────────────────────────────
Total:            ~22 KB
```

**Winner:** GEORegistry (24x smaller - no full_text storage)

**Note:** UnifiedDatabase stores extracted full_text, GEORegistry doesn't (different purposes)

---

## Recommendation Matrix

| Your Priority | Recommended Option | Reason |
|--------------|-------------------|---------|
| **Fastest to implement** | Option 2 (Keep Both) | Zero refactoring needed |
| **Best long-term** | Option 3 (Hybrid) | Single DB, separate APIs |
| **Most data integrity** | Option 3 (Hybrid) | Foreign keys across systems |
| **Lowest risk** | Option 2 (Keep Both) | No breaking changes |
| **Simplest architecture** | Option 1 (Merge) | One system only |
| **Best performance** | Option 2 (Keep Both) | Each optimized for use case |

---

## Final Recommendation: **Option 3 (Hybrid Integration)** 🎯

### **Implementation Plan (1-2 days)**

**Phase 1: Database Consolidation (4 hours)**
1. Merge database files
2. Add foreign key constraints
3. Create migration script
4. Test data integrity

**Phase 2: Shared Tables (2 hours)**
1. Deduplicate geo_datasets table
2. Update both systems to use shared table
3. Add cross-references

**Phase 3: Documentation (2 hours)**
1. Update architecture docs
2. Create usage guidelines
3. Add code examples

**Phase 4: Testing (2 hours)**
1. Test PipelineCoordinator workflows
2. Test GEORegistry queries
3. Test cross-system queries
4. Verify frontend still works

### **Migration Script Example**

```python
#!/usr/bin/env python3
"""Merge UnifiedDatabase and GEORegistry into single database."""

import sqlite3
from pathlib import Path

def migrate():
    # Paths
    unified_db = Path("data/database/omics_oracle.db")
    registry_db = Path("data/omics_oracle.db")
    
    # Create backup
    backup = registry_db.with_suffix(".db.backup")
    registry_db.copy(backup)
    
    # Attach UnifiedDatabase
    conn = sqlite3.connect(registry_db)
    conn.execute(f"ATTACH '{unified_db}' AS unified")
    
    # Copy UnifiedDatabase tables
    conn.executescript("""
        -- Copy tables (only if not exists)
        CREATE TABLE IF NOT EXISTS url_discovery AS 
        SELECT * FROM unified.url_discovery;
        
        CREATE TABLE IF NOT EXISTS pdf_acquisition AS
        SELECT * FROM unified.pdf_acquisition;
        
        CREATE TABLE IF NOT EXISTS content_extraction AS
        SELECT * FROM unified.content_extraction;
        
        CREATE TABLE IF NOT EXISTS event_log AS
        SELECT * FROM unified.event_log;
        
        -- Add foreign keys
        -- (requires table recreation - see full migration script)
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Migration complete")
    print(f"   Backup saved: {backup}")
    print(f"   Unified DB: {registry_db}")

if __name__ == "__main__":
    migrate()
```

---

## Conclusion

**Don't discard either system.** They serve complementary purposes:

- **UnifiedDatabase** = Audit trail, pipeline tracking, quality metrics
- **GEORegistry** = Frontend data access, O(1) queries, retry capability

**Best path forward:**
1. Merge into single database file (Option 3)
2. Keep separate query APIs (no code changes)
3. Add foreign key integrity
4. Document which system to use when

**Total effort:** 1-2 days  
**Risk:** Low (backward compatible)  
**Benefit:** Best of both worlds

Would you like me to:
1. Create the migration script?
2. Continue with the current refactoring (using GEORegistry)?
3. Implement the hybrid integration?
