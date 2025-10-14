# Simplified Relevance Scoring - Design Document

**Date:** October 14, 2025  
**Status:** Implemented, ready for testing  
**Philosophy:** Simplicity over complexity - focus on what matters

---

## Overview

After extensive discussion and iteration, we've simplified the relevance scoring system from a complex 6-factor model to a clean **4-factor model** that focuses on the essentials:

1. **What the paper discusses** (content + keywords = 70%)
2. **When it was published** (recency = 20%)  
3. **Its impact** (citations = 10%)

### Why Simplify?

**Removed factors:**
- ❌ **Source Quality (was 5-15%)**: Too arbitrary. A bad paper from PubMed is still bad. A great paper from Semantic Scholar is still great.
- ❌ **Journal Relevance (was 10%)**: Added complexity without clear benefit. Prestigious journals don't guarantee relevance.

**Result:** Cleaner, more transparent, easier to understand and maintain.

---

## Scoring Weights (Total = 100%)

### 1. Content Similarity: 40% ⭐⭐⭐ PRIMARY SIGNAL

**What it measures:** How similar is the paper's content to the GEO dataset description?

**Method:** Fuzzy string matching (SequenceMatcher) between:
- GEO title + summary
- Paper title + abstract

**Why it's #1:** If a paper discusses the same topics using similar language, it's highly relevant regardless of keywords, citations, or prestige.

**Example:**
- GEO: "Lead exposure effects on DNA methylation in children"
- Paper: "Heavy metal environmental exposure alters epigenetic marks in pediatric populations"
- Similarity: HIGH (different words, same concept)

---

### 2. Keyword Matching: 30% ⭐⭐ SECONDARY SIGNAL

**What it measures:** Does the paper contain keywords from the GEO metadata?

**Sources checked:**
- Paper title
- Paper abstract
- Author-provided keywords
- MeSH terms (if available)

**Scoring:** Proportion of GEO keywords found in paper

**Why it's important:** Direct keyword matches are strong signals of topical overlap.

**Example:**
- GEO keywords: ["methylation", "lead", "children", "epigenetics"]
- Paper contains: 3 out of 4 keywords
- Score: 0.75 (75%)

**Why it's not #1:** Keywords can be missed due to:
- Synonyms ("pediatric" vs "children")
- Different terminology ("DNA modification" vs "methylation")
- Incomplete extraction from GEO

---

### 3. Recency: 20% ⏰ TEMPORAL RELEVANCE

**What it measures:** How recent is the publication?

**Philosophy:** Sharp 5-year cutoff - older methods/findings become less relevant quickly in genomics.

**Scoring curve:**
```
Year 0 (this year):  1.0  ████████████
Year 1:              0.9  ███████████
Year 2:              0.8  ██████████
Year 3:              0.7  █████████
Year 4:              0.6  ████████
Year 5:              0.4  ██████      ← Cutoff starts
Year 6:              0.2  ███         ← Sharp drop
Year 7+:             <0.2 ██          ← Exponential decay
```

**Why sharp cutoff?**
- Genomics/epigenetics methods evolve rapidly
- Newer papers cite more recent techniques
- 5+ year old papers may use outdated approaches
- Exception: Foundational/landmark papers still appear if highly cited

**Example:**
- Paper from 2025: score = 1.0
- Paper from 2020: score = 0.4 (5 years old)
- Paper from 2015: score = 0.2 (10 years old)

---

### 4. Citation Count: 10% 📊 IMPACT INDICATOR

**What it measures:** How influential is the paper?

**Method:** Logarithmic scale to prevent highly-cited papers from dominating

**Scoring:**
```
0 citations:     0.0
10 citations:    0.5
50 citations:    0.7
100 citations:   0.75
500 citations:   0.85
1000+ citations: 0.9
```

**Why only 10%?**
- **Recency bias:** Older papers have more time to accumulate citations
- **Field variation:** Some fields cite less than others
- **Self-citation:** Can inflate numbers
- **Recency already captures impact:** Recent papers that are influential will have citations despite being new

