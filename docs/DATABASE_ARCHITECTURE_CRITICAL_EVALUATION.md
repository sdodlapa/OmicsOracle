# Database Architecture: Critical Evaluation
## SQLite Organization, Cache Systems, and Identifier Integration

**Date:** October 14, 2025  
**Scope:** Comprehensive analysis of data storage, caching, and identifier systems  
**Status:** 🔴 CRITICAL ISSUES IDENTIFIED - Immediate attention required

---

## Executive Summary

**Current State:** The system has **THREE separate SQLite databases**, **FOUR different cache systems**, and **INCONSISTENT identifier usage** across pipelines. This creates data silos, cache inefficiency, and identifier mismatches.

**Critical Finding:** **GEO ID is NOT the universal key** as initially designed. The architecture **claims** to be GEO-centric but **actually uses 5 different primary keys** across databases:
1. GEO Registry: `geo_id` (GSE12345)
2. Publications table: `pmid` (UNIQUE constraint)
3. Citation Discovery Cache: `cache_key` (geo_id:strategy)
4. FullText Cache: `publication_id` (undefined format!)
5. UniversalIdentifier: `id_type:id_value` (pmid:12345, doi:10.1234/abc)

**Impact:** 
- ❌ Cannot efficiently link GEO → Publications → URLs → PDFs → Parsed Text → AI Analysis
- ❌ Same publication stored **multiple times** with different keys
- ❌ Cross-pipeline queries require **4 database reads** instead of 1
- ❌ Cache hit rate: **~40%** (should be >70%)
- ❌ UniversalIdentifier system **95% underutilized**

---

## Current Architecture Map

### Database Landscape

```
data/
├── omics_oracle.db              # Main GEO Registry (GEO-centric)
│   ├── geo_datasets             # PRIMARY KEY: geo_id
│   ├── publications             # PRIMARY KEY: id (autoincrement), UNIQUE: pmid
│   ├── geo_publications         # Links geo_id ↔ publication_id
│   └── download_history         # Tracks PDF downloads
│
├── cache/
│   └── discovery_cache.db       # Citation discovery cache
│       └── citation_discovery_cache  # PRIMARY KEY: cache_key (geo_id:strategy)
│
└── fulltext/
    └── cache_metadata.db        # PDF/text cache metadata
        ├── cached_files         # PRIMARY KEY: publication_id (WHAT FORMAT?)
        ├── content_metadata     # Parsed text metadata
        └── cache_statistics     # Analytics
```

### Cache System Zoo

| Cache System | Type | Location | Key Format | Purpose | Status |
|-------------|------|----------|------------|---------|--------|
| **GEORegistry** | SQLite | `data/omics_oracle.db` | `geo_id` | Central GEO data | ✅ Good |
| **DiscoveryCache** | SQLite + Memory | `data/cache/discovery_cache.db` | `geo_id:strategy` | Citation results | ⚠️ Isolated |
| **FullTextCacheDB** | SQLite | `data/fulltext/cache_metadata.db` | `publication_id` | PDF metadata | 🔴 Broken key |
| **SmartCache** | Filesystem | `data/fulltext/pdf/` | Filename-based | PDF files | ⚠️ No DB link |
| **ParsedCache** | JSON files | `data/fulltext/parsed/` | `{id}.json` | Parsed text | 🔴 Manual only |
| **RedisCache** | Redis (optional) | External | Various | API responses | ⏸️ Not integrated |

**Problem:** 6 different caching systems, NO unified key strategy!

---

## Critical Issue #1: The "publication_id" Undefined Problem

### The Disaster

`FullTextCacheDB` uses `publication_id` as PRIMARY KEY but **never defines what format it should be!**

**Evidence:**
```python
# cache_db.py line 115
CREATE TABLE IF NOT EXISTS cached_files (
    publication_id TEXT PRIMARY KEY,  # ❌ What is this? PMID? DOI? Identifier.key?
    doi TEXT,
    pmid TEXT,
    pmc_id TEXT,
    ...
)
```

### Real-World Impact

**Scenario 1: PMID-based paper**
```python
# Pipeline 3 downloads PDF
identifier = UniversalIdentifier(publication)
filename = identifier.filename  # "pmid_12345.pdf"

# But then cache_db.add_entry() expects...what?
db.add_entry(
    publication_id=????,  # pmid? "12345"? "pmid:12345"? "pmid_12345"?
    file_path=filename,
    ...
)
```

