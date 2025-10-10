# Phase 2B: Synonym Expansion & Entity Normalization
## Implementation Plan

**Sprint:** Phase 2B
**Duration:** 3-5 days
**Priority:** CRITICAL
**Goal:** Add synonym expansion and canonical normalization to achieve 95%+ coverage

---

## Gap Analysis: What We're Missing

### 🔴 CRITICAL Gaps (Must Fix)

1. **No Synonym Expansion**
   - Problem: "ATAC-seq" query only searches for exact text
   - Missing: "Assay for Transposase-Accessible Chromatin", "ATACseq", "ATAC assay"
   - Impact: Missing 60-70% of relevant papers

2. **No Canonical Normalization**
   - Problem: "ATAC-seq", "ATACseq", "ATAC" treated as different queries
   - Missing: Single canonical ID (OBI:0002039) for all variants
   - Impact: Duplicate results, fragmented search

3. **No Abbreviation Detection**
   - Problem: Can't extract "ATAC-seq ↔ Assay for Transposase-Accessible Chromatin"
   - Missing: Schwartz-Hearst algorithm from scispaCy
   - Impact: Lost bidirectional mappings

4. **No Ontology Integration**
   - Problem: No connection to OBI, MeSH, EDAM, EFO
   - Missing: Official synonyms, hierarchies, semantic types
   - Impact: No authoritative validation

5. **No Embedding-based Discovery**
   - Problem: Can't find unknown/new variants
   - Missing: SapBERT, E5 similarity search
   - Impact: Zero discovery of corpus-specific terms

---

## Immediate Actions (Days 1-2)

### Task 1: Abbreviation Detection ⭐⭐⭐
**Effort:** 2-3 hours
**Impact:** HIGH (50% improvement)

#### Implementation
```python
# File: omics_oracle_v2/lib/nlp/biomedical_ner.py

from scispacy.abbreviation import AbbreviationDetector

class BiomedicalNER:
    def __init__(self):
        # Existing code...

        # Add abbreviation detector
        if "abbreviation_detector" not in self.nlp.pipe_names:
            self.nlp.add_pipe("abbreviation_detector")

    def extract_entities(self, text: str) -> List[Entity]:
        doc = self.nlp(text)
        entities = []

        # Extract abbreviations FIRST
        abbreviations = {}
        for abrv in doc._.abbreviations:
            abbreviations[abrv.text] = abrv._.long_form.text
            entities.append(Entity(
                text=abrv.text,
                entity_type=EntityType.TECHNIQUE,
                start=abrv.start_char,
                end=abrv.end_char,
                expansion=abrv._.long_form.text
            ))

        # Then extract other entities...
        # Existing code
```

#### Test
```python
# test_abbreviation_detection.py

def test_abbreviation_extraction():
    ner = BiomedicalNER()

    text = "Assay for Transposase-Accessible Chromatin (ATAC-seq) was used"
    entities = ner.extract_entities(text)

    atac = [e for e in entities if e.text == "ATAC-seq"][0]
    assert atac.expansion == "Assay for Transposase-Accessible Chromatin"
    assert atac.entity_type == EntityType.TECHNIQUE

def test_bidirectional_mapping():
    ner = BiomedicalNER()

    # Test 1: Abbreviation → expansion
    text1 = "We performed ATAC-seq analysis"
    entities1 = ner.extract_entities(text1)
    # Should use cached expansion from corpus

    # Test 2: Expansion → abbreviation
    text2 = "Assay for Transposase-Accessible Chromatin results"
    entities2 = ner.extract_entities(text2)
    # Should recognize as same as ATAC-seq
```

---

### Task 2: Variant Generation ⭐⭐
**Effort:** 1-2 hours
**Impact:** MEDIUM (30% improvement)

