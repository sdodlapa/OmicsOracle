# Citation Scoring & Ranking Methods: Comprehensive Analysis

**Date:** October 11, 2025
**Purpose:** Evaluate state-of-the-art methods for scoring publications by citations and recency
**Status:** Research & Critical Evaluation

---

## Executive Summary

Citation scoring is **complex** and **context-dependent**. Different use cases require different approaches:

- **Literature Review**: Favor highly-cited foundational papers (PageRank, h-index)
- **Recent Discoveries**: Favor recent papers regardless of citations (time-decay)
- **Trending Research**: Favor papers with rapid citation growth (velocity metrics)
- **Balanced Search**: Combine multiple signals (our current approach)

**Key Finding:** No single "best" method exists. The optimal approach depends on **user intent**.

---

## 1. Current Implementation (OmicsOracle v0.3)

### Method: Multi-Factor Linear Combination

```
Total Score = 0.40 * title_match + 0.30 * abstract_match + 0.20 * recency + 0.10 * citations
```

### Citation Scoring: 3-Tier Dampening

```python
# Linear: 0-100 citations → 0.0-0.6 score
if citations <= 100:
    score = (citations / 100) * 0.6

# Square root: 100-1000 citations → 0.6-0.8 score
elif citations <= 1000:
    normalized = (citations - 100) / 900
    score = 0.6 + (sqrt(normalized) * 0.2)

# Logarithmic: 1000+ citations → 0.8-1.0 score
else:
    log_score = log10(citations)
    normalized = (log_score - 3.0) / (5.0 - 3.0)  # 1K-100K range
    score = 0.8 + (normalized * 0.2)
```

### Examples:
- 50 citations → 0.30 score (30% of max)
- 500 citations → 0.73 score (73% of max)
- 10,000 citations → 0.89 score (89% of max)
- 30,000 citations → 0.93 score (93% of max, HOMA-IR paper)

### Critical Evaluation:

**✅ Strengths:**
1. **Diminishing returns**: Prevents 30K-citation papers from dominating
2. **Fair to recent papers**: 50-100 citations can compete with 1000+ citations
3. **Interpretable**: Clear scoring ranges, easy to debug
4. **Computationally cheap**: O(1) calculation per paper

**❌ Weaknesses:**
1. **Ignores citation velocity**: Recent paper with 50 citations/year (growing) treated same as old paper with 50 citations total (stagnant)
2. **No field normalization**: 100 citations in physics ≠ 100 citations in biology
3. **Time-agnostic citations**: Doesn't account for "citations per year" or "recent citation rate"
4. **Fixed weights**: 20% recency + 10% citations might not suit all queries
5. **No author reputation**: Doesn't consider h-index, institutional prestige
6. **Missing context**: Ignores self-citations, review vs research articles

---

## 2. Google Scholar Approach

### Method: Relevance-Weighted Citation Score

Google Scholar uses a **proprietary algorithm** but key principles are known:

```
Score = f(text_match, citations, recency, author_reputation, venue_prestige)
```

### Key Features:

1. **Citation Weighting by Source**
   - Citations from high-impact journals > citations from low-impact journals
   - Self-citations given lower weight
   - Review articles separated from research articles

2. **Time Decay Function**
   ```
   age_factor = exp(-λ * age_years)  # Exponential decay
   λ ≈ 0.1-0.2 (tuned per field)
   ```

3. **PageRank for Citations**
   - Papers cited by influential papers rank higher
   - Recursive calculation: importance flows through citation network
   - Similar to web page ranking

4. **Field Normalization**
   - Citations normalized by field average
   - Accounts for different citation cultures (physics vs humanities)

### Critical Evaluation:

**✅ Strengths:**
1. **Context-aware**: Considers citation quality, not just quantity
2. **Network effects**: Captures importance through citation graph
3. **Field-adjusted**: Fair comparison across disciplines
4. **Battle-tested**: Billions of searches, continuously refined

**❌ Weaknesses:**
1. **Opaque**: Exact algorithm unknown, can't replicate
2. **Computationally expensive**: Requires citation graph, PageRank calculation
3. **Data requirements**: Needs journal impact factors, author h-indices
4. **Black box**: Hard to debug, explain to users
5. **Gaming vulnerable**: Can be manipulated with citation rings

**Implementation Complexity:** 🔴 HIGH (requires citation network data)

---

## 3. Semantic Scholar: Citation Velocity & Influence

### Method: Multi-Dimensional Impact Metrics

Semantic Scholar provides **multiple scores** instead of one:

1. **Citation Count**: Total citations (traditional)
2. **Citation Velocity**: Recent citation rate (trending)
3. **Influential Citations**: High-quality citations only
4. **Recency Score**: Time-based relevance

### Citation Velocity Formula:

```python
# Citations in last N years
recent_citations = citations_in_last_3_years
velocity = recent_citations / 3  # Citations per year

# Boost for accelerating papers
acceleration = (citations_year_1 - citations_year_3) / 3
if acceleration > 0:
    velocity_score = velocity * (1 + acceleration)
```

### Influential Citations:

```python
# Only count citations from papers that:
# 1. Cited this paper in their introduction/methods (not just bibliography)
# 2. Come from highly-cited papers themselves
# 3. Are from different authors (no self-citation networks)

influential_ratio = influential_citations / total_citations
quality_score = total_citations * influential_ratio
```

### Critical Evaluation:

**✅ Strengths:**
1. **Trend detection**: Identifies emerging hot papers early
2. **Quality over quantity**: Influential citations matter more
3. **Transparent metrics**: Multiple scores, users can interpret
4. **Gaming-resistant**: Hard to fake "influential" citations

**❌ Weaknesses:**
1. **Data dependency**: Requires citation context analysis (expensive)
2. **Recency bias**: May miss foundational older papers
3. **Metric proliferation**: Users confused by multiple scores
4. **Computation cost**: Requires full-text citation analysis

**Implementation Complexity:** 🟡 MEDIUM (can use Semantic Scholar API)

---

## 4. PubMed/NIH: MeSH-Weighted Relevance

### Method: Medical Subject Heading (MeSH) Term Matching

PubMed uses **controlled vocabulary** instead of citation counts:

```python
# Score based on MeSH term hierarchy
score = sum([
    major_mesh_match * 10,    # Main topic of paper
    minor_mesh_match * 5,     # Secondary topic
    title_match * 3,          # Title keywords
    abstract_match * 1,       # Abstract keywords
])

# Citations used only as tie-breaker
if score_A == score_B:
    return citations_A > citations_B
```

### Critical Evaluation:

**✅ Strengths:**
1. **Precision**: MeSH terms more accurate than free text
2. **Expert-curated**: Medical librarians assign MeSH terms
3. **Hierarchy-aware**: Understands "breast cancer" ⊂ "cancer"
4. **Field-specific**: Optimized for biomedical literature

**❌ Weaknesses:**
1. **Biomedical only**: Doesn't work outside medicine
2. **Lag time**: MeSH terms assigned months after publication
3. **Citation-agnostic**: Ignores paper impact almost entirely
4. **Manual curation**: Expensive, doesn't scale to all papers

**Implementation Complexity:** 🟢 LOW (use PubMed API with MeSH filters)

---

## 5. ArXiv/ResearchGate: Altmetrics Approach

### Method: Social & Usage Signals

Modern "altmetrics" go beyond citations:

```python
score = weighted_sum([
    downloads * 0.05,           # Paper views/downloads
    saves * 0.10,               # Bookmarks, Mendeley saves
    tweets * 0.02,              # Social media mentions
    citations * 0.60,           # Traditional citations
    recency_bonus * 0.20,       # Time decay
    author_followers * 0.03,    # Author reputation
])
```

### Critical Evaluation:

**✅ Strengths:**
1. **Early signals**: Downloads/tweets happen before citations
2. **Broader impact**: Captures non-academic influence
3. **Real-time**: Updates daily vs citations (yearly)
4. **User engagement**: Reflects actual usage, not just citations

**❌ Weaknesses:**
1. **Gaming**: Easy to manipulate (bot downloads, fake tweets)
2. **Noise**: Popularity ≠ quality (viral clickbait)
3. **Data silos**: Requires integrating many platforms
4. **Privacy concerns**: Tracking user behavior
5. **Unstable**: Metrics fluctuate wildly day-to-day

**Implementation Complexity:** 🔴 HIGH (requires multiple data sources)

---

## 6. CiteScore / Impact Factor: Journal-Level Metrics

### Method: Venue Prestige as Proxy

```python
# Assumption: Good papers in good journals
journal_impact_factor = citations_to_journal / papers_in_journal

# Boost papers from high-IF journals
paper_score = base_relevance * (1 + log(impact_factor))
```

### Critical Evaluation:

**✅ Strengths:**
1. **Simple**: One number per journal, easy to compute
2. **Established**: Widely recognized in academia
3. **Stable**: Changes slowly over time

