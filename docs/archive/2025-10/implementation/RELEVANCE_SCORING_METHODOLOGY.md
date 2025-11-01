# Relevance Scoring Methodology

## Overview

Papers are scored on **6 factors** to rank them by relevance to a GEO dataset. This document explains how each factor is calculated and why it matters.

---

## Scoring Weights (Total = 100%)

### **Core Relevance Signals (80%)** ⭐ DOMINANT
The most important factors - **what the paper is actually about**:

1. **Keyword Matching: 35%** ⭐⭐⭐ HIGHEST PRIORITY
   - Checks if paper contains keywords from GEO metadata
   - Looks in: title, abstract, author keywords, MeSH terms
   - **Why it matters:** Direct keyword matches = high relevance
   - **Example:** GEO about "DNA methylation" → papers mentioning "methylation" score higher

2. **Content Similarity: 30%** ⭐⭐ VERY IMPORTANT  
   - Fuzzy string matching between GEO and paper content
   - Compares: GEO title/summary vs paper title/abstract
   - **Why it matters:** Similar language = similar research
   - **Example:** GEO about "lead exposure epigenetics" → papers about "heavy metal DNA modifications" score higher

3. **Recency: 15%**
   - Exponential decay: newer papers score higher
   - **Why it matters:** Recent papers cite newer methods/findings
   - **Decay curve:**
     - This year: 1.0
     - 1 year old: 0.9
     - 5 years old: ~0.6
     - 10 years old: ~0.4

### **Context Signals (15%)**
Additional factors that provide context:

4. **Journal Relevance: 10%** 🆕 NEW
   - Scores based on journal name and field
   - **Top journals (1.0):** Nature, Science, Cell, Genome Research, etc.
   - **Field-relevant (0.7-0.9):** Journals containing GEO keywords
   - **Generic biomedical (0.6):** Generic journals
   - **Unknown (0.5):** No journal info
   - **Why it matters:** Field-specific journals = more relevant papers

5. **Citation Count: 5%** ⚠️ LOW WEIGHT
   - Log scale to prevent domination by highly-cited papers
   - **Why so low?**
     - Biased toward older papers (more time to accumulate)
     - Field-specific (some fields cite less)
     - Self-citation inflates numbers
     - Recency already favors impactful papers
   - **Scale:**
     - 0 citations: 0.0
     - 10 citations: ~0.5
     - 100 citations: ~0.75
     - 1000+ citations: ~0.9

### **Minimal Quality Signal (5%)**

6. **Source Quality: 5%** ⚠️ MINIMAL WEIGHT (REDUCED from 15%)
   - **Why reduced?** Source quality is somewhat arbitrary:
     - A bad paper from PubMed is still bad
     - A great paper from Semantic Scholar is still great
     - Metadata completeness already affects keyword/content scores
   - **What it measures:** Mostly metadata completeness
     - Papers with abstracts score higher on content anyway
     - Papers with complete metadata slightly boosted
   - **Scoring:**
     - PubMed/PMC with full metadata: ~1.0
     - OpenAlex/Semantic Scholar with full metadata: ~0.85
     - Any source with missing metadata: reduced score
   - **Why keep it at all?** As a minimal indicator of data quality

---

## Source Quality Explained

### Why Source Quality Matters
Different sources have different strengths:
- **PubMed/PMC:** Manually curated, highest accuracy
- **OpenAlex:** Comprehensive, good metadata
- **Semantic Scholar:** ML-based, can have extraction errors
- **Google Scholar:** Web scraping, variable quality

### Quality Factors
Each source is rated on:

1. **Curation Level**
   - Manual (PubMed): Highest trust
   - Peer-reviewed (PMC): Very high trust
   - Automated (OpenAlex): Good trust
   - ML-based (Semantic Scholar): Moderate trust
   - Scraped (Google Scholar): Lower trust

2. **Metadata Completeness**
   - Does the source typically provide:
     - Complete abstracts?
     - Full author lists?
     - Accurate dates?
     - DOIs and identifiers?

3. **Citation Accuracy**
   - How accurate are the citations?
   - PubMed: 98% accurate (verified)
   - OpenAlex: 90% accurate (algorithm-based)
   - Google Scholar: 75% accurate (can have duplicates)

4. **Actual Completeness** (NEW)
   - We now check EACH paper's metadata:
     - Has abstract? +20%
     - Has authors? +20%
     - Has date? +20%
     - Has DOI? +20%
     - Has journal? +20%
   - Formula: `(base_score × 70%) + (completeness × 30%)`

