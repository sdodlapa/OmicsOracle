# 🤖 AI Analysis Quick Reference

## TL;DR - How "Analyze with AI" Works

**In 3 Steps:**

1. **You search** → Get results (e.g., 2 datasets about DNA methylation + Hi-C)
2. **Click "🤖 Analyze with AI"** → Sends to GPT-4 with smart prompt
3. **AI responds** → Expert comparison, insights, recommendations (15-30 sec)

---

## The Magic Prompt Formula

```
User searched for: "{YOUR_QUERY}"

Found {N} datasets:
1. **GSE123** (Relevance: X%)
   Title: ...
   Summary: ... (300 chars)

2. **GSE456** (Relevance: Y%)
   Title: ...
   Summary: ... (300 chars)

Analyze and provide:
1. Overview: Which most relevant and why?
2. Comparison: Methodology differences?
3. Key Insights: Main findings?
4. Recommendations: For basic/advanced/method dev?

Be specific. Cite GSE numbers.
```

**System message:** "You are an expert bioinformatics advisor..."

---

## What GPT-4 Does

1. **Reads** your query: "joint DNA methylation and HiC profiling"
2. **Analyzes** each dataset's title, summary, metadata
3. **Compares** methodologies (sci-L3 vs NOMe-HiC)
4. **Evaluates** relevance (can disagree with search scores!)
5. **Recommends** which dataset for what purpose
6. **Formats** as beautiful markdown

---

## Real Example

**Your Query:** `"joint DNA methylation and HiC profiling"`

**Search Results:**
- GSE281238 (10% relevance) - sci-L3 method
- GSE189158 (5% relevance) - NOMe-HiC method

**GPT-4's Analysis:**
> **GSE189158 is MORE relevant** (despite lower search score)
> 
> Why? NOMe-HiC **specifically** does joint methylation + Hi-C.
> GSE281238 focuses on amplification method, not methylation + Hi-C combo.
>
> **Recommendation:** Use GSE189158 for your research.

**Key Insight:** AI understands **semantic meaning**, not just keywords!

---

## Why This is Powerful

| Traditional Search | AI Analysis |
|-------------------|-------------|
| ✅ Fast (< 1 sec) | ⏱️ Slower (15-30 sec) |
| ✅ Free | 💰 ~$0.03 per analysis |
| ❌ No context | ✅ **Expert guidance** |
| ❌ Just lists datasets | ✅ **Compares & recommends** |
| ❌ Can't explain why | ✅ **Explains reasoning** |
| ❌ No scientific understanding | ✅ **Understands biology** |

---

## Configuration

**Required:**
```bash
export OMICS_AI_OPENAI_API_KEY="sk-..."
```

**Optional:**
```bash
export OMICS_AI_MODEL="gpt-4-turbo-preview"  # or gpt-3.5-turbo
export OMICS_AI_MAX_TOKENS="800"
export OMICS_AI_TEMPERATURE="0.7"
```

---

## Cost & Speed

| Model | Speed | Cost/Analysis | Quality |
|-------|-------|---------------|---------|
| **gpt-4-turbo** | 15-30s | ~$0.03 | ⭐⭐⭐⭐⭐ (Recommended) |
| gpt-4 | 20-40s | ~$0.06 | ⭐⭐⭐⭐⭐ |
| gpt-3.5-turbo | 3-8s | ~$0.002 | ⭐⭐⭐ |

**Budget example:**
- 100 analyses/month with GPT-4-turbo = ~$3
- 1000 analyses/month = ~$30

Set spending limits in OpenAI dashboard!

---

## Output Format

**Markdown structure:**
```markdown
### Overview
Which dataset is most relevant and why...

### Comparison
How datasets differ in methodology...

### Key Insights
- Dataset A: Main finding...
- Dataset B: Novel approach...

### Recommendations
**For Basic Understanding:** Use GSE123...
**For Advanced Analysis:** Use GSE456...
**For Method Development:** Compare both...
```

