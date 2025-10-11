# Citation Scoring: Implementation Comparisons

**Companion Document to:** `citation_scoring_analysis.md`  
**Focus:** Concrete code examples and implementation details

---

## Implementation Comparison Matrix

| Method | Complexity | Data Requirements | Latency | Interpretability | Gaming Resistance |
|--------|-----------|-------------------|---------|------------------|-------------------|
| **Current (3-tier dampening)** | 🟢 Low | PubMed citations | <1ms | 🟢 High | 🟡 Medium |
| **Citation velocity** | 🟢 Low | Citations + date | <1ms | 🟢 High | 🟡 Medium |
| **Semantic Scholar API** | 🟡 Medium | API key | 50-200ms | 🟢 High | 🟢 High |
| **PageRank** | 🔴 High | Citation graph | 100ms-1s | 🔴 Low | 🟢 High |
| **Learn-to-Rank (ML)** | 🔴 Very High | Click data | 10-50ms | 🔴 Very Low | 🟡 Medium |
| **Journal Impact Factor** | 🟢 Low | Journal metadata | <1ms | 🟡 Medium | 🔴 Low |
| **Altmetrics** | 🟡 Medium | Social APIs | 100-500ms | 🟡 Medium | 🔴 Very Low |

---

## 1. Current Implementation: Detailed Analysis

### Full Code Walkthrough

```python
def _calculate_citation_score(self, citations: int) -> float:
    """
    3-tier dampening to prevent highly-cited papers from dominating.
    
    Tier 1 (0-100): Linear growth
    - 0 citations → 0.0
    - 50 citations → 0.3  
    - 100 citations → 0.6
    
    Tier 2 (100-1000): Square root growth (slower)
    - 100 citations → 0.6
    - 500 citations → 0.73
    - 1000 citations → 0.8
    
    Tier 3 (1000+): Logarithmic growth (slowest)
    - 1000 citations → 0.8
    - 10,000 citations → 0.9
    - 100,000 citations → 1.0
    """
    if citations <= 100:
        # Linear: 0-100 citations map to 0.0-0.6
        return (citations / 100) * 0.6
    
    elif citations <= 1000:
        # Square root: 100-1000 citations map to 0.6-0.8
        normalized = (citations - 100) / 900  # 0.0-1.0 range
        sqrt_scaled = sqrt(normalized)       # Slower growth
        return 0.6 + (sqrt_scaled * 0.2)     # 0.6-0.8 range
    
    else:
        # Logarithmic: 1000+ citations map to 0.8-1.0
        log_score = log10(citations)         # log10(1000)=3.0, log10(100000)=5.0
        normalized = (log_score - 3.0) / (5.0 - 3.0)  # 0.0-1.0 range
        clamped = min(normalized, 1.0)       # Cap at 1.0
        return 0.8 + (clamped * 0.2)         # 0.8-1.0 range
```

### Visualization

```
Citations vs Score (Current Method)
1.0 |                                    ████████
    |                              ██████
0.8 |                        ██████
    |                  ██████
0.6 |            ██████
    |      ██████
0.4 |  ████
    |██
0.2 |█
    |
0.0 +----+----+----+----+----+----+----+----+----+----+
    0   100  200  500  1K   2K   5K  10K  20K  50K 100K
                        Citations

Legend:
  Linear region (0-100): Steep slope
  Square root region (100-1000): Moderate slope  
  Logarithmic region (1000+): Gentle slope
```

### Edge Cases & Problems

**Problem 1: Recent paper with moderate citations undervalued**
```python
# Example: Breakthrough COVID-19 paper (2023)
paper_A = {
    'title': 'Novel SARS-CoV-2 Omicron variant structural analysis',
    'citations': 120,
    'date': '2023-03-15',
    'age_years': 1.5
}

citation_score_A = _calculate_citation_score(120)  # ~0.62
recency_score_A = _calculate_recency_score('2023-03-15')  # ~0.95

total_A = 0.62 * 0.10 + 0.95 * 0.20 = 0.062 + 0.190 = 0.252
```