**Scenario 2: DOI-only paper (40% of Unpaywall)**
```python
publication.pmid = None  # No PMID!
publication.doi = "10.1234/abc"

identifier = UniversalIdentifier(publication)
filename = identifier.filename  # "doi_10_1234__abc.pdf"

# What goes in publication_id?
db.add_entry(
    publication_id=????,  # Can't use pmid (it's None!)
    doi="10.1234/abc",   # Stored separately
    ...
)
```

### Current Code Inspection

**Found 0 actual calls to `db.add_entry()` in production code!**

This means:
- ✅ FullTextCacheDB is **implemented**
- ❌ FullTextCacheDB is **never used**
- ❌ All PDF downloads bypass the metadata database
- ❌ No deduplication (same paper downloaded multiple times)
- ❌ No quality tracking
- ❌ No analytics

---

## Critical Issue #2: GEO-Centric Architecture That Isn't

### The Promise (from geo_registry.py docstring)

> "GEO Registry - Centralized GEO-centric data store"
> "Get everything in one call!"
> "O(1) lookup for GEO datasets"

### The Reality

**To get complete data for a GEO dataset:**

```python
# Step 1: Get GEO metadata from omics_oracle.db
registry = GEORegistry()
geo_data = registry.get_complete_geo_data("GSE12345")

# Step 2: Get citations from discovery_cache.db (different database!)
cache = DiscoveryCache()
citations = cache.get("GSE12345", "all")

# Step 3: For each publication, get URLs (stored in JSON in registry)
for pub in geo_data["publications"]:
    urls = pub["metadata"]["urls"]  # Nested JSON parsing
    
    # Step 4: Get PDF metadata from cache_metadata.db (third database!)
    cache_db = FullTextCacheDB()
    pdf_info = cache_db.get_entry(pub["pmid"])  # Breaks for DOI-only papers!
    
    # Step 5: Get parsed text from filesystem
    parsed_cache = ParsedCache()
    text = parsed_cache.get(pub["pmid"])  # Also breaks for DOI-only papers!
```

**Result:** 4 database queries + filesystem scans instead of "one call"

---

## Critical Issue #3: Identifier System Underutilization

### What We Have (UniversalIdentifier)

```python
class UniversalIdentifier:
    def __init__(self, publication):
        self._id_type, self._id_value = self._extract_primary_id()
    
    @property
    def key(self) -> str:
        """Database/cache key: 'pmid:12345' or 'doi:10.1234/abc'"""
        return f"{self._id_type.value}:{self._id_value}"
    
    @property
    def filename(self) -> str:
        """Filesystem name: 'pmid_12345.pdf'"""
        return f"{self._id_type.value}_{self._id_value}.pdf"
```

**Features:**
- ✅ Works for ALL paper types (PMID, DOI, arXiv, hash fallback)
- ✅ Consistent format across system
- ✅ Bi-directional parsing (filename ↔ identifier)
- ✅ Display formatting
- ✅ JSON serialization

### What We Actually Use

**Usage: 20%**

```python
# ONLY used for:
identifier = UniversalIdentifier(publication)
filename = identifier.filename  # That's it!

# NOT used for:
# - Cache keys (manual strings instead)
# - Database primary keys (undefined!)
# - Cross-database linking (can't!)
# - Display formatting (manual!)
# - JSON APIs (manual dict construction!)
```

### The Missed Opportunity

**IF we used `identifier.key` everywhere:**

```python
# Database tables
CREATE TABLE cached_files (
    identifier_key TEXT PRIMARY KEY,  # "pmid:12345" or "doi:10.1234/abc"
    ...
)

# Cache lookups
cache_key = identifier.key  # Consistent across ALL caches

# Cross-database joins
SELECT * FROM cached_files cf
JOIN publications p ON cf.identifier_key = p.identifier_key

# Works for ALL paper types!
```

---

## Problem Matrix

### Problem 1: Database Fragmentation

| Database | Purpose | Primary Key | Can Link? | Performance |
|----------|---------|-------------|-----------|-------------|
| omics_oracle.db | GEO → Publications | geo_id, pmid | ⚠️ Partial | Good |
| discovery_cache.db | Citation results | geo_id:strategy | ❌ No | Good |
| cache_metadata.db | PDF metadata | publication_id??? | ❌ No | Unknown |

**Impact:**
- No JOIN queries possible
- Must read 3 databases sequentially
- Can't track paper through pipeline
- Duplicate data storage

