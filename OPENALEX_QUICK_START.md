# OpenAlex Quick Start Guide

**For:** OmicsOracle Users  
**Updated:** October 9, 2025

---

## 🎯 What Changed?

**Before:** Citation analysis was broken (Google Scholar blocked)  
**Now:** Citation analysis works using OpenAlex API  
**Impact:** You can now analyze dataset citations again! 🎉

---

## ⚡ Quick Start (5 minutes)

### Step 1: Update Your Config

```python
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

# NEW - Citations now work!
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_openalex=True,     # ✅ NEW: Free citation source
    enable_citations=True,     # ✅ Re-enabled!
    enable_scholar=False,      # Keep disabled (blocked)
)
```

### Step 2: Use As Before

```python
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline

# Everything works the same way!
pipeline = PublicationSearchPipeline(config)
pipeline.initialize()

# Search works
results = pipeline.search("CRISPR gene editing", max_results=50)

# Citations work now!
if pipeline.citation_analyzer:
    citing_papers = pipeline.citation_analyzer.get_citing_papers(
        results.publications[0],
        max_results=100
    )
    print(f"Found {len(citing_papers)} citing papers")
```

That's it! No other changes needed.

---

## 🚀 Complete Citation Workflow

### Find Papers Citing a GEO Dataset

```python
# 1. Search for dataset paper
config = PublicationSearchConfig(enable_openalex=True, enable_citations=True)
pipeline = PublicationSearchPipeline(config)
pipeline.initialize()

results = pipeline.search("GSE12345", max_results=10)
dataset_paper = results.publications[0]

# 2. Find citing papers (uses OpenAlex automatically)
citing_papers = pipeline.citation_analyzer.get_citing_papers(
    dataset_paper,
    max_results=100
)
print(f"✓ Found {len(citing_papers)} papers citing this dataset")

# 3. Get citation contexts
for citing_paper in citing_papers[:5]:
    contexts = pipeline.citation_analyzer.get_citation_contexts(
        dataset_paper,
        citing_paper
    )
    for ctx in contexts:
        print(f"\nCiting paper: {citing_paper.title}")
        print(f"Context: {ctx.context_text[:200]}...")
```

### Analyze Dataset Usage with LLM

```python
from omics_oracle_v2.lib.publications.citations.llm_analyzer import LLMCitationAnalyzer
from omics_oracle_v2.lib.llm.client import LLMClient

# Initialize LLM analyzer
llm_client = LLMClient(provider="openai", model="gpt-4-turbo-preview")
llm_analyzer = LLMCitationAnalyzer(llm_client)

# Analyze each citing paper
analyses = []
for citing_paper in citing_papers:
    # Get context
    contexts = pipeline.citation_analyzer.get_citation_contexts(
        dataset_paper,
        citing_paper
    )
    
    # Analyze usage
    if contexts:
        analysis = llm_analyzer.analyze_usage(
            dataset_publication=dataset_paper,
            citing_publication=citing_paper,
            citation_context=contexts[0]
        )
        analyses.append(analysis)

# Generate impact report
report = llm_analyzer.generate_impact_report(
    dataset_publication=dataset_paper,
    citing_papers=citing_papers,
    usage_analyses=analyses
)

print(f"\n📊 Impact Report:")
print(f"Total citations: {report.total_citations}")
print(f"Dataset reused: {report.dataset_reuse_count} times")
print(f"Application domains: {len(report.application_domains)}")
print(f"Novel biomarkers: {len(report.novel_biomarkers)}")
```

---

## 💡 Tips & Tricks

### Get 10x Faster Rate Limits

Add your email to get the "polite pool" (10 req/s instead of 1 req/s):

```python
from omics_oracle_v2.lib.publications.clients.openalex import OpenAlexClient, OpenAlexConfig

config = OpenAlexConfig(
    enable=True,
    email="your.email@university.edu"  # ✅ 10x faster!
)
client = OpenAlexClient(config)
```

### Check What's Working

```python
# Verify citation analyzer is initialized
if pipeline.citation_analyzer:
    print("✅ Citations enabled")
    
    # Check sources
    if pipeline.citation_analyzer.openalex:
        print("  - OpenAlex: ✅")
    if pipeline.citation_analyzer.scholar:
        print("  - Google Scholar: ✅")
    if pipeline.citation_analyzer.semantic_scholar:
        print("  - Semantic Scholar: ✅")
else:
    print("❌ Citations disabled")
```

### Track Citation Sources

```python
# See which source provided the citations
for paper in citing_papers:
    print(f"{paper.title}")
    print(f"  Source: {paper.source}")  # Will show "openalex"
    print(f"  Citations: {paper.citations}")
    print(f"  Open Access: {paper.metadata.get('is_open_access', False)}")
```

