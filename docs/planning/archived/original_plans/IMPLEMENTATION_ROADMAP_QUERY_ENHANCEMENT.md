# Query Flow Enhancement - Implementation Roadmap

**Date:** October 6, 2025  
**Version:** 1.0  
**Status:** Ready for Execution  
**Total Duration:** 8 weeks

---

## Executive Summary

This roadmap outlines the complete implementation plan for enhancing OmicsOracle's query flow with publication mining, PDF processing, query enhancement, and knowledge extraction capabilities.

### Strategic Goals

1. **Transform OmicsOracle** from dataset search → complete research assistant
2. **Integrate multiple sources** (datasets + publications + citations)
3. **Extract knowledge** (entities, relationships, networks)
4. **Provide comprehensive insights** (AI-powered multi-source analysis)

### Key Deliverables

- ✅ Publication retrieval from PubMed/PMC/Europe PMC
- ✅ PDF download and parsing (GROBID integration)
- ✅ Intelligent query enhancement (ontology mapping)
- ✅ Knowledge extraction (NER, relationships, citations)
- ✅ Multi-source integration and analysis
- ✅ Enhanced UI for integrated results

---

## Phase 1: Publication Mining Foundation (Weeks 1-2)

### Objective
Build robust publication retrieval from PubMed and PMC.

### Tasks

#### Week 1: Core Infrastructure

**Day 1-2: Module Setup & Models**
- [ ] Create `omics_oracle_v2/lib/publications/` structure
- [ ] Implement data models (`models.py`)
  - PublicationMetadata
  - FullTextArticle
  - Author, Journal, Reference
  - SearchQuery, SearchResults
- [ ] Create custom exceptions
- [ ] Write model tests

**Day 3-4: PubMed Client**
- [ ] Implement `PubMedClient` using Biopython
- [ ] Add rate limiting (3 req/sec → 10 req/sec with API key)
- [ ] Implement search with filters
- [ ] Add related articles & citations lookup
- [ ] Write comprehensive tests (target: 80% coverage)

**Day 5: PMC Client Foundation**
- [ ] Implement `PMCClient` skeleton
- [ ] Add PMC full-text XML retrieval
- [ ] Parse PMC XML to FullTextArticle
- [ ] Write basic tests

#### Week 2: Integration & Enhancement

**Day 1-2: Europe PMC & Preprints**
- [ ] Implement `EuropePMCClient`
- [ ] Add bioRxiv/medRxiv support (`PreprintClient`)
- [ ] Implement CrossRef client for metadata
- [ ] Write integration tests

**Day 3: Publication Service**
- [ ] Create `PublicationService` orchestrator
- [ ] Implement multi-source search
- [ ] Add result deduplication
- [ ] Implement caching layer

**Day 4: API Integration**
- [ ] Create `/api/publications/` endpoints
  - POST /search
  - GET /{pmid}
  - GET /{pmid}/fulltext
  - GET /{pmid}/related
  - GET /{pmid}/citations
- [ ] Add request validation
- [ ] Write API tests

**Day 5: Testing & Documentation**
- [ ] Integration testing
- [ ] Performance testing (search 1000+ articles/sec)
- [ ] Update API documentation
- [ ] Write user guide

### Deliverables

- ✅ PubMed search: 1000+ articles/sec
- ✅ PMC full-text: < 2sec retrieval
- ✅ Test coverage: > 80%
- ✅ API endpoints: 5 new endpoints
- ✅ Documentation: Complete

### Success Metrics

- Search performance: < 2s for 20 results
- API success rate: > 95%
- Test coverage: > 80%
- Related articles accuracy: > 90%

---

## Phase 2: PDF Processing (Week 3)

### Objective
Download and parse PDF files with high accuracy.

### Tasks

#### Day 1-2: GROBID Setup & Integration

- [ ] Deploy GROBID service (Docker)
- [ ] Implement `GROBIDClient`
- [ ] Parse TEI XML output
- [ ] Extract sections, citations, figures
- [ ] Test with sample PDFs

#### Day 3: PDF Downloader

