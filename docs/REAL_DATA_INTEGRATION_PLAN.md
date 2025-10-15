# Real GEO Data Integration Plan

**Date:** October 14, 2025  
**Goal:** Integrate real GEO data into production validation script  
**Current System:** FastAPI backend with existing routes and infrastructure

---

## 📋 Executive Summary

**What We're Doing:**
Replacing mock data in `scripts/production_validation.py` with real GEO API calls to validate the unified database system with actual publications and datasets.

**Why This is Simple:**
- ✅ All infrastructure already exists (unified database, storage, pipelines)
- ✅ FastAPI routing system already configured
- ✅ All components tested individually (Phases 1-5 complete)
- ✅ Only need to wire up existing components in validation script

**What We're NOT Doing:**
- ❌ Not creating a new web interface
- ❌ Not modifying the existing FastAPI API
- ❌ Not changing any routing or middleware
- ❌ Not adding new features

---

## 🏗️ Current Architecture Overview

### **Existing FastAPI Backend**

**Location:** `omics_oracle_v2/api/`

**Structure:**
```
omics_oracle_v2/api/
├── main.py                    # FastAPI app factory (326 lines)
│   ├── create_app()           # Creates FastAPI application
│   ├── lifespan()             # Startup/shutdown manager
│   └── Routers included:
│       ├── /health            # Health checks
│       ├── /api/agents        # Agent operations
│       ├── /api/auth          # Authentication
│       ├── /api/users         # User management
│       ├── /ws                # WebSocket connections
│       └── /metrics           # Prometheus metrics
├── routes/
│   ├── agents.py              # Agent endpoints
│   ├── auth.py                # Auth endpoints
│   ├── health.py              # Health endpoints
│   ├── metrics.py             # Metrics endpoints
│   ├── users.py               # User endpoints
│   └── websockets.py          # WebSocket handlers
├── middleware.py              # Error handling, logging
├── dependencies.py            # Dependency injection
├── config.py                  # API settings
└── static/                    # Static files for dashboard
```

**Startup Script:** `start_omics_oracle.sh`
```bash
# Starts FastAPI server on port 8000
python -m omics_oracle_v2.api.main

# Services:
# - API: http://localhost:8000
# - Dashboard: http://localhost:8000/dashboard  
# - Docs: http://localhost:8000/docs
```

**Current Features:**
- ✅ FastAPI web server with REST API
- ✅ HTML dashboard at `/dashboard`
- ✅ WebSocket support for real-time updates
- ✅ Authentication and rate limiting
- ✅ Prometheus metrics
- ✅ Health checks
- ✅ OpenAPI docs at `/docs`

### **Our New Unified Database System (Phases 1-5)**

**Location:** `omics_oracle_v2/lib/`

**Components:**
```
omics_oracle_v2/lib/
├── database/
│   ├── database.py            # UnifiedDatabase (Phase 1)
│   └── schema.sql             # 8 tables: citations, urls, pdfs, etc.
├── storage/
│   ├── geo_storage.py         # GEOStorage (Phase 2)
│   ├── integrity.py           # SHA256 verification
│   └── queries.py             # DatabaseQueries (15+ methods)
│   └── analytics.py           # Analytics (10+ methods)
├── pipelines/
│   └── coordinator.py         # PipelineCoordinator (Phase 3)
└── integration/
    └── complete_pipeline_integration.py  # Example usage
```

**What It Does:**
1. **P1: Citation Discovery** - Find publications for GEO datasets
2. **P2: URL Discovery** - Find PDF URLs for publications
3. **P3: PDF Acquisition** - Download PDFs
4. **P4: Content Extraction** - Extract and enrich text

**Status:** All phases complete, tested, and committed!

---

## 🎯 Integration Plan: Production Validation Script

### **Current State (Mock Data)**

**File:** `scripts/production_validation.py`

**What It Does Now:**
```python
class ProductionValidator:
    def _get_publications_for_geo(self, geo_id: str, max_papers: int):
        """CURRENT: Returns mock data"""
        # Creates fake PMIDs and publication data
        return [
            {
                "pmid": f"mock_pmid_{i}",
                "title": f"Mock Publication {i}",
                "authors": ["Smith J", "Doe J"],
                # ... more mock fields
            }
            for i in range(max_papers)
        ]
```

**Problem:** Not testing with real GEO datasets, real publications, or real PDFs!

### **Target State (Real Data)**

