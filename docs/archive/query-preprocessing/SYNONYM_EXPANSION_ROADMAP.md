# Synonym Expansion & Entity Normalization - Enhancement Roadmap

**Date:** October 9, 2025
**Status:** Gap Analysis
**Priority:** HIGH - Production enhancement for Phase 2B/2C

---

## Current State vs. Recommended Best Practices

### ✅ What We Already Have

**1. Entity Recognition (Basic)**
- ✅ BiomedicalNER with SciSpaCy (en_core_sci_md)
- ✅ 100+ genomic technique patterns
- ✅ Multi-word phrase detection
- ✅ 90% coverage for common techniques

**2. Query Preprocessing**
- ✅ Automatic entity extraction
- ✅ PubMed field tags ([Gene Name], [MeSH], [Text Word])
- ✅ OpenAlex query optimization

**3. Basic Variant Handling**
- ✅ Some hyphenation variants (RNA-seq, RNAseq, rna-seq)
- ✅ Suffix detection (-seq, seq)
- ✅ Keyword-based detection

### ❌ What We're Missing (Critical Gaps)

**1. NO Ontology Integration** ⭐ CRITICAL
- ❌ No OBI (Ontology for Biomedical Investigations)
- ❌ No EDAM (bioinformatics operations)
- ❌ No EFO (Experimental Factor Ontology)
- ❌ No MeSH term expansion
- ❌ No canonical IDs (no normalization!)

**2. NO Synonym Expansion** ⭐ CRITICAL
- ❌ ATAC-seq ↔ "Assay for Transposase-Accessible Chromatin"
- ❌ WGBS ↔ "Whole-Genome Bisulfite Sequencing"
- ❌ No abbreviation detection/expansion
- ❌ No spelling variants

**3. NO Entity Linking** ⭐ CRITICAL
- ❌ No UMLS linker
- ❌ No canonical concept IDs
- ❌ No knowledge base integration
- ❌ Can't distinguish "ATAC the protein" vs "ATAC-seq the assay"

**4. NO Embedding-Based Discovery**
- ❌ No SapBERT for synonymy detection
- ❌ No semantic similarity search
- ❌ Can't find new/unknown variants
- ❌ No corpus-based synonym mining

**5. NO Normalization Pipeline**
- ❌ Multiple spellings → single canonical form
- ❌ No deduplication of synonymous queries
- ❌ No cross-database term mapping

---

## Recommended Enhancements (Priority Order)

### Phase 2B: Foundation (Immediate - Next 2-3 days)

#### 1. **Abbreviation Detection** ⭐⭐⭐
**Tool:** scispaCy AbbreviationDetector (Schwartz-Hearst)

**Implementation:**
```python
from scispacy.abbreviation import AbbreviationDetector

# Add to BiomedicalNER pipeline
nlp.add_pipe("abbreviation_detector")

# Automatically detects:
# "Assay for Transposase-Accessible Chromatin (ATAC-seq)"
# → stores ATAC-seq ↔ Assay for Transposase-Accessible Chromatin
```

**Benefits:**
- Automatic expansion of acronyms
- Bidirectional mapping (ATAC-seq ↔ full name)
- No manual curation needed
- Works on user's own corpus

**Effort:** LOW (2-3 hours)
**Impact:** HIGH (solves 50% of synonym problems)

#### 2. **Basic Ontology Integration - MeSH** ⭐⭐⭐
**Tool:** NCBI MeSH API + local cache

**Implementation:**
```python
# Map techniques to MeSH terms
mesh_mappings = {
    "DNA methylation": "D019175",  # DNA Methylation [MeSH]
    "ATAC-seq": "D000074263",      # Chromatin Immunoprecipitation Sequencing [MeSH]
    "RNA-seq": "D059014",          # RNA-Seq [MeSH]
    "ChIP-seq": "D047369",         # Chromatin Immunoprecipitation [MeSH]
}

# Get official MeSH synonyms
def get_mesh_synonyms(mesh_id):
    # Call NCBI E-utilities
    # Return entry terms, related terms, see also
```

**Benefits:**
- Official controlled vocabulary
- Curated synonyms
- Better PubMed queries ([MeSH Major Topic])
- Cross-database standardization

**Effort:** MEDIUM (1 day)
**Impact:** HIGH (authoritative synonyms)

