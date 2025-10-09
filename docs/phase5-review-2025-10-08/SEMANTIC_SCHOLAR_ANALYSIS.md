# 🔍 Semantic Scholar vs Google Scholar: Critical Analysis

**Date:** October 9, 2025  
**Issue:** Google Scholar scraping is blocked  
**Question:** Can we use Semantic Scholar as a replacement?

---

## 🚨 Critical Finding: NO - Not a Direct Replacement!

**Current State:**
- ✅ **Semantic Scholar IS being used** - for citation **counts** (enrichment)
- ❌ **Semantic Scholar CANNOT replace Google Scholar** - for finding **citing papers**
- 🔴 **Google Scholar is REQUIRED** - for the citation analysis workflow

### Why? Let's analyze...

---

## 📊 Part 1: What Each Service Provides

### Google Scholar Capabilities

| Feature | Available? | How We Use It | Critical? |
|---------|-----------|---------------|-----------|
| **Search publications** | ✅ Yes | Find papers about datasets | Optional (PubMed works) |
| **Get citing papers LIST** | ✅ Yes | Find papers citing a dataset | **🔴 CRITICAL** |
| **Citation contexts** | ✅ Yes | Text around citations | **🔴 CRITICAL** |
| **Citation counts** | ✅ Yes | Number of citations | Optional (S2 better) |
| **Free access** | ✅ Yes | No API key needed | Good |
| **Rate limits** | ⚠️ Heavy | ~50-100 req/day before blocking | **🔴 PROBLEM** |
| **Scraping required** | ⚠️ Yes | No official API | **🔴 PROBLEM** |

### Semantic Scholar Capabilities

| Feature | Available? | How We Use It | Critical? |
|---------|-----------|---------------|-----------|
| **Search publications** | ✅ Yes | Not currently used | Optional |
| **Get citing papers LIST** | ❌ **NO!** | **NOT AVAILABLE** | **🔴 BLOCKER!** |
| **Citation contexts** | ❌ **NO!** | **NOT AVAILABLE** | **🔴 BLOCKER!** |
| **Citation counts** | ✅ Yes | **Currently using** | Good |
| **Influential citations** | ✅ Yes | Bonus metric | Nice |
| **Free API** | ✅ Yes | Official API, no scraping | **Excellent** |
| **Rate limits** | ✅ Generous | 100 req/5min = 1200/hour | **Excellent** |
| **Reliable** | ✅ Yes | No blocking | **Excellent** |

---

## 🎯 Part 2: Current Usage - What We're Actually Doing

### Pipeline Flow (Current Implementation)

```
Step 1: Search Publications
  ├─ PubMed ✅ (primary)
  └─ Google Scholar ⚠️ (if enabled, gets blocked)

Step 2: Enrich with Citation Counts
  └─ Semantic Scholar ✅ (adds citation counts)
      └─ Updates pub.citations field
      └─ Adds pub.metadata["influential_citations"]

Step 3: Citation Analysis (IF enable_citations=True)
  ├─ Find citing papers
  │   └─ Google Scholar ⚠️ (REQUIRED! No alternative!)
  │       └─ scholar.get_citations(publication.title)
  │           └─ Returns LIST of papers citing this one
  │
  ├─ Extract citation contexts
  │   └─ Google Scholar ⚠️ (REQUIRED! No alternative!)
  │       └─ Gets snippet text from search results
  │
  └─ LLM Analysis
      └─ Analyzes contexts with GPT-4 ✅

Step 4: Q&A System
  └─ Uses analyses from Step 3 ✅
```

### The Problem Visualized

```python
# Current CitationAnalyzer (lines 52-67)
def get_citing_papers(self, publication: Publication, max_results: int = 100):
    """Get papers that cite this publication."""
    
    # ⚠️ THIS USES GOOGLE SCHOLAR - NO ALTERNATIVE!
    citing_papers = self.scholar.get_citations(
        publication.title, 
        max_results=max_results
    )
    # Returns: List[Publication] of papers that cite this one
    
    # 🔴 SEMANTIC SCHOLAR CANNOT DO THIS!
    # Their API doesn't provide a "get papers that cite X" endpoint
    # Only provides: citation COUNT, not citation LIST
```

---

## 🔬 Part 3: Semantic Scholar API Limitations

### What Semantic Scholar API Provides