**Why keep it at all?**
- Indicates community validation
- Helps break ties between similar papers
- Higher weight (10% vs previous 5%) gives more influence to impactful recent papers

**Example:**
- Recent paper (2023) with 50 citations = HIGH relevance (recent + impactful)
- Old paper (2010) with 1000 citations = MODERATE relevance (high citations, but old)

---

## Design Philosophy

### Content-First Approach

**70% of score = What the paper says**
- Content similarity: 40%
- Keyword matching: 30%

**Rationale:** If a paper doesn't discuss relevant topics, it doesn't matter how prestigious the journal is, how many citations it has, or where the data came from.

### Simplicity Over Completeness

**Removed complexity:**
- No source quality tiers (PubMed vs Semantic Scholar)
- No journal impact factors
- No author reputation scoring
- No institutional rankings

**Why?** These factors:
1. Are often arbitrary or subjective
2. Don't directly measure relevance
3. Add maintenance burden (keeping lists updated)
4. Can introduce bias

### Transparency

**Score breakdown always available:**
```python
score.breakdown = {
    "total": 0.782,
    "content_similarity": 0.85,  # 40% weight
    "keyword_match": 0.75,       # 30% weight
    "recency": 0.70,             # 20% weight
    "citation_count": 0.65       # 10% weight
}
```

Users can see exactly why a paper scored high or low.

---

## Example Scenarios

### Scenario 1: Highly Relevant Recent Paper

**Paper:** "DNA methylation changes in lead-exposed children (2024)"
- Content similarity: 0.90 (very similar language)
- Keyword match: 0.85 (most keywords present)
- Recency: 1.0 (this year)
- Citations: 0.3 (only 5 citations, very new)

**Total Score:**
```
0.90 × 0.40 = 0.360
0.85 × 0.30 = 0.255
1.00 × 0.20 = 0.200
0.30 × 0.10 = 0.030
─────────────────
TOTAL:        0.845  ← HIGH SCORE
```

**Why high?** Directly relevant, very recent, despite few citations.

---

### Scenario 2: Highly Cited But Less Relevant

**Paper:** "General epigenetics review (2015)"
- Content similarity: 0.50 (mentions methylation, but not lead/children)
- Keyword match: 0.40 (only 2 of 5 keywords)
- Recency: 0.2 (10 years old)
- Citations: 0.9 (1500 citations)

**Total Score:**
```
0.50 × 0.40 = 0.200
0.40 × 0.30 = 0.120
0.20 × 0.20 = 0.040
0.90 × 0.10 = 0.090
─────────────────
TOTAL:        0.450  ← MODERATE SCORE
```

**Why moderate?** Highly cited, but old and only partially relevant.

---

### Scenario 3: Perfect Match, Moderate Age

**Paper:** "Lead exposure DNA methylation children (2021)"
- Content similarity: 0.95 (nearly identical topic)
- Keyword match: 0.90 (all keywords present)
- Recency: 0.6 (4 years old)
- Citations: 0.7 (75 citations)

**Total Score:**
```
0.95 × 0.40 = 0.380
0.90 × 0.30 = 0.270
0.60 × 0.20 = 0.120
0.70 × 0.10 = 0.070
─────────────────
TOTAL:        0.840  ← HIGH SCORE
```

**Why high?** Highly relevant content, moderately recent, good citations.

---

## Implementation Details

### Code Structure

**Files:**
- `relevance_scoring.py`: Core scoring logic (~320 lines)
- `geo_discovery.py`: Integration (~10 lines changed)

**Key Classes:**
```python
@dataclass
class ScoringWeights:
    content_similarity: float = 0.40
    keyword_match: float = 0.30
    recency: float = 0.20
    citation_count: float = 0.10

@dataclass
class RelevanceScore:
    total: float
    content_similarity: float
    keyword_match: float
    recency: float
    citation_count: float
```

### Recency Implementation