#### Implementation
```python
# File: omics_oracle_v2/lib/nlp/variant_generator.py

from typing import Set

class VariantGenerator:
    """Generate spelling/format variants for technique terms."""

    @staticmethod
    def generate_variants(term: str) -> Set[str]:
        """Generate all possible variants of a term."""
        variants = {term}

        # 1. Hyphenation variants
        if "-" in term:
            variants.add(term.replace("-", " "))
            variants.add(term.replace("-", ""))
        if " " in term:
            variants.add(term.replace(" ", "-"))
            variants.add(term.replace(" ", ""))

        # 2. Capitalization variants
        variants.add(term.upper())
        variants.add(term.lower())
        variants.add(term.title())

        # 3. seq/sequencing variants
        if term.endswith("-seq"):
            base = term[:-4]
            variants.add(f"{base}seq")
            variants.add(f"{base} seq")
            variants.add(f"{base} sequencing")
            variants.add(f"{base}-sequencing")
        elif term.endswith("seq") and not term.endswith("-seq"):
            base = term[:-3]
            variants.add(f"{base}-seq")
            variants.add(f"{base} seq")

        # 4. Pluralization
        if not term.endswith('s'):
            variants.add(f"{term}s")

        return variants

    @staticmethod
    def generate_expanded_variants(term: str, expansion: str) -> Set[str]:
        """Generate variants including expansion."""
        variants = VariantGenerator.generate_variants(term)
        variants.update(VariantGenerator.generate_variants(expansion))

        # Add mixed variants
        if expansion:
            words = expansion.split()
            if len(words) > 2:
                # Partial expansions
                variants.add(" ".join(words[:3]))  # First 3 words
                variants.add(" ".join(words[-3:]))  # Last 3 words

        return variants

# Example usage:
# ATAC-seq → {ATAC-seq, ATACseq, ATAC seq, atac-seq, ATAC sequencing, ...}
```

#### Test
```python
def test_variant_generation():
    variants = VariantGenerator.generate_variants("ATAC-seq")

    assert "ATAC-seq" in variants
    assert "ATACseq" in variants
    assert "ATAC seq" in variants
    assert "atac-seq" in variants
    assert "ATAC sequencing" in variants

    assert len(variants) >= 10  # Should generate many variants
```

---

### Task 3: MeSH Integration ⭐⭐⭐
**Effort:** 1 day
**Impact:** HIGH (authoritative synonyms)

#### Implementation
```python
# File: omics_oracle_v2/lib/nlp/ontology_mapper.py

import requests
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class MeSHMapping:
    mesh_id: str
    mesh_name: str
    entry_terms: List[str]
    tree_numbers: List[str]

class MeSHMapper:
    """Map techniques to MeSH terms and get synonyms."""

    # Curated mappings for top 50 techniques
    TECHNIQUE_TO_MESH = {
        # DNA Methylation
        "DNA methylation": "D019175",
        "WGBS": "D019175",
        "RRBS": "D019175",
        "bisulfite sequencing": "D019175",

        # Chromatin
        "ATAC-seq": "D000074263",  # Chromatin Immunoprecipitation Sequencing
        "ChIP-seq": "D047369",     # Chromatin Immunoprecipitation
        "DNase-seq": "D000074263",

        # RNA
        "RNA-seq": "D059014",      # Sequence Analysis, RNA
        "scRNA-seq": "D059014",
        "microarray": "D020869",   # Oligonucleotide Array Sequence Analysis

        # Add 40 more...
    }

    def __init__(self, cache_dir: str = "config/mesh_cache"):
        self.cache_dir = cache_dir
        self.cache = {}

    def get_mesh_info(self, mesh_id: str) -> Optional[MeSHMapping]:
        """Get MeSH term info from NCBI E-utilities."""
        if mesh_id in self.cache:
            return self.cache[mesh_id]

        # Call NCBI E-utilities
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "mesh",
            "id": mesh_id,
            "retmode": "xml"
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            # Parse XML and extract entry terms
            # (Implementation details omitted)
            mapping = self._parse_mesh_xml(response.text)
            self.cache[mesh_id] = mapping
            return mapping

        return None

    def get_synonyms(self, technique: str) -> List[str]:
        """Get all MeSH synonyms for a technique."""
        mesh_id = self.TECHNIQUE_TO_MESH.get(technique.lower())
        if not mesh_id:
            return []

        mesh_info = self.get_mesh_info(mesh_id)
        if mesh_info:
            return mesh_info.entry_terms
        return []

# Example:
# mapper.get_synonyms("ATAC-seq")
# → ["Chromatin Accessibility Sequencing", "ATAC assay", ...]
```

#### Test
```python
def test_mesh_mapping():
    mapper = MeSHMapper()

    # Test known mappings
    assert mapper.TECHNIQUE_TO_MESH["RNA-seq"] == "D059014"
    assert mapper.TECHNIQUE_TO_MESH["DNA methylation"] == "D019175"

    # Test synonym retrieval
    synonyms = mapper.get_synonyms("RNA-seq")
    assert "RNA sequencing" in [s.lower() for s in synonyms]
    assert len(synonyms) >= 3
```

---

## Advanced Features (Days 3-5)

### Task 4: OBI Ontology Integration ⭐⭐⭐
**Effort:** 2-3 days
**Impact:** VERY HIGH (comprehensive coverage)

