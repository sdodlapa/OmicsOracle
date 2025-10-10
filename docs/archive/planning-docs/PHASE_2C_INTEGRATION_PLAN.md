# Phase 2C Integration Plan: Synonym Expansion + GEO Search

**Date:** October 9, 2025
**Goal:** Integrate Phase 2B synonym expansion into existing GEO search agent

---

## Current State Analysis

### ✅ What We Have

**1. GEO Client** (`omics_oracle_v2/lib/geo/client.py`)
- `GEOClient` class with search and metadata fetching
- Async operations with rate limiting
- Caching support
- Batch metadata fetching (10x faster)

**2. Search Agent** (`omics_oracle_v2/agents/search_agent.py`)
- `SearchAgent` class that orchestrates GEO searches
- Uses `_build_search_query()` to construct queries
- Supports keyword and semantic search modes
- Has ranking and filtering

**3. Synonym Expansion** (`omics_oracle_v2/lib/nlp/synonym_expansion.py`)
- `SynonymExpander` with 26 techniques, 643 terms
- `expand_query()` method to expand technique terms
- 100% test coverage

### ❌ What's Missing

1. **Integration Point:** Synonym expansion not called in Search Agent
2. **Query Preprocessing:** Search Agent doesn't use our NER/synonym pipeline
3. **GEO-Specific Optimization:** No technique → platform mapping
4. **Testing:** No integration tests for GEO + synonym expansion

---

## Integration Strategy

### Option 1: Direct Integration (SIMPLE - 30 min)

**Approach:** Add synonym expansion directly to `SearchAgent._build_search_query()`

```python
# In SearchAgent.__init__
from omics_oracle_v2.lib.nlp.synonym_expansion import SynonymExpander

self._synonym_expander = SynonymExpander()

# In SearchAgent._build_search_query()
def _build_search_query(self, input_data: SearchInput) -> str:
    # Apply synonym expansion first
    if self._synonym_expander:
        expanded_terms = []
        for term in filtered_terms:
            synonyms = self._synonym_expander.expand(term)
            # Add top 3 synonyms
            expanded_terms.extend(list(synonyms)[:3])
        filtered_terms = expanded_terms

    # Continue with existing logic...
```

**Pros:**
- Fast implementation (30 min)
- Minimal changes to existing code
- Works immediately

**Cons:**
- Doesn't leverage full pipeline integration
- Manual synonym handling
- Not using query preprocessing pipeline

### Option 2: Pipeline Integration (RECOMMENDED - 1 hour)

**Approach:** Use `PublicationSearchPipeline._preprocess_query()` in Search Agent

```python
# In SearchAgent.__init__
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

# Initialize preprocessing pipeline
config = PublicationSearchConfig()
config.enable_query_preprocessing = True
config.enable_synonym_expansion = True
config.enable_pubmed = False  # We only need preprocessing
config.enable_openalex = False
config.enable_scholar = False
config.enable_citations = False
config.enable_pdf_download = False
config.enable_fulltext = False
config.enable_institutional_access = False
config.enable_cache = False

self._preprocessing_pipeline = PublicationSearchPipeline(config)

# In SearchAgent._execute()
def _execute(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
    # Preprocess original query
    if self._preprocessing_pipeline and input_data.original_query:
        preprocessed = self._preprocessing_pipeline._preprocess_query(input_data.original_query)

        # Extract expanded query
        expanded_query = preprocessed.get("expanded", input_data.original_query)

        # Extract technique entities
        entities = preprocessed.get("entities", {})

        # Build GEO-optimized query
        search_query = self._build_geo_query(expanded_query, entities)
    else:
        # Fallback to existing logic
        search_query = self._build_search_query(input_data)
```

**Pros:**
- Leverages full pipeline (NER + synonym expansion)
- Consistent with publication search
- Entity-aware query building
- Better GEO-specific optimization

**Cons:**
- More code changes
- Need new method `_build_geo_query()`

### Option 3: Unified Query Builder (FUTURE - 2-3 hours)

**Approach:** Create `UnifiedQueryBuilder` that works for both publications and GEO

```python
# New file: omics_oracle_v2/lib/query/builder.py

class UnifiedQueryBuilder:
    def __init__(self, ner, synonym_expander):
        self.ner = ner
        self.synonym_expander = synonym_expander

    def build_query(self, query: str, target: str) -> dict:
        # Preprocess with NER + synonyms
        # Build target-specific query (PubMed, OpenAlex, GEO)
        # Return optimized query for target database
```

**Pros:**
- Clean architecture
- Reusable across all databases
- Easy to test

**Cons:**
- Requires refactoring
- More time investment
- Should wait until we have more databases

