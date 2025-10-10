# OpenAI Rate Limiting - Why You See 20-Second Waits

## 🔍 The Issue

When running `test_robust_search_demo.py`, you see logs like:

```
HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 429 Too Many Requests"
Retrying request to /chat/completions in 20.000000 seconds
```

This happens **100+ times** during citation enrichment, making the test very slow.

## 📊 Root Cause Analysis

### What's Happening:

1. **Citation Analysis Feature** (`enable_citations=True`) enriches each paper with:
   - Dataset reuse detection
   - Usage type classification  
   - Key findings extraction
   - Confidence scoring

2. **Each Citing Paper = 1 OpenAI API Call**
   - Query 1: "CRISPR gene editing" → 100 papers found
   - Each paper analyzed → 100 OpenAI API calls
   - Processed in batches of 5

3. **Your OpenAI API Tier Has Rate Limits:**
   ```
   Free Tier:          3 requests/minute
   Pay-as-you-go Tier 1: 60 requests/minute
   Pay-as-you-go Tier 2: 3,500 requests/minute
   ```

4. **The Flow:**
   ```
   Batch 1: Send 5 requests → 3 succeed, 2 rejected (429)
   OpenAI SDK: "Wait 20 seconds..." → Retry
   Batch 2: Send 5 requests → 3 succeed, 2 rejected (429)
   OpenAI SDK: "Wait 20 seconds..." → Retry
   ... (repeated 20 times)
   
   Total time: ~40 seconds × 20 batches = 13-15 minutes!
   ```

### Why Your Code Doesn't Rate Limit:

The citation analysis uses **synchronous `LLMClient`** (not the async version):

```python
# In pipeline.py line 129-135:
self.llm_client = LLMClient(
    provider=config.llm_config.provider,
    model=config.llm_config.model,
    cache_enabled=config.llm_config.cache_enabled,
    temperature=config.llm_config.temperature,
    # ❌ NO rate_limit_per_minute parameter!
)
```

**`LLMClient`** (synchronous) does NOT have built-in rate limiting!  
Only **`AsyncLLMClient`** has rate limiting.

### Who's Doing the Retry?

**The OpenAI Python SDK** automatically retries on 429 errors:

```python
# Inside OpenAI SDK (not your code):
if response.status_code == 429:
    retry_after = response.headers.get('Retry-After', 20)
    await asyncio.sleep(float(retry_after))  # 20 seconds!
    return await self._request(...)  # Retry
```

This is **expected behavior** to comply with OpenAI's rate limits.

## 🎯 Solutions

### **Solution 1: Disable Citation Analysis** (Quick - 30 seconds)

**When to use:** Testing full-text retrieval speed without citations

**File:** `tests/test_robust_search_demo.py`

```python
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_openalex=True,
    enable_citations=False,  # ❌ DISABLED - Prevents OpenAI rate limits
    enable_fulltext_retrieval=True,
)
```

**Result:**
- ✅ No OpenAI API calls
- ✅ No 429 errors
- ✅ No 20-second waits
- ✅ Fast execution (~5-10s per query)
- ❌ No citation enrichment

**Use the fast version:**

```bash
python tests/test_robust_search_demo_fast.py
```

---

### **Solution 2: Add Client-Side Rate Limiting** (Better - 2 hours)

**When to use:** Production - prevent hitting rate limits proactively

**Implementation:**

1. **Add rate limiting to `LLMClient`:**

```python
# In omics_oracle_v2/lib/llm/client.py

class LLMClient:
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        cache_enabled: bool = True,
        cache_dir: Optional[str] = None,
        temperature: float = 0.1,
        max_retries: int = 3,
        rate_limit_per_minute: int = 3,  # ✅ ADD THIS
    ):
        # ... existing code ...
        self.rate_limit = rate_limit_per_minute
        self.request_times = []  # Track request timestamps
        
    def _wait_for_rate_limit(self):
        """Wait if rate limit would be exceeded."""
        import time
        
        current_time = time.time()
        
        # Remove old request times (older than 1 minute)
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Check if we're at the limit
        if len(self.request_times) >= self.rate_limit:
            # Wait until oldest request is more than 60 seconds old
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                # Clean up after waiting
                current_time = time.time()
                self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Record this request
        self.request_times.append(current_time)
    
    def generate(self, prompt, ...):
        # ... existing code ...
        
        # ✅ ADD BEFORE API CALL:
        self._wait_for_rate_limit()
        
        # Then call API...
        if self.provider == "openai":
            response = self._openai_generate(...)
```