**Problem 2: Old classic with many citations overvalued (relative to recency)**
```python
# Example: HOMA-IR insulin resistance paper (2000)
paper_B = {
    'title': 'Homeostasis model assessment insulin resistance',
    'citations': 30000,
    'date': '2000-01-01',
    'age_years': 24.8
}

citation_score_B = _calculate_citation_score(30000)  # ~0.93
recency_score_B = _calculate_recency_score('2000-01-01')  # ~0.0

total_B = 0.93 * 0.10 + 0.0 * 0.20 = 0.093 + 0.000 = 0.093
```

**Analysis:**
- Paper B (old classic) gets 0.093 from citations alone
- Paper A (recent breakthrough) gets 0.252 from citations + recency
- **Current system handles this WELL** - recent paper scores higher
- **BUT** only because recency has 2x weight (20% vs 10%)
- If query is "HOMA-IR" (exact match), text relevance will dominate anyway

**Problem 3: Citation inflation over time**
```python
# Same paper quality, published in different years
paper_2005 = {'citations': 500, 'age': 19}  # Had 20 years to accumulate
paper_2020 = {'citations': 100, 'age': 4}   # Had 4 years to accumulate

# But citations per year is similar!
cpy_2005 = 500 / 19 = 26.3 citations/year
cpy_2020 = 100 / 4 = 25.0 citations/year

# Current scoring:
score_2005 = _calculate_citation_score(500)  # ~0.73
score_2020 = _calculate_citation_score(100)  # ~0.60

# Paper from 2005 scores higher despite similar impact rate!
```

**This is the REAL problem** - we don't account for "time to accumulate citations"

---

## 2. Citation Velocity: Simple Enhancement

### Implementation Option A: Citations Per Year

```python
def _calculate_citation_velocity_score(
    self, 
    citations: int, 
    publication_date: str
) -> float:
    """
    Score based on citation rate, not absolute count.
    
    Hypothesis: 100 citations in 2 years > 500 citations in 20 years
    """
    age_years = self._get_age_years(publication_date)
    
    # Avoid division by zero
    if age_years < 0.1:
        age_years = 0.1  # Treat <1 month as 0.1 years
    
    citations_per_year = citations / age_years
    
    # Tiered scoring based on velocity
    if citations_per_year >= 100:
        return 1.0  # Blockbuster (100+ cites/year)
    elif citations_per_year >= 50:
        return 0.9  # Very high impact
    elif citations_per_year >= 20:
        return 0.75  # High impact
    elif citations_per_year >= 10:
        return 0.6   # Good impact
    elif citations_per_year >= 5:
        return 0.45  # Moderate impact
    elif citations_per_year >= 1:
        return 0.3   # Some impact
    else:
        return citations_per_year / 1.0 * 0.3  # Linear below 1/year
```

**Examples:**
```python
# Recent high-velocity paper
velocity_score(citations=100, age=2) 
# → 50 cites/year → 0.9 ✅ EXCELLENT

# Old slow paper  
velocity_score(citations=500, age=20)
# → 25 cites/year → 0.75 ✅ GOOD

# Classic that's slowing down
velocity_score(citations=5000, age=30)
# → 167 cites/year → 1.0 ✅ BLOCKBUSTER (but maybe stagnant recently?)

# Brand new paper
velocity_score(citations=5, age=0.5)
# → 10 cites/year → 0.6 ✅ PROMISING
```

**Problem with Option A:**
- Doesn't distinguish between "100 citations in first 2 years" vs "100 citations spread over 20 years"
- A paper with 1000 citations accumulated 20 years ago might have 0 recent citations
- Velocity should measure RECENT citation rate, not lifetime average

### Implementation Option B: Recent Citation Rate (Better)