#### Implementation
```python
# File: omics_oracle_v2/lib/nlp/obi_mapper.py

from owlready2 import get_ontology
from typing import Dict, List, Optional

class OBIMapper:
    """Map techniques to OBI (Ontology for Biomedical Investigations)."""

    # Curated OBI mappings
    TECHNIQUE_TO_OBI = {
        "ATAC-seq": "OBI:0002039",
        "ChIP-seq": "OBI:0000716",
        "RNA-seq": "OBI:0001271",
        "WGBS": "OBI:0002042",
        "RRBS": "OBI:0002043",
        "Hi-C": "OBI:0002086",
        "scRNA-seq": "OBI:0002631",
        # Add 100+ more
    }

    def __init__(self, obi_path: str = "config/ontologies/obi.owl"):
        self.obi_path = obi_path
        self.ontology = None

    def load_ontology(self):
        """Load OBI ontology (one-time setup)."""
        if not self.ontology:
            self.ontology = get_ontology(self.obi_path).load()

    def get_obi_info(self, obi_id: str) -> Dict:
        """Get OBI term information."""
        self.load_ontology()

        term = self.ontology.search_one(id=obi_id)
        if term:
            return {
                "id": obi_id,
                "label": term.label[0] if term.label else "",
                "definition": term.definition[0] if hasattr(term, 'definition') else "",
                "synonyms": list(term.hasExactSynonym) if hasattr(term, 'hasExactSynonym') else [],
                "related_synonyms": list(term.hasRelatedSynonym) if hasattr(term, 'hasRelatedSynonym') else [],
            }
        return {}

    def get_canonical_id(self, technique: str) -> Optional[str]:
        """Get canonical OBI ID for a technique."""
        return self.TECHNIQUE_TO_OBI.get(technique.lower())

# Example:
# mapper.get_obi_info("OBI:0002039")
# → {"label": "ATAC-seq assay", "synonyms": ["ATAC assay", ...]}
```

---

### Task 5: SapBERT Synonym Discovery ⭐⭐⭐
**Effort:** 2-3 days
**Impact:** VERY HIGH (discovers unknown variants)

#### Implementation
```python
# File: omics_oracle_v2/lib/nlp/embedding_synonyms.py

from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SapBERTSynonymFinder:
    """Find synonyms using SapBERT embeddings."""

    def __init__(self, model_name: str = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def encode_terms(self, terms: List[str]) -> np.ndarray:
        """Encode terms to embeddings."""
        with torch.no_grad():
            inputs = self.tokenizer(terms, padding=True, truncation=True, return_tensors="pt")
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token
            embeddings = embeddings.cpu().numpy()
        return embeddings

    def are_synonyms(self, term1: str, term2: str, threshold: float = 0.85) -> bool:
        """Check if two terms are synonymous."""
        embeddings = self.encode_terms([term1, term2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return similarity >= threshold

    def find_synonyms(self, canonical_term: str, candidate_terms: List[str],
                      top_k: int = 10, threshold: float = 0.80) -> List[tuple]:
        """Find most similar terms."""
        canonical_emb = self.encode_terms([canonical_term])
        candidate_embs = self.encode_terms(candidate_terms)

        similarities = cosine_similarity(canonical_emb, candidate_embs)[0]

        # Filter by threshold
        valid_indices = [i for i, sim in enumerate(similarities) if sim >= threshold]

        # Sort and take top-k
        top_indices = sorted(valid_indices, key=lambda i: similarities[i], reverse=True)[:top_k]

        return [(candidate_terms[i], similarities[i]) for i in top_indices]

# Example:
# finder.find_synonyms("ATAC-seq", ["ATACseq", "chromatin accessibility", "DNA-seq", ...])
# → [("ATACseq", 0.98), ("chromatin accessibility", 0.87), ...]
```

#### Test
```python
def test_sapbert_synonyms():
    finder = SapBERTSynonymFinder()

    # Test synonym detection
    assert finder.are_synonyms("ATAC-seq", "ATACseq", threshold=0.85)
    assert finder.are_synonyms("RNA-seq", "RNA sequencing", threshold=0.85)

    # Test synonym finding
    candidates = [
        "ATACseq",
        "chromatin accessibility",
        "DNA methylation",  # Not synonym
        "ATAC assay",
        "whole genome sequencing",  # Not synonym
    ]

    synonyms = finder.find_synonyms("ATAC-seq", candidates, threshold=0.80)

    # Should find ATACseq and ATAC assay, not DNA methylation
    synonym_texts = [s[0] for s in synonyms]
    assert "ATACseq" in synonym_texts
    assert "ATAC assay" in synonym_texts
    assert "DNA methylation" not in synonym_texts
```