```python
def _score_recency(self, pub: Publication) -> float:
    years_old = current_year - pub_year
    
    if years_old == 0: return 1.0
    elif years_old == 1: return 0.9
    elif years_old == 2: return 0.8
    elif years_old == 3: return 0.7
    elif years_old == 4: return 0.6
    elif years_old == 5: return 0.4  # Cutoff
    elif years_old == 6: return 0.2  # Sharp drop
    else: return max(0.0, 0.2 * (0.7 ** (years_old - 6)))
```

### Citation Implementation

```python
def _score_citations(self, pub: Publication) -> float:
    if citations <= 0: return 0.0
    
    # Logarithmic scale
    score = math.log10(citations + 1) / 4.0
    return min(1.0, max(0.0, score))
```

---

## Testing Strategy

### Test Dataset: GSE69633

**GEO Title:** "DNA methylation profiles in lead-exposed children"

**Expected rankings:**
1. **High scores (0.7-0.9):** Papers about lead + methylation + children (recent)
2. **Medium scores (0.5-0.7):** Papers about 2 of 3 topics OR older but highly relevant
3. **Low scores (0.3-0.5):** Papers about only 1 topic OR very old
4. **Very low (<0.3):** Tangentially related or very outdated

### Validation Criteria

✅ **Pass:** Recent, topically relevant papers rank higher than old, tangentially related papers  
✅ **Pass:** Papers with similar content rank higher than those with just keywords  
✅ **Pass:** 5-year-old papers score significantly lower than 1-year-old papers  
❌ **Fail:** Highly cited but irrelevant papers dominate rankings

---

## Comparison: Old vs New

### Old Model (6 Factors)
```
Keywords:          35%  ⭐⭐
Content:           30%  ⭐⭐
Recency:           15%
Journal:           10%  ← REMOVED
Citations:          5%
Source Quality:     5%  ← REMOVED
─────────────────────
Total:            100%
```

**Issues:**
- Source quality was arbitrary (PubMed vs Semantic Scholar)
- Journal relevance required maintaining journal lists
- Too many factors to tune and explain
- Only 65% on content relevance

### New Model (4 Factors) ✨
```
Content:           40%  ⭐⭐⭐ PRIMARY
Keywords:          30%  ⭐⭐ SECONDARY
Recency:           20%  ⏰ 5-year cutoff
Citations:         10%  📊 Impact
─────────────────────
Total:            100%
```

**Improvements:**
- **70% on content** (vs 65%) - more focus on relevance
- **20% on recency** (vs 15%) - sharper temporal preference
- **10% on citations** (vs 5%) - more credit for impact
- **Simpler** - easier to understand and maintain
- **No arbitrary quality judgments**

---

## Future Enhancements (Maybe)

### What We're NOT Adding (For Good Reason)

❌ **Author reputation:** Complex to calculate, doesn't measure paper relevance  
❌ **Institution ranking:** Introduces bias, doesn't measure content quality  
❌ **Journal impact factor:** Already rejected as too subjective  
❌ **MeSH term weighting:** Over-optimization for PubMed-specific features

### What MIGHT Be Useful Later

✅ **User feedback learning:** Adjust weights based on which papers users select  
✅ **Dataset-specific optimization:** Different weights for different GEO types  
✅ **Confidence scoring:** Flag papers with low-quality metadata separately

**Principle:** Only add complexity if it demonstrably improves results.

---

## Summary

**The Simplified Model:**
- **4 factors** instead of 6
- **70% on content relevance** (what the paper discusses)
- **20% on recency** (with sharp 5-year cutoff)
- **10% on impact** (citations, but limited influence)
- **No arbitrary quality judgments**

**Philosophy:**
> "If a paper doesn't discuss your topic, it's not relevant - regardless of how prestigious the journal is, how many citations it has, or where the metadata came from."

**Result:** Clean, transparent, maintainable, and focused on what actually matters.

---

**Next Steps:**
1. Test with GSE69633 ✅ Ready
2. Validate rankings ⏳ Pending
3. Commit Phase 5 ⏳ After testing
4. Move to Phase 6 (add more citation sources) ⏳ Future