```python
def _calculate_citation_velocity_score(
    self,
    citations_last_3_years: int,  # NEW: Need this data!
    total_citations: int
) -> float:
    """
    Score based on RECENT citation activity.
    
    Requires: Citations in last 3 years (from Semantic Scholar or OpenAlex)
    """
    recent_per_year = citations_last_3_years / 3
    
    # Acceleration bonus: If recent rate > historical average
    if total_citations > 0:
        historical_rate = total_citations / max(self._get_age_years(...), 1)
        acceleration = recent_per_year / historical_rate
        
        if acceleration > 2.0:
            bonus = 1.3  # Citations accelerating!
        elif acceleration > 1.5:
            bonus = 1.15
        else:
            bonus = 1.0
    else:
        bonus = 1.0
    
    # Score with acceleration bonus
    raw_score = self._citations_per_year_to_score(recent_per_year)
    return min(raw_score * bonus, 1.0)
```

**Examples:**
```python
# Trending paper: 60 recent citations, 100 total, 5 years old
recent_rate = 60 / 3 = 20 cites/year recently
historical_rate = 100 / 5 = 20 cites/year historically
acceleration = 20 / 20 = 1.0  # Steady
score = _citations_per_year_to_score(20) = 0.75  # No bonus

# Hot paper: 90 recent citations, 100 total, 5 years old  
recent_rate = 90 / 3 = 30 cites/year recently
historical_rate = 100 / 5 = 20 cites/year historically
acceleration = 30 / 20 = 1.5  # Accelerating!
score = _citations_per_year_to_score(30) * 1.15 = 0.8 * 1.15 = 0.92  ✅

# Declining classic: 10 recent citations, 1000 total, 20 years old
recent_rate = 10 / 3 = 3.3 cites/year recently
historical_rate = 1000 / 20 = 50 cites/year historically  
acceleration = 3.3 / 50 = 0.066  # Declining!
# No acceleration bonus, just use recent rate
score = _citations_per_year_to_score(3.3) = 0.4  ✅ Correctly penalized
```

**Data Requirements for Option B:**
- Need `citations_last_3_years` field
- Semantic Scholar API provides this: `paper['citationStats']['citationsInLast3Years']`
- OpenAlex might have this too (need to verify)

---

## 3. Semantic Scholar API Integration

### API Response Example

```json
{
  "paperId": "649def34f8be52c8b66281af98ae884c09aef38b",
  "title": "BERT: Pre-training of Deep Bidirectional Transformers",
  "year": 2019,
  "citationCount": 58000,
  "influentialCitationCount": 9200,
  "citationStyles": {
    "bibtex": "..."
  },
  "citationStats": {
    "citationsInLast3Years": 42000,
    "citationsInLast5Years": 57000
  },
  "fieldsOfStudy": ["Computer Science"],
  "authors": [
    {
      "authorId": "...",
      "name": "Jacob Devlin",
      "hIndex": 45
    }
  ]
}
```

### Integration Code

```python
from typing import Optional
import httpx
import asyncio

class SemanticScholarClient:
    """
    Semantic Scholar API client for enhanced citation metrics.
    
    Rate Limits (Free Tier):
    - 100 requests per 5 minutes
    - 1 request per second
    
    Cost: FREE (no API key required for basic access)
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key  # Optional, increases rate limits
        self.client = httpx.AsyncClient(timeout=10.0)
        self._last_request_time = 0
        
    async def get_paper_metrics(self, doi: str) -> dict:
        """
        Get enhanced metrics for a paper by DOI.
        
        Returns:
            {
                'citation_count': 58000,
                'influential_citation_count': 9200,
                'citations_last_3_years': 42000,
                'authors': [{'name': '...', 'h_index': 45}],
                'fields': ['Computer Science']
            }
        """
        # Rate limiting: 1 request per second
        now = time.time()
        if now - self._last_request_time < 1.0:
            await asyncio.sleep(1.0 - (now - self._last_request_time))
        
        url = f"{self.BASE_URL}/paper/DOI:{doi}"
        params = {
            'fields': 'citationCount,influentialCitationCount,citationStats,authors,fieldsOfStudy'
        }
        headers = {}
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
        response = await self.client.get(url, params=params, headers=headers)
        self._last_request_time = time.time()
        
        if response.status_code == 404:
            return None  # Paper not found
        response.raise_for_status()
        
        data = response.json()
        return {
            'citation_count': data.get('citationCount', 0),
            'influential_citation_count': data.get('influentialCitationCount', 0),
            'citations_last_3_years': data.get('citationStats', {}).get('citationsInLast3Years', 0),
            'authors': [
                {'name': a['name'], 'h_index': a.get('hIndex', 0)}
                for a in data.get('authors', [])
            ],
            'fields': data.get('fieldsOfStudy', [])
        }
```

