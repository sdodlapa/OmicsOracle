# Google Scholar Access & Citation Metrics Guide

**Issue:** Citations showing as 0 - PubMed doesn't provide citation counts
**Solution:** Enable Google Scholar (currently blocked/rate-limited)

---

## 🔍 Current Status

**PubMed:** ✅ Working - Provides publications but **NO citation counts**
**Google Scholar:** ❌ Blocked - "Cannot Fetch from Google Scholar"

**Result:** Citations show as 0 for all publications

---

## 📊 Why Citations Are Missing

| Feature | PubMed | Google Scholar |
|---------|--------|----------------|
| Publications | ✅ 35M+ biomedical | ✅ All academic |
| **Citation Counts** | ❌ **NO** | ✅ **YES** |
| PDFs | Limited | Often available |

**Key:** Google Scholar is the ONLY source providing citation metrics

---

## 🚀 Solutions (Ranked by Ease)

### Option 1: Wait 30-60 Minutes ⏰ (EASIEST - Try First!)

Google blocks are temporary. Test every 30 min:

```bash
PYTHONHTTPSVERIFY=0 python -c "
from scholarly import scholarly
result = next(scholarly.search_pubs('cancer'))
print(f'Citations: {result.get(\"num_citations\", 0)}')
"
```

✅ **Free** | ⏱️ **30-60 min** | 🎯 **High success rate**

---

### Option 2: Slow Down Requests 🐌 (FREE - Quick Fix!)

Current: 3 seconds between requests (too fast)
Solution: Increase to 10 seconds

**Method A: Environment Variable**
```bash
# Add to .env
SCHOLAR_RATE_LIMIT_SECONDS=10.0

# Restart
./start_omics_oracle_ssl_bypass.sh
```

**Method B: Edit Config**
```python
# omics_oracle_v2/lib/publications/config.py
# Line ~85
rate_limit_seconds: float = Field(
    10.0,  # Change from 3.0
    ...
)
```

✅ **Free** | ⏱️ **5 min** | 🎯 **Medium success**

---

### Option 3: Use Proxy Service 🔒 (PRODUCTION - Most Reliable!)

**Recommended: ScraperAPI**
- Website: https://www.scraperapi.com
- Cost: $49/month (100K requests)
- Success rate: 95%+

**Setup:**

1. **Sign up** for ScraperAPI
2. **Get API key** from dashboard
3. **Install dependencies:**
   ```bash
   pip install scholarly requests[socks]
   ```

4. **Configure:**
   ```bash
   # Add to .env
   SCHOLAR_USE_PROXY=true
   SCHOLAR_PROXY_KEY=your_api_key_here
   ```

5. **Modify** `omics_oracle_v2/lib/publications/clients/scholar.py`:
   ```python
   import os
   from scholarly import scholarly, ProxyGenerator

   # In __init__ method
   if os.getenv("SCHOLAR_USE_PROXY") == "true":
       pg = ProxyGenerator()
       pg.ScraperAPI(os.getenv("SCHOLAR_PROXY_KEY"))
       scholarly.use_proxy(pg)
       logger.info("Google Scholar proxy enabled")
   ```

6. **Restart services**

💰 **$49/mo** | ⏱️ **30 min setup** | 🎯 **Very high success**

---

### Option 4: Semantic Scholar API 📚 (FREE Alternative!)

Instead of Google Scholar, use Semantic Scholar:

- **Free tier:** 100 requests/5 min
- **Has citation counts**
- **Easier to use** (official API)

**Quick Implementation:**

```python
import requests

def get_semantic_scholar_citations(doi):
    """Get citations from Semantic Scholar API"""
    url = f"https://api.semanticscholar.org/v1/paper/{doi}"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        return data.get('citationCount', 0)
    return 0

# Use after PubMed search to enrich with citations
for pub in pubmed_results:
    if pub.doi:
        pub.citations = get_semantic_scholar_citations(pub.doi)
```

✅ **Free** | ⏱️ **2 hours coding** | 🎯 **Reliable**

---

## 🎯 Recommended Action Plan

### Today (Next 2 Hours):

1. **Wait 30 minutes** ⏰
   ```bash
   # Test if unblocked
   PYTHONHTTPSVERIFY=0 python -c "from scholarly import scholarly; print(next(scholarly.search_pubs('test')))"
   ```

2. **If still blocked, slow down to 10s** 🐌
   - Edit config file
   - Restart dashboard
   - Test again

### This Week:

3. **Sign up for ScraperAPI** 🔒
   - $49/month trial
   - Integrate proxy
   - Production-ready solution

### Alternative (If Budget Constrained):

4. **Implement Semantic Scholar API** 📚
   - Free forever
   - Requires coding (~2 hours)
   - Good citation coverage

---

## 📝 Testing Commands

### Check if Scholar unblocked:
```bash
PYTHONHTTPSVERIFY=0 python test_search_debug.py
# Look for: Sources used: ['pubmed', 'google_scholar']
```

### Test in Dashboard:
1. Check **both PubMed and Google Scholar**
2. Search: "cancer"
3. Expected: Citations > 0

---

## ✅ Expected Results After Fix

**Before:**
```
Title: NOMe-HiC...
Citations: 0  ❌
```

**After:**
```
Title: NOMe-HiC...
Citations: 15  ✅
```

---

## 🆘 Quick Reference

| Solution | Cost | Time | When to Use |
|----------|------|------|-------------|
| **Wait** | Free | 30 min | Try first! |
| **Slow down** | Free | 5 min | If blocked again |
| **Proxy** | $49/mo | 30 min | Production |
| **Semantic Scholar** | Free | 2 hrs | Budget option |

---

**Next Step:** Try Option 1 (wait 30 min) right now! Test with the command above.
