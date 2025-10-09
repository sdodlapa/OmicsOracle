# ⚠️ Citation Analysis Status Update - Oct 9, 2025

## Current Situation

**Problem:** Google Scholar scraping is being blocked  
**Impact:** Citation analysis workflow cannot function  
**Status:** Temporarily disabled pending alternative implementation

---

## What's Affected

### ❌ NOT Working (Temporarily)
- Finding papers that cite datasets
- Citation context extraction  
- LLM analysis of dataset usage
- Biomarker discovery from citing papers
- Q&A chat about dataset usage
- Dataset impact reports

### ✅ Still Working
- Publication search (PubMed)
- Citation count enrichment (Semantic Scholar)
- PDF downloads
- Full-text extraction
- All other features

---

## Why Semantic Scholar Can't Replace Google Scholar

**Short Answer:** Semantic Scholar provides citation **counts** but not citation **lists** or **contexts**.

### What We Need vs What We Get

| Requirement | Google Scholar | Semantic Scholar | OpenAlex |
|------------|----------------|------------------|----------|
| Find citing papers | ✅ Yes | ❌ No* | ✅ Yes |
| Citation contexts | ✅ Yes | ❌ No | ⚠️ Partial |
| Citation counts | ✅ Yes | ✅ Yes | ✅ Yes |
| Free API | ❌ No (scraping) | ✅ Yes | ✅ Yes |
| Rate limits | 🔴 Heavy | ✅ Generous | ✅ Very generous |
| Reliability | 🔴 Gets blocked | ✅ Stable | ✅ Stable |

*Technically possible but requires 100+ API calls for 100 citations

---

## Current Configuration

```python
# omics_oracle_v2/lib/publications/config.py (Lines 247-254)

enable_pubmed: bool = True                    ✅ Working
enable_scholar: bool = False                  ❌ Disabled (blocked)
enable_citations: bool = False                ❌ Disabled (depends on Scholar)
enable_pdf_download: bool = True              ✅ Working
enable_fulltext: bool = True                  ✅ Working
enable_institutional_access: bool = True      ✅ Working
```

---

## Recommended Solution: OpenAlex

### Why OpenAlex?

**OpenAlex** is a free, open-source alternative to Google Scholar:
- ✅ Official API (no scraping)
- ✅ No authentication needed
- ✅ Very generous rate limits (10,000 req/day)
- ✅ Provides citing papers list
- ✅ Has citation data
- ✅ Sustainable long-term solution

### Implementation Plan

**Phase 1: Basic Integration (1-2 days)**
1. Create `OpenAlexClient` class
2. Implement citing papers discovery
3. Update `CitationAnalyzer` to use OpenAlex
4. Test with real datasets

**Phase 2: Context Enhancement (2-3 days)**
1. Extract contexts from abstracts
2. Extract contexts from PDFs
3. Fallback context generation

**Phase 3: Testing & Optimization (1 day)**
1. Compare results with old Scholar data
2. Optimize performance
3. Update documentation

**Total Time:** 4-6 days

---

## Temporary Workaround

Until OpenAlex is implemented, users can:

1. **Use PubMed search only**
   ```python
   config = PRESET_CONFIGS["minimal"]  # PubMed only
   ```

2. **Get citation counts from Semantic Scholar**
   - Still works!
   - Provides reliable citation metrics

3. **Manual citation analysis**
   - Search Google Scholar manually
   - Record citing papers
   - Use our LLM analysis separately

---

## What We Learned

### ✅ Correctly Using Semantic Scholar
- For citation count enrichment ✅
- As a complement, not replacement ✅
- For reliable metrics ✅

### ❌ Cannot Use Semantic Scholar For
- Finding citing papers list ❌
- Getting citation contexts ❌
- Replacing Google Scholar entirely ❌

### 🎯 Better Solution
- **OpenAlex** for citing papers
- **Semantic Scholar** for citation counts  
- **PDF extraction** for contexts
- Best of all worlds!

---

## Action Items

### Immediate (Today)
- [x] Disable Google Scholar
- [x] Disable citation analysis
- [x] Document limitation
- [x] Analyze Semantic Scholar capabilities
- [x] Identify OpenAlex as solution

### This Week
- [ ] Implement OpenAlexClient
- [ ] Update CitationAnalyzer
- [ ] Add fallback logic
- [ ] Test with datasets
- [ ] Re-enable citation analysis

### Next Week
- [ ] Enhance citation contexts
- [ ] Optimize performance
- [ ] Update documentation
- [ ] Deploy to production

---

## References

- **Analysis Document:** `SEMANTIC_SCHOLAR_ANALYSIS.md`
- **OpenAlex API:** https://docs.openalex.org/
- **Semantic Scholar API:** https://api.semanticscholar.org/
- **Current Config:** `omics_oracle_v2/lib/publications/config.py`

---

## Questions?

**Q: Can we use the system now?**  
A: Yes! Everything except citation analysis works. Use `PRESET_CONFIGS["standard"]` for PubMed + Semantic Scholar enrichment.

**Q: When will citation analysis work again?**  
A: 4-6 days after we start OpenAlex implementation.

**Q: Will it be better than before?**  
A: YES! OpenAlex is more reliable, and we can extract better contexts from PDFs.

**Q: What about costs?**  
A: OpenAlex is completely free, no API key needed.

---

**Status:** 🟡 Partially operational, full functionality restored in ~1 week