**❌ Weaknesses:**
1. **Journal ≠ paper**: Great papers in low-IF journals ignored
2. **Field bias**: Clinical journals have higher IF than basic science
3. **Gaming**: Journals manipulate IF with self-citations
4. **Lag**: IF calculated on 2-year window, misses recent papers
5. **Controversial**: Many researchers oppose IF use

**Implementation Complexity:** 🟢 LOW (journal IF databases available)

---

## 7. h-index & Variants: Author-Centric Metrics

### Method: Author Reputation Transfer

```python
# h-index: Largest N where author has N papers with ≥ N citations
# Example: h=50 means 50 papers with ≥50 citations each

# Transfer to paper
author_boost = sum([log(author.h_index) for author in paper.authors]) / len(authors)
paper_score = base_score * (1 + author_boost)
```

### Variants:
- **g-index**: Emphasizes highly-cited papers more
- **i10-index**: Count of papers with ≥10 citations
- **m-quotient**: h-index / years since first publication (career stage)

### Critical Evaluation:

**✅ Strengths:**
1. **Career quality**: Rewards consistent high-impact work
2. **Gaming-resistant**: Hard to fake h=50
3. **Simple**: Single number, easy to understand

**❌ Weaknesses:**
1. **Favors senior researchers**: Young authors penalized
2. **Field bias**: Different h-index ranges per field
3. **Team size**: Multi-author papers complicate credit
4. **Static**: Doesn't update in real-time
5. **Author disambiguation**: "John Smith" problem

**Implementation Complexity:** 🟡 MEDIUM (requires author profiles)

---

## 8. Machine Learning: Learn to Rank (LTR)

### Method: Train Model on User Clicks

```python
# Features for each paper
features = [
    citation_count,
    citations_per_year,
    recency_score,
    author_h_index,
    journal_impact_factor,
    text_match_score,
    institution_prestige,
    downloads_last_month,
    # ... 100+ features
]

# Train model on historical search data
model = LambdaMART(features, labels=user_clicked)

# Predict relevance for new queries
score = model.predict(features)
```

### Popular Algorithms:
- **LambdaMART**: Gradient boosted decision trees for ranking
- **RankNet**: Neural network pairwise ranking
- **BERT-based**: Transformer models for semantic matching

### Critical Evaluation:

**✅ Strengths:**
1. **Optimal**: Learns from actual user behavior
2. **Adaptive**: Improves over time with more data
3. **Non-linear**: Captures complex feature interactions
4. **State-of-the-art**: Used by Google, Microsoft, etc.

**❌ Weaknesses:**
1. **Data hungry**: Needs millions of labeled examples
2. **Black box**: Hard to interpret, explain
3. **Computational cost**: Expensive training, inference
4. **Cold start**: Doesn't work for new papers (no clicks yet)
5. **Bias amplification**: Learns user biases, creates filter bubbles

**Implementation Complexity:** 🔴 VERY HIGH (requires ML infrastructure)

---

## 9. Hybrid Approaches: Best of Multiple Worlds

### Method: Ensemble of Methods

```python
# Combine multiple scoring methods
scores = {
    'citation_quality': semantic_scholar_influential_score,
    'citation_velocity': citations_last_3_years / 3,
    'author_reputation': mean([author.h_index for author in authors]),
    'journal_prestige': journal_impact_factor,
    'recency': exp(-0.1 * age_years),
    'text_match': tfidf_score,
}

# Weighted ensemble
final_score = sum([
    scores['citation_quality'] * 0.25,
    scores['citation_velocity'] * 0.20,
    scores['author_reputation'] * 0.10,
    scores['journal_prestige'] * 0.10,
    scores['recency'] * 0.15,
    scores['text_match'] * 0.20,
])
```

### Critical Evaluation:

**✅ Strengths:**
1. **Robust**: Multiple signals reduce reliance on any one metric
2. **Tunable**: Can adjust weights per query type
3. **Explainable**: Can show contribution of each component
4. **Practical**: Balances accuracy vs complexity

**❌ Weaknesses:**
1. **Weight tuning**: How to set optimal weights?
2. **Data requirements**: Needs all component data sources
3. **Maintenance**: More systems to maintain
4. **Complexity**: Hard to debug when one component breaks

**Implementation Complexity:** 🟡 MEDIUM (depends on components chosen)

---

## 10. Recommendations for OmicsOracle

### Use Case Analysis

**Primary Use Case:** Biomedical researchers searching for relevant datasets and publications

