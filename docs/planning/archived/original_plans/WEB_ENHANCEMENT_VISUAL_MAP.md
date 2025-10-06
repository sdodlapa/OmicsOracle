# Web Enhancement Mapping - Visual Guide

**Quick Reference:** Which web methods enhance which modules/phases

---

## 🗺️ Enhancement Mapping by Module

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: PUBLICATION MINING                  │
│                         (Weeks 1-2)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EXISTING (API Only):                                           │
│  ├── PubMedClient          → 35M articles                       │
│  ├── PMCClient             → 20% full-text                      │
│  └── EuropePMCClient       → Better coverage                    │
│                                                                 │
│  🆕 WEB ENHANCEMENTS:                                           │
│  ├── GoogleScholarClient   → +Citation metrics                 │
│  │   ├── Citation counts (papers citing this)                  │
│  │   ├── H-index & author metrics                              │
│  │   ├── "Cited by" links                                      │
│  │   ├── Related articles discovery                            │
│  │   └── PDF link detection                                    │
│  │                                                              │
│  └── TrendingTopicsDetector → +Trend analysis                  │
│      ├── Google Trends (search volume)                         │
│      ├── Emerging topics detection                             │
│      ├── Hot genes/diseases                                    │
│      └── Query suggestions based on trends                     │
│                                                                 │
│  IMPACT: +150% coverage, citation analysis enabled             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 2: PDF PROCESSING                     │
│                          (Week 3)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EXISTING (API Only):                                           │
│  ├── PDFDownloader                                              │
│  │   ├── PMC FTP          → 20% coverage                       │
│  │   └── Unpaywall API    → 25% coverage                       │
│  │                                                              │
│  ├── GROBIDClient          → High quality parsing              │
│  └── Fallback parsers      → pdfminer, PyPDF2                  │
│                                                                 │
│  🆕 WEB ENHANCEMENTS:                                           │
│  └── WebPDFScraper         → +5 new PDF sources                │
│      ├── Google Scholar PDF links    (direct PDFs)             │
│      ├── ResearchGate               (author uploads)           │
│      ├── Academia.edu               (academic profiles)        │
│      ├── Institutional repos        (arXiv, bioRxiv, etc.)     │
│      ├── Publisher sites            (JavaScript rendering)     │
│      └── Playwright automation      (modern web scraping)      │
│                                                                 │
│  METHODS:                                                       │
│  - JavaScript rendering (Playwright)                           │
│  - Multi-source fallback (try 7 sources)                       │
│  - PDF quality validation                                      │
│  - Preprint detection                                          │
│                                                                 │
│  IMPACT: 40% → 70-80% PDF acquisition success                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 3: QUERY ENHANCEMENT                   │
│                          (Week 4)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EXISTING (Ontology Only):                                      │
│  ├── QueryAnalyzer         → Intent detection                  │
│  ├── QueryEnhancer         → MeSH ontology                     │
│  ├── OntologyMapper        → Fixed vocabularies                │
│  └── QueryValidator        → Feasibility checks                │
│                                                                 │
│  🆕 WEB ENHANCEMENTS:                                           │
│  ├── Google Trends Integration                                 │
│  │   ├── Search volume over time                               │
│  │   ├── Rising/declining topics                               │
│  │   ├── Related queries                                       │
│  │   └── Trending keywords                                     │
│  │                                                              │
│  ├── Google Autocomplete                                       │
│  │   ├── Real user query patterns                              │
│  │   ├── "People also search for"                              │
│  │   └── Query completion suggestions                          │
│  │                                                              │
│  └── Scholar Alerts Integration                                │
│      ├── New papers in field                                   │
│      ├── Emerging techniques                                   │
│      └── Hot research areas                                    │
│                                                                 │
│  METHODS:                                                       │
│  - pytrends library (Google Trends API)                        │
│  - Google autocomplete endpoint                                │
│  - Trend signal combination                                    │
│                                                                 │
│  IMPACT: +40% better query suggestions, trend-aware            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 4: KNOWLEDGE EXTRACTION                  │
│                        (Weeks 5-6)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EXISTING (NER Only):                                           │
│  ├── EntityExtractor       → scispaCy NER                      │
│  ├── RelationshipExtractor → Text-based                        │
│  ├── CitationAnalyzer      → Network analysis                  │
│  └── KnowledgeGraph        → From extracted data               │
│                                                                 │
│  🆕 WEB ENHANCEMENTS:                                           │
│  └── WebKnowledgeEnricher  → +External validation              │
│      ├── Wikipedia/Wikidata Integration                        │
│      │   ├── Entity descriptions (layman + technical)          │
│      │   ├── Canonical names (aliases → standard)              │
│      │   ├── Structured relationships (is-a, part-of)          │
│      │   └── Cross-lingual matching                            │
│      │                                                          │
│      ├── Google Knowledge Graph                                │
│      │   ├── Entity IDs (canonical identifiers)                │
│      │   ├── Entity types (gene, disease, protein)             │
│      │   ├── Related entities                                  │
│      │   └── Popularity scores                                 │
│      │                                                          │
│      └── DBpedia (Structured Knowledge)                        │
│          ├── Ontology alignment                                │
│          ├── SPARQL queries                                    │
│          └── Semantic relationships                            │
│                                                                 │
│  USE CASES:                                                     │
│  - Entity disambiguation ("TP53" gene vs protein)              │
│  - Canonical name resolution                                   │
│  - External knowledge enrichment                               │
│  - Popularity scoring                                          │
│                                                                 │
│  IMPACT: +10% entity accuracy (80% → 90%)                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 5: INTEGRATION                          │
│                        (Weeks 7-8)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EXISTING (Basic Ranking):                                      │
│  ├── MultiSourceRanker     → Relevance + recency              │
│  ├── ResultFusion          → Deduplication                     │
│  └── DatasetPublicationLinker → Cross-reference               │
│                                                                 │
│  🆕 WEB ENHANCEMENTS:                                           │
│  └── Web Signal Integration → +Multi-factor ranking            │
│      ├── Citation Metrics (from GoogleScholarClient)           │
│      │   ├── Citation count                                    │
│      │   ├── Citation velocity (trending)                      │
│      │   ├── H-index influence                                 │
│      │   └── Network centrality                                │
│      │                                                          │
│      ├── Trend Signals (from TrendingTopicsDetector)           │
│      │   ├── Search volume trend                               │
│      │   ├── Topic emergence score                             │
│      │   └── Recency boost for trending                        │
│      │                                                          │
│      └── Quality Signals (from WebPDFScraper)                  │
│          ├── PDF availability                                  │
│          ├── Source credibility                                │
│          ├── Version tracking                                  │
│          └── Download statistics                               │
│                                                                 │
│  RANKING ALGORITHM:                                             │
│  score = (relevance × 0.3) +                                   │
│          (citations × 0.25) +                                  │
│          (h_index × 0.15) +                                    │
│          (trend_score × 0.15) +                                │
│          (recency × 0.10) +                                    │
│          (quality × 0.05)                                      │
│                                                                 │
│  IMPACT: +25% ranking quality (nDCG improvement)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Feature-to-Method Mapping