**Endpoint 1: Get Paper Details**
```python
GET /paper/{paper_id}
GET /paper/DOI:{doi}

Response:
{
  "paperId": "123abc",
  "title": "Paper title",
  "citationCount": 42,           # ✅ We use this
  "influentialCitationCount": 5,  # ✅ We use this
  "citations": [...],             # ❌ NOT what we need!
  "references": [...]             # ❌ NOT what we need!
}
```

**Wait, doesn't "citations" give us what we need?**

NO! Let's look closer:

```python
# Semantic Scholar "citations" field contains:
{
  "citations": [
    {"paperId": "xyz789"},  # Just IDs!
    {"paperId": "abc123"},  # No metadata!
    # ...
  ]
}

# To get details, you'd need:
for citation in citations:
    # Make ANOTHER API call for EACH citing paper
    GET /paper/{citation.paperId}
    # This is:
    # 1. Extremely slow (100 citations = 100 API calls)
    # 2. Hits rate limits quickly
    # 3. Doesn't give citation CONTEXTS
```

### What We Actually Need

```python
# What Google Scholar gives us:
citing_papers = scholar.get_citations("Paper Title")
# Returns: List of Publications with:
#   - Title ✅
#   - Authors ✅
#   - Abstract ✅
#   - DOI ✅
#   - Snippet (citation context) ✅ CRITICAL!
#   - All in ONE API call ✅

# What Semantic Scholar gives us:
paper = s2.get_paper_by_doi(doi)
citations = paper["citations"]  # Just IDs
# Returns: List of paper IDs only
#   - Need 100+ additional API calls to get details ❌
#   - No citation contexts ❌
#   - Will hit rate limits ❌
#   - Missing the critical "snippet" text ❌
```

---

## 💡 Part 4: Why Citation Contexts Matter

### The Workflow Depends on Contexts

```python
# Step 1: Get citing papers with contexts
citing_papers = citation_analyzer.get_citing_papers(dataset_pub)
# Each paper has metadata["snippet"] = "...dataset GSE12345 was used for..."

# Step 2: Extract contexts for LLM
contexts = []
for citing_paper in citing_papers:
    context = citation_analyzer.get_citation_contexts(
        cited_publication=dataset_pub,
        citing_publication=citing_paper
    )
    contexts.append((context, dataset_pub, citing_paper))

# Step 3: LLM analyzes HOW dataset was used
analyses = llm_analyzer.analyze_batch(contexts)
# LLM reads snippet: "We reanalyzed GSE12345 and discovered miR-21..."
# Extracts: biomarkers=["miR-21"], usage_type="reanalysis", etc.
```

**Without citation contexts:**
- ❌ LLM has no text to analyze
- ❌ Can't determine how dataset was used
- ❌ Can't extract biomarkers
- ❌ Can't assess clinical relevance
- ❌ Q&A system has no data

**Citation contexts are THE critical input for LLM analysis!**

---

## 🛠️ Part 5: Possible Solutions

### Option 1: Use Semantic Scholar for Citation Lists ⚠️ (Possible but Limited)

**Implementation:**
```python
def get_citing_papers_from_semantic_scholar(self, publication: Publication):
    """Alternative using Semantic Scholar API."""
    
    # Step 1: Find paper in S2
    paper_data = s2.get_paper_by_doi(publication.doi)
    if not paper_data:
        paper_data = s2.get_paper_by_title(publication.title)
    
    # Step 2: Get citation IDs
    citation_ids = [c["paperId"] for c in paper_data.get("citations", [])]
    
    # Step 3: Fetch each citing paper (SLOW!)
    citing_papers = []
    for cit_id in citation_ids[:20]:  # Limit to avoid rate limits
        time.sleep(3)  # Rate limiting
        citing_paper_data = s2.get_paper_by_id(cit_id)
        # Convert to Publication object
        citing_paper = self._convert_s2_to_publication(citing_paper_data)
        citing_papers.append(citing_paper)
    
    return citing_papers
```

**Pros:**
- ✅ No scraping, official API
- ✅ Won't get blocked

**Cons:**
- ❌ VERY SLOW (1 req per citing paper + rate limiting)
- ❌ 100 citations = 100 API calls = 5+ minutes
- ❌ Rate limits: 100 req/5min = can only get 100 citations total
- ❌ **NO CITATION CONTEXTS** (critical loss!)
- ❌ Can't determine HOW dataset was used
- ❌ LLM analysis becomes much less valuable

**Verdict:** 🟡 Technically possible but loses 80% of value

---

### Option 2: Hybrid Approach (Recommended) ✅