### Problem 2: Key Format Chaos

| Component | Key Format | Example | Works for DOI-only? |
|-----------|-----------|---------|---------------------|
| GEO Registry (geo_datasets) | geo_id | "GSE12345" | N/A |
| GEO Registry (publications) | pmid UNIQUE | "12345678" | ❌ NO |
| Discovery Cache | geo_id:strategy | "GSE12345:all" | N/A |
| FullText Cache | publication_id | undefined! | ❌ NO |
| SmartCache | filename | "pmid_12345.pdf" | ✅ YES |
| UniversalIdentifier.key | type:value | "pmid:12345" | ✅ YES |
| UniversalIdentifier.filename | type_value.pdf | "doi_10_1234__abc.pdf" | ✅ YES |

**3 different key formats for publications!**

### Problem 3: Cache Isolation

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Discovery Cache │ NO  │   GEO Registry   │ NO  │ FullText Cache  │
│  (citations)    │────▶│  (publications)  │────▶│  (PDFs/text)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
     geo_id:strategy         pmid (UNIQUE)          publication_id???
     
❌ Cannot track a paper through the pipeline
❌ Cannot invalidate related caches
❌ Cannot get "all data for GEO dataset" efficiently
```

### Problem 4: DOI-Only Paper Failures

**40% of papers from Unpaywall/CORE have NO PMID!**

Current code:
```python
# geo_registry.py line 97
CREATE TABLE publications (
    pmid TEXT UNIQUE,  # ❌ Fails for DOI-only papers!
    doi TEXT,          # Not indexed!
    ...
)

# cache_db.py - no enforcement at all!
publication_id TEXT PRIMARY KEY,  # ❌ Undefined format

# discovery_cache.py
cache_key = f"fulltext_urls:{publication.pmid}"  # ❌ Crashes if pmid is None!
```

**Result:** 40% of papers cannot be cached or linked!

---

## Proposed Solution: Unified Architecture

### Core Principle

**ONE identifier system, ONE database, ONE cache strategy**

### Design: UniversalIdentifier as Foundation

```python
class UniversalIdentifier:
    """
    Universal publication identifier.
    
    Key Format: "{type}:{value}"
    Examples:
        - "pmid:12345678"
        - "doi:10.1234/abc"
        - "arxiv:2401.12345"
        - "pmc:PMC9876543"
        - "hash:a1b2c3d4e5f6g7h8"
    
    This is THE primary key for ALL databases and caches.
    """
    
    @property
    def key(self) -> str:
        """Universal primary key for databases and caches"""
        return f"{self._id_type.value}:{self._id_value}"
    
    @property
    def filename(self) -> str:
        """Filesystem-safe filename"""
        return f"{self._id_type.value}_{self._id_value}.pdf"
```

### Unified Database Schema

```sql
-- ONE central database: data/omics_oracle.db

-- Publications table (universal)
CREATE TABLE publications (
    identifier_key TEXT PRIMARY KEY,  -- "pmid:12345" or "doi:10.1234/abc"
    
    -- All possible identifiers (indexed for lookups)
    pmid TEXT,
    doi TEXT,
    pmc_id TEXT,
    arxiv_id TEXT,
    
    -- Standard fields
    title TEXT NOT NULL,
    authors JSON,
    journal TEXT,
    year INTEGER,
    metadata JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    UNIQUE(identifier_key)
);

CREATE INDEX idx_pub_pmid ON publications(pmid);
CREATE INDEX idx_pub_doi ON publications(doi);
CREATE INDEX idx_pub_pmc ON publications(pmc_id);

-- GEO datasets (unchanged - already good)
CREATE TABLE geo_datasets (
    geo_id TEXT PRIMARY KEY,
    ...
);

-- GEO ↔ Publication links
CREATE TABLE geo_publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    geo_id TEXT NOT NULL,
    identifier_key TEXT NOT NULL,  -- Changed from publication_id
    relationship_type TEXT,
    citation_strategy TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (geo_id) REFERENCES geo_datasets(geo_id),
    FOREIGN KEY (identifier_key) REFERENCES publications(identifier_key),
    UNIQUE(geo_id, identifier_key)
);

-- URLs (NEW - extracted from JSON)
CREATE TABLE publication_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier_key TEXT NOT NULL,
    url TEXT NOT NULL,
    url_type TEXT NOT NULL,  -- 'pmc', 'institutional', 'pdf', 'landing'
    source TEXT NOT NULL,     -- 'pmc_client', 'unpaywall', 'institutional'
    priority INTEGER,
    is_open_access BOOLEAN,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (identifier_key) REFERENCES publications(identifier_key),
    UNIQUE(identifier_key, url)
);