---

## Integrated Pipeline

### Enhanced Entity Model
```python
# File: omics_oracle_v2/lib/nlp/models.py

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class EnhancedEntity(Entity):
    """Entity with normalization and synonyms."""

    # Original fields (unchanged)
    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float = 1.0

    # NEW: Normalization
    canonical_id: Optional[str] = None          # OBI:0002039, MESH:D019175
    canonical_name: Optional[str] = None        # Official name
    ontology_source: Optional[str] = None       # OBI, MeSH, EDAM

    # NEW: Synonyms & Variants
    synonyms: List[str] = field(default_factory=list)
    spelling_variants: List[str] = field(default_factory=list)
    abbreviation: Optional[str] = None          # ATAC-seq
    expansion: Optional[str] = None             # Assay for Transposase...

    # NEW: UMLS (future)
    umls_cui: Optional[str] = None              # C1234567
    semantic_type: Optional[str] = None         # T059 (Laboratory Procedure)
```

### Query Builder with Synonyms
```python
# File: omics_oracle_v2/lib/publications/pipeline.py

def _build_pubmed_query_with_synonyms(self, entities: List[EnhancedEntity],
                                       original_query: str) -> str:
    """Build PubMed query with synonym expansion."""

    # Group by entity type
    genes = []
    techniques = []
    diseases = []

    for entity in entities:
        # Use all variants for search
        all_variants = [entity.text]
        if entity.synonyms:
            all_variants.extend(entity.synonyms)
        if entity.spelling_variants:
            all_variants.extend(entity.spelling_variants)
        if entity.expansion:
            all_variants.append(entity.expansion)

        if entity.entity_type == EntityType.GENE:
            genes.extend(all_variants)
        elif entity.entity_type == EntityType.TECHNIQUE:
            techniques.extend(all_variants)
        elif entity.entity_type == EntityType.DISEASE:
            diseases.extend(all_variants)

    # Build query with OR for synonyms
    components = []

    if genes:
        gene_clause = " OR ".join([f'"{g}"[Gene Name]' for g in set(genes)])
        components.append(f"({gene_clause})")

    if diseases:
        disease_clause = " OR ".join([f'"{d}"[MeSH]' for d in set(diseases)])
        components.append(f"({disease_clause})")

    if techniques:
        tech_clause = " OR ".join([f'"{t}"[Text Word]' for t in set(techniques)])
        components.append(f"({tech_clause})")

    # Combine with AND
    if components:
        optimized = "(" + " AND ".join(components) + ")"
        return f"({optimized}) OR ({original_query}[Text Word])"

    return f"{original_query}[Text Word]"

# Example output:
# Query: "ATAC-seq diabetes"
# Result: (("ATAC-seq"[Text Word] OR "ATACseq"[Text Word] OR
#           "Assay for Transposase-Accessible Chromatin"[Text Word] OR
#           "chromatin accessibility"[Text Word]) AND
#          ("diabetes"[MeSH] OR "diabetes mellitus"[MeSH])) OR
#         ("ATAC-seq diabetes"[Text Word])
```

---

## Testing Strategy

### Unit Tests
```python
# test_synonym_expansion.py

class TestSynonymExpansion:

    def test_abbreviation_detection(self):
        """Test abbreviation extraction."""
        ner = BiomedicalNER()
        text = "Assay for Transposase-Accessible Chromatin (ATAC-seq) profiling"
        entities = ner.extract_entities(text)

        atac = [e for e in entities if e.text == "ATAC-seq"][0]
        assert atac.expansion == "Assay for Transposase-Accessible Chromatin"

    def test_variant_generation(self):
        """Test variant generation."""
        variants = VariantGenerator.generate_variants("ATAC-seq")
        assert len(variants) >= 10
        assert "ATACseq" in variants
        assert "ATAC sequencing" in variants

    def test_mesh_mapping(self):
        """Test MeSH integration."""
        mapper = MeSHMapper()
        synonyms = mapper.get_synonyms("RNA-seq")
        assert len(synonyms) >= 3

    def test_obi_mapping(self):
        """Test OBI integration."""
        mapper = OBIMapper()
        obi_id = mapper.get_canonical_id("ATAC-seq")
        assert obi_id == "OBI:0002039"

        info = mapper.get_obi_info(obi_id)
        assert "ATAC" in info["label"]

    def test_sapbert_synonyms(self):
        """Test SapBERT synonym finding."""
        finder = SapBERTSynonymFinder()
        assert finder.are_synonyms("ATAC-seq", "ATACseq", threshold=0.85)

    def test_query_expansion(self):
        """Test query expansion with synonyms."""
        pipeline = PublicationSearchPipeline()

        query = "ATAC-seq diabetes"
        entities = pipeline._preprocess_query(query)
        pubmed_query = pipeline._build_pubmed_query_with_synonyms(entities, query)

        # Should contain multiple ATAC variants
        assert "ATAC-seq" in pubmed_query
        assert "ATACseq" in pubmed_query or "chromatin accessibility" in pubmed_query
        assert "diabetes" in pubmed_query
```

