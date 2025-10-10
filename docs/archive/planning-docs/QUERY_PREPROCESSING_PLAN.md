# Query Preprocessing & Biological Term Extraction - Implementation Plan

**Date:** October 9, 2025  
**Context:** Enhancing query execution flow for better GEO search results  
**Status:** Planning Phase

---

## Current State Analysis

### What We Have ✅

**1. BiomedicalNER (Entity Extraction)**
- Location: `omics_oracle_v2/lib/nlp/biomedical_ner.py`
- Capabilities:
  - Extracts genes, proteins, diseases, chemicals, organisms, tissues, cell types
  - Uses SciSpaCy models for biomedical text
  - Provides confidence scores and entity linking
  - Already integrated in QueryAgent

**2. QueryAgent (Query Processing)**
- Location: `omics_oracle_v2/agents/query_agent.py`
- Current Process:
  ```
  User Query → Intent Detection → Entity Extraction (NER) → 
  Search Term Generation → GEO Search
  ```

**3. PublicationSearchPipeline**
- Just enhanced with OpenAlex search ✅
- Searches: PubMed + OpenAlex + (Scholar if enabled)
- Missing: Query preprocessing for genomic databases

### What's Missing ❌

**1. Query preprocessing is NOT used in publication search**
- The NER/QueryAgent is separate from publication pipeline
- Publication search uses raw query string directly
- No biological term extraction before searching PubMed/OpenAlex

**2. No GEO-specific query optimization**
- No MeSH term mapping for PubMed
- No GEO-specific field mapping (e.g., organism, study type)
- No query expansion with biological synonyms

**3. No database-specific query builders**
- Each database (PubMed, OpenAlex, GEO) has different query syntax
- Currently using same query for all sources
- Missing field-specific searches (e.g., [MeSH], [TIAB])

---

## The Gap: Two Separate Systems

### System 1: GEO Dataset Search (QueryAgent + SearchAgent)
```
User: "breast cancer RNA-seq datasets"
  ↓
QueryAgent:
  - Extract entities: ["breast cancer" (disease), "RNA-seq" (technique)]
  - Generate search terms: ["breast cancer", "breast carcinoma", "RNA-seq", "RNA sequencing"]
  ↓
SearchAgent:
  - Search NCBI GEO with extracted terms
  - Return GEO datasets (GSE12345, etc.)
```

### System 2: Publication Search (Pipeline)
```
User: "breast cancer RNA-seq" 
  ↓
PublicationSearchPipeline:
  - Search PubMed with RAW query ❌
  - Search OpenAlex with RAW query ❌
  - No entity extraction!
  - No query optimization!
  ↓
Returns: Publications about the topic
```

**The Problem:** We have sophisticated NER in QueryAgent but it's NOT used in PublicationSearchPipeline!

---

## Solution: Integrate Query Preprocessing

### Option 1: Use Existing QueryAgent (Quick Win)

**Modify PublicationSearchPipeline to use QueryAgent:**

```python
class PublicationSearchPipeline:
    def __init__(self, config):
        # ... existing code ...
        
        # Add QueryAgent for query preprocessing
        if config.enable_query_preprocessing:
            from omics_oracle_v2.agents.query_agent import QueryAgent
            self.query_agent = QueryAgent(settings)
    
    def search(self, query: str, max_results: int = 50):
        """Search with query preprocessing."""
        
        # Step 0: Preprocess query (NEW!)
        if self.query_agent:
            query_result = self.query_agent.execute(QueryInput(query=query))
            preprocessed = self._build_optimized_queries(query_result.output)
        else:
            preprocessed = {"default": query}  # Fallback to raw query
        
        # Step 1: Search sources with optimized queries
        if self.pubmed_client:
            # Use PubMed-optimized query
            pubmed_query = preprocessed.get("pubmed", query)
            pubmed_results = self.pubmed_client.search(pubmed_query, ...)
        
        if self.openalex_client:
            # Use OpenAlex-optimized query
            openalex_query = preprocessed.get("openalex", query)
            openalex_results = self.openalex_client.search(openalex_query, ...)
        
        # ... rest of pipeline
```

**Benefits:**
- Reuses existing NER infrastructure
- Quick to implement (1-2 hours)
- Immediate improvement in search quality