### Want Citations? → Google Scholar
```python
Feature: Citation analysis, h-index, citation graphs
Method:  GoogleScholarClient (scholarly library)
Phase:   Week 1, Day 3-5
Impact:  NEW capability (not possible with PubMed API)
```

### Want More PDFs? → Web Scraping
```python
Feature: 70%+ PDF success rate
Methods: WebPDFScraper (Playwright + multiple sources)
         - Google Scholar PDF links
         - ResearchGate scraping
         - Institutional repositories
Phase:   Week 3, Day 3-5
Impact:  +75% PDF acquisition (40% → 70-80%)
```

### Want Trending Topics? → Google Trends
```python
Feature: Trending biomedical topics, query suggestions
Method:  TrendingTopicsDetector (pytrends)
         - Google Trends API
         - Google autocomplete
         - Search volume analysis
Phase:   Week 2, Day 3-4
Impact:  +40% better query suggestions
```

### Want Entity Validation? → Wikipedia/Knowledge Graph
```python
Feature: Entity disambiguation, canonical names
Method:  WebKnowledgeEnricher
         - Wikipedia/Wikidata APIs
         - Google Knowledge Graph
         - DBpedia SPARQL
Phase:   Week 6, Day 1-3
Impact:  +10% entity accuracy (80% → 90%)
```