### Enhanced Scoring with Semantic Scholar

```python
def _calculate_enhanced_citation_score(
    self,
    total_citations: int,
    influential_citations: int,
    citations_last_3_years: int,
    age_years: float
) -> Tuple[float, dict]:
    """
    Multi-dimensional citation scoring using Semantic Scholar data.
    
    Components:
    1. Citation velocity (recent activity)
    2. Citation quality (influential citations)
    3. Total citations (dampened)
    """
    # Component 1: Velocity (40% weight)
    recent_per_year = citations_last_3_years / 3
    velocity_score = min(recent_per_year / 50, 1.0)  # 50 cites/year = max
    
    # Component 2: Quality (40% weight)
    if total_citations > 0:
        quality_ratio = influential_citations / total_citations
    else:
        quality_ratio = 0
    quality_score = quality_ratio  # Already 0-1 range
    
    # Component 3: Total citations (20% weight)
    total_score = self._calculate_citation_score(total_citations)  # Our existing method
    
    # Weighted combination
    combined = (
        velocity_score * 0.40 +
        quality_score * 0.40 +
        total_score * 0.20
    )
    
    breakdown = {
        'velocity': velocity_score,
        'quality': quality_score,
        'total': total_score,
        'combined': combined,
        'recent_per_year': recent_per_year,
        'influential_ratio': quality_ratio
    }
    
    return combined, breakdown
```

**Example Scoring:**

```python
# Paper A: Recent high-quality paper
# 2023 publication, 150 total citations, 120 influential, 140 in last 3 years
velocity = 140 / 3 / 50 = 0.93  # 47 cites/year
quality = 120 / 150 = 0.80      # 80% influential
total = 0.65                     # From 3-tier dampening
combined = 0.93 * 0.4 + 0.80 * 0.4 + 0.65 * 0.2 = 0.822  ✅ EXCELLENT

# Paper B: Old highly-cited but low quality
# 2005 publication, 5000 total citations, 500 influential, 100 in last 3 years
velocity = 100 / 3 / 50 = 0.67  # 33 cites/year  
quality = 500 / 5000 = 0.10     # Only 10% influential
total = 0.88                     # From 3-tier dampening
combined = 0.67 * 0.4 + 0.10 * 0.4 + 0.88 * 0.2 = 0.484  ✅ MODERATE

# Paper C: Classic foundational work
# 1995 publication, 20000 total citations, 8000 influential, 500 in last 3 years
velocity = 500 / 3 / 50 = 1.0   # 167 cites/year (capped)
quality = 8000 / 20000 = 0.40   # 40% influential
total = 0.92                     # From 3-tier dampening
combined = 1.0 * 0.4 + 0.40 * 0.4 + 0.92 * 0.2 = 0.744  ✅ VERY GOOD
```

**Analysis:**
- Recent high-quality paper (A) scores highest (0.822)
- Old low-quality paper (B) penalized despite 5K citations (0.484)
- Classic foundational work (C) still scores well (0.744) due to continued citations

**This is much better than current approach!**

---