**What We'll Change:**
```python
class ProductionValidator:
    def __init__(self, db_path, storage_path):
        # ALREADY EXISTS - just initialize
        self.coordinator = PipelineCoordinator(db_path, storage_path)
        self.queries = DatabaseQueries(db_path)
        self.analytics = Analytics(db_path)
        
        # ADD: Real GEO client for fetching datasets
        from omics_oracle_v2.lib.geo import GEOClient
        self.geo_client = GEOClient()
    
    def _get_publications_for_geo(self, geo_id: str, max_papers: int):
        """NEW: Use real GEO API"""
        # Use existing GEO client to fetch real dataset
        dataset_info = self.geo_client.get_dataset(geo_id)
        
        # Extract real publication PMIDs
        publications = []
        for pubmed_id in dataset_info.pubmed_ids[:max_papers]:
            pub_data = self.geo_client.get_publication_metadata(pubmed_id)
            publications.append({
                "pmid": pubmed_id,
                "title": pub_data.get("title", ""),
                "authors": pub_data.get("authors", []),
                "journal": pub_data.get("journal", ""),
                "year": pub_data.get("year", ""),
                "doi": pub_data.get("doi", ""),
                "abstract": pub_data.get("abstract", "")
            })
        
        return publications
```

**That's It!** The rest of the script already works because it uses:
- ✅ `self.coordinator.save_citation_discovery()` - Already works (Phase 3)
- ✅ `self.coordinator.save_url_discovery()` - Already works (Phase 3)
- ✅ `self.coordinator.save_pdf_acquisition()` - Already works (Phase 3)
- ✅ `self.coordinator.save_content_extraction()` - Already works (Phase 3)
- ✅ `self.queries.*` - All 15+ queries already work (Phase 4)
- ✅ `self.analytics.*` - All 10+ analytics already work (Phase 4)

---

## 🔌 How Components Connect

### **Data Flow (Production Validation)**

```
┌─────────────────────────────────────────────────────────────────┐
│  scripts/production_validation.py                               │
│  (Command-line script - NOT part of FastAPI)                    │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Uses components from:
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  omics_oracle_v2/lib/                                           │
│                                                                  │
│  1. GEOClient (lib/geo/)                                        │
│     ↓ Fetches real GEO dataset metadata                        │
│                                                                  │
│  2. PipelineCoordinator (lib/pipelines/)                       │
│     ↓ Executes P1 → P2 → P3 → P4                              │
│                                                                  │
│  3. UnifiedDatabase (lib/database/)                            │
│     ↓ Stores all results in SQLite                             │
│                                                                  │
│  4. GEOStorage (lib/storage/)                                  │
│     ↓ Manages PDF files and manifests                          │
│                                                                  │
│  5. DatabaseQueries + Analytics (lib/storage/)                 │
│     ↓ Generates metrics and reports                            │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Stores data in:
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  data/                                                          │
│  ├── database/production_validation.db    (SQLite database)    │
│  ├── pdfs/by_geo/GSE12345/...            (PDF files)          │
│  └── validation_results/*.json            (Reports)            │
└─────────────────────────────────────────────────────────────────┘
```

### **Separation of Concerns**

**FastAPI Web Application** (`omics_oracle_v2/api/`):
- **Purpose:** Web interface, REST API, dashboard
- **Routes:** `/health`, `/api/agents`, `/api/auth`, `/ws`, etc.
- **Runs:** `python -m omics_oracle_v2.api.main` (port 8000)
- **Users:** Web browsers, API clients, WebSocket clients

**Production Validation Script** (`scripts/production_validation.py`):
- **Purpose:** Batch testing, validation, metrics collection
- **Routes:** NONE (standalone command-line script)
- **Runs:** `python scripts/production_validation.py --papers 100`
- **Users:** Developers, CI/CD, testing

**Both Use Same Core Libraries** (`omics_oracle_v2/lib/`):
- UnifiedDatabase
- GEOStorage
- PipelineCoordinator
- DatabaseQueries
- Analytics

---

## 🛠️ Implementation Steps

### **Step 1: Identify Existing GEO Client** (5 minutes)

**Find existing GEO integration code:**
```bash
# Search for GEO client implementations
grep -r "class.*GEO.*Client" omics_oracle_v2/
grep -r "get_dataset" omics_oracle_v2/ --include="*.py"
```

**Expected locations:**
- `omics_oracle_v2/lib/geo/client.py` (if exists)
- `omics_oracle_v2/integrations/geo/` (if exists)
- Or use existing GEOparse integration from `lib/fulltext/`

### **Step 2: Update Production Validator** (15-30 minutes)

**Modify `scripts/production_validation.py`:**

1. **Add import for GEO client:**
   ```python
   from omics_oracle_v2.lib.geo.client import GEOClient  # Adjust path as needed
   # OR use existing integration:
   from omics_oracle_v2.lib.fulltext.geo_integration import GEODatasetFetcher
   ```

2. **Initialize in `__init__`:**
   ```python
   def __init__(self, db_path: str = "data/database/production_validation.db",
                storage_path: str = "data/pdfs"):
       # ... existing code ...
       
       # Add GEO client
       self.geo_client = GEOClient()  # Or GEODatasetFetcher()
       logger.info("GEO client initialized")
   ```