### Want Better Ranking? → Multi-source Signals
```python
Feature: Multi-factor ranking (citations, trends, quality)
Methods: All web enhancements combined
         - Citation metrics (Scholar)
         - Trend scores (Trends)
         - Quality signals (PDF availability)
Phase:   Week 7, Day 3-4
Impact:  +25% ranking quality
```

---

## 🔧 Technical Implementation Map

### New Module Created: `lib/web/`

```python
omics_oracle_v2/lib/web/
├── __init__.py
│
├── google_scholar.py              # PHASE 1 (Week 1)
│   └── class GoogleScholarClient:
│       ├── search(query) → List[ScholarArticle]
│       ├── get_citation_graph(article_id) → Dict
│       ├── get_author_metrics(author_name) → Dict
│       └── get_cited_by(article_id) → List[ScholarArticle]
│
├── web_scraper.py                 # PHASE 2 (Week 3)
│   └── class WebPDFScraper:
│       ├── find_pdf_sources(...) → List[PDFSource]
│       ├── _find_on_google_scholar() → List[PDFSource]
│       ├── _find_on_researchgate() → List[PDFSource]
│       ├── _find_in_repositories() → List[PDFSource]
│       └── download_pdf(source) → bool
│
├── trends.py                      # PHASE 3 (Week 4)
│   └── class TrendingTopicsDetector:
│       ├── get_trending_topics(category) → List[Dict]
│       ├── enhance_query_with_trends(query) → Dict
│       └── _get_google_autocomplete(query) → List[str]
│
├── knowledge_graph.py             # PHASE 4 (Week 6)
│   └── class WebKnowledgeEnricher:
│       ├── enrich_entity(text, type, context) → Dict
│       ├── _get_wikidata(entity) → Dict
│       └── _get_knowledge_graph(entity) → Dict
│
└── utils.py                       # ALL PHASES
    ├── class EthicalWebScraper
    ├── check_robots_txt()
    ├── rate_limit_decorator()
    └── cache_web_response()
```

### Integration Points

**Phase 1 Integration:**
```python
# In PublicationService:
async def search(self, query: str):
    # Existing: PubMed + PMC
    pubmed_results = await self.pubmed_client.search(query)

    # 🆕 Add: Google Scholar
    scholar_results = await self.scholar_client.search(query)

    # Merge with citation data
    enriched_results = self._merge_with_citations(
        pubmed_results,
        scholar_results
    )
    return enriched_results
```

**Phase 2 Integration:**
```python
# In PDFDownloader:
async def download(self, pmid, pmcid, doi, url):
    # Try existing sources first
    if pdf := await self._download_from_pmc(pmcid):
        return pdf

    # 🆕 Fallback to web scraping
    web_sources = await self.web_scraper.find_pdf_sources(
        title=article.title,
        authors=article.authors,
        doi=doi
    )

    for source in web_sources:
        if pdf := await self.web_scraper.download_pdf(source):
            return pdf
```

**Phase 3 Integration:**
```python
# In QueryEnhancer:
async def enhance(self, query: str):
    # Existing: MeSH ontology
    ontology_expansion = await self._expand_with_ontology(query)

    # 🆕 Add: Web trends
    web_trends = await self.trends_detector.enhance_query_with_trends(query)

    return {
        'ontology': ontology_expansion,
        'trending': web_trends['suggestions'],
        'autocomplete': web_trends['autocomplete']
    }
```