**Rendered as:**
- Beautiful purple gradient panel
- Proper headings (H3)
- Bold dataset IDs
- Clean paragraphs
- Bullet lists

---

## When to Use

✅ **Use AI Analysis when:**
- Multiple datasets look similar
- Need expert opinion on which to use
- Want to understand methodology differences
- Research is high-stakes (thesis, grant)
- Not familiar with the domain

❌ **Skip AI Analysis when:**
- Only 1 dataset found (obvious choice)
- Just need quick metadata check
- Already expert in the domain
- Want to save API costs
- Need instant results

---

## Advanced Tips

### Customize Prompts

**File:** `omics_oracle_v2/api/routes/agents.py`

Add user context:
```python
analysis_prompt = f"""
User's research area: {user.research_area}
User's expertise: {user.level}

User searched for: "{request.query}"
...
```

Change focus:
```python
Analyze and provide:
1. Statistical Power: Sample size comparison
2. Data Quality: Publication & SRA availability
3. Citation Impact: Which is more cited?
4. Reproducibility: Code/protocols available?
```

### Use Different Models

**GPT-3.5-turbo** (fast & cheap):
```bash
export OMICS_AI_MODEL="gpt-3.5-turbo"
```
- Speed: 3-8 seconds
- Cost: $0.002 per analysis
- Quality: Good (may miss nuances)

**GPT-4** (maximum accuracy):
```bash
export OMICS_AI_MODEL="gpt-4"
```
- Speed: 20-40 seconds
- Cost: $0.06 per analysis
- Quality: Excellent

### Cache Responses

**Future feature:** Save AI responses per query hash
```python
cache_key = f"ai_analysis:{hash(query)}:{dataset_ids}"
if cached := redis.get(cache_key):
    return cached
```
- Saves 100% cost on repeat searches
- Instant results (no API call)

---

## Troubleshooting

**"AI analysis unavailable"**
```
Error: OpenAI API key not configured
```
**Fix:**
```bash
export OMICS_AI_OPENAI_API_KEY="sk-proj-..."
./start_dev_server.sh
```

**"Analysis takes too long"**
```
Waited 60+ seconds...
```
**Fix:** Use GPT-3.5-turbo instead
```bash
export OMICS_AI_MODEL="gpt-3.5-turbo"
```

**"Analysis not relevant"**
```
AI talks about wrong topic
```
**Cause:** Search results not relevant to query
**Fix:** Refine search query first, then analyze

**"Markdown not rendering"**
```
Showing raw text: ### Overview...
```
**Fix:** Clear browser cache, refresh page (marked.js should load)

---

## Code References

| Feature | File | Function |
|---------|------|----------|
| Frontend Button | `semantic_search.html` | Line ~1262 |
| API Call | `semantic_search.html` | `analyzeWithAI()` |
| Backend Endpoint | `api/routes/agents.py` | `analyze_datasets()` |
| Prompt Building | `api/routes/agents.py` | Lines 587-611 |
| OpenAI Call | `lib/ai/client.py` | `_call_llm()` |
| Markdown Parsing | `semantic_search.html` | `marked.parse()` |
| CSS Styles | `semantic_search.html` | Lines 1000-1120 |

---

## Full Documentation

📚 **Detailed Explanation:** `docs/AI_ANALYSIS_EXPLAINED.md`
📊 **Visual Diagram:** `docs/AI_ANALYSIS_FLOW_DIAGRAM.md`
🏗️ **Architecture:** `docs/COMPLETE_ARCHITECTURE_OVERVIEW.md`

---

## Summary

**"Analyze with AI" = Having a senior bioinformatician review your search results**

- 🧠 Understands biology
- 🔍 Evaluates relevance
- 📊 Compares methodologies
- 💡 Provides actionable recommendations
- ⚡ Takes 15-30 seconds
- 💰 Costs ~$0.03 per analysis
- 🎨 Beautiful markdown output

**Start using it today to make better dataset choices!** 🚀