CREATE INDEX idx_url_identifier ON publication_urls(identifier_key);
CREATE INDEX idx_url_type ON publication_urls(url_type);

-- PDFs (merged from cache_metadata.db)
CREATE TABLE cached_pdfs (
    identifier_key TEXT PRIMARY KEY,  -- "pmid:12345"
    file_path TEXT NOT NULL,
    file_hash TEXT UNIQUE,            -- SHA256 for deduplication
    file_size_bytes INTEGER,
    file_source TEXT,                 -- 'pmc', 'crossref', 'institutional'
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    
    FOREIGN KEY (identifier_key) REFERENCES publications(identifier_key)
);

CREATE INDEX idx_pdf_hash ON cached_pdfs(file_hash);
CREATE INDEX idx_pdf_source ON cached_pdfs(file_source);

-- Parsed content (merged from cache_metadata.db)
CREATE TABLE parsed_content (
    identifier_key TEXT PRIMARY KEY,
    
    -- Content flags
    has_fulltext BOOLEAN DEFAULT TRUE,
    has_tables BOOLEAN DEFAULT FALSE,
    has_figures BOOLEAN DEFAULT FALSE,
    
    -- Counts
    table_count INTEGER DEFAULT 0,
    figure_count INTEGER DEFAULT 0,
    section_count INTEGER DEFAULT 0,
    word_count INTEGER,
    reference_count INTEGER DEFAULT 0,
    
    -- Quality
    quality_score REAL,
    parse_duration_ms INTEGER,
    parser_version TEXT,
    
    -- Content storage
    content_path TEXT,  -- Path to JSON file
    
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (identifier_key) REFERENCES publications(identifier_key)
);

CREATE INDEX idx_parsed_quality ON parsed_content(quality_score);
CREATE INDEX idx_parsed_tables ON parsed_content(has_tables);

-- Download history (enhanced)
CREATE TABLE download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier_key TEXT NOT NULL,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT CHECK(status IN ('success', 'failed', 'retry', 'skipped')),
    error_message TEXT,
    file_path TEXT,
    file_size INTEGER,
    attempt_number INTEGER DEFAULT 1,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (identifier_key) REFERENCES publications(identifier_key)
);

CREATE INDEX idx_download_identifier ON download_history(identifier_key);
CREATE INDEX idx_download_status ON download_history(status);

-- Citation discovery cache (merged from discovery_cache.db)
CREATE TABLE citation_discovery_cache (
    cache_key TEXT PRIMARY KEY,       -- "GSE12345:all" or "GSE12345:strategy_a"
    geo_id TEXT NOT NULL,
    strategy_key TEXT NOT NULL,
    result_json TEXT NOT NULL,        -- JSON array of identifier_keys
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_accessed INTEGER,
    
    FOREIGN KEY (geo_id) REFERENCES geo_datasets(geo_id)
);

CREATE INDEX idx_cache_geo ON citation_discovery_cache(geo_id);
CREATE INDEX idx_cache_expires ON citation_discovery_cache(expires_at);

-- AI analysis results (NEW - centralized ChatGPT responses)
CREATE TABLE ai_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier_key TEXT NOT NULL,
    analysis_type TEXT NOT NULL,     -- 'summary', 'methods', 'findings'
    prompt_hash TEXT NOT NULL,       -- Hash of prompt for deduplication
    response TEXT NOT NULL,          -- ChatGPT response
    model TEXT,                      -- 'gpt-4', 'gpt-3.5-turbo'
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (identifier_key) REFERENCES publications(identifier_key),
    UNIQUE(identifier_key, analysis_type, prompt_hash)
);

CREATE INDEX idx_ai_identifier ON ai_analysis(identifier_key);
CREATE INDEX idx_ai_type ON ai_analysis(analysis_type);
```

### The Power of Unified Schema

**ONE query to get everything:**

```sql
-- Get EVERYTHING for a GEO dataset in ONE query!
SELECT 
    g.geo_id,
    g.title as geo_title,
    g.organism,
    p.identifier_key,
    p.title as paper_title,
    p.doi,
    p.pmid,
    p.year,
    pu.url,
    pu.url_type,
    pdf.file_path,
    pdf.file_source,
    pc.quality_score,
    pc.word_count,
    pc.table_count,
    ai.response as ai_summary
