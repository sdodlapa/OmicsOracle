# Corrected Pipeline Locations - October 14, 2025

## 🎯 The Truth: Where Code ACTUALLY Lives

You were RIGHT to question my analysis! There's significant duplication and my initial mapping was wrong.

---

## 📁 ACTUAL Pipeline Locations (After Investigation)

### **Pipeline 1: Citation Discovery** ✅ CLEAR

**Primary Location**: `omics_oracle_v2/lib/pipelines/citation_discovery/`
- ✅ `geo_discovery.py` - Main discovery class
- ✅ `clients/` - API clients (OpenAlex, PubMed, etc.)
- ✅ Actively used by API

**Duplicate Location**: `omics_oracle_v2/lib/citations/discovery/`
- ⚠️ Older structure, may have duplicate `geo_discovery.py`
- Need to verify which one is canonical

---

### **Pipeline 2: URL Collection** ⚠️ DUPLICATE IMPLEMENTATIONS

**Location 1**: `omics_oracle_v2/lib/enrichment/fulltext/`
- ✅ `manager.py` - FullTextManager (11 sources)
- ✅ `sources/` - All source clients
- ✅ **ACTIVELY USED** by API (line 373 in agents.py)

**Location 2**: `omics_oracle_v2/lib/pipelines/citation_url_collection/` (if exists)
- ❌ Marked as DELETED in Phase 1 cleanup
- Status: Should be archived/removed

**Verdict**: Pipeline 2 lives in `lib/enrichment/fulltext/manager.py`

---

### **Pipeline 3: PDF Download** 🔴 CRITICAL DUPLICATION!

**Location 1**: `omics_oracle_v2/lib/enrichment/fulltext/download_manager.py`
- ✅ PDFDownloadManager class (541 lines)
- ✅ **ACTIVELY USED** by API (line 372 in agents.py)
- ✅ Has `download_with_fallback()` method (correct waterfall)

**Location 2**: `omics_oracle_v2/lib/pipelines/citation_download/download_manager.py`
- ⚠️ PDFDownloadManager class (541 lines - DUPLICATE?)
- ⚠️ NOT imported by API
- ⚠️ Has deprecation warning in `download_batch()` method

**Location 3**: `omics_oracle_v2/lib/storage/pdf/download_manager.py` (may exist?)
- Need to check if this exists

**Verdict**: **DUPLICATION DETECTED** - Need to determine canonical version

---

### **Pipeline 4: Parsing/Enrichment** ❌ INCOMPLETE

**Location**: `omics_oracle_v2/lib/enrichment/fulltext/`
- ⚠️ `pdf_parser.py` - Only 46 lines (basic pypdf)
- ❌ No GROBID integration
- ❌ No enrichment
- ❌ No ChatGPT formatting

**Specs (NOT implemented)**: `docs/planning/archived/original_plans/PDF_PROCESSING_SPEC.md`

---

## 🚨 CRITICAL FINDINGS

### Finding 1: Pipeline 3 Has DUPLICATE Implementations

There are **TWO PDFDownloadManager classes**:

1. **`omics_oracle_v2/lib/enrichment/fulltext/download_manager.py`** ← API uses THIS
2. **`omics_oracle_v2/lib/pipelines/citation_download/download_manager.py`** ← NOT used by API

**Questions**:
- Are they identical?
- Which one is canonical?
- Why does `lib/pipelines/citation_download/` exist if it's not used?

### Finding 2: Pipeline 2 & 3 Share Same Parent Folder

Both Pipeline 2 and Pipeline 3 are in `omics_oracle_v2/lib/enrichment/fulltext/`:
- `manager.py` = Pipeline 2 (URL collection)
- `download_manager.py` = Pipeline 3 (PDF download)

This is why I was confused earlier!

### Finding 3: `lib/pipelines/` Structure is Partially Used

**What EXISTS in `lib/pipelines/`**:
- ✅ `citation_discovery/` - Pipeline 1 (USED)
- ⚠️ `citation_download/` - Pipeline 3 (NOT USED by API)

**What's MISSING**:
- ❌ Pipeline 2 is NOT in `lib/pipelines/`
- ❌ Pipeline 4 is NOT in `lib/pipelines/`