**Phase 4 Integration:**
```python
# In EntityExtractor:
async def extract_and_enrich(self, text: str):
    # Existing: NER extraction
    entities = await self._extract_with_ner(text)

    # 🆕 Add: Web enrichment
    for entity in entities:
        enriched = await self.knowledge_enricher.enrich_entity(
            entity_text=entity.text,
            entity_type=entity.type,
            context=text
        )
        entity.canonical_name = enriched['canonical_name']
        entity.wikipedia_url = enriched['wikipedia_url']
        entity.confidence = enriched['confidence']

    return entities
```

**Phase 5 Integration:**
```python
# In MultiSourceRanker:
def rank(self, results: List[Result]):
    for result in results:
        score = (
            self._relevance_score(result) * 0.3 +
            self._citation_score(result) * 0.25 +      # 🆕 Scholar
            self._h_index_score(result) * 0.15 +       # 🆕 Scholar
            self._trend_score(result) * 0.15 +         # 🆕 Trends
            self._recency_score(result) * 0.10 +
            self._quality_score(result) * 0.05         # 🆕 PDF availability
        )
        result.final_score = score

    return sorted(results, key=lambda r: r.final_score, reverse=True)
```

---

## ⚡ Quick Decision Matrix

### Should I Use Web Methods For...?

| Need | Use This | Phase | Why |
|------|----------|-------|-----|
| **Citation counts** | GoogleScholarClient | 1 | Only source for citations |
| **More PDFs** | WebPDFScraper | 2 | +75% success rate |
| **Query suggestions** | TrendingTopicsDetector | 3 | Real user patterns |
| **Trending topics** | Google Trends | 3 | Search volume data |
| **Entity disambiguation** | WebKnowledgeEnricher | 4 | Wikipedia validation |
| **Better ranking** | All of the above | 5 | Multi-signal ranking |
| **Gray literature** | Scholar + Web Scraper | 1-2 | Theses, reports, repos |
| **Author metrics** | GoogleScholarClient | 1 | H-index, i10-index |
| **Preprint versions** | WebPDFScraper | 2 | arXiv, bioRxiv |
| **Related work** | GoogleScholarClient | 1 | "Related articles" |

---

## 🎯 Priority Recommendations

### Must Implement (High Impact, Low Cost)
1. ✅ **GoogleScholarClient** - Citation analysis is game-changer
2. ✅ **WebPDFScraper** - Need more full-text access
3. ✅ **TrendingTopicsDetector** - Better UX, query suggestions

### Should Implement (Medium Impact)
4. ✅ **WebKnowledgeEnricher** - Improves entity accuracy
5. ✅ **Multi-signal ranking** - Better result quality

### Nice to Have (Lower Priority)
6. ⏭️ Advanced citation visualizations
7. ⏭️ Author collaboration networks
8. ⏭️ Research trend forecasting

---

## 📋 Implementation Checklist

### Week 1: Setup + Scholar
- [ ] Create `omics_oracle_v2/lib/web/` module
- [ ] Install dependencies (`playwright`, `scholarly`, `pytrends`)
- [ ] Run `playwright install chromium`
- [ ] Implement `GoogleScholarClient`
- [ ] Test citation extraction
- [ ] Integrate with PublicationService

### Week 2: Trends
- [ ] Implement `TrendingTopicsDetector`
- [ ] Test Google Trends API
- [ ] Test autocomplete suggestions
- [ ] Integrate with QueryEnhancer

### Week 3: PDF Scraping
- [ ] Implement `WebPDFScraper`
- [ ] Test Playwright automation
- [ ] Test multi-source fallback
- [ ] Integrate with PDFDownloader

### Week 6: Knowledge Enrichment
- [ ] Implement `WebKnowledgeEnricher`
- [ ] Test Wikipedia/Wikidata APIs
- [ ] Test Google Knowledge Graph
- [ ] Integrate with EntityExtractor

### Week 7: Ranking
- [ ] Implement multi-signal ranking
- [ ] Test citation-based ranking
- [ ] Test trend-based boosting
- [ ] Validate ranking quality

---

**Summary:** Web methods enhance **EVERY phase** with significant impact and minimal cost. Strongly recommended for implementation! 🚀