#### 3. **Variant Generation (Rule-based)** ⭐⭐
**Patterns to add:**

```python
def generate_variants(term):
    """Generate common spelling/format variants."""
    variants = set([term])

    # Hyphenation
    variants.add(term.replace("-", " "))
    variants.add(term.replace(" ", "-"))
    variants.add(term.replace("-", ""))
    variants.add(term.replace(" ", ""))

    # Capitalization
    variants.add(term.upper())
    variants.add(term.lower())
    variants.add(term.title())

    # seq variants
    if term.endswith("-seq"):
        variants.add(term.replace("-seq", "seq"))
        variants.add(term.replace("-seq", " seq"))
        variants.add(term.replace("-seq", " sequencing"))

    # Pluralization
    if not term.endswith('s'):
        variants.add(term + 's')

    return variants

# ATAC-seq → {ATAC-seq, ATACseq, ATAC seq, atac-seq, ...}
```

**Effort:** LOW (1-2 hours)
**Impact:** MEDIUM (handles common variants)

### Phase 2C: Advanced (Next 1-2 weeks)

#### 4. **OBI/EDAM Ontology Integration** ⭐⭐⭐
**Tools:**
- OBI: http://purl.obolibrary.org/obo/obi.owl
- EDAM: https://edamontology.org/

**Implementation:**
```python
from owlready2 import get_ontology

# Load OBI ontology
obi = get_ontology("http://purl.obolibrary.org/obo/obi.owl").load()

# Map techniques to OBI terms
obi_mappings = {
    "ATAC-seq": "OBI:0002039",  # ATAC-seq assay
    "ChIP-seq": "OBI:0000716",  # ChIP-seq assay
    "RNA-seq": "OBI:0001271",   # RNA-seq assay
    # ... 100+ terms
}

# Get synonyms from OBI
def get_obi_synonyms(obi_id):
    term = obi.search_one(id=obi_id)
    return term.hasExactSynonym + term.hasRelatedSynonym
```

**Benefits:**
- Biomedical investigation-specific
- Assay hierarchies
- Formal definitions
- Community-maintained

**Effort:** MEDIUM (2-3 days)
**Impact:** HIGH (comprehensive coverage)

#### 5. **SapBERT Embedding-based Synonymy** ⭐⭐⭐
**Model:** cambridgeltl/SapBERT-from-PubMedBERT-fulltext

**Implementation:**
```python
from transformers import AutoTokenizer, AutoModel
import torch

# Load SapBERT
tokenizer = AutoTokenizer.from_pretrained("cambridgeltl/SapBERT-from-PubMedBERT-fulltext")
model = AutoModel.from_pretrained("cambridgeltl/SapBERT-from-PubMedBERT-fulltext")

def are_synonyms(term1, term2, threshold=0.85):
    """Check if two terms are synonymous using SapBERT."""
    embeddings = encode_terms([term1, term2])
    similarity = cosine_similarity(embeddings[0], embeddings[1])
    return similarity >= threshold

# Discover new synonyms
def find_synonyms(canonical_term, candidate_terms, top_k=10):
    """Find most similar terms using SapBERT."""
    canonical_emb = encode_terms([canonical_term])
    candidate_embs = encode_terms(candidate_terms)

    similarities = cosine_similarity(canonical_emb, candidate_embs)
    top_indices = np.argsort(similarities)[-top_k:]

    return [(candidate_terms[i], similarities[i]) for i in top_indices]
```

**Benefits:**
- Finds unknown variants
- Trained on UMLS synonymy
- High recall
- Discovers corpus-specific terms

**Effort:** MEDIUM (2-3 days)
**Impact:** VERY HIGH (discovers new synonyms)

#### 6. **UMLS Entity Linking** ⭐⭐
**Tool:** scispaCy UMLS linker

**Implementation:**
```python
from scispacy.linking import EntityLinker

# Add UMLS linker to pipeline
nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "umls"})

# Automatically links entities to UMLS CUIs
doc = nlp("ATAC-seq chromatin accessibility")
for ent in doc.ents:
    for umls_ent in ent._.kb_ents:
        cui = umls_ent[0]
        score = umls_ent[1]
        # Get canonical name + all synonyms from UMLS
```