**Drawbacks:**
- Adds QueryAgent dependency to publication pipeline
- May need Settings configuration

---

### Option 2: Lightweight Query Preprocessor (Clean Architecture)

**Create a dedicated query preprocessor:**

```python
# omics_oracle_v2/lib/publications/query_preprocessor.py

class QueryPreprocessor:
    """Lightweight query preprocessing for publication search."""
    
    def __init__(self, ner: Optional[BiomedicalNER] = None):
        self.ner = ner or BiomedicalNER()
    
    def preprocess(self, query: str) -> PreprocessedQuery:
        """Extract structure from query."""
        
        # Extract entities
        ner_result = self.ner.extract_entities(query)
        
        # Categorize entities
        entities_by_type = {
            "genes": [],
            "diseases": [],
            "techniques": [],
            "organisms": [],
        }
        
        for entity in ner_result.entities:
            if entity.entity_type == EntityType.GENE:
                entities_by_type["genes"].append(entity.text)
            elif entity.entity_type == EntityType.DISEASE:
                entities_by_type["diseases"].append(entity.text)
            # ... etc
        
        return PreprocessedQuery(
            original=query,
            entities=entities_by_type,
            pubmed_query=self._build_pubmed_query(entities_by_type, query),
            openalex_query=self._build_openalex_query(entities_by_type, query),
            geo_query=self._build_geo_query(entities_by_type, query),
        )
    
    def _build_pubmed_query(self, entities: dict, original: str) -> str:
        """Build PubMed-optimized query with MeSH terms."""
        parts = []
        
        # Add gene terms with field tags
        if entities["genes"]:
            gene_terms = " OR ".join(f"{g}[Gene Name]" for g in entities["genes"])
            parts.append(f"({gene_terms})")
        
        # Add disease terms with MeSH
        if entities["diseases"]:
            disease_terms = " OR ".join(f"{d}[MeSH]" for d in entities["diseases"])
            parts.append(f"({disease_terms})")
        
        # Combine with AND
        if parts:
            return " AND ".join(parts)
        
        # Fallback to original
        return original
    
    def _build_openalex_query(self, entities: dict, original: str) -> str:
        """Build OpenAlex-optimized query."""
        # OpenAlex supports filters
        parts = [original]
        
        # Could add year filters, type filters etc.
        # Example: "cancer AND has_fulltext:true AND publication_year:>2020"
        
        return " ".join(parts)
    
    def _build_geo_query(self, entities: dict, original: str) -> str:
        """Build GEO-specific query."""
        # GEO has specific fields
        parts = []
        
        if entities["genes"]:
            parts.extend(entities["genes"])
        
        if entities["diseases"]:
            parts.extend(entities["diseases"])
        
        if entities["organisms"]:
            parts.append(f"organism:{entities['organisms'][0]}")
        
        return " ".join(parts) if parts else original
```

**Benefits:**
- Clean separation of concerns
- No agent dependency
- Lightweight and fast
- Database-specific optimization

**Drawbacks:**
- Need to implement query builders for each database
- More code to write

---

## Recommended Approach: Hybrid (Best of Both)

### Phase 1: Quick Win (TODAY)

**Add basic query preprocessing to pipeline:**

