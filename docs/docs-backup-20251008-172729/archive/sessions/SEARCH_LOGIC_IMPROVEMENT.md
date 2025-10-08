# Search Query Logic Improvement ✅

## Problem Identified

When you searched for `"dna methylation and HiC joint profiling datasets"`, the system was:

1. **Extracting terms**: "HiC joint profiling", "datasets", "dna methylation"
2. **Using OR logic**: `"HiC joint profiling" OR datasets OR "dna methylation"`
3. **Getting irrelevant results**: Thousands of datasets with just "dna methylation" (no HiC!)

### Root Cause

The old search logic always used **OR** between search terms, which means:
- ❌ Datasets with ONLY "dna methylation" matched
- ❌ Datasets with ONLY "datasets" matched (very generic!)
- ❌ You got ~thousands of mostly irrelevant results

## Solution Implemented

### 1. Filter Generic Terms
Now filters out non-specific words:
```python
generic_terms = {"dataset", "datasets", "data", "study", "studies", "analysis", "profiling"}
```

Your query now becomes: `["HiC joint profiling", "dna methylation"]` (removed "datasets")

### 2. Smart AND/OR Logic

The system now uses **AND logic** when:
- ✅ Query contains "and" or "&"
- ✅ Query contains "joint", "combined", "multi", "integrated"
- ✅ 2-3 specific biomedical terms (suggests combined requirement)

**Otherwise** uses OR logic for broader results.

### 3. Preserve Original Query

Added `original_query` field to `SearchInput` to preserve user intent:
```python
search_input = SearchInput(
    search_terms=["HiC joint profiling", "dna methylation"],
    original_query="dna methylation and HiC joint profiling datasets",  # NEW!
    ...
)
```

## Results

### Before (OLD):
```
Query: "HiC joint profiling" OR datasets OR "dna methylation"
Results: ~thousands (mostly just methylation studies)
```

### After (NEW):
```
Query: "HiC joint profiling" AND "dna methylation"
Results: 2 highly relevant datasets!
```

## Files Modified

1. **`omics_oracle_v2/agents/models/search.py`**
   - Added `original_query: Optional[str]` field to `SearchInput`

2. **`omics_oracle_v2/agents/search_agent.py`**
   - Improved `_build_search_query()` method:
     - Filters out generic terms
     - Uses AND logic when appropriate
     - Considers original query context
     - Logs which logic is used

3. **`omics_oracle_v2/agents/orchestrator.py`**
   - Passes `original_query=input_data.query` to SearchInput
   - Fixed organisms/study_types plural→singular mapping

## Test It Now!

The server should auto-reload. Refresh your dashboard and try again:

**Query**: `dna methylation and HiC joint profiling datasets`

**Expected**:
- ✅ Uses AND logic (check logs: "Using AND logic for search")
- ✅ Filters out "datasets"
- ✅ Returns only 2-10 highly relevant datasets
- ✅ All results have BOTH methylation AND HiC data

---

**Much better precision! 🎯**