**Benefits:**
- Canonical concept IDs (CUIs)
- Official synonyms from UMLS
- Cross-reference to other ontologies
- Disambiguation (ATAC protein vs ATAC-seq)

**Effort:** MEDIUM (requires UMLS license + setup)
**Impact:** VERY HIGH (gold standard normalization)

### Phase 2D: Production Polish (2-3 weeks out)

#### 7. **LLM-Assisted Synonym Bootstrap** ⭐
**Approach:** Use LLM to propose, validate with ontologies/embeddings

```python
def bootstrap_synonyms(technique, llm_client):
    """Use LLM to propose synonyms, then validate."""
    prompt = f"""Given the genomic assay '{technique}', list:
    1. Full expansion (if acronym)
    2. Common synonyms
    3. Spelling variants
    4. Related but DISTINCT techniques (to exclude)

    Return JSON with keys: expansion, synonyms, variants, distinct_from
    """

    response = llm_client.complete(prompt)
    proposed = json.loads(response)

    # Validate each synonym
    validated = []
    for syn in proposed['synonyms']:
        # Check 1: Ontology match
        if has_ontology_match(syn, technique):
            validated.append(syn)
        # Check 2: SapBERT similarity
        elif are_synonyms(technique, syn, threshold=0.80):
            validated.append(syn)

    return validated
```

**Benefits:**
- Fast coverage for new techniques
- Discovers colloquial terms
- Human-readable explanations

**Effort:** LOW (1 day)
**Impact:** MEDIUM (good for bootstrapping)

#### 8. **Corpus-based Synonym Mining** ⭐⭐
**Approach:** Mine your own papers/abstracts for variants

```python
def mine_corpus_synonyms(corpus, canonical_techniques, encoder="SapBERT"):
    """Find technique variants in your corpus."""

    # Extract all noun chunks
    noun_chunks = extract_noun_chunks(corpus)

    # Encode with SapBERT/E5
    chunk_embeddings = encode_terms(noun_chunks, encoder)
    canonical_embeddings = encode_terms(canonical_techniques, encoder)

    # Find nearest neighbors
    for canonical, canonical_emb in zip(canonical_techniques, canonical_embeddings):
        similarities = cosine_similarity([canonical_emb], chunk_embeddings)[0]
        top_candidates = [(noun_chunks[i], similarities[i])
                          for i in np.argsort(similarities)[-20:]]

        # Filter with rules
        synonyms = []
        for candidate, score in top_candidates:
            if score >= 0.85:  # High similarity
                if not is_hypernym(candidate, canonical):  # Not "sequencing"
                    if not is_distinct_technique(candidate, canonical):
                        synonyms.append(candidate)

        yield canonical, synonyms
```

**Benefits:**
- Discovers domain-specific variants
- Finds new acronyms
- Corpus-tailored

**Effort:** MEDIUM (2 days)
**Impact:** MEDIUM-HIGH (finds unknown terms)

---

## Proposed Architecture

### Synonym Expansion Pipeline

```
User Query: "ATAC-seq chromatin accessibility diabetes"
    ↓
[1. Abbreviation Detection]
    ATAC-seq → "Assay for Transposase-Accessible Chromatin sequencing"
    ↓
[2. Variant Generation]
    ATAC-seq → {ATACseq, ATAC seq, atac-seq, atacseq}
    ↓
[3. Ontology Lookup]
    ATAC-seq → OBI:0002039 → synonyms: ["ATAC assay", "Accessible chromatin assay"]
    chromatin accessibility → MeSH:D002843 + related terms
    ↓
[4. Embedding Mining] (optional)
    Find nearest neighbors in corpus with SapBERT
    ↓
[5. Canonical Normalization]
    All variants → canonical ID (e.g., OBI:0002039)
    ↓
[6. Query Building]
    PubMed: ("ATAC-seq"[MeSH] OR "chromatin accessibility"[MeSH] OR ...) AND ("diabetes"[MeSH])
    OpenAlex: "ATAC-seq" OR "Assay for Transposase-Accessible Chromatin" OR ...
```

### Enhanced Entity Model

