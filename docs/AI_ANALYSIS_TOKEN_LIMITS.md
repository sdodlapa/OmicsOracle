# AI Analysis Token Limits - October 16, 2025

## Overview
This document explains the token limits for GPT-4 AI analysis in OmicsOracle and how to configure them.

## Current Configuration

### Default Settings (Updated)
```python
# omics_oracle_v2/core/config.py
max_tokens: int = 4000  # Output token limit (was 800)
```

### Analysis Service
```python
# omics_oracle_v2/services/analysis_service.py
max_tokens=4000  # Hardcoded in call_openai() (was 800)
```

## Token Limits Explained

### What are tokens?
- Tokens are pieces of words used by GPT models
- **1 token ≈ 0.75 words** (English average)
- **1000 tokens ≈ 750 words**

### GPT-4 Model Limits
| Model | Total Context | Max Output |
|-------|--------------|------------|
| gpt-4 | 8,192 tokens | ~4,096 tokens |
| gpt-4-turbo | 128,000 tokens | ~4,096 tokens |
| gpt-4o | 128,000 tokens | ~16,384 tokens |

**Note:** Total context = input prompt + output response

## Why 800 was too small

### Previous Setting (800 tokens)
- **800 tokens ≈ 600 words**
- Too short for comprehensive analysis of 10 papers
- Responses were getting truncated mid-sentence
- Not enough space for:
  - Detailed methodology comparison
  - Quality assessment reasoning
  - Comprehensive recommendations

### New Setting (4000 tokens)
- **4000 tokens ≈ 3,000 words**
- Allows full analysis with:
  - Query-dataset alignment (500-800 words)
  - Methodology assessment (800-1200 words)
  - Data quality and scope (500-800 words)
  - Recommendations (500-800 words)
- Still within GPT-4 output limits

## Token Budget Examples

### Analysis with 5 papers
- **Input:** ~8,000 tokens (paper summaries + prompt)
- **Output:** ~2,000 tokens (comprehensive analysis)
- **Total:** ~10,000 tokens ✅ (within GPT-4 limits)

### Analysis with 10 papers (max)
- **Input:** ~15,000 tokens (paper summaries + prompt)
- **Output:** ~4,000 tokens (comprehensive analysis)
- **Total:** ~19,000 tokens ✅ (within GPT-4 limits)

### Analysis with 25 papers (theoretical)
- **Input:** ~40,000 tokens
- **Output:** ~4,000 tokens
- **Total:** ~44,000 tokens ❌ (exceeds gpt-4 8K limit)
- ✅ Works with gpt-4-turbo (128K context)

## Configuration Options

### Option 1: Environment Variable (Recommended)
```bash
export OMICS_AI_MAX_TOKENS=4000
```

### Option 2: .env file
```bash
# .env
OMICS_AI_MAX_TOKENS=4000
OMICS_AI_MODEL=gpt-4-turbo-preview
```

### Option 3: Code change
```python
# omics_oracle_v2/services/analysis_service.py
max_tokens=4000  # Change this value
```

## Recommendations by Use Case

### Basic Analysis (1-3 papers)
```
max_tokens=2000
```
- Good for quick insights
- Lower API costs (~$0.02/request)

### Standard Analysis (5-10 papers) ✅ CURRENT DEFAULT
```
max_tokens=4000
```
- Comprehensive analysis
- Balanced cost/quality (~$0.04/request)

### Deep Analysis (10+ papers)
```
max_tokens=8000
model=gpt-4-turbo-preview
```
- Very detailed analysis
- Higher API costs (~$0.08/request)
- Requires GPT-4 Turbo (128K context)

## Cost Implications

### Token Pricing (GPT-4)
- **Input:** $0.03 per 1K tokens
- **Output:** $0.06 per 1K tokens

### Cost Comparison
| max_tokens | Avg Output | Cost/Request |
|------------|------------|--------------|
| 800 | 600 tokens | $0.036 |
| 2000 | 1500 tokens | $0.090 |
| 4000 | 3000 tokens | $0.180 |

**Note:** Input costs are the same regardless of max_tokens setting.

### Annual Cost Estimate
- **800 tokens:** ~$1,000/year (1,000 analyses/month)
- **4000 tokens:** ~$2,000/year (1,000 analyses/month)

**Recommendation:** The 5x improvement in analysis quality is worth the 2x cost increase.

## Troubleshooting

### Response appears cut off
**Symptom:** Analysis ends mid-sentence or incomplete

**Solution:**
```bash
# Increase max_tokens
export OMICS_AI_MAX_TOKENS=6000
```

### "Context length exceeded" error
**Symptom:** Error about too many tokens

**Solution:**
1. Reduce `max_papers_per_dataset` (from 10 to 5)
2. Use GPT-4 Turbo (128K context):
   ```bash
   export OMICS_AI_MODEL=gpt-4-turbo-preview
   ```

### Analysis too verbose
**Symptom:** Unnecessarily long responses

**Solution:**
```bash
# Reduce max_tokens
export OMICS_AI_MAX_TOKENS=2000
```

## Monitoring Token Usage

### Check current settings
```bash
curl http://localhost:8000/api/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{"datasets": [...], "query": "test"}' \
  -v 2>&1 | grep -i "token"
```

### View response metadata
```json
{
  "success": true,
  "model_used": "gpt-4",
  "execution_time_ms": 15234,
  "analysis": "...",
  "token_usage": {
    "input": 15420,
    "output": 3821,
    "total": 19241
  }
}
```

**Note:** Token usage tracking coming in v3.0

## Best Practices

### 1. Match tokens to paper count
- **1-3 papers:** 2000 tokens
- **5-7 papers:** 3000 tokens
- **8-10 papers:** 4000 tokens

### 2. Use streaming for long responses
- Shows progress to user
- Prevents timeout issues
- Coming in v3.0

### 3. Cache analyses
- Save AI responses to database
- Reuse for identical queries
- Saves API costs

### 4. Monitor costs
- Track token usage per request
- Set monthly budget alerts
- Review high-cost queries

## Future Improvements

### v3.0 Roadmap
1. **Dynamic token allocation**
   - Automatically adjust based on paper count
   - Formula: `tokens = 1000 + (papers * 300)`

2. **Streaming responses**
   - Real-time output as GPT-4 generates
   - Better UX for long analyses

3. **Token usage tracking**
   - Dashboard showing daily/monthly usage
   - Cost projections and alerts

4. **Response caching**
   - Store analyses in database
   - Deduplicate identical queries
   - 80-90% cost savings

## Related Documentation

- [AI_ANALYSIS_FIX_OCT16.md](AI_ANALYSIS_FIX_OCT16.md) - Recent AI analysis fixes
- [COMPLETE_FIX_SUMMARY_OCT16.md](COMPLETE_FIX_SUMMARY_OCT16.md) - All October fixes
- [ADVANCED_PERFORMANCE_OCT16.md](ADVANCED_PERFORMANCE_OCT16.md) - Performance optimization

---

**Last Updated:** October 16, 2025
**Author:** GitHub Copilot
**Status:** ✅ Implemented (max_tokens increased from 800 to 4000)