## 4. Field Normalization: Accounting for Discipline Differences

### Problem Statement

```python
# Biology paper: 500 citations is EXCELLENT (top 5%)
bio_paper = {'citations': 500, 'field': 'molecular_biology'}

# Physics paper: 500 citations is GOOD (top 20%)
physics_paper = {'citations': 500, 'field': 'high_energy_physics'}

# Current scoring: Both get same score (0.73)
# Should be: Biology paper scores higher
```

### Field Citation Averages (Example Data)

```python
FIELD_CITATION_STATS = {
    # Format: (median, 75th_percentile, 95th_percentile)
    'molecular_biology': (15, 50, 200),
    'genomics': (20, 80, 350),
    'immunology': (18, 60, 250),
    'neuroscience': (12, 40, 180),
    'high_energy_physics': (30, 150, 800),
    'astrophysics': (25, 120, 600),
    'computer_science': (8, 25, 100),
    'machine_learning': (10, 40, 200),
}

def get_field_percentile(citations: int, field: str) -> float:
    """
    Convert citations to percentile within field.
    
    Returns 0-1 score based on field distribution.
    """
    if field not in FIELD_CITATION_STATS:
        # Unknown field: Use absolute citation score
        return _calculate_citation_score(citations)
    
    median, p75, p95 = FIELD_CITATION_STATS[field]
    
    if citations < median:
        # Below median: 0-0.5 range
        return (citations / median) * 0.5
    elif citations < p75:
        # Median to 75th: 0.5-0.75 range  
        normalized = (citations - median) / (p75 - median)
        return 0.5 + (normalized * 0.25)
    elif citations < p95:
        # 75th to 95th: 0.75-0.95 range
        normalized = (citations - p75) / (p95 - p75)
        return 0.75 + (normalized * 0.20)
    else:
        # Above 95th percentile: 0.95-1.0 range
        # Logarithmic scaling above p95
        excess = citations - p95
        log_excess = log10(excess + 1)  # +1 to avoid log(0)
        normalized = min(log_excess / 2.0, 1.0)  # 100x above p95 = 1.0
        return 0.95 + (normalized * 0.05)
```

**Example:**
```python
# Biology paper with 500 citations
bio_field = 'molecular_biology'  # p95 = 200
percentile = get_field_percentile(500, bio_field)
# 500 > 200 (p95), so in top 5%
# excess = 500 - 200 = 300
# log_excess = log10(301) = 2.48
# normalized = min(2.48 / 2.0, 1.0) = 1.0
# score = 0.95 + 1.0 * 0.05 = 1.0 ✅ TOP TIER

# Physics paper with 500 citations
physics_field = 'high_energy_physics'  # p95 = 800
percentile = get_field_percentile(500, physics_field)
# 500 is between p75 (150) and p95 (800)
# normalized = (500 - 150) / (800 - 150) = 0.54
# score = 0.75 + 0.54 * 0.20 = 0.86 ✅ GOOD but not top tier
```

### Field Detection

**Option 1: Use MeSH Terms (PubMed only)**
```python
def detect_field_from_mesh(mesh_terms: List[str]) -> str:
    """
    Map MeSH terms to broad field categories.
    """
    MESH_TO_FIELD = {
        'Genomics': 'genomics',
        'Proteomics': 'proteomics',
        'Gene Expression': 'genomics',
        'Neoplasms': 'oncology',
        'Diabetes Mellitus': 'endocrinology',
        # ... hundreds more mappings
    }
    
    for term in mesh_terms:
        if term in MESH_TO_FIELD:
            return MESH_TO_FIELD[term]
    
    return 'general_biology'  # Default
```

**Option 2: Use Semantic Scholar Fields**
```python
# Already in API response!
semantic_scholar_data = {
    'fieldsOfStudy': ['Medicine', 'Biology', 'Genetics']
}

# Use first field as primary
primary_field = semantic_scholar_data['fieldsOfStudy'][0].lower()
```