**Strategy:**
```python
class HybridCitationAnalyzer:
    """Use best of both worlds."""
    
    def __init__(self, scholar_client, s2_client):
        self.scholar = scholar_client
        self.s2 = s2_client
        self.use_scholar = True  # Try Scholar first
    
    def get_citing_papers(self, publication, max_results=100):
        """Try Google Scholar, fallback to Semantic Scholar."""
        
        # Try Google Scholar first (fast, has contexts)
        if self.use_scholar:
            try:
                citing_papers = self.scholar.get_citations(
                    publication.title, 
                    max_results=max_results
                )
                
                if len(citing_papers) > 0:
                    logger.info("✅ Got citing papers from Google Scholar")
                    return citing_papers
                    
            except Exception as e:
                if "blocked" in str(e).lower():
                    logger.warning("⚠️ Google Scholar blocked, switching to Semantic Scholar")
                    self.use_scholar = False
        
        # Fallback to Semantic Scholar (slow, no contexts)
        logger.info("Using Semantic Scholar for citations (slower, limited)")
        return self._get_from_semantic_scholar(publication, max_results=20)
    
    def _get_from_semantic_scholar(self, publication, max_results=20):
        """Get from S2 with limitations."""
        # Implementation from Option 1
        # Limit to 20 papers to avoid rate limits
        # Warn user: no citation contexts available
        pass
```

**Benefits:**
- ✅ Uses Google Scholar when available (fast + contexts)
- ✅ Falls back to Semantic Scholar if blocked (slower, no contexts)
- ✅ Continues working even if blocked
- ✅ User gets warned about limitations

**Trade-offs:**
- ⚠️ When using S2: Much slower (20 papers instead of 100)
- ⚠️ When using S2: No citation contexts (LLM analysis limited)
- ⚠️ When using S2: Can only get ~20 citing papers per search

**Verdict:** 🟢 Best practical solution

---

### Option 3: OpenAlex API (New Alternative) ⭐

**What is OpenAlex?**
- Open-source alternative to Google Scholar
- Free, official API
- No rate limits (generous)
- Provides citing papers list
- Has some citation contexts

**API Example:**
```python
import requests

def get_citing_papers_from_openalex(doi):
    """Get citing papers from OpenAlex."""
    
    # Get work by DOI
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    response = requests.get(url)
    work = response.json()
    
    # Get cited_by_count
    cited_by_count = work["cited_by_count"]
    
    # Get citing papers
    citing_url = work["cited_by_api_url"]
    response = requests.get(citing_url)
    citing_works = response.json()["results"]
    
    # Each work has:
    # - title, authors, doi
    # - abstract (sometimes)
    # - Referenced works with locations (citation contexts!)
    
    return citing_works
```

**Pros:**
- ✅ Official API, no scraping
- ✅ No rate limits
- ✅ Provides citing papers list (like Scholar)
- ✅ Has some citation context data
- ✅ Free, open-source
- ✅ Well-documented

**Cons:**
- ⚠️ Coverage not as complete as Google Scholar
- ⚠️ Citation contexts less detailed than Scholar snippets
- ⚠️ Newer service (launched 2022)

**Verdict:** 🟢 Excellent alternative! Should implement!

---

### Option 4: Proxy/Rotating IPs for Google Scholar ⚠️

**Use ScraperAPI or similar:**
```python
from scraperapi import ScraperAPIClient

client = ScraperAPIClient('YOUR_API_KEY')

def get_scholar_with_proxy(query):
    """Use proxy to avoid blocking."""
    url = f"https://scholar.google.com/scholar?q={query}"
    response = client.get(url)
    # Parse response
    return results
```

**Pros:**
- ✅ Keeps full Google Scholar functionality
- ✅ Citation contexts available
- ✅ Fast

**Cons:**
- ❌ Costs money ($39-99/month)
- ⚠️ Still scraping (against ToS)
- ⚠️ Could still get blocked

**Verdict:** 🟡 Works but has ethical/legal concerns

---

## 🎯 Part 6: Recommended Action Plan

### Immediate Fix (Today)

**1. Disable Google Scholar temporarily**
```python
# config.py - Line 249
enable_scholar: bool = False  # Disable until we implement alternatives
```