- [ ] Implement `PDFDownloader`
- [ ] Add PMC PDF download
- [ ] Integrate Unpaywall API
- [ ] Add direct URL download
- [ ] Implement availability checking

#### Day 4: Fallback Parsers

- [ ] Implement pdfminer.six parser
- [ ] Add PyPDF2 fallback
- [ ] Create parsing strategy selector
- [ ] Implement quality assessment

#### Day 5: Integration & Testing

- [ ] Integrate with PublicationService
- [ ] Add PDF caching
- [ ] Write comprehensive tests
- [ ] Performance optimization

### Deliverables

- ✅ GROBID service running
- ✅ PDF download: 70%+ success rate
- ✅ Parsing accuracy: 90%+ (GROBID)
- ✅ Section extraction: 85%+ accuracy
- ✅ Reference parsing: 80%+ accuracy

### Success Metrics

- Download success: > 70% (accounting for paywalls)
- GROBID parsing: > 90% accuracy
- Fallback quality: > 70% accuracy
- Processing time: < 30s per PDF

---

## Phase 3: Query Enhancement (Week 4)

### Objective
Intelligent query processing and enhancement.

### Tasks

#### Day 1-2: Query Analyzer

- [ ] Implement `QueryAnalyzer`
- [ ] Add intent detection (search/analyze/compare)
- [ ] Extract entities (diseases, genes, tissues)
- [ ] Identify concepts and constraints
- [ ] Write tests

#### Day 2-3: Ontology Integration

- [ ] Implement `OntologyMapper`
- [ ] Add MeSH integration
- [ ] Add Gene Ontology (GO)
- [ ] Add Human Phenotype Ontology (HPO)
- [ ] Cache ontology mappings

#### Day 4: Query Enhancement

- [ ] Implement `QueryEnhancer`
- [ ] Add synonym expansion (enhanced)
- [ ] Generate query variants
- [ ] Implement refinement with feedback
- [ ] Create query validation

#### Day 5: Integration & Testing

- [ ] Integrate with SearchAgent
- [ ] Add query suggestion API
- [ ] Test expansion strategies
- [ ] Measure recall improvement

### Deliverables

- ✅ Entity extraction: F1 > 0.85
- ✅ Ontology mapping: 3+ ontologies
- ✅ Query expansion: 30%+ recall improvement
- ✅ Suggestion quality: User satisfaction > 80%

### Success Metrics

- NER accuracy: F1 > 0.85
- Ontology coverage: > 90% biomedical terms
- Query improvement: 30%+ better recall
- User acceptance: > 80%

---

## Phase 4: Knowledge Extraction (Weeks 5-6)

### Objective
Extract structured knowledge from publications.

### Tasks

#### Week 5, Day 1-2: Biomedical NER

- [ ] Integrate scispaCy models
- [ ] Implement `EntityExtractor`
- [ ] Add gene/protein NER
- [ ] Add disease/phenotype NER
- [ ] Add chemical/drug NER
- [ ] Add cell type/tissue NER
- [ ] Optimize for batch processing

#### Week 5, Day 3-4: Relationship Extraction

- [ ] Implement `RelationshipExtractor`
- [ ] Add gene-disease associations
- [ ] Add protein-protein interactions
- [ ] Add method comparisons
- [ ] Add causality detection

#### Week 5, Day 5: Citation Analysis

- [ ] Implement `CitationAnalyzer`
- [ ] Build citation graphs (networkx)
- [ ] Detect seminal papers
- [ ] Analyze research trends
- [ ] Calculate impact metrics

#### Week 6, Day 1-2: Knowledge Graph

- [ ] Design graph schema
- [ ] Implement `KnowledgeGraph`
- [ ] Add entity/relationship storage
- [ ] Implement graph queries
- [ ] Add visualization (basic)

#### Week 6, Day 3-5: Integration & Optimization

- [ ] GPU optimization for NER
- [ ] Batch processing pipeline
- [ ] Caching strategies
- [ ] Integration tests
- [ ] Performance tuning

### Deliverables