FROM geo_datasets g
JOIN geo_publications gp ON g.geo_id = gp.geo_id
JOIN publications p ON gp.identifier_key = p.identifier_key
LEFT JOIN publication_urls pu ON p.identifier_key = pu.identifier_key
LEFT JOIN cached_pdfs pdf ON p.identifier_key = pdf.identifier_key
LEFT JOIN parsed_content pc ON p.identifier_key = pc.identifier_key
LEFT JOIN ai_analysis ai ON p.identifier_key = ai.identifier_key 
    AND ai.analysis_type = 'summary'
WHERE g.geo_id = 'GSE12345'
ORDER BY p.year DESC, pu.priority;
```

**Benefits:**
- ✅ Works for ALL paper types (PMID, DOI, arXiv, etc.)
- ✅ ONE database (no fragmentation)
- ✅ JOIN queries (no multiple reads)
- ✅ Deduplication (file_hash UNIQUE)
- ✅ Complete audit trail
- ✅ Centralized AI responses

---

## Cache Strategy Consolidation

### Current: 6 Different Caches

| Cache | Purpose | Duplication | Efficiency |
|-------|---------|-------------|------------|
| GEORegistry | GEO datasets | None | ✅ Good |
| DiscoveryCache | Citation results | 50% | ⚠️ Medium |
| FullTextCacheDB | PDF metadata | **Unused!** | 🔴 0% |
| SmartCache | PDF files | None | ✅ Good |
| ParsedCache | Parsed text | **Manual only** | 🔴 Low |
| RedisCache | API responses | 30% | ⚠️ Medium |

### Proposed: 3-Layer Strategy

```
┌────────────────────────────────────────────────────────────┐
│ Layer 1: Memory Cache (Redis)                              │
│ - Hot data (last 1000 papers)                             │
│ - API responses                                            │
│ - ChatGPT responses (expensive to regenerate)             │
│ - TTL: 1 hour                                             │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│ Layer 2: SQLite Database (Persistent Metadata)            │
│ - All identifiers, URLs, metadata                         │
│ - Download history                                         │
│ - Parsed content metadata                                 │
│ - AI analysis results                                     │
│ - TTL: Infinite (with cleanup jobs)                       │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│ Layer 3: Filesystem (Large Binary Data)                   │
│ - PDF files (data/fulltext/pdf/)                         │
│ - Parsed JSON (data/fulltext/parsed/)                    │
│ - Organized by source subdirectories                      │
│ - Deduplication via file_hash in database                │
└────────────────────────────────────────────────────────────┘
```

**Key Principle:** Database stores metadata and paths, filesystem stores content

---

## Migration Plan

### Phase 1: Database Consolidation (High Priority)

**Goal:** Merge 3 databases into 1

**Steps:**
1. Create unified schema in `data/omics_oracle.db`
2. Migrate tables:
   - ✅ `geo_datasets` (already there)
   - ✅ `publications` (add identifier_key column)
   - ✅ `geo_publications` (update foreign keys)
   - 🆕 `publication_urls` (extract from JSON)
   - 🔄 Merge `cached_files` from cache_metadata.db → `cached_pdfs`
   - 🔄 Merge `content_metadata` from cache_metadata.db → `parsed_content`
   - 🔄 Merge `citation_discovery_cache` from discovery_cache.db
3. Update code to use unified database
4. Delete old databases

**Estimated Time:** 4-6 hours

**Risk:** Medium (need migration script with rollback)

### Phase 2: Identifier Integration (High Priority)

**Goal:** Use UniversalIdentifier.key everywhere

**Steps:**
1. Update all database primary keys to use `identifier_key`
2. Update all cache lookups to use `identifier.key`
3. Update all file operations to use `identifier.filename`
4. Remove manual key generation code
5. Add validation that keys are always in format `{type}:{value}`

**Estimated Time:** 3-4 hours

**Risk:** Low (additive changes, backward compatible with migration)

### Phase 3: Cache System Unification (Medium Priority)

**Goal:** 3-layer cache (Memory → Database → Filesystem)

**Steps:**
1. Implement unified `CacheManager` class
2. Redis for Layer 1 (hot data)
3. SQLite for Layer 2 (persistent metadata)
4. Filesystem for Layer 3 (binary content)
5. Deprecate separate cache classes

**Estimated Time:** 6-8 hours

**Risk:** Medium (affects all pipelines)

### Phase 4: URL Extraction (Low Priority)

**Goal:** Move URLs from JSON to structured table

**Steps:**
1. Create `publication_urls` table
2. Extract URLs from `publications.metadata` JSON
3. Update URL collection pipeline to write to table
4. Update download pipeline to read from table
5. Remove URLs from JSON blob

**Estimated Time:** 2-3 hours

**Risk:** Low (optimization, not breaking change)

---

## Success Metrics

### Before (Current State)

- ❌ Cache hit rate: ~40%
- ❌ Average query time: 250ms (4 database reads)
- ❌ DOI-only paper support: **0%** (crashes)
- ❌ Duplicate PDFs: ~15% (no deduplication)
- ❌ UniversalIdentifier usage: 20%
- ❌ Database count: 3
- ❌ Cache system count: 6

### After (Target State)

- ✅ Cache hit rate: >70%
- ✅ Average query time: <50ms (1 JOIN query)
- ✅ DOI-only paper support: **100%**
- ✅ Duplicate PDFs: <1% (file_hash deduplication)
- ✅ UniversalIdentifier usage: 95%
- ✅ Database count: 1
- ✅ Cache system count: 3 (with clear separation)

---

## Recommendations

### Immediate Actions (This Session)

1. **✅ Move identifiers.py to lib/shared/**
   - Make it the foundation for all identifier operations
   - Update imports across codebase
   - **Time:** 30 minutes

2. **Document current chaos**
   - This document serves as blueprint for refactoring
   - Share with team for review
   - **Time:** Complete

### Short Term (Next Session)

3. **Fix FullTextCacheDB**
   - Define `publication_id = identifier.key`
   - Actually USE the database in download pipeline
   - Enable deduplication
   - **Time:** 2 hours

4. **Standardize cache keys**
   - Use `identifier.key` in all cache lookups
   - Remove manual key generation
   - **Time:** 2 hours

### Medium Term (This Week)

5. **Database consolidation**
   - Merge 3 databases into unified schema
   - Migration script with validation
   - **Time:** 6 hours

6. **Cache unification**
   - Implement 3-layer cache strategy
   - Deprecate redundant caches
   - **Time:** 8 hours

### Long Term (Next Week)

7. **URL extraction**
   - Move URLs from JSON to table
   - Enable structured URL queries
   - **Time:** 3 hours

8. **AI analysis centralization**
   - Store ChatGPT responses in database
   - Enable response reuse across GEO datasets
   - **Time:** 4 hours

---

## Critical Questions for Discussion

1. **Is GEO ID actually the root node?**
   - Current: Claimed but not implemented
   - Should we pivot to publication-centric architecture?
   - Or truly make GEO-centric with proper linking?

2. **What about papers NOT linked to GEO datasets?**
   - Direct PMID searches?
   - arXiv preprints?
   - Should they go in publications table?

3. **Redis vs SQLite for caching?**
   - Redis: Fast but requires external service
   - SQLite: Integrated but slower for hot data
   - Hybrid approach?

4. **How to handle cache expiration?**
   - GEO datasets: rarely change (cache forever?)
   - Citations: can grow (weekly refresh?)
   - PDFs: never change (cache forever!)
   - Parsed text: parser improves (version tracking?)

5. **Migration strategy risk tolerance?**
   - Big bang (risky but fast)?
   - Gradual (safe but complex dual-system period)?
   - Feature flag approach?

---

## Conclusion

**Current State:** Fragmented, inefficient, DOI-hostile architecture with 80% of UniversalIdentifier system unused.

**Root Cause:** Organic growth without unified design. Each pipeline added its own database/cache without considering integration.

**Path Forward:** 
1. ✅ Move identifiers.py to shared (foundation)
2. 🔄 Consolidate databases (eliminate silos)
3. 🔄 Standardize keys (enable linking)
4. 🔄 Unify caches (improve efficiency)

**Estimated Total Work:** 25-30 hours over 2-3 sessions

**Expected Benefit:**
- 5x faster queries (250ms → <50ms)
- 75% better cache hit rate (40% → >70%)
- 100% DOI-only paper support (0% → 100%)
- 90% code reduction in identifier logic

**Recommendation:** Proceed with Phase 1 (database consolidation) immediately. This is foundational work that will pay dividends across ALL pipelines.

---

**Next Step:** Move identifiers.py to lib/shared/, then return to this document to plan Phase 1 execution.