### Integration Tests
```python
def test_end_to_end_synonym_expansion():
    """Test complete pipeline with synonym expansion."""
    pipeline = PublicationSearchPipeline()

    # Query with technique acronym
    results = pipeline.search("WGBS breast cancer", limit=20)

    # Verify synonyms were used
    assert len(results) > 0

    # Check that we found papers with variants
    titles = " ".join([r.title for r in results]).lower()
    assert any(variant in titles for variant in [
        "wgbs", "whole genome bisulfite", "methylation"
    ])
```

---

## Performance Optimization

### Caching Strategy
```python
# File: omics_oracle_v2/lib/nlp/synonym_cache.py

import json
from pathlib import Path
from typing import Dict, Set

class SynonymCache:
    """Cache for technique synonyms and variants."""

    def __init__(self, cache_file: str = "config/synonym_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Set[str]] = {}
        self.load()

    def load(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            with open(self.cache_file) as f:
                data = json.load(f)
                self.cache = {k: set(v) for k, v in data.items()}

    def save(self):
        """Save cache to disk."""
        with open(self.cache_file, 'w') as f:
            data = {k: list(v) for k, v in self.cache.items()}
            json.dump(data, f, indent=2)

    def get_synonyms(self, term: str) -> Set[str]:
        """Get cached synonyms."""
        return self.cache.get(term.lower(), set())

    def add_synonyms(self, term: str, synonyms: Set[str]):
        """Add synonyms to cache."""
        key = term.lower()
        if key not in self.cache:
            self.cache[key] = set()
        self.cache[key].update(synonyms)
        self.save()
```

---

## Success Metrics

### Coverage Improvement
```python
# Before synonym expansion:
Query: "ATAC-seq diabetes"
PubMed: ~150 results
Coverage: 50-60% of relevant papers

# After synonym expansion:
Query: "ATAC-seq diabetes"
Expanded: ATAC-seq OR ATACseq OR "Assay for Transposase..." OR "chromatin accessibility"
PubMed: ~400-500 results
Coverage: 90-95% of relevant papers (3x improvement!)
```

### Quality Metrics
- **Synonym recall:** 50% → 95%+ (target)
- **Variant detection:** 60% → 98%+ (target)
- **Canonical normalization:** 0% → 100% (OBI/MeSH IDs)
- **Query precision:** Maintain 85%+ (no quality loss)
- **Search results:** 2-3x more coverage
- **Performance:** <50ms overhead for synonym expansion

---

## Implementation Checklist

### Day 1-2: Foundation
- [ ] Task 1: Add abbreviation detection (2-3 hours)
- [ ] Task 2: Implement variant generation (1-2 hours)
- [ ] Task 3: Create MeSH mapper (1 day)
- [ ] Unit tests for all components
- [ ] Integration with BiomedicalNER

### Day 3-4: Advanced
- [ ] Task 4: OBI ontology integration (2 days)
- [ ] Task 5: SapBERT setup (1 day)
- [ ] Synonym cache system
- [ ] Query builder enhancement

### Day 5: Testing & Validation
- [ ] Comprehensive test suite (95% coverage)
- [ ] Performance benchmarking
- [ ] End-to-end validation
- [ ] Documentation

---

## Next Steps After Phase 2B

**Phase 2C (Week 2):**
1. UMLS entity linking
2. Corpus-based synonym mining
3. LLM-assisted bootstrap

**Phase 2D (Week 3):**
1. GEO database integration
2. Multi-database support
3. Production deployment

---

**Status:** Ready to implement! 🚀

**Start with:** Abbreviation detection (highest ROI, 2-3 hours) →
**Then:** MeSH integration (authoritative synonyms, 1 day) →
**Finally:** OBI + SapBERT (comprehensive coverage, 2-3 days)