**Option 3: Use OpenAlex Concepts**
```python
openalex_data = {
    'concepts': [
        {'display_name': 'Genomics', 'score': 0.95, 'level': 2},
        {'display_name': 'Biology', 'score': 0.80, 'level': 1},
    ]
}

# Use highest-scoring level-2 concept
field = max(
    [c for c in openalex_data['concepts'] if c['level'] == 2],
    key=lambda c: c['score']
)['display_name']
```

---

## 5. Query Intent Detection: Adaptive Weights

### Keyword-Based Rules

```python
def detect_query_intent(query: str) -> str:
    """
    Classify user query into intent categories.
    
    Returns: 'review', 'recent', 'method', 'dataset', 'balanced'
    """
    query_lower = query.lower()
    
    # Review intent: User wants overview/summary
    if any(kw in query_lower for kw in ['review', 'overview', 'survey', 'meta-analysis']):
        return 'review'
    
    # Recent intent: User wants latest research
    if any(kw in query_lower for kw in ['recent', 'latest', 'new', '2024', '2025']):
        return 'recent'
    
    # Method intent: User wants protocols/techniques
    if any(kw in query_lower for kw in ['method', 'protocol', 'technique', 'how to', 'analysis']):
        return 'method'
    
    # Dataset intent: User wants data, not papers
    if any(kw in query_lower for kw in ['dataset', 'data', 'GSE', 'GEO']):
        return 'dataset'
    
    # Default: Balanced
    return 'balanced'

def get_intent_weights(intent: str) -> dict:
    """
    Return scoring weights optimized for query intent.
    """
    INTENT_WEIGHTS = {
        'review': {
            'title': 0.30,
            'abstract': 0.20,
            'citations': 0.40,  # Highly-cited reviews
            'recency': 0.10,    # Recent reviews less important
        },
        'recent': {
            'title': 0.35,
            'abstract': 0.25,
            'citations': 0.05,  # Citations barely matter
            'recency': 0.35,    # Recency most important
        },
        'method': {
            'title': 0.30,
            'abstract': 0.30,
            'citations': 0.30,  # Well-cited methods
            'recency': 0.10,    # Methods age well
        },
        'dataset': {
            'title': 0.40,
            'abstract': 0.40,
            'citations': 0.05,  # Datasets rarely cited properly
            'recency': 0.15,    # Recent data preferred
        },
        'balanced': {
            'title': 0.40,
            'abstract': 0.30,
            'citations': 0.15,  # Moderate citation weight
            'recency': 0.15,    # Moderate recency weight
        }
    }
    
    return INTENT_WEIGHTS.get(intent, INTENT_WEIGHTS['balanced'])
```

### Usage in Ranking

```python
async def rank_publications(
    self,
    publications: List[Publication],
    query: str
) -> List[Publication]:
    """
    Rank publications with intent-aware weights.
    """
    # Detect user intent from query
    intent = detect_query_intent(query)
    weights = get_intent_weights(intent)
    
    # Update ranker weights
    self.weights = weights
    
    # Score publications
    for pub in publications:
        pub.score = self._score_publication(pub, query)
    
    # Sort by score
    return sorted(publications, key=lambda p: p.score, reverse=True)
```

**Examples:**

```python
# Query 1: "review of CRISPR gene editing"
intent = 'review'
weights = {'title': 0.30, 'abstract': 0.20, 'citations': 0.40, 'recency': 0.10}
# → Highly-cited review papers rank highest

# Query 2: "recent Alzheimer's breakthroughs 2024"  
intent = 'recent'
weights = {'title': 0.35, 'abstract': 0.25, 'citations': 0.05, 'recency': 0.35}
# → Papers from 2024 rank highest regardless of citations

# Query 3: "RNA-seq analysis method"
intent = 'method'
weights = {'title': 0.30, 'abstract': 0.30, 'citations': 0.30, 'recency': 0.10}
# → Well-cited methods papers rank highest

# Query 4: "breast cancer GEO datasets"
intent = 'dataset'
weights = {'title': 0.40, 'abstract': 0.40, 'citations': 0.05, 'recency': 0.15}
# → Title/abstract match most important, citations ignored
```

