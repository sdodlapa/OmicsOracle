# Troubleshooting AI Analysis Errors - October 16, 2025

## Error: "Analysis failed - Please try again"

### Common Causes

#### 1. Context Length Exceeded ⚠️ **MOST COMMON**

**Symptoms:**
- Error message: "Analysis failed"
- Logs show: `context_length_exceeded` or `maximum context length is 8192 tokens`

**Root Cause:**
GPT-4 base model has limited context (8,192 tokens total for input + output)

**Quick Fixes:**

##### Option A: Use GPT-4 Turbo (Recommended)
```bash
# Set environment variable
export OMICS_AI_MODEL=gpt-4-turbo-preview

# Restart server
./start_omics_oracle.sh
```

Benefits:
- ✅ 128,000 token context (16x larger)
- ✅ Supports 10+ papers without issues
- ✅ Slightly faster than GPT-4 base
- ✅ Same quality analysis

Cost:
- ~Same price as GPT-4 base ($0.01/1K input, $0.03/1K output)

##### Option B: Reduce Papers Per Analysis
In dashboard, when clicking "AI Analysis":
- Default: 10 papers (may exceed GPT-4 base limit)
- Try: 5-7 papers (usually works)
- Minimum: 3 papers (always works)

**Current Smart Allocation:**
The system now automatically adjusts:
```python
# GPT-4 base (8K context)
prompt_tokens = 4,665
max_output = 3,300  # Auto-calculated
total = 7,965 ✅

# GPT-4-turbo (128K context)  
prompt_tokens = 4,665
max_output = 4,000  # Full allocation
total = 8,665 ✅
```

#### 2. API Key Issues

**Symptoms:**
- "OpenAI API key not provided"
- "Authentication failed"

**Solution:**
```bash
# Check if key is set
echo $OPENAI_API_KEY

# If not set, add to .env
echo "OPENAI_API_KEY=sk-..." >> .env

# Restart server
./start_omics_oracle.sh
```

#### 3. Network/Timeout Issues

**Symptoms:**
- Takes >60 seconds
- "Request timeout"

**Solutions:**
```bash
# Increase timeout (in .env or export)
export OMICS_AI_TIMEOUT=120

# Or reduce papers to speed up
# (fewer papers = faster analysis)
```

#### 4. Rate Limit Exceeded

**Symptoms:**
- "Rate limit exceeded"
- "Too many requests"

**Solutions:**
1. Wait 1 minute and try again
2. Upgrade OpenAI plan (if making many requests)
3. Check OpenAI dashboard for usage limits

---

## How to Check Logs

```bash
# View last 50 lines
tail -50 logs/omics_api.log

# Search for errors
grep -i "error\|failed" logs/omics_api.log | tail -20

# Watch logs in real-time
tail -f logs/omics_api.log | grep "analyze"
```

---

## Model Comparison

| Model | Context Window | Max Output | Cost | Best For |
|-------|---------------|------------|------|----------|
| gpt-4 | 8,192 | 3,500* | $0.03/1K | 3-7 papers |
| gpt-4-turbo | 128,000 | 4,000 | $0.01/1K | 10+ papers ✅ |
| gpt-4o | 128,000 | 4,000 | $0.005/1K | High volume |

*Auto-adjusted to prevent context overflow

---

## Configuration Examples

### Minimal Setup (Works Always)
```bash
# .env
OPENAI_API_KEY=sk-...
OMICS_AI_MODEL=gpt-4
# Uses smart allocation (3,500 tokens max)
```

### Recommended Setup
```bash
# .env
OPENAI_API_KEY=sk-...
OMICS_AI_MODEL=gpt-4-turbo-preview
OMICS_AI_MAX_TOKENS=4000
OMICS_AI_TEMPERATURE=0.7
```

### High-Volume Setup
```bash
# .env
OPENAI_API_KEY=sk-...
OMICS_AI_MODEL=gpt-4o
OMICS_AI_MAX_TOKENS=4000
OMICS_AI_TIMEOUT=120
```

---

## Testing Your Setup

### Test 1: Small Analysis (Should Always Work)
```bash
# In dashboard:
1. Search for "GSE570"
2. Click "AI Analysis"
3. Change max_papers to 3
4. Click "Analyze"

Expected: ✅ Analysis completes in 10-20 seconds
```

### Test 2: Medium Analysis (Needs GPT-4-turbo or 5-7 papers)
```bash
# In dashboard:
1. Search for "GSE570"
2. Click "AI Analysis"
3. Keep default 10 papers
4. Click "Analyze"

Expected: 
- GPT-4 base: ❌ May fail (context exceeded)
- GPT-4-turbo: ✅ Works fine
```

### Test 3: Check Token Usage
```bash
# View logs after analysis
grep "max_output_tokens" logs/omics_api.log | tail -1

# Example output:
# max_output_tokens=3300 (prompt_chars=18660, est_tokens=4665)
```

---

## Emergency Fixes

### Fix 1: Force Low Token Mode
```python
# In analysis_service.py (line ~610)
max_output_tokens = 2000  # Force low limit
```

### Fix 2: Reduce Papers in Code
```python
# In agents.py (line ~201)
max_papers_per_dataset: int = Field(
    default=5,  # Changed from 10
    ge=1, le=10
)
```

### Fix 3: Upgrade Model in Code
```python
# In config.py (line ~132)
model: str = Field(
    default="gpt-4-turbo-preview",  # Changed from "gpt-4"
)
```

---

## FAQ

### Q: Should I use GPT-4 or GPT-4-turbo?
**A:** Use GPT-4-turbo. It's cheaper, faster, and has 16x more context.

### Q: Why does analysis fail even with 5 papers?
**A:** Check your OpenAI API key and rate limits. The token limit should not be an issue with 5 papers.

### Q: Can I use gpt-3.5-turbo?
**A:** Not recommended. Quality is significantly lower for complex genomics analysis.

### Q: How much does each analysis cost?
**A:** 
- GPT-4: ~$0.15-0.25 per 10-paper analysis
- GPT-4-turbo: ~$0.08-0.12 per 10-paper analysis
- GPT-4o: ~$0.04-0.06 per 10-paper analysis

### Q: What's the optimal number of papers?
**A:**
- **3 papers:** Fast, cheap, basic insights
- **5-7 papers:** Good balance (recommended)
- **10 papers:** Comprehensive (needs GPT-4-turbo)

---

## Related Documentation

- [AI_ANALYSIS_TOKEN_LIMITS.md](AI_ANALYSIS_TOKEN_LIMITS.md) - Token limit details
- [AI_ANALYSIS_FIX_OCT16.md](AI_ANALYSIS_FIX_OCT16.md) - Recent fixes
- [COMPLETE_FIX_SUMMARY_OCT16.md](COMPLETE_FIX_SUMMARY_OCT16.md) - All October fixes

---

**Last Updated:** October 16, 2025  
**Status:** ✅ Smart token allocation implemented  
**Recommended Model:** gpt-4-turbo-preview