**User Intent Patterns:**
1. **Exploratory**: "What's known about APOE in Alzheimer's?" → Favor review papers, highly-cited classics
2. **Recent discoveries**: "Latest CRISPR applications" → Favor papers from last 2 years
3. **Methodology**: "How to analyze RNA-seq data?" → Favor highly-cited methods papers
4. **Dataset finding**: "GEO datasets for breast cancer" → Citations less relevant, metadata match primary

### Recommended Approach: **Adaptive Hybrid**

```python
# Detect query intent
if "review" in query or "overview" in query:
    weights = {'citations': 0.40, 'recency': 0.10, 'text': 0.50}  # Favor classics
elif "recent" in query or "latest" in query or "2024" in query:
    weights = {'citations': 0.05, 'recency': 0.45, 'text': 0.50}  # Favor new
elif "method" in query or "protocol" in query or "how to" in query:
    weights = {'citations': 0.30, 'recency': 0.10, 'text': 0.60}  # Favor methods
else:
    weights = {'citations': 0.15, 'recency': 0.25, 'text': 0.60}  # Balanced (current)
```

### Three-Tier Implementation Plan

#### Tier 1: Quick Wins (Week 4, 2-4 hours)
**Keep current 3-tier citation dampening, but:**

1. **Add Citation Velocity**
   ```python
   # Enhance citation score with velocity
   citations_per_year = total_citations / max(age_years, 1)
   if citations_per_year > 10:  # Hot paper
       citation_score *= 1.3  # 30% boost
   ```

2. **Query-Dependent Weights**
   ```python
   # Simple keyword detection
   if "recent" in query.lower() or any(year in query for year in ["2023", "2024", "2025"]):
       weights['recency'] = 0.40  # Increase from 0.20
       weights['citations'] = 0.05  # Decrease from 0.10
   ```

3. **Cap Citation Dominance**
   ```python
   # Prevent any single factor from dominating
   max_component_contribution = 0.40  # No factor can contribute >40% to total score
   ```

**Pros:** Minimal code change, addresses recency concern, low risk
**Cons:** Still simplistic, doesn't use citation quality
**Effort:** 2-4 hours implementation + testing

#### Tier 2: Medium-Term (Month 2, 1-2 weeks)

1. **Integrate Semantic Scholar API**
   ```python
   # Use their pre-computed metrics
   paper_data = semantic_scholar.get_paper(doi)
   influential_citations = paper_data['influentialCitationCount']
   citation_velocity = paper_data['citationVelocity']

   quality_score = influential_citations / max(total_citations, 1)
   combined_score = (quality_score * 0.5) + (velocity * 0.5)
   ```

2. **Field Normalization**
   ```python
   # Get field-average citation count
   field = detect_field(paper.mesh_terms)  # "genomics", "immunology", etc
   field_avg = FIELD_CITATION_AVERAGES[field]  # Pre-computed from corpus

   normalized_citations = citations / field_avg
   # Now 1.0 = average for field, 2.0 = 2x above average
   ```

3. **Author h-index Boost**
   ```python
   # Use OpenAlex author data
   author_scores = [get_author_h_index(author) for author in paper.authors]
   author_boost = log(1 + mean(author_scores))  # Diminishing returns
   ```

**Pros:** Leverages expert systems, higher quality signals
**Cons:** API dependencies, rate limits, data coverage gaps
**Effort:** 1-2 weeks implementation + validation

#### Tier 3: Long-Term (Month 6+, 1-2 months)

1. **Build Citation Graph**
   - Crawl citation network for papers in corpus
   - Compute PageRank scores
   - Identify citation clusters/communities

2. **Learn from User Behavior**
   - Track which papers users click/download
   - Train LTR model (LambdaMART or neural)
   - A/B test ranking changes

3. **Multi-Objective Ranking**
   - Diversity: Don't show 10 papers from same author
   - Freshness: Always include 1-2 recent papers in top 10
   - Coverage: Represent different subtopics

**Pros:** Industry-grade quality, adaptive learning
**Cons:** Significant infrastructure, data collection, maintenance
**Effort:** 1-2 months + ongoing ML operations

---

## 11. Critical Decision Factors

### What Data Do We Have Access To?

✅ **Currently Available:**
- Citation counts (PubMed, OpenAlex, Semantic Scholar)
- Publication dates
- Titles, abstracts
- PubMed IDs, DOIs
- Author names

❓ **Partially Available:**
- MeSH terms (PubMed only)
- Journal names
- Author h-indices (OpenAlex API)
- Recent citation counts (Semantic Scholar API)