```python
class PublicationSearchPipeline:
    
    def __init__(self, config):
        # ... existing ...
        
        # Add lightweight NER for query preprocessing
        if config.enable_query_preprocessing:
            from omics_oracle_v2.lib.nlp import BiomedicalNER
            self.ner = BiomedicalNER()
    
    def _preprocess_query(self, query: str) -> dict:
        """Basic query preprocessing."""
        if not hasattr(self, 'ner') or not self.ner:
            return {"default": query}
        
        # Extract entities
        result = self.ner.extract_entities(query)
        
        # Build source-specific queries
        return {
            "original": query,
            "entities": result.entities,
            "pubmed": self._enhance_for_pubmed(query, result.entities),
            "openalex": self._enhance_for_openalex(query, result.entities),
        }
    
    def _enhance_for_pubmed(self, query: str, entities: List[Entity]) -> str:
        """Add PubMed field tags."""
        # Extract genes and diseases
        genes = [e.text for e in entities if e.entity_type == EntityType.GENE]
        diseases = [e.text for e in entities if e.entity_type == EntityType.DISEASE]
        
        parts = []
        
        # Add gene terms with [Gene Name] tag
        if genes:
            gene_query = " OR ".join(f'"{g}"[Gene Name]' for g in genes)
            parts.append(f"({gene_query})")
        
        # Add disease terms with [MeSH] tag
        if diseases:
            disease_query = " OR ".join(f'"{d}"[MeSH]' for d in diseases[:3])  # Limit to top 3
            parts.append(f"({disease_query})")
        
        # If we have enhanced terms, use them; otherwise fallback
        if parts:
            enhanced = " AND ".join(parts)
            # Also include original as OR to catch everything
            return f"({enhanced}) OR ({query})"
        
        return query
    
    def _enhance_for_openalex(self, query: str, entities: List[Entity]) -> str:
        """Enhance query for OpenAlex."""
        # OpenAlex uses simple keywords, but we can prioritize terms
        genes = [e.text for e in entities if e.entity_type == EntityType.GENE]
        diseases = [e.text for e in entities if e.entity_type == EntityType.DISEASE]
        
        # Build query with important terms first
        important_terms = genes + diseases
        if important_terms:
            return " ".join(important_terms) + " " + query
        
        return query
```

**Implementation Time:** 1-2 hours  
**Impact:** Immediate improvement in result quality

### Phase 2: Advanced Features (NEXT SPRINT)

1. **MeSH Term Mapping**
   - Map disease terms to official MeSH headings
   - Use NCBI EUtils to validate MeSH terms

2. **Synonym Expansion**
   - Integrate BiologicalSynonymMapper
   - Expand gene names (BRCA1 → "breast cancer 1", "BRCA-1")

3. **Query Templates**
   - Disease + Technique: "diabetes RNA-seq"
   - Gene + Disease: "TP53 breast cancer"
   - Organism-specific: "mouse Alzheimer's microarray"

4. **GEO Integration**
   - Build GEO-specific query builder
   - Map to GEO fields (organism, study type, platform)

---

## Testing Strategy

### Test 1: Basic Entity Extraction
```python
query = "breast cancer BRCA1 RNA-seq"
preprocessed = preprocessor.preprocess(query)

assert "breast cancer" in preprocessed.entities["diseases"]
assert "BRCA1" in preprocessed.entities["genes"]
assert "RNA-seq" in preprocessed.entities["techniques"]
```

### Test 2: PubMed Query Enhancement
```python
query = "diabetes TP53"
pubmed_query = preprocessor._enhance_for_pubmed(query, entities)

# Should have MeSH tags
assert "[MeSH]" in pubmed_query or "[Gene Name]" in pubmed_query
```

### Test 3: Search Quality Comparison
```python
# Before: Raw query
results_raw = pipeline.search("breast cancer RNA-seq")

# After: Preprocessed query
results_preprocessed = pipeline.search("breast cancer RNA-seq", preprocess=True)

# Should get more relevant results
assert len(results_preprocessed) >= len(results_raw)
```

---

## Next Steps

### Immediate (TODAY):
1. ✅ Add OpenAlex to search sources (DONE)
2. ⏳ Add basic query preprocessing to pipeline
3. ⏳ Test with sample queries

### This Week:
4. ⏳ Implement MeSH term mapping
5. ⏳ Add synonym expansion
6. ⏳ Create query templates

### Next Week:
7. ⏳ GEO-specific query builder
8. ⏳ Extend beyond GEO (ArrayExpress, SRA, etc.)
9. ⏳ Performance optimization

---

## Success Metrics

**Before Query Preprocessing:**
- Search "breast cancer RNA-seq" → 30 results from PubMed
- Search "BRCA1 mutations" → 25 results from PubMed

**After Query Preprocessing:**
- Search "breast cancer RNA-seq" → 75 results (PubMed + OpenAlex with optimized queries)
- PubMed uses: `("breast cancer"[MeSH]) AND ("RNA-seq"[Text Word])`
- Search "BRCA1 mutations" → 60 results
- PubMed uses: `("BRCA1"[Gene Name]) OR ("breast cancer 1"[Text Word])`

**Target Improvements:**
- 2-3x more relevant results
- Better precision (fewer false positives)
- Database-specific optimization
- Support for complex queries

---

**Ready to implement Phase 1!** 🚀