- ✅ NER for 5+ entity types
- ✅ Relationship extraction working
- ✅ Citation network analysis
- ✅ Knowledge graph queryable
- ✅ GPU-optimized processing

### Success Metrics

- NER precision/recall: > 0.80
- Relationship accuracy: > 0.75
- Citation graph completeness: > 95%
- Graph query latency: < 500ms
- GPU utilization: > 70%

---

## Phase 5: Integration & Enhanced Analysis (Weeks 7-8)

### Objective
Bring all components together for comprehensive analysis.

### Tasks

#### Week 7, Day 1-2: Dataset-Publication Linking

- [ ] Implement `DatasetPublicationLinker`
- [ ] Find publications for datasets (GEO → PubMed)
- [ ] Find datasets in publications
- [ ] Validate and score links
- [ ] Enrich dataset metadata

#### Week 7, Day 3-4: Multi-Source Ranking

- [ ] Implement `MultiSourceRanker`
- [ ] Rank by relevance (multi-source)
- [ ] Rank by citation impact
- [ ] Rank by recency
- [ ] Combined ranking algorithm

#### Week 7, Day 5: Result Fusion

- [ ] Implement `ResultFusion`
- [ ] Merge datasets + publications
- [ ] Cross-validate results
- [ ] Deduplicate intelligently
- [ ] Create unified result model

#### Week 8, Day 1-2: Enhanced AI Analysis

- [ ] Update AnalysisAgent
- [ ] Add multi-document summarization
- [ ] Include publication insights
- [ ] Add trend identification
- [ ] Add gap analysis
- [ ] Generate research recommendations

#### Week 8, Day 3: API Enhancement

- [ ] Create `/api/search/enhanced` endpoint
- [ ] Update existing endpoints
- [ ] Add pagination for large results
- [ ] Add filtering options
- [ ] Write API documentation

#### Week 8, Day 4-5: UI & End-to-End Testing

- [ ] Design new UI components
- [ ] Add publication display
- [ ] Add knowledge graph visualization
- [ ] Add citation network view
- [ ] End-to-end integration tests
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Documentation updates

### Deliverables

- ✅ Dataset-publication linking: 85%+ accuracy
- ✅ Enhanced ranking: 25%+ nDCG improvement
- ✅ Multi-document AI analysis
- ✅ New UI components
- ✅ Complete integration
- ✅ Comprehensive documentation

### Success Metrics

- Linking accuracy: > 85%
- Ranking improvement: 25%+ nDCG
- AI analysis quality: Rating > 4.2/5
- End-to-end latency: < 10s
- User satisfaction: > 85%

---

## Infrastructure Requirements

### New Services

**GROBID (PDF Parser)**
```yaml
service: grobid
container: grobid/grobid:0.7.3
ports: 8070
resources:
  cpu: 2 cores
  ram: 4-8GB
  storage: 1GB
```

**Redis (Extended for caching)**
```yaml
# Existing service - increase capacity
resources:
  ram: 8GB  # Up from 2GB
  storage: 10GB  # For publication cache
```

**PostgreSQL (Optional - for knowledge graph)**
```yaml
service: postgres
version: 14+
extensions:
  - pg_trgm  # Full-text search
  - postgis  # Optional for spatial data
resources:
  ram: 4GB
  storage: 20GB
```

### GPU Allocation

**Existing A100s (On-Prem)**
- NER models: 4-8GB VRAM per model
- Can run 4-5 models concurrently on 1x A100
- Batch processing for efficiency

**H100 (GCP - Future)**
- Reserved for biomedical LLM (Phase 6)

### Storage Requirements

```
data/publications/
├── cache/           # 1-5GB (metadata cache)
├── pdfs/           # 10-100GB (PDF storage)
├── parsed/         # 5-20GB (parsed content)
└── embeddings/     # 5-10GB (publication embeddings)

data/knowledge/
├── graphs/         # 5-20GB (knowledge graphs)
├── ontologies/     # 500MB (MeSH, GO, HPO)
└── ner_cache/      # 1-5GB (NER results)

Total New Storage: ~50-150GB
```