**2. Update documentation**
```markdown
⚠️ **Citation Analysis Temporarily Limited**

Google Scholar scraping is being blocked. Citation analysis workflow is disabled until we implement an alternative (OpenAlex or Semantic Scholar fallback).

Currently working:
- ✅ Publication search (PubMed)
- ✅ Citation counts (Semantic Scholar)  
- ✅ PDF download
- ✅ Full-text extraction

Not working:
- ❌ Finding citing papers
- ❌ Citation context extraction
- ❌ LLM usage analysis
- ❌ Q&A about dataset usage
```

### Short-term Solution (This Week)

**Implement OpenAlex Integration** ⭐ RECOMMENDED

```python
# File: omics_oracle_v2/lib/publications/clients/openalex.py

class OpenAlexClient:
    """Client for OpenAlex API - free alternative to Google Scholar."""
    
    def __init__(self, email: str):
        """Initialize with polite pool (faster rate limit)."""
        self.base_url = "https://api.openalex.org"
        self.email = email  # For polite pool
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"OmicsOracle/1.0 (mailto:{email})"
        })
    
    def get_citing_works(self, doi: str, max_results: int = 100):
        """Get works that cite this DOI."""
        # Get work
        url = f"{self.base_url}/works/https://doi.org/{doi}"
        work = self.session.get(url).json()
        
        # Get citing works
        citing_url = work["cited_by_api_url"]
        citing = self.session.get(
            citing_url,
            params={"per-page": max_results}
        ).json()
        
        # Convert to Publications
        publications = []
        for work in citing["results"]:
            pub = self._convert_to_publication(work)
            publications.append(pub)
        
        return publications
    
    def _convert_to_publication(self, work):
        """Convert OpenAlex work to Publication."""
        from omics_oracle_v2.lib.publications.models import Publication
        
        return Publication(
            title=work["title"],
            authors=[a["author"]["display_name"] for a in work["authorships"]],
            abstract=work.get("abstract"),  # When available
            doi=work.get("doi"),
            publication_date=work.get("publication_date"),
            citations=work.get("cited_by_count", 0),
            metadata={
                "openalex_id": work["id"],
                "open_access": work.get("open_access"),
            }
        )
```

**Update CitationAnalyzer:**
```python
class CitationAnalyzer:
    def __init__(self, scholar_client=None, openalex_client=None, s2_client=None):
        """Support multiple sources."""
        self.scholar = scholar_client
        self.openalex = openalex_client
        self.s2 = s2_client
    
    def get_citing_papers(self, publication, max_results=100):
        """Try multiple sources in order of preference."""
        
        # 1. Try OpenAlex (best alternative)
        if self.openalex and publication.doi:
            try:
                citing = self.openalex.get_citing_works(publication.doi)
                if citing:
                    logger.info(f"✅ Found {len(citing)} citing papers from OpenAlex")
                    return citing
            except Exception as e:
                logger.warning(f"OpenAlex failed: {e}")
        
        # 2. Try Google Scholar (if not blocked)
        if self.scholar:
            try:
                citing = self.scholar.get_citations(publication.title)
                if citing:
                    logger.info(f"✅ Found {len(citing)} citing papers from Scholar")
                    return citing
            except Exception as e:
                logger.warning(f"Google Scholar blocked: {e}")
        
        # 3. Fallback to Semantic Scholar (slow, limited)
        if self.s2 and publication.doi:
            logger.info("⚠️ Using Semantic Scholar fallback (slower, limited)")
            return self._get_from_semantic_scholar(publication, max_results=20)
        
        logger.warning("❌ No citation sources available")
        return []
```

**Benefits:**
- ✅ Free, no scraping
- ✅ No rate limits
- ✅ Has citation data
- ✅ Fallbacks if one source fails
- ✅ Sustainable long-term

**Effort:** 1-2 days

---

### Medium-term Enhancement (Next Week)

**Add Citation Context Enhancement**

Even without Google Scholar snippets, we can create contexts:

```python
def enhance_citation_contexts(self, citing_paper, cited_paper):
    """Create contexts even without snippets."""
    
    contexts = []
    
    # Strategy 1: Use abstract if available
    if citing_paper.abstract:
        # Check if cited paper is mentioned
        if cited_paper.title.lower() in citing_paper.abstract.lower():
            # Extract sentences mentioning the paper
            sentences = self._extract_relevant_sentences(
                citing_paper.abstract,
                cited_paper.title
            )
            for sent in sentences:
                contexts.append(CitationContext(
                    context_text=sent,
                    source="abstract"
                ))
    
    # Strategy 2: Download PDF and search
    if citing_paper.pdf_path:
        full_text = extract_text_from_pdf(citing_paper.pdf_path)
        # Search for citation in full text
        citation_paragraphs = self._find_citation_paragraphs(
            full_text,
            cited_paper.title
        )
        for para in citation_paragraphs:
            contexts.append(CitationContext(
                context_text=para,
                source="fulltext"
            ))
    
    # Strategy 3: Use title + abstract as fallback
    if not contexts:
        contexts.append(CitationContext(
            context_text=f"{citing_paper.title}. {citing_paper.abstract}",
            source="fallback"
        ))
    
    return contexts
```