### Example
**Paper A from PubMed:**
- Base quality: 1.0 (highest tier)
- Has abstract, authors, date, DOI, journal: 5/5 = 100%
- Final score: `(1.0 × 0.7) + (1.0 × 0.3) = 1.0`

**Paper B from Semantic Scholar:**
- Base quality: 0.80
- Missing abstract, has others: 4/5 = 80%
- Final score: `(0.80 × 0.7) + (0.80 × 0.3) = 0.80`

**Paper C from Semantic Scholar (incomplete):**
- Base quality: 0.80
- Only has title and authors: 2/5 = 40%
- Final score: `(0.80 × 0.7) + (0.40 × 0.3) = 0.68` ⬇️ **Lower due to missing metadata**

---

## Why These Weights?

### **Keywords (30%) and Content (25%) dominate:**
- **Combined 55%** = Direct relevance to GEO dataset
- If a paper doesn't mention the relevant topics, it's probably not relevant
- No amount of citations or prestige makes an irrelevant paper relevant

### **Citation count is only 5%:**
- ❌ **OLD approach:** 20% weight on citations
  - Problem: Older papers accumulate more citations
  - Bias: Classic papers from 1990s score higher than relevant papers from 2020s
- ✅ **NEW approach:** 5% weight on citations
  - Citations still matter (highly-cited = impactful)
  - But don't let them dominate scoring
  - Recency (15%) balances this out

### **Source (15%) and Journal (10%) = Quality:**
- **Combined 25%** = Quality indicators
- A well-curated paper from Nature Genetics is more reliable
- But quality doesn't override relevance

---

## Example Scoring

**GEO Dataset: GSE69633**
- Title: "Lead exposure induces changes in 5-hydroxymethylcytosine clusters..."
- Keywords: lead, exposure, epigenetics, methylation, DNA, hydroxymethylcytosine

**Paper 1: "Heavy metals alter DNA methylation patterns in neural cells" (2023)**
- Keywords: 8/10 match → **0.80**
- Content: 60% similar → **0.60**
- Recency: 1 year old → **0.90**
- Source: OpenAlex with full metadata → **0.85**
- Journal: "Epigenetics" → **1.0**
- Citations: 15 → **0.56**
- **TOTAL: `(0.80×0.30) + (0.60×0.25) + (0.90×0.15) + (0.85×0.15) + (1.0×0.10) + (0.56×0.05) = 0.76`** ⭐

**Paper 2: "Machine learning in genomics" (2020)**
- Keywords: 2/10 match → **0.20**
- Content: 15% similar → **0.15**
- Recency: 4 years old → **0.67**
- Source: Semantic Scholar → **0.80**
- Journal: "Bioinformatics" → **1.0**
- Citations: 500 (highly cited!) → **0.87**
- **TOTAL: `(0.20×0.30) + (0.15×0.25) + (0.67×0.15) + (0.80×0.15) + (1.0×0.10) + (0.87×0.05) = 0.42`** ⬇️

**Result:** Paper 1 ranks higher despite fewer citations because it's more relevant!

---

## Trade-offs and Future Improvements

### Current Limitations
1. **Keyword extraction is simple** - Uses regex, not NLP
2. **Content similarity is basic** - SequenceMatcher, not semantic embeddings
3. **Journal list is incomplete** - Only covers major journals
4. **No author reputation** - Doesn't consider author h-index

### Potential Enhancements
1. **Semantic embeddings** - Use BERT/SciBERT for better content matching
2. **Named entity recognition** - Extract genes, proteins, diseases
3. **Author reputation score** - Factor in h-index, citations
4. **Citation context** - How the paper cites the GEO dataset
5. **Field-specific weights** - Different weights for different research areas

---

## Configuration

Weights are configurable:

```python
from omics_oracle_v2.lib.pipelines.citation_discovery import RelevanceScorer, ScoringWeights

# Custom weights
weights = ScoringWeights(
    keyword_match=0.40,      # Increase keyword importance
    content_similarity=0.20,  # Decrease content
    recency=0.10,            # Decrease recency
    source_quality=0.15,
    journal_relevance=0.10,
    citation_count=0.05,
)

scorer = RelevanceScorer(weights)
```

---

## References

**Source Quality Research:**
- [PubMed Data Quality](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7233333/)
- [OpenAlex Coverage Analysis](https://arxiv.org/abs/2205.01833)
- [Semantic Scholar Accuracy](https://arxiv.org/abs/1805.02262)

**Citation Bias:**
- [Citation Age Effect](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0198943)
- [Field-Specific Citation Practices](https://www.nature.com/articles/nature10194)