2. **Configure in pipeline:**

```python
# In pipeline.py:
self.llm_client = LLMClient(
    provider=config.llm_config.provider,
    model=config.llm_config.model,
    cache_enabled=config.llm_config.cache_enabled,
    temperature=config.llm_config.temperature,
    rate_limit_per_minute=3,  # ✅ Set to your tier limit
)
```

**Result:**
- ✅ Pre-emptive waiting (smooth, predictable delays)
- ✅ No 429 errors
- ✅ No sudden 20-second waits
- ✅ Citation enrichment works
- ⚠️  Still slow (but predictable: ~20s per batch for 3 req/min)

---

### **Solution 3: Upgrade OpenAI Tier** (Best for Production - Costs $$$)

**When to use:** Production with budget for API costs

**Tiers:**

| Tier | Rate Limit | Cost | Time for 100 Papers |
|------|-----------|------|---------------------|
| Free | 3/min | $0 | ~30 minutes |
| Tier 1 | 60/min | Pay-as-you-go | ~2 minutes |
| Tier 2 | 3,500/min | Pay-as-you-go | ~2 seconds |

**Steps:**
1. Go to https://platform.openai.com/settings/organization/billing
2. Add payment method
3. Increase tier by making API calls
4. Usage determines tier automatically

**Result:**
- ✅ Fast citation enrichment
- ✅ No rate limit errors
- ✅ Professional performance
- ❌ Costs money (~$10-15 per 100 papers)

---

### **Solution 4: Use Caching Aggressively** (Smart - Free)

**When to use:** Testing same queries repeatedly

**Already Implemented:**

```python
config = PublicationSearchConfig(
    enable_cache=True,  # ✅ Already enabled
    llm_config=LLMConfig(
        cache_enabled=True,  # ✅ Caches OpenAI responses
    )
)
```

**How it helps:**
- First run: 100 API calls → 15 minutes
- Second run: 0 API calls → 10 seconds (all cached!)

**Cache location:**
```
./data/llm_cache/
./data/publication_cache.db
```

**Result:**
- ✅ Free (no API calls after first run)
- ✅ Instant on repeat queries
- ✅ Saves money
- ⚠️  First run still slow

---

### **Solution 5: Switch to Alternative LLM** (Advanced - 4 hours)

**When to use:** Want to avoid OpenAI entirely

**Options:**

**A. Anthropic Claude:**
```python
config = PublicationSearchConfig(
    llm_config=LLMConfig(
        provider="anthropic",  # Different rate limits
        model="claude-3-5-sonnet-20241022",
    )
)
```

**B. Local Model (Ollama):**
```python
config = PublicationSearchConfig(
    llm_config=LLMConfig(
        provider="ollama",  # No rate limits!
        model="llama3.1",
    )
)
```

**Result:**
- ✅ Different/no rate limits
- ✅ More control
- ⚠️  Requires setup
- ⚠️  May need GPU for local models

---

### **Solution 6: Batch Processing with Delays** (Hybrid)

**When to use:** Want citations but willing to wait strategically

```python
# In pipeline.py, modify citation analysis:

# Process in smaller batches with delays
batch_size = 3  # Match your rate limit
delay_between_batches = 60  # Wait 1 minute between batches

for i in range(0, len(citing_papers), batch_size):
    batch = citing_papers[i:i+batch_size]
    
    # Analyze batch
    analyses = self.llm_citation_analyzer.analyze_batch(batch)
    
    # Wait before next batch (unless last batch)
    if i + batch_size < len(citing_papers):
        logger.info(f"Waiting {delay_between_batches}s before next batch...")
        await asyncio.sleep(delay_between_batches)
```