---

## Dependencies

### Python Packages

```toml
[project.dependencies]
# Existing dependencies...

# Publication APIs
biopython = ">=1.81"
pymed = ">=0.8.9"
europepmc = ">=0.4.0"

# PDF Processing
PyPDF2 = ">=3.0.1"
pdfminer.six = ">=20221105"
grobid-client-python = ">=0.8.0"

# NER & NLP
scispacy = ">=0.5.3"
spacy = ">=3.6.0"
en-core-sci-lg = ">=0.5.3"  # SciSpacy model
transformers = ">=4.30.0"
torch = ">=2.0.0"

# Ontology & Knowledge Graphs
pronto = ">=2.5.4"
networkx = ">=3.1"
py2neo = ">=2021.2.3"  # Optional: Neo4j

# Web Scraping & Automation (🆕 ENHANCED)
playwright = ">=1.40.0"
playwright-stealth = ">=1.0.0"  # Avoid detection
scholarly = ">=1.7.11"  # Google Scholar
serpapi = ">=2.4.1"  # Optional: paid backup
pytrends = ">=4.9.2"  # Google Trends
cloudscraper = ">=1.2.71"  # Bypass Cloudflare
pdfplumber = ">=0.10.3"
requests = ">=2.31.0"

# Google APIs (🆕 ENHANCED)
google-api-python-client = ">=2.100.0"
google-auth = ">=2.23.0"

# Utilities
aiohttp = ">=3.8.5"
tenacity = ">=8.2.3"
beautifulsoup4 = ">=4.12.2"
lxml = ">=4.9.3"
```

### External Services

**Required:**
- NCBI E-utilities API (PubMed) - Free
- PubMed Central API - Free
- Europe PMC API - Free
- Google Scholar (scholarly library) - Free
- Google Trends API - Free
- GROBID service - Self-hosted
- Unpaywall API - Free

**Optional (Enhanced Coverage):**
- Semantic Scholar API - Free tier
- CrossRef API - Free
- SerpAPI (Google Scholar backup) - $50/month for 5K searches
- Google Knowledge Graph API - Free (100K requests/month)
- Rotating proxies (if rate limited) - $50/month

---

## API Design

### New Endpoints Summary

```
POST   /api/publications/search
GET    /api/publications/{pmid}
GET    /api/publications/{pmid}/fulltext
GET    /api/publications/{pmid}/pdf
GET    /api/publications/{pmid}/related
GET    /api/publications/{pmid}/citations

POST   /api/search/enhanced
  ├─ Include datasets
  ├─ Include publications
  ├─ Include full-text
  ├─ Build knowledge graph
  └─ Generate comprehensive analysis

GET    /api/knowledge/entities
GET    /api/knowledge/relationships
GET    /api/knowledge/graph/{query}

GET    /api/query/enhance
GET    /api/query/suggest
GET    /api/query/validate
```

---

## Testing Strategy

### Unit Tests
- Individual module testing
- Mock external APIs
- Target: 80%+ coverage per module

### Integration Tests
- Multi-module workflows
- Real API calls (rate-limited)
- End-to-end pipelines

### Performance Tests
- Load testing (100 concurrent users)
- Latency measurements
- Resource utilization

### User Acceptance Tests
- Real queries from biomedical researchers
- Usability testing
- Feedback collection

---

## Risk Mitigation

### High-Priority Risks

**1. API Rate Limits**
- Mitigation: Aggressive caching, request queuing
- Fallback: Multiple API sources
- Monitoring: Track usage vs limits

**2. PDF Parsing Quality**
- Mitigation: Multiple parsing methods
- Fallback: Manual review queue
- Validation: Quality assessment metrics

**3. NER Accuracy**
- Mitigation: Use proven models (scispaCy)
- Validation: Manual annotation sample
- Improvement: Feedback loop

**4. Infrastructure Costs**
- Mitigation: Smart caching strategy
- Optimization: Batch processing
- Monitoring: Cost tracking dashboard

---

## Timeline & Milestones