❌ **Not Available:**
- Full citation network
- User click data
- Full-text content (for most papers)
- Self-citation identification
- Citation context (intro vs methods)

### What Are User Expectations?

**Scientific Search Tools Benchmark:**
- **PubMed**: Precision over recall, MeSH-driven
- **Google Scholar**: Broad recall, relevance unclear
- **Semantic Scholar**: Transparent metrics, multiple views
- **Web of Science**: Citation network, curated

**Users Expect:**
1. **Relevant** papers appear in top 10
2. **Recent** papers not buried by old classics
3. **Diverse** results (not 10 papers from same group)
4. **Explainable** ranking (why is this #1?)

### Performance Constraints

- **Latency**: <2s total search time (database + ranking)
- **Throughput**: 100+ papers ranked per query
- **API Costs**: Free tier limits (1000 requests/day typical)
- **Complexity**: Maintainable by small team

---

## 12. Final Recommendations

### ✅ DO (Priority Order)

1. **Add Citation Velocity** (Week 4, Day 1)
   - Quick win: `citations_per_year = total / age`
   - Boost papers with >10 citations/year
   - Low risk, high impact

2. **Query Intent Detection** (Week 4, Day 2)
   - Keyword-based weight adjustment
   - "recent", "review", "method" → different weights
   - Improves UX without complexity

3. **Semantic Scholar Integration** (Month 2)
   - Use their pre-computed influential citations
   - Add citation velocity from their API
   - Leverage expert data, don't reinvent

4. **A/B Testing Framework** (Month 3)
   - Log which papers users click
   - Test ranking changes with real users
   - Data-driven optimization

### ❌ DON'T (At Least Not Yet)

1. **Build Citation Graph**
   - Too complex, too much data
   - Semantic Scholar already has this
   - Not worth reinventing

2. **Train ML Ranking Model**
   - Need millions of labeled examples
   - Requires ML infrastructure
   - Overkill for current scale

3. **Use Journal Impact Factor**
   - Controversial, being phased out
   - Misleading for individual papers
   - Better alternatives exist

4. **Altmetrics (tweets, downloads)**
   - Too noisy, easily gamed
   - Integration headaches
   - Academic users don't trust them

### 🤔 MAYBE (Evaluate Later)

1. **Field Normalization**
   - Good idea, but needs field detection
   - Wait until we have MeSH term coverage
   - Could use OpenAlex concepts instead

2. **Author h-index Boost**
   - Helpful, but penalizes young researchers
   - Could be unfair, creates bias
   - Use cautiously, with small weight

---

## 13. Proposed Next Steps

### Immediate (This Week)

1. **Do NOT implement** the `_calculate_impact_score()` method I just added
2. **Revert** those changes to keep current simple approach
3. **Document** current scoring clearly for users
4. **Add tests** to validate scoring edge cases

### Short-Term (Week 4)

1. **Research citation velocity calculation**
   - How to get "citations in last 3 years" efficiently?
   - OpenAlex API? Semantic Scholar API? Calculate ourselves?

2. **Prototype query intent detection**
   - Simple keyword rules first
   - Test with real queries from logs

3. **User survey**
   - Ask researchers: "What do you want to see first?"
   - Show example rankings, get feedback

### Medium-Term (Month 2-3)

1. **API integration evaluation**
   - Semantic Scholar: Free tier limits? Data coverage?
   - OpenAlex: Rate limits? Field quality?

2. **Benchmark against baselines**
   - Compare our rankings to PubMed, Google Scholar
   - Identify where we're better/worse

3. **User testing**
   - Real users, real queries
   - Measure: relevance, diversity, recency balance

---

## 14. Conclusion

**Citation scoring is NOT a solved problem.** Even Google Scholar's algorithm is proprietary and imperfect.

**Our current approach is REASONABLE for v0.3:**
- Simple, interpretable, maintainable
- Balances citations, recency, relevance
- Adequate for current user base

**Proposed evolution:**
1. Week 4: Add citation velocity (simple enhancement)
2. Month 2: Integrate Semantic Scholar (leverage experts)
3. Month 6: User feedback → adaptive weights

**Key Principle:** **Don't optimize in isolation. Get user feedback first.**

We should implement **small, measurable improvements** and **validate with real users** before committing to complex solutions.

---

**Document Status:** DRAFT for review
**Next Action:** Review with team, decide on Week 4 scope
**Estimated Review Time:** 30-45 minutes