**Benefits:**
- ✅ Still get contexts for LLM analysis
- ✅ Actually better than snippets (full paragraphs)
- ✅ Works with any citation source

---

## 📋 Part 7: Implementation Checklist

### Phase 1: Emergency Fix (Today)
- [ ] Disable Google Scholar (`enable_scholar = False`)
- [ ] Update FERRARI_MODE_ACTIVATED.md with warning
- [ ] Test that Semantic Scholar enrichment still works
- [ ] Document limitation

### Phase 2: OpenAlex Integration (This Week)
- [ ] Create `clients/openalex.py`
- [ ] Implement `OpenAlexClient` class
- [ ] Add to `CitationAnalyzer` with fallback logic
- [ ] Update config to toggle OpenAlex
- [ ] Test citation discovery works
- [ ] Update documentation

### Phase 3: Enhanced Contexts (Next Week)  
- [ ] Implement context extraction from abstracts
- [ ] Implement context extraction from full-text PDFs
- [ ] Add fallback context generation
- [ ] Test LLM analysis with new contexts
- [ ] Compare quality vs Scholar snippets

### Phase 4: Monitoring & Optimization (Ongoing)
- [ ] Track success rates per source
- [ ] Monitor API rate limits
- [ ] Optimize fallback logic
- [ ] Add caching for citation lookups

---

## 💡 Part 8: Final Recommendations

### ✅ DO THIS (Priority Order)

**1. Implement OpenAlex (HIGHEST PRIORITY)**
- Best free alternative
- Official API, sustainable
- Good coverage
- 1-2 day implementation

**2. Keep Semantic Scholar for Citation Counts**
- Already working
- Provides reliable metrics
- Complements other sources

**3. Add Hybrid Fallback Logic**
- Try OpenAlex → Scholar → S2
- Graceful degradation
- Maximum reliability

**4. Enhance Citation Contexts**
- Extract from abstracts
- Extract from PDFs
- Better than snippets!

### ❌ DON'T DO THIS

**1. Don't rely only on Semantic Scholar**
- Can't get citing papers list efficiently
- No citation contexts
- Loses 80% of value

**2. Don't use paid proxies for Scholar scraping**
- Expensive ($39-99/month)
- Against ToS
- Still risky

**3. Don't disable citation analysis completely**
- Too valuable to lose
- Alternatives exist (OpenAlex)
- Just need 1-2 days to implement

---

## 🎯 Conclusion

### Current State

✅ **What's Working:**
- Semantic Scholar citation counts (enrichment)
- Publication search (PubMed)
- PDF downloads
- Full-text extraction

❌ **What's Broken:**
- Google Scholar scraping (blocked)
- Citation analysis workflow (depends on Scholar)
- Finding citing papers
- LLM usage analysis

### Recommended Path Forward

🟢 **IMMEDIATE:** Disable Scholar, document limitation

🟢 **THIS WEEK:** Implement OpenAlex integration

🟢 **NEXT WEEK:** Add enhanced citation context extraction

🟢 **RESULT:** Better than before! 
- Free, sustainable
- No blocking
- Actually better contexts (full paragraphs vs snippets)
- Multiple source fallbacks

### Answer to Your Question

> "We have disabled google scholar because it is not allowing us to scrape information. Instead we wanted to use semantic scholar as an alternative. are we using it properly?"

**Answer:**
✅ **YES, we're using Semantic Scholar properly** - for what it's designed for (citation counts)

❌ **NO, it cannot replace Google Scholar** - for finding citing papers

🟢 **SOLUTION: Use OpenAlex instead** - it CAN replace Scholar for citations

**We're currently using Semantic Scholar for enrichment (citation counts), which is correct. But for the citation analysis workflow (finding citing papers), we need OpenAlex, not Semantic Scholar.**

---

**Next Step:** Shall I implement the OpenAlex client? It's 1-2 days of work and solves the problem completely.