---

## 6. Implementation Recommendation Summary

### Tier 1: Quick Wins (Week 4, 4-6 hours)

**RECOMMENDED APPROACH:**

```python
# Step 1: Keep current 3-tier dampening as baseline
# Step 2: Add citation velocity calculation (simple version)
# Step 3: Add query intent detection (keyword-based)
# Step 4: Combine with weighted ensemble

def _calculate_citation_component(
    self,
    citations: int,
    age_years: float
) -> Tuple[float, dict]:
    """
    Enhanced citation scoring with velocity.
    
    Combines:
    - Absolute citation count (dampened)
    - Citations per year (velocity)
    """
    # Existing method: absolute citations
    absolute_score = self._calculate_citation_score(citations)
    
    # New: citations per year
    citations_per_year = citations / max(age_years, 0.1)
    velocity_score = min(citations_per_year / 50, 1.0)  # 50/year = max
    
    # Weighted combination: 60% absolute, 40% velocity
    combined = absolute_score * 0.6 + velocity_score * 0.4
    
    breakdown = {
        'absolute': absolute_score,
        'velocity': velocity_score,
        'citations_per_year': citations_per_year,
        'combined': combined
    }
    
    return combined, breakdown

# Then use intent-aware weights
intent = detect_query_intent(query)
weights = get_intent_weights(intent)

# Final score
score = (
    title_match * weights['title'] +
    abstract_match * weights['abstract'] +
    citation_component * weights['citations'] +
    recency_score * weights['recency']
)
```

**Effort:** 4-6 hours  
**Risk:** Low (all calculations local, no API dependencies)  
**Impact:** Medium (improves recency handling, query-specific optimization)

### Tier 2: API Integration (Month 2, 1 week)

```python
# Add Semantic Scholar client
from omics_oracle_v2.lib.publications.semantic_scholar import SemanticScholarClient

# In publication pipeline:
async def enrich_with_metrics(self, publications: List[Publication]):
    """
    Enhance publications with Semantic Scholar metrics.
    """
    ss_client = SemanticScholarClient()
    
    for pub in publications:
        if pub.doi:
            metrics = await ss_client.get_paper_metrics(pub.doi)
            if metrics:
                pub.influential_citations = metrics['influential_citation_count']
                pub.citations_last_3_years = metrics['citations_last_3_years']
                pub.author_h_indices = [a['h_index'] for a in metrics['authors']]

# In ranker:
def _calculate_enhanced_citation_score(self, pub: Publication):
    if hasattr(pub, 'influential_citations'):
        # Use Semantic Scholar enhanced scoring
        return self._semantic_scholar_score(pub)
    else:
        # Fall back to simple scoring
        return self._calculate_citation_score(pub.citations)
```

**Effort:** 1 week  
**Risk:** Medium (API rate limits, data coverage)  
**Impact:** High (significant quality improvement)

### Tier 3: NOT RECOMMENDED (Yet)

**DON'T implement:**
- PageRank citation network analysis
- Machine learning ranking models
- Altmetrics integration
- Author reputation boosting (bias concern)

**Reasons:**
- Too complex for current scale
- Requires infrastructure we don't have
- User feedback needed first to validate simpler approaches

---

## 7. Testing Strategy

### Test Cases for Citation Scoring