```python
@dataclass
class EnhancedEntity(Entity):
    """Entity with normalization and synonyms."""

    # Original fields
    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float

    # NEW: Normalization
    canonical_id: Optional[str] = None  # OBI:0002039, MESH:D019175, etc.
    canonical_name: Optional[str] = None  # Official name

    # NEW: Synonyms
    synonyms: List[str] = field(default_factory=list)
    abbreviation: Optional[str] = None  # ATAC-seq
    expansion: Optional[str] = None     # Assay for Transposase...

    # NEW: Ontology links
    ontology_source: Optional[str] = None  # OBI, MeSH, EDAM
    umls_cui: Optional[str] = None        # C1234567

    # NEW: Variants
    spelling_variants: List[str] = field(default_factory=list)
```

---

## Implementation Priorities

### Must-Have (Phase 2B - Next Sprint)
1. ⭐⭐⭐ **Abbreviation Detection** (2-3 hours)
   - scispaCy AbbreviationDetector
   - Immediate 50% improvement

2. ⭐⭐⭐ **MeSH Integration** (1 day)
   - Map 50 top techniques to MeSH
   - Get official synonyms
   - Better PubMed queries

3. ⭐⭐ **Variant Generation** (1-2 hours)
   - Rule-based spelling/format variants
   - Hyphenation, capitalization, seq variants

### High-Value (Phase 2C - 1-2 weeks)
4. ⭐⭐⭐ **OBI Ontology Integration** (2-3 days)
   - Comprehensive assay coverage
   - Formal definitions
   - Community standard

5. ⭐⭐⭐ **SapBERT Synonym Discovery** (2-3 days)
   - Find unknown variants
   - High recall
   - Corpus mining

6. ⭐⭐ **UMLS Entity Linking** (3-4 days)
   - Canonical IDs (CUIs)
   - Cross-database normalization
   - Disambiguation

### Nice-to-Have (Phase 2D - Future)
7. ⭐ **LLM Bootstrap** (1 day)
   - Fast synonym proposals
   - Validate with ontologies

8. ⭐⭐ **Corpus Mining** (2 days)
   - Domain-specific variants
   - New acronyms

---

## Canonical ID Mappings (Starter Set)

### Epigenetics
```python
CANONICAL_MAPPINGS = {
    # DNA Methylation
    "WGBS": {
        "expansion": "Whole-Genome Bisulfite Sequencing",
        "obi_id": "OBI:0002042",
        "mesh_id": "D019175",  # DNA Methylation [MeSH]
        "synonyms": ["whole genome bisulfite sequencing", "WGBS-seq"],
    },
    "RRBS": {
        "expansion": "Reduced Representation Bisulfite Sequencing",
        "obi_id": "OBI:0002043",
        "mesh_id": "D019175",
        "synonyms": ["reduced representation bisulfite sequencing"],
    },
    "DNA methylation": {
        "edam_id": "EDAM:operation_3204",  # DNA methylation profiling
        "mesh_id": "D019175",
        "synonyms": ["methylation profiling", "methylation analysis"],
    },

    # Chromatin Accessibility
    "ATAC-seq": {
        "expansion": "Assay for Transposase-Accessible Chromatin using sequencing",
        "obi_id": "OBI:0002039",
        "mesh_id": "D000074263",  # Chromatin Immunoprecipitation Sequencing [MeSH]
        "synonyms": ["ATAC assay", "transposase-accessible chromatin sequencing"],
    },
    "DNase-seq": {
        "expansion": "DNase I hypersensitive sites sequencing",
        "obi_id": "OBI:0001853",
        "synonyms": ["DNase hypersensitivity sequencing", "DHS-seq"],
    },
    "FAIRE-seq": {
        "expansion": "Formaldehyde-Assisted Isolation of Regulatory Elements sequencing",
        "obi_id": "OBI:0001861",
        "synonyms": ["FAIRE", "formaldehyde-assisted isolation"],
    },
    "chromatin accessibility": {
        "edam_id": "EDAM:operation_3222",
        "synonyms": ["open chromatin", "chromatin openness", "accessible chromatin"],
        "subtechniques": ["ATAC-seq", "DNase-seq", "FAIRE-seq"],
    },

    # Gene Expression
    "RNA-seq": {
        "expansion": "RNA sequencing",
        "obi_id": "OBI:0001271",
        "mesh_id": "D059014",  # Sequence Analysis, RNA [MeSH]
        "synonyms": ["RNA sequencing", "transcriptome sequencing", "RNAseq"],
    },
    "scRNA-seq": {
        "expansion": "single-cell RNA sequencing",
        "obi_id": "OBI:0002631",
        "synonyms": ["single cell RNA-seq", "scRNAseq"],
    },

    # ChIP-based
    "ChIP-seq": {
        "expansion": "Chromatin Immunoprecipitation Sequencing",
        "obi_id": "OBI:0000716",
        "mesh_id": "D047369",  # Chromatin Immunoprecipitation [MeSH]
        "synonyms": ["ChIP sequencing", "chromatin immunoprecipitation sequencing"],
    },

    # 3D Genome
    "Hi-C": {
        "expansion": "Chromosome conformation capture high-throughput",
        "obi_id": "OBI:0002086",
        "synonyms": ["HiC", "high-throughput chromosome conformation capture"],
    },
}
```