3. **Replace `_get_publications_for_geo()`:**
   ```python
   def _get_publications_for_geo(self, geo_id: str, max_papers: int) -> List[Dict]:
       """Get real publications for a GEO dataset."""
       try:
           # Fetch real GEO dataset
           dataset = self.geo_client.fetch_dataset(geo_id)
           
           # Extract publication metadata
           publications = []
           pubmed_ids = dataset.get_pubmed_ids()[:max_papers]
           
           for pmid in pubmed_ids:
               # Fetch publication metadata
               pub_data = self.geo_client.fetch_publication(pmid)
               publications.append({
                   "pmid": pmid,
                   "title": pub_data.title,
                   "authors": pub_data.authors,
                   "journal": pub_data.journal,
                   "year": pub_data.year,
                   "doi": pub_data.doi,
                   "abstract": pub_data.abstract
               })
           
           logger.info(f"Found {len(publications)} publications for {geo_id}")
           return publications
           
       except Exception as e:
           logger.error(f"Failed to fetch publications for {geo_id}: {e}")
           return []
   ```

4. **Update P2-P4 to use real implementations:**
   
   Currently they use placeholders. Replace with actual pipeline calls:
   
   ```python
   def _run_p2_urls(self, geo_id: str, pmid: str) -> bool:
       """Execute P2: URL Discovery with REAL URL finder."""
       try:
           # Use real URL collection manager
           from omics_oracle_v2.lib.url_collection import URLCollectionManager
           url_manager = URLCollectionManager()
           
           # Actually find URLs
           urls = url_manager.find_pdf_urls(pmid)
           sources = url_manager.get_sources_queried()
           
           # Save to database (this already works)
           self.coordinator.save_url_discovery(geo_id, pmid, urls, sources)
           return len(urls) > 0
           
       except Exception as e:
           logger.error(f"P2 failed for {pmid}: {e}")
           self.metrics["p2_errors"].append(str(e))
           return False
   
   def _run_p3_pdf(self, geo_id: str, pmid: str) -> bool:
       """Execute P3: PDF Acquisition with REAL download."""
       try:
           # Use real PDF download manager
           from omics_oracle_v2.lib.pdf_download import PDFDownloadManager
           pdf_manager = PDFDownloadManager()
           
           # Get URLs from database
           urls = self.queries.get_urls_for_publication(pmid)
           
           # Actually download PDF
           pdf_path = pdf_manager.download_pdf(pmid, urls)
           
           if pdf_path:
               # Save to database (this already works)
               self.coordinator.save_pdf_acquisition(geo_id, pmid, pdf_path)
               return True
           return False
           
       except Exception as e:
           logger.error(f"P3 failed for {pmid}: {e}")
           self.metrics["p3_errors"].append(str(e))
           return False
   
   def _run_p4_content(self, geo_id: str, pmid: str) -> bool:
       """Execute P4: Content Extraction with REAL extraction."""
       try:
           # Use real text extraction pipeline
           from omics_oracle_v2.lib.text_extraction import TextExtractionPipeline
           extraction_pipeline = TextExtractionPipeline()
           
           # Get PDF path from database
           pdf_info = self.queries.get_pdf_info(pmid)
           
           if not pdf_info:
               return False
           
           # Actually extract content
           extraction_data = extraction_pipeline.extract(pdf_info["pdf_path"])
           
           # Save to database (this already works)
           self.coordinator.save_content_extraction(geo_id, pmid, extraction_data)
           return True
           
       except Exception as e:
           logger.error(f"P4 failed for {pmid}: {e}")
           self.metrics["p4_errors"].append(str(e))
           return False
   ```

### **Step 3: Test with Small Sample** (10 minutes)

```bash
# Test with 5 papers from 1 GEO dataset
python scripts/production_validation.py --papers 5 --geo-datasets 1 \
  --output data/validation_results/real_data_test.json

# Check logs for errors
tail -f logs/production_validation.log

# Verify database
sqlite3 data/database/production_validation.db "SELECT COUNT(*) FROM citations;"
```

### **Step 4: Quick Validation (20-50 papers)** (30-60 minutes)

```bash
# Run with real data
python scripts/production_validation.py --papers 30 --geo-datasets 5 \
  --output data/validation_results/quick_validation.json

# Review results
cat data/validation_results/quick_validation.txt
```

**Success Criteria:**
- ✅ At least 60% end-to-end success rate (real data has failures)
- ✅ All pipeline stages execute without crashes
- ✅ Database populated with real publications
- ✅ PDF files downloaded for successful papers
- ✅ Quality scores calculated correctly