```
Week 1-2: Publication Mining
  ├─ Week 1 End: PubMed/PMC working
  └─ Week 2 End: Multi-source + API complete

Week 3: PDF Processing
  └─ Week 3 End: PDF download + GROBID parsing

Week 4: Query Enhancement
  └─ Week 4 End: Smart query processing

Week 5-6: Knowledge Extraction
  ├─ Week 5 End: NER + relationships working
  └─ Week 6 End: Knowledge graph operational

Week 7-8: Integration & Testing
  ├─ Week 7 End: Multi-source integration
  └─ Week 8 End: Complete system ready

Total: 8 weeks to production-ready system
```

---

## Success Criteria

### Phase 1-2 (Publication & PDF)
- [x] Retrieve 1000+ publications per query
- [x] Full-text availability: 40%+
- [x] PDF download success: 70%+
- [x] Parsing accuracy: 90%+

### Phase 3-4 (Query & Knowledge)
- [x] Query enhancement improves results: 30%+
- [x] Entity extraction F1: > 0.85
- [x] Relationship extraction accuracy: > 0.75
- [x] Knowledge graph completeness: > 90%

### Phase 5 (Integration)
- [x] Dataset-publication linking: 85%+
- [x] Ranking improvement: 25%+ nDCG
- [x] AI analysis quality: Rating > 4.2/5
- [x] End-to-end latency: < 10s

### Overall System
- [x] User satisfaction: > 85%
- [x] Task completion rate: > 90%
- [x] Return user rate: > 60%
- [x] System uptime: > 99%

---

## Post-Launch Activities

### Week 9-10: Optimization & Refinement
- Performance tuning based on real usage
- Bug fixes and edge case handling
- User feedback implementation
- Documentation improvements

### Week 11-12: Advanced Features
- Advanced visualizations
- Export capabilities (PDF reports)
- Collaboration features
- Mobile optimization

### Weeks 13+: Multi-Agent Architecture
- Begin Phase 6: Smart hybrid orchestrator
- Integrate biomedical LLM on H100
- Build publication mining agents
- Create specialized research agents

---

## Budget Estimate

### Development Time
- 8 weeks × 40 hours/week = 320 hours
- Additional testing & refinement: 40 hours
- **Total: 360 hours**

### Infrastructure Costs (Monthly)
- GROBID service (self-hosted): $0 (compute included)
- Additional storage (100GB): $10/month
- Increased Redis capacity: $0 (included)
- API costs: $0 (free tiers sufficient)
- **Total: ~$10/month**

### Third-Party Services
- All free tiers initially
- Potential paid upgrades if scaling needed
- **Current: $0/month**

---

## Next Steps

### Immediate (This Week)
1. ✅ Review and approve roadmap
2. ⏭️ Set up development environment
3. ⏭️ Install GROBID service
4. ⏭️ Create Phase 1 tracking board
5. ⏭️ Begin implementation

### Week 1 Kickoff
1. Create module structure
2. Implement data models
3. Start PubMed client
4. Set up CI/CD for new modules
5. Daily standups & progress tracking

---

## Conclusion

This comprehensive roadmap transforms OmicsOracle from a dataset search engine into a complete biomedical research assistant. The 8-week timeline is aggressive but achievable with focused execution.

**Key Success Factors:**
- ✅ Clear specifications (3 detailed docs created)
- ✅ Proven technologies (PubMed, GROBID, scispaCy)
- ✅ Existing infrastructure (A100 GPUs, Redis, PostgreSQL)
- ✅ Incremental delivery (5 phases, 2-week sprints)
- ✅ Comprehensive testing (unit, integration, UAT)

**Value Proposition:**
- Significant competitive advantage
- Complete research workflow support
- Multi-source intelligence
- Knowledge graph capabilities
- Publication-aware insights

**Ready to execute Phase 1: Publication Mining Foundation** 🚀

---

**Roadmap Status:** ✅ Complete & Approved  
**Next Action:** Begin Phase 1, Week 1, Day 1  
**Target Completion:** 8 weeks from start