---

## Recommended Approach: Option 2 (Pipeline Integration)

### Implementation Steps

**Step 1: Add preprocessing to SearchAgent (15 min)**

```python
# File: omics_oracle_v2/agents/search_agent.py

class SearchAgent(Agent[SearchInput, SearchOutput]):
    def __init__(self, settings: Settings, enable_semantic: bool = False, enable_publications: bool = False):
        super().__init__(settings)
        # ... existing init ...

        # Add query preprocessing (Phase 2B integration)
        self._init_query_preprocessing()

    def _init_query_preprocessing(self):
        """Initialize query preprocessing pipeline."""
        try:
            from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline
            from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

            config = PublicationSearchConfig()
            config.enable_query_preprocessing = True
            config.enable_synonym_expansion = True
            # Disable everything except preprocessing
            config.enable_pubmed = False
            config.enable_openalex = False
            config.enable_scholar = False
            config.enable_citations = False
            config.enable_pdf_download = False
            config.enable_fulltext = False
            config.enable_institutional_access = False
            config.enable_cache = False

            self._preprocessing_pipeline = PublicationSearchPipeline(config)
            logger.info("Query preprocessing enabled for SearchAgent")
        except Exception as e:
            logger.warning(f"Failed to initialize query preprocessing: {e}")
            self._preprocessing_pipeline = None
```

**Step 2: Use preprocessing in _execute() (15 min)**

```python
def _execute(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
    try:
        # Preprocess query if available
        preprocessed_query = None
        entities_by_type = {}

        if self._preprocessing_pipeline and input_data.original_query:
            logger.info(f"Preprocessing query: {input_data.original_query}")
            try:
                preprocessed = self._preprocessing_pipeline._preprocess_query(
                    input_data.original_query
                )
                preprocessed_query = preprocessed.get("expanded", input_data.original_query)
                entities_by_type = preprocessed.get("entities", {})

                logger.info(f"Query expanded: {input_data.original_query} → {preprocessed_query}")
                context.set_metric("query_preprocessing", "enabled")
                context.set_metric("original_query", input_data.original_query)
                context.set_metric("expanded_query", preprocessed_query)
            except Exception as e:
                logger.warning(f"Query preprocessing failed: {e}. Using original query.")
                preprocessed_query = input_data.original_query
        else:
            preprocessed_query = input_data.original_query
            context.set_metric("query_preprocessing", "disabled")

        # Build GEO query
        if preprocessed_query != input_data.original_query:
            # Use expanded query
            search_query = self._build_geo_query_from_preprocessed(
                preprocessed_query,
                entities_by_type
            )
        else:
            # Fallback to existing logic
            search_query = self._build_search_query(input_data)

        # Continue with existing search logic...
```

**Step 3: Create GEO-optimized query builder (30 min)**

```python
def _build_geo_query_from_preprocessed(
    self,
    expanded_query: str,
    entities_by_type: dict
) -> str:
    """
    Build GEO-optimized query from preprocessed/expanded query.

    Args:
        expanded_query: Query with synonym expansion (OR clauses)
        entities_by_type: Entities grouped by type (GENE, TECHNIQUE, etc.)

    Returns:
        GEO-optimized query string
    """
    from omics_oracle_v2.lib.nlp.models import EntityType

    # GEO search supports:
    # - Title/Abstract search (default)
    # - Field-specific: [Organism], [Platform], [Submission Date]
    # - Boolean: AND, OR, NOT

    query_parts = []

    # Add technique terms (high priority for GEO)
    if EntityType.TECHNIQUE in entities_by_type:
        techniques = entities_by_type[EntityType.TECHNIQUE]
        if techniques:
            # Get expanded synonyms for each technique
            tech_terms = []
            for tech in techniques[:5]:  # Top 5 techniques
                if hasattr(self, '_preprocessing_pipeline') and \
                   self._preprocessing_pipeline.synonym_expander:
                    synonyms = self._preprocessing_pipeline.synonym_expander.expand(
                        tech.text,
                        max_synonyms=3
                    )
                    tech_terms.extend(synonyms)
                else:
                    tech_terms.append(tech.text)

            if tech_terms:
                # Group technique synonyms with OR
                tech_query = "(" + " OR ".join(f'"{t}"' for t in tech_terms[:10]) + ")"
                query_parts.append(tech_query)

    # Add organism filter if specified
    if EntityType.ORGANISM in entities_by_type:
        organisms = entities_by_type[EntityType.ORGANISM]
        if organisms:
            org = organisms[0].text
            query_parts.append(f'"{org}"[Organism]')

    # Add tissue/cell type if specified
    if EntityType.TISSUE in entities_by_type or EntityType.CELL_TYPE in entities_by_type:
        tissues = entities_by_type.get(EntityType.TISSUE, [])
        cell_types = entities_by_type.get(EntityType.CELL_TYPE, [])
        all_types = tissues + cell_types
        if all_types:
            type_query = "(" + " OR ".join(f'"{t.text}"' for t in all_types[:5]) + ")"
            query_parts.append(type_query)

    # Add disease/phenotype if specified
    if EntityType.DISEASE in entities_by_type or EntityType.PHENOTYPE in entities_by_type:
        diseases = entities_by_type.get(EntityType.DISEASE, [])
        phenotypes = entities_by_type.get(EntityType.PHENOTYPE, [])
        all_conditions = diseases + phenotypes
        if all_conditions:
            condition_query = "(" + " OR ".join(f'"{c.text}"' for c in all_conditions[:5]) + ")"
            query_parts.append(condition_query)

    # If no entities found, fall back to expanded query
    if not query_parts:
        return expanded_query

    # Combine with AND logic (all conditions must match)
    final_query = " AND ".join(query_parts)

    logger.info(f"Built GEO-optimized query: {final_query}")
    return final_query
```