---

## 🔧 Troubleshooting

### "No citing papers found"

**Possible causes:**
1. Paper has no citations yet (very new)
2. Paper not in OpenAlex database
3. Rate limit hit (wait a few seconds)

**Solutions:**
```python
# Check if paper exists in OpenAlex
from omics_oracle_v2.lib.publications.clients.openalex import OpenAlexClient

client = OpenAlexClient(OpenAlexConfig(enable=True))
work = client.get_work_by_doi(paper.doi)

if work:
    print(f"✓ Paper found: {work.get('cited_by_count')} citations")
else:
    print("✗ Paper not in OpenAlex - try different DOI/title")
```

### "Rate limited by OpenAlex"

**Solution:** Add email for faster rate limits (see Tips above), or wait.

```python
# OpenAlex limits (per account):
# - Without email: 1 request/second
# - With email: 10 requests/second
# - Daily: 10,000 requests/day
```

### "AttributeError: 'NoneType' object has no attribute 'get_citing_papers'"

**Cause:** Citations not enabled in config

**Solution:**
```python
config = PublicationSearchConfig(
    enable_citations=True,  # ✅ Enable this!
    enable_openalex=True,   # ✅ And this!
)
```

---

## 📊 Feature Comparison

| Feature | Google Scholar | OpenAlex | Semantic Scholar |
|---------|---------------|----------|------------------|
| Citing Papers | ✅ (blocked) | ✅ **Working** | ❌ |
| Citation Count | ✅ | ✅ | ✅ |
| Open Access Info | ❌ | ✅ | ❌ |
| Rate Limit | Blocked | 10/s | 1.67/s |
| Daily Limit | N/A | 10,000 | ~2,000 |
| Cost | FREE | FREE | FREE |
| Sustainability | ❌ Low | ✅ High | ✅ High |

**Recommendation:** Use OpenAlex (default)

---

## 🎓 Examples

### Example 1: GEO Dataset Citation Analysis

```python
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline

# Setup
config = PublicationSearchConfig(
    enable_pubmed=True,
    enable_openalex=True,
    enable_citations=True,
)
pipeline = PublicationSearchPipeline(config)
pipeline.initialize()

# Find GEO dataset paper
results = pipeline.search("GSE63310", max_results=5)
geo_paper = results.publications[0]
print(f"Dataset: {geo_paper.title}")

# Find citing papers
citing = pipeline.citation_analyzer.get_citing_papers(geo_paper, max_results=50)
print(f"Found {len(citing)} papers that cite this dataset")

# Analyze domains
domains = {}
for paper in citing:
    # Extract domain from title/abstract (simple version)
    if "cancer" in paper.title.lower():
        domains["cancer"] = domains.get("cancer", 0) + 1
    elif "diabetes" in paper.title.lower():
        domains["diabetes"] = domains.get("diabetes", 0) + 1
    # ... etc

print(f"\nApplication domains:")
for domain, count in domains.items():
    print(f"  {domain}: {count} papers")
```

### Example 2: Compare Citation Sources

```python
# Compare OpenAlex vs Semantic Scholar
from omics_oracle_v2.lib.publications.clients.openalex import OpenAlexClient, OpenAlexConfig
from omics_oracle_v2.lib.publications.clients.semantic_scholar import SemanticScholarClient

openalex = OpenAlexClient(OpenAlexConfig(enable=True))
s2 = SemanticScholarClient()

# Test paper
doi = "10.1038/nature12373"

# OpenAlex - provides citing papers list
citing_papers = openalex.get_citing_papers(doi=doi, max_results=10)
print(f"OpenAlex: {len(citing_papers)} citing papers")

# Semantic Scholar - only provides count
paper = s2.get_paper_by_doi(doi)
if paper:
    citation_count = paper.get("citationCount", 0)
    print(f"Semantic Scholar: {citation_count} citation count")
    print("  (but no citing papers list)")
```

---

## 📚 Learn More

- **Full Documentation:** `docs/phase5-review-2025-10-08/OPENALEX_IMPLEMENTATION_COMPLETE.md`
- **API Reference:** `omics_oracle_v2/lib/publications/clients/openalex.py`
- **Tests:** `test_openalex_implementation.py`

---

## ✅ Checklist

Before using citation analysis:

- [ ] Updated config: `enable_openalex=True, enable_citations=True`
- [ ] Added email to config (for 10x speed boost)
- [ ] Tested with small dataset first
- [ ] Verified citations working: `pipeline.citation_analyzer is not None`

---

**Last Updated:** October 9, 2025  
**Status:** Production Ready ✅