### **Step 5: Full 100-Paper Validation** (2-4 hours)

```bash
# Final production validation
python scripts/production_validation.py --papers 100 --geo-datasets 10 \
  --output data/validation_results/production_validation_100.json

# Monitor progress
tail -f logs/production_validation.log
```

**Success Criteria:**
- ✅ End-to-end success rate: ≥75%
- ✅ Database performance: <50ms per query
- ✅ SHA256 integrity: 100% for successful downloads
- ✅ Quality distribution: Reasonable spread (not all F grades)
- ✅ Comprehensive error logging for failures

---

## 🔍 What We're Using (Existing Code)

### **From Existing Codebase**

**GEO Integration** (likely exists in):
- `omics_oracle_v2/lib/fulltext/geo_*.py`
- `omics_oracle_v2/lib/geo/`
- `omics_oracle_v2/integrations/`

**URL Collection** (likely exists in):
- `omics_oracle_v2/lib/url_collection/`
- `omics_oracle_v2/lib/fulltext/url_finder.py`

**PDF Download** (likely exists in):
- `omics_oracle_v2/lib/pdf_download/`
- `omics_oracle_v2/lib/fulltext/pdf_downloader.py`

**Text Extraction** (likely exists in):
- `omics_oracle_v2/lib/text_extraction/`
- `omics_oracle_v2/lib/fulltext/extractor.py`

**Already Integrated (Phases 1-5)**:
- ✅ `omics_oracle_v2/lib/database/database.py` - UnifiedDatabase
- ✅ `omics_oracle_v2/lib/storage/geo_storage.py` - GEOStorage
- ✅ `omics_oracle_v2/lib/pipelines/coordinator.py` - PipelineCoordinator
- ✅ `omics_oracle_v2/lib/storage/queries.py` - DatabaseQueries
- ✅ `omics_oracle_v2/lib/storage/analytics.py` - Analytics

---

## ❓ FAQ: Why Not Use FastAPI Routes?

**Q: Should we add a new FastAPI route for validation?**

**A: No!** Here's why:

1. **Purpose Mismatch:**
   - **FastAPI routes** = Interactive web API for users
   - **Validation script** = Batch testing tool for developers

2. **Use Cases:**
   - **Web API:** "User searches for GEO datasets via web interface"
   - **Validation:** "Developer tests system with 100 papers overnight"

3. **Execution Model:**
   - **Web API:** Quick responses (<30 seconds), async, multiple concurrent users
   - **Validation:** Long-running (hours), synchronous, single execution

4. **Resource Requirements:**
   - **Web API:** Lightweight, fast, memory-efficient
   - **Validation:** Heavy (downloads 100 PDFs, processes GB of data)

**Analogy:**
- FastAPI = Restaurant kitchen serving customers
- Validation script = Quality inspector testing all recipes in batch

You wouldn't ask customers to wait 3 hours while you test all menu items!

---

## 🎯 Summary

### **What We're Doing:**

1. ✅ **Find existing GEO client code** (5 min)
2. ✅ **Update `production_validation.py`** (30 min)
   - Import GEO client
   - Replace mock data with real API calls
   - Use real URL finder, PDF downloader, text extractor
3. ✅ **Test with 5 papers** (10 min)
4. ✅ **Quick validation with 30 papers** (1 hour)
5. ✅ **Full validation with 100 papers** (2-4 hours)

### **What We're NOT Doing:**

- ❌ Not modifying FastAPI application
- ❌ Not adding new routes or endpoints
- ❌ Not changing middleware or authentication
- ❌ Not creating new web interfaces

### **Why This Works:**

- ✅ All infrastructure already exists (Phases 1-5)
- ✅ All components tested individually
- ✅ Only wiring up existing pieces
- ✅ Production validation script is standalone (not part of web API)

### **Expected Timeline:**

- **Integration:** 30-45 minutes
- **Testing:** 5-10 minutes
- **Quick validation:** 1-2 hours
- **Full 100-paper validation:** 2-4 hours
- **Total:** ~4-6 hours for complete validation

### **Expected Results:**

- **Success rate:** 75-85% (real data has failures - some papers lack PDFs)
- **Database:** 100 publications, 60-85 with full extraction
- **Performance:** <50ms queries, efficient storage
- **Quality:** Reasonable distribution of quality scores
- **Errors:** Well-documented failures for papers without accessible PDFs

---

## 📝 Next Steps

1. **Read this document** ✅ (you are here!)
2. **Locate existing GEO client** (grep search)
3. **Update production_validation.py** (30 min coding)
4. **Test with real data** (5 papers first)
5. **Quick validation** (30 papers)
6. **Full validation** (100 papers)
7. **Generate production readiness report**

**Ready to proceed?** Let me know and I'll start with Step 1: locating the existing GEO client code!