---

## Benefits Summary

### With Synonym Expansion
**Before:**
```
Query: "ATAC-seq diabetes"
PubMed search: "ATAC-seq"[Text Word] AND "diabetes"[MeSH]
Results: 150 papers (many missed due to variant spellings)
```

**After:**
```
Query: "ATAC-seq diabetes"
Expanded: "ATAC-seq" OR "ATACseq" OR "Assay for Transposase-Accessible Chromatin"
          OR "transposase-accessible chromatin sequencing"
PubMed search: ("ATAC-seq"[Text Word] OR "ATACseq"[Text Word]
                OR "chromatin accessibility"[MeSH]) AND "diabetes"[MeSH]
Results: 450 papers (3x more coverage!)
```

### With Canonical Normalization
**Before:**
```
Query 1: "ATAC-seq"
Query 2: "ATACseq"
Query 3: "chromatin accessibility ATAC"
→ Three separate searches, duplicate results, missed connections
```

**After:**
```
All queries → normalize to OBI:0002039
→ Single canonical search, deduplicated results, comprehensive coverage
```

---

## Recommended Timeline

### Week 1 (Phase 2B Foundation)
- Day 1-2: Abbreviation detection + variant generation
- Day 3-4: MeSH integration (50 top techniques)
- Day 5: Testing and validation

### Week 2 (Phase 2C Advanced)
- Day 1-3: OBI ontology integration
- Day 4-5: SapBERT setup and testing

### Week 3 (Phase 2C+ Production)
- Day 1-2: UMLS linker setup
- Day 3-4: Corpus-based synonym mining
- Day 5: Integration testing

### Week 4 (Phase 2D Polish)
- Day 1-2: LLM bootstrap pipeline
- Day 3-4: Performance optimization
- Day 5: Documentation and handoff

---

## Files to Create/Modify

### New Files
1. `omics_oracle_v2/lib/nlp/synonym_expander.py` - Synonym expansion pipeline
2. `omics_oracle_v2/lib/nlp/ontology_mapper.py` - OBI/MeSH/EDAM integration
3. `omics_oracle_v2/lib/nlp/canonical_mappings.py` - Technique → canonical ID mappings
4. `config/ontologies/` - Cached ontology data
5. `test_synonym_expansion.py` - Comprehensive synonym tests

### Modified Files
1. `omics_oracle_v2/lib/nlp/biomedical_ner.py` - Add abbreviation detector, linker
2. `omics_oracle_v2/lib/nlp/models.py` - Extend Entity with normalization fields
3. `omics_oracle_v2/lib/publications/pipeline.py` - Use synonyms in query building

---

## Success Metrics

**Coverage:**
- Synonym recall: 50% → 95%+
- Variant detection: 60% → 98%+
- Canonical normalization: 0% → 100%

**Query Quality:**
- Search results: +2-3x coverage
- Precision: Same or better (filtered by relevance)
- Deduplication: Automatic via canonical IDs

**Production Readiness:**
- Ontology-backed (high precision)
- Embedding-assisted (high recall)
- LLM-validated (comprehensive)
- Test coverage: 95%+

---

**Status:** Roadmap complete - ready to implement Phase 2B! 🚀

**Priority 1:** Abbreviation detection + MeSH integration (Week 1)
**Priority 2:** OBI ontology + SapBERT (Week 2)
**Priority 3:** UMLS + corpus mining (Week 3-4)