```python
# tests/unit/test_citation_scoring.py

def test_recent_paper_beats_old_paper_with_same_velocity():
    """
    Recent paper (2 years, 100 cites) should score similar to
    old paper (20 years, 1000 cites) - both have 50 cites/year
    """
    ranker = PublicationRanker()
    
    recent = Publication(
        title="Recent breakthrough",
        citations=100,
        publication_date="2023-01-01"
    )
    
    old = Publication(
        title="Old classic",
        citations=1000,
        publication_date="2005-01-01"
    )
    
    recent_score = ranker._calculate_citation_component(100, 2.0)
    old_score = ranker._calculate_citation_component(1000, 20.0)
    
    # Velocity is same (50 cites/year), scores should be close
    assert abs(recent_score - old_score) < 0.1


def test_accelerating_paper_beats_declining_paper():
    """
    Paper with increasing citations should beat paper with decreasing citations.
    """
    # Requires Semantic Scholar data
    accelerating = Publication(
        title="Trending paper",
        citations=200,
        citations_last_3_years=150,  # 50/year recently
        publication_date="2020-01-01"  # 5 years old
    )
    
    declining = Publication(
        title="Fading classic",
        citations=2000,
        citations_last_3_years=100,  # 33/year recently (was 400/year historically)
        publication_date="2020-01-01"  # Same age
    )
    
    acc_score = ranker._calculate_enhanced_citation_score(accelerating)
    dec_score = ranker._calculate_enhanced_citation_score(declining)
    
    assert acc_score > dec_score


def test_query_intent_changes_ranking():
    """
    Same papers rank differently based on query intent.
    """
    papers = [
        Publication(title="Review of cancer genomics", citations=5000, date="2010-01-01"),
        Publication(title="Novel cancer mutation discovery", citations=50, date="2024-01-01")
    ]
    
    # Intent: review → old highly-cited paper wins
    review_ranked = ranker.rank_publications(papers, query="review of cancer")
    assert review_ranked[0].title == "Review of cancer genomics"
    
    # Intent: recent → new paper wins
    recent_ranked = ranker.rank_publications(papers, query="recent cancer discoveries 2024")
    assert recent_ranked[0].title == "Novel cancer mutation discovery"
```

### Benchmark Tests

```python
# tests/benchmarks/test_ranking_quality.py

GROUND_TRUTH_QUERIES = [
    {
        'query': 'CRISPR gene editing',
        'expected_top_papers': [
            'Multiplex genome engineering using CRISPR/Cas systems',  # Foundational
            'Improved CRISPR-Cas9 gene editing',  # High impact
            'CRISPR-Cas9 guide design',  # Methodology
        ]
    },
    {
        'query': 'recent COVID-19 variants 2024',
        'expected_top_papers': [
            # All from 2024, specific variant papers
            'Omicron BA.2.86 structural analysis',
            'JN.1 variant immune escape',
        ]
    }
]

def test_ranking_matches_expert_judgment():
    """
    Compare our rankings to expert-curated lists.
    """
    for test_case in GROUND_TRUTH_QUERIES:
        results = search_publications(test_case['query'])
        top_10_titles = [r.title for r in results[:10]]
        
        # At least 2 of the expected papers should be in top 10
        matches = sum(
            1 for expected in test_case['expected_top_papers']
            if any(expected.lower() in title.lower() for title in top_10_titles)
        )
        
        assert matches >= 2, f"Only {matches} expected papers in top 10 for: {test_case['query']}"
```

---

## 8. Final Recommendation

**IMPLEMENT TIER 1 (Week 4):**

1. ✅ Add citations-per-year calculation (simple, no API needed)
2. ✅ Add query intent detection (keyword-based)
3. ✅ Combine citation absolute + velocity with 60/40 weighting
4. ✅ Test with edge cases (recent vs old papers)
5. ✅ Document scoring clearly for users

**DEFER TO MONTH 2:**

1. Semantic Scholar API integration (requires testing rate limits)
2. Field normalization (requires field detection method)
3. User feedback collection and analysis

**DO NOT IMPLEMENT:**

1. PageRank / citation network
2. Machine learning ranking
3. Journal Impact Factor
4. Altmetrics

---

**This gives us a measurable improvement without over-engineering.**