---

## 📊 What the API Actually Imports

From `omics_oracle_v2/api/routes/agents.py` line 372-373:

```python
from omics_oracle_v2.lib.enrichment.fulltext.download_manager import PDFDownloadManager  # Pipeline 3
from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager, FullTextManagerConfig  # Pipeline 2
```

**API does NOT import from `lib/pipelines/citation_download/`!**

---

## 🎯 Corrected Pipeline Map

| Pipeline | Canonical Location | Alternative/Duplicate | API Uses? |
|----------|-------------------|----------------------|-----------|
| **Pipeline 1** | `lib/pipelines/citation_discovery/` | `lib/citations/discovery/` (older?) | ✅ YES |
| **Pipeline 2** | `lib/enrichment/fulltext/manager.py` | ❌ None (was in `pipelines/citation_url_collection/`, deleted) | ✅ YES |
| **Pipeline 3** | `lib/enrichment/fulltext/download_manager.py` | ⚠️ `lib/pipelines/citation_download/download_manager.py` (duplicate?) | ✅ YES (from `enrichment/`) |
| **Pipeline 4** | `lib/enrichment/fulltext/pdf_parser.py` (incomplete) | ❌ None | ⚠️ Basic only |

---

## 🔍 What Needs Verification

### 1. Check Pipeline 3 Duplication

Compare these two files:
```bash
diff omics_oracle_v2/lib/enrichment/fulltext/download_manager.py \
     omics_oracle_v2/lib/pipelines/citation_download/download_manager.py
```

**If identical**: Delete `lib/pipelines/citation_download/` (redundant)  
**If different**: Determine which is correct and consolidate

### 2. Check Pipeline 1 Duplication

Compare:
```bash
diff omics_oracle_v2/lib/pipelines/citation_discovery/geo_discovery.py \
     omics_oracle_v2/lib/citations/discovery/geo_discovery.py
```

**Determine canonical location**

### 3. Check if `lib/storage/pdf/` exists

```bash
ls -la omics_oracle_v2/lib/storage/pdf/
```

---

## 🚀 Recommended Cleanup

### Phase 1: Verify Duplicates
1. Compare Pipeline 3 implementations
2. Compare Pipeline 1 implementations
3. Document which is canonical

### Phase 2: Consolidate
1. Keep ONLY the versions used by API
2. Archive/delete duplicates
3. Update all imports

### Phase 3: Reorganize (Optional)
Move everything to consistent structure:
```
omics_oracle_v2/lib/pipelines/
├── citation_discovery/     # Pipeline 1 ✅
├── url_collection/         # Pipeline 2 (move from enrichment/fulltext/manager.py)
├── pdf_download/           # Pipeline 3 (move from enrichment/fulltext/download_manager.py)
└── text_enrichment/        # Pipeline 4 (implement GROBID, etc.)
```

---

## 📝 My Original Error

I said:
> "Pipelines 2, 3, and 4 share the same folder: `omics_oracle_v2/lib/enrichment/fulltext/`"

This was PARTIALLY correct:
- ✅ Pipeline 2 IS in `lib/enrichment/fulltext/manager.py`
- ✅ Pipeline 3 IS in `lib/enrichment/fulltext/download_manager.py`
- ✅ Pipeline 4 IS in `lib/enrichment/fulltext/pdf_parser.py`

**BUT I MISSED**:
- ⚠️ Pipeline 3 ALSO exists in `lib/pipelines/citation_download/` (duplicate!)
- ⚠️ `lib/pipelines/` structure exists but is only partially used

---

## ✅ Summary

**You were RIGHT to question my analysis!**

1. **Pipeline 3 has duplicate implementations** - Need to verify which is canonical
2. **API uses `lib/enrichment/fulltext/` versions**, NOT `lib/pipelines/citation_download/`
3. **`lib/pipelines/` structure exists but is incomplete**:
   - Has Pipeline 1 ✅
   - Has Pipeline 3 (duplicate, not used) ⚠️
   - Missing Pipeline 2 ❌
   - Missing Pipeline 4 ❌

**Next Steps**: Compare duplicate files and consolidate to single canonical location for each pipeline.
