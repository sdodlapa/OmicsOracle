# 🔍 OmicsOracle: Caching and Result Storage Analysis

## Current State Investigation (June 24, 2025)

### ❌ **Critical Issue Identified:**
AI summaries are showing the **same content for different datasets** - this indicates a fundamental problem with how results are cached and associated with specific datasets.

### 📊 **How Results Are Currently Cached/Stored:**

#### 1. **AI Summary Caching (SQLite-based)**
- **Location**: `src/omics_oracle/services/cache.py`
- **Storage**: SQLite database at `data/cache/ai_summaries.db`
- **Cache Key Generation**: Based on `query + summary_type + max_results`
- **Problem**: Cache keys are **query-level**, not dataset-specific!

```python
def _generate_cache_key(self, query: str, summary_type: str, max_results: int = 10) -> str:
    cache_input = f"{query.lower().strip()}_{summary_type}_{max_results}"
    return hashlib.sha256(cache_input.encode("utf-8")).hexdigest()
```

#### 2. **Result Structure Flow:**
```
Pipeline.process_query()
  ↓
_generate_ai_summaries()
  ↓
result.ai_summaries = {
    "batch_summary": {...},          # ✅ Query-level summary
    "individual_summaries": [        # ❌ ISSUE: Not dataset-specific!
        {"accession": "X", "summary": {...}},
        {"accession": "Y", "summary": {...}},
    ],
    "brief_overview": {...}          # ✅ Single overview
}
```

#### 3. **Web Interface Processing:**
- Individual summaries are accessed by **index** (`individual_summaries[i]`)
- **No verification** that `individual_summaries[i]` belongs to `results.metadata[i]`
- **Fallback logic** uses `brief_overview` when individual summary is missing
- Result: Same summary gets displayed for different datasets!

---

## 🐛 **Root Cause Analysis:**

### **Issue 1: Cache Key Design**
- Cache keys are query-based, not dataset-based
- Same query retrieves same cached summaries regardless of which datasets were found
- When dataset order changes, wrong summaries get matched to wrong datasets

### **Issue 2: Summary-Dataset Association**
- `individual_summaries` array relies on positional matching
- No explicit `geo_id` or `accession` linkage verification
- Fallback to `brief_overview` spreads same content across multiple datasets

### **Issue 3: Missing Metadata Extraction**
- GEO IDs showing as "unknown" due to inconsistent metadata field extraction
- Multiple field names being checked but not finding the right ones
- Original abstracts not being properly extracted

---

## 🔧 **Storage and Caching Locations:**

### **In-Memory Storage:**
1. **Search Analytics**: `search_analytics` dict in `main.py`
   - Recent queries, popular terms, search history
   - **Scope**: Per server instance (lost on restart)

### **Persistent Storage:**
1. **AI Summary Cache**: `data/cache/ai_summaries.db` (SQLite)
   - Query-level AI summaries with TTL
   - **Scope**: Persistent across server restarts
   - **TTL**: 168 hours (1 week) by default

2. **GEO Metadata**: Retrieved fresh from NCBI GEO API
   - **Scope**: No local persistence (fetched on demand)
   - **Caching**: Only at HTTP client level (temporary)

---

## 🎯 **Priority Fixes Needed:**

### **Immediate (Server Stability):**
1. ✅ Fix JavaScript/Python syntax errors in main.py (DONE)
2. 🔧 **Fix AI summary association**: Ensure each dataset gets the correct summary
3. 🔧 **Improve metadata extraction**: Fix GEO ID extraction from multiple possible fields
4. 🔧 **Prevent generic summary reuse**: Add dataset-specific validation

### **Short-term (Enhanced Functionality):**
1. **Add dataset-specific caching**: Cache summaries by `query + geo_id`
2. **Implement summary validation**: Ensure summaries match their datasets
3. **Add internal database connection**: For sample details (pending user requirements)

### **Medium-term (Dual-Summary UI):**
1. **Only after server is stable**: Implement tabbed interface for original vs AI summaries
2. **User experience**: Allow toggling between summary types
3. **Export functionality**: Include both summary types in exports

---

## 🚨 **Next Actions:**

1. **Test current server**: Verify it's working with the syntax fixes
2. **Fix summary-dataset matching**: Ensure each dataset gets its own unique summary
3. **Document database requirements**: Get user input on internal database type/structure
4. **Plan dual-summary UI**: Only after core issues are resolved

This analysis shows that the core issue is architectural - we need to fix how AI summaries are associated with specific datasets before implementing any UI enhancements.