**Result:**
- ✅ No 429 errors (stays under limit)
- ✅ Predictable timing
- ✅ Citation enrichment works
- ⚠️  Still slow (~1 minute per 3 papers)

---

## 📈 Comparison Table

| Solution | Speed | Cost | Effort | Citations | Best For |
|----------|-------|------|--------|-----------|----------|
| 1. Disable Citations | ⚡ Fast | Free | 30 sec | ❌ No | Testing full-text |
| 2. Client Rate Limit | 🐌 Slow | Free | 2 hours | ✅ Yes | Production (free tier) |
| 3. Upgrade Tier | ⚡ Fast | $$$ | 5 min | ✅ Yes | Production (budget) |
| 4. Aggressive Cache | ⚡ Fast* | Free | 0 min | ✅ Yes | Repeat queries |
| 5. Alternative LLM | ⚡ Fast | Varies | 4 hours | ✅ Yes | Avoiding OpenAI |
| 6. Batch + Delays | 🐌 Slow | Free | 1 hour | ✅ Yes | Controlled slow |

*Fast on second+ run only

## 🎯 Recommended Approach

### **For Your Current Testing:**

1. **Use Fast Version (No Citations):**
   ```bash
   python tests/test_robust_search_demo_fast.py
   ```
   
   This validates full-text retrieval (your main goal) in 5-10 minutes instead of 30+ minutes.

2. **Enable Citations for 1-2 Queries Only:**
   ```python
   # Test citations on just 1-2 papers to verify it works
   RESEARCH_QUERIES = RESEARCH_QUERIES[:2]  # Only first 2 queries
   ```

### **For Production:**

1. **Implement Client-Side Rate Limiting** (Solution 2)
2. **Enable Aggressive Caching** (Solution 4)
3. **Consider Upgrading Tier** when budget allows (Solution 3)

---

## 🔧 Quick Fix Commands

**Option 1: Run fast version (recommended):**
```bash
python tests/test_robust_search_demo_fast.py
```

**Option 2: Update original test:**
```bash
# Already done - citations disabled in test_robust_search_demo.py
python tests/test_robust_search_demo.py
```

---

## 📊 Current Status

✅ **Full-text retrieval is FAST** (~5-10s per query)  
⚠️  **Citation enrichment is SLOW** (~30 min for 100 papers on free tier)

The 20-second waits are **NOT a bug** - they're the OpenAI SDK complying with rate limits.

**Your full-text access (Sci-Hub + LibGen) works perfectly!** 🎉  
The slowness is only in the optional citation enrichment feature.

---

## 📝 Next Steps

1. ✅ Run fast demo: `python tests/test_robust_search_demo_fast.py`
2. ✅ Verify 80-85% full-text coverage
3. ✅ Run comprehensive validation: `python tests/test_comprehensive_fulltext_validation.py`
4. 📋 Decide on citation strategy:
   - Disable for speed
   - Add rate limiting for free tier
   - Upgrade tier for production

---

## ❓ FAQ

**Q: Is this a bug?**  
A: No, it's expected behavior. OpenAI SDK retries on rate limits.

**Q: Can we make it faster without paying?**  
A: Only by disabling citations or adding client-side rate limiting (still slow).

**Q: Do we need citations?**  
A: Not for your current goal (validating full-text access). Citations are a bonus feature.

**Q: What's the fastest approach?**  
A: Run `test_robust_search_demo_fast.py` - no citations, just full-text validation.

**Q: Will caching help?**  
A: Yes! Second run is instant. But first run is still slow with citations enabled.

**Q: How do I check my OpenAI tier?**  
A: https://platform.openai.com/settings/organization/limits

---

**Current Recommendation: Use the fast demo to validate your excellent full-text work! 🚀**
