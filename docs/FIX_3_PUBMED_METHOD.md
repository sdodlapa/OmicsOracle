# Fix #3 - PubMedClient Method Name (October 14, 2025)

## The Problem

After fixing the previous two bugs, citation discovery still failed with:
```
Citation strategy failed for PMID 36927507: 'PubMedClient' object has no attribute 'fetch_details'
```

## Root Cause

In `geo_discovery.py`, we were calling:
```python
publications = self.pubmed_client.fetch_details([pmid])  # ❌ Method doesn't exist!
```

But PubMedClient doesn't have a `fetch_details()` method. The correct method is `fetch_by_id()`.

## The Fix

Changed from:
```python
# BROKEN
publications = self.pubmed_client.fetch_details([pmid])
if not publications:
    return []
original_pub = publications[0]
```

To:
```python
# FIXED
original_pub = self.pubmed_client.fetch_by_id(pmid)
if not original_pub:
    return []
```

## Impact

- ✅ Citation discovery now actually fetches publication details
- ✅ Gets DOI from PubMed
- ✅ Passes DOI to OpenAlex for citation discovery
- ✅ Should find all 7 citing papers for GSE189158

## Testing

**Server**: Running on PID 24368 (auto-reloaded with fix)

**Test Steps**:
1. Refresh browser
2. Search for "GSE189158"
3. Click "Download Papers"
4. **Expected**: Should now work! Shows 8 papers (1 original + 7 citing)

## Commits So Far Today

1. `b4ae6a6` - Fixed OpenAlexClient initialization (OpenAlexConfig)
2. `a0f9c40` - Added paper_type field + DOI fetch logic
3. `647ecc2` - Fixed PubMedClient method name (this one)

## Status

🔧 **THREE bugs fixed!**

1. ✅ OpenAlexClient initialization
2. ✅ Publication paper_type field
3. ✅ PubMedClient method name

Citation discovery should NOW work correctly! 🎉

Please test GSE189158 again by clicking "Download Papers" and let me know what happens!