---

## Testing Plan

### Unit Tests (30 min)

```python
# File: test_geo_synonym_integration.py

def test_search_agent_with_synonym_expansion():
    """Test SearchAgent uses synonym expansion."""
    settings = get_test_settings()
    agent = SearchAgent(settings)

    # Test input with technique term
    input_data = SearchInput(
        original_query="RNA-seq in liver",
        search_terms=["RNA-seq", "liver"],
        max_results=10
    )

    context = AgentContext()
    output = agent.execute(input_data, context)

    # Should have expanded query
    assert context.get_metric("query_preprocessing") == "enabled"
    assert context.get_metric("expanded_query") is not None

def test_geo_query_with_techniques():
    """Test GEO query building with technique entities."""
    agent = SearchAgent(get_test_settings())
    agent._init_query_preprocessing()

    # Simulate preprocessed entities
    from omics_oracle_v2.lib.nlp.models import Entity, EntityType

    entities = {
        EntityType.TECHNIQUE: [Entity(text="RNA-seq", start=0, end=7)],
        EntityType.TISSUE: [Entity(text="liver", start=11, end=16)]
    }

    query = agent._build_geo_query_from_preprocessed(
        "RNA-seq in liver",
        entities
    )

    # Should include synonyms and tissue filter
    assert "RNA" in query or "transcriptome" in query
    assert "liver" in query
```

### Integration Tests (30 min)

```python
def test_end_to_end_geo_search_with_synonyms():
    """Test complete GEO search with synonym expansion."""
    settings = get_test_settings()
    agent = SearchAgent(settings)

    input_data = SearchInput(
        original_query="ATAC-seq chromatin accessibility",
        search_terms=["ATAC-seq", "chromatin", "accessibility"],
        max_results=20
    )

    context = AgentContext()
    output = agent.execute(input_data, context)

    # Should return results
    assert len(output.datasets) > 0

    # Should have used preprocessing
    assert context.get_metric("query_preprocessing") == "enabled"

    # Results should be relevant
    for dataset in output.datasets[:5]:
        # Title/summary should contain technique or synonyms
        text = (dataset.title + " " + dataset.summary).lower()
        assert any(term in text for term in [
            "atac", "chromatin", "accessibility", "transposase"
        ])
```

---

## Timeline

| Task | Time | Status |
|------|------|--------|
| 1. Add preprocessing init | 15 min | ⏳ TODO |
| 2. Integrate in _execute() | 15 min | ⏳ TODO |
| 3. Build GEO query optimizer | 30 min | ⏳ TODO |
| 4. Write unit tests | 30 min | ⏳ TODO |
| 5. Write integration tests | 30 min | ⏳ TODO |
| 6. Manual testing | 30 min | ⏳ TODO |
| 7. Documentation | 15 min | ⏳ TODO |

**Total:** ~2.5 hours

---

## Success Criteria

- [ ] SearchAgent initializes synonym expansion
- [ ] Queries are preprocessed with NER + synonyms
- [ ] GEO queries include expanded technique terms
- [ ] Tests pass (unit + integration)
- [ ] Real queries return 3-5x more results
- [ ] Performance acceptable (< 100ms overhead)

---

## Next Steps

1. ✅ **Analyzed existing code** - Found GEOClient and SearchAgent
2. ⏭️ **Implement Option 2** - Pipeline integration
3. 📋 **Test thoroughly** - Unit + integration tests
4. 🚀 **Deploy** - Phase 2C complete

Let's proceed with Option 2! 🎯
