# Genomic Technique Recognition - Enhancement Plan

**Date:** October 9, 2025  
**Status:** Gap Analysis Complete  
**Current Coverage:** 70% (needs improvement to 95%+)

---

## Current State Analysis

### ✅ What We Recognize Well (14 techniques)
- RNA-seq, scRNA-seq
- ChIP-seq
- microarray, Affymetrix microarray
- DNase-seq, DNase hypersensitivity sequencing
- CLIP-seq
- bisulfite sequencing, whole genome bisulfite sequencing
- transcriptome sequencing
- chromatin immunoprecipitation sequencing

### ❌ What We're Missing (Critical Gaps)

**1. Epigenetics Terms (30% miss rate)**
- ❌ DNA methylation (classified as GENERAL)
- ❌ WGBS - whole genome bisulfite sequencing (classified as GENE!)
- ❌ RRBS - reduced representation bisulfite sequencing (classified as GENE!)
- ❌ methylation profiling (not recognized)

**2. Chromatin Accessibility (50% miss rate)**
- ❌ ATAC-seq chromatin (classified as CHEMICAL!)
- ❌ ATAC-seq alone (works only in full phrase)
- ❌ FAIRE-seq (not recognized)
- ❌ chromatin accessibility (classified as GENERAL)
- ✅ DNase-seq (works)

**3. Other NGS Techniques (60% miss rate)**
- ❌ Hi-C (classified as GENERAL)
- ❌ CAGE-seq (partial recognition)
- ❌ single-cell RNA-seq (classified as CELL_TYPE!)
- ✅ scRNA-seq (works)

**4. Multi-word Technique Phrases**
- ❌ "DNA methylation" (should be TECHNIQUE, not GENERAL)
- ❌ "chromatin accessibility" (should be TECHNIQUE)
- ❌ "gene expression profiling" (partially recognized)
- ❌ "transcription factor binding" (not recognized)

---

## Root Cause Analysis

### Issue 1: Limited Pattern Matching
Current patterns in `_is_experimental_technique()`:
```python
technique_patterns = {
    "pcr", "qpcr", "rt-pcr",
    "western blot",
    "microarray",
    "rna-seq", "chip-seq",  # ✅ Works
    "proteomics", "genomics",
    "sequencing",
    "flow cytometry",
    "immunofluorescence",
}
```

**Problems:**
- Missing acronyms: WGBS, RRBS, ATAC-seq, FAIRE-seq, Hi-C, CAGE-seq
- Missing full names: DNA methylation, chromatin accessibility
- Missing compound terms: bisulfite sequencing variants

### Issue 2: Wrong Classification Priority
```python
def _classify_entity(self, ent, text_lower: str) -> EntityType:
    # Priority order matters - check most specific first
    if self._is_gene_entity(ent, text_lower):  # ❌ WGBS matches here!
        return EntityType.GENE
    # ...
    elif self._is_experimental_technique(ent, text_lower):  # Too low priority!
        return EntityType.TECHNIQUE
```

**Problems:**
- WGBS/RRBS match gene pattern (short uppercase)
- ATAC-seq matches chemical pattern (ends with "ase"?)
- Technique check is LAST (should be earlier)

### Issue 3: Incomplete Genomic Vocabulary
Missing critical genomic data analysis terms:
- Epigenetic profiling techniques
- Single-cell methods variants
- 3D genome structure methods
- RNA modification techniques

---

## Enhancement Strategy

### Phase 2A: Expand Technique Patterns (Priority 1)

**Add comprehensive genomic technique patterns:**

```python
# Epigenetics
"dna methylation", "methylation", "methylation profiling",
"wgbs", "rrbs", 
"bisulfite", "bisulfite-seq",
"whole genome bisulfite", "reduced representation bisulfite",

# Chromatin accessibility  
"atac-seq", "atac", "atacseq",
"dnase-seq", "dnase", "dnaseseq", "dnase hypersensitivity",
"faire-seq", "faire",
"chromatin accessibility", "open chromatin",

# Gene expression
"rna-seq", "rnaseq", "rna seq",
"scrna-seq", "scrnaseq", "single-cell rna-seq", "single cell rna-seq",
"microarray", "gene chip",
"qpcr", "rt-qpcr", "quantitative pcr",

# Chromatin structure
"chip-seq", "chipseq", "chip seq",
"cut&run", "cut&tag",
"hi-c", "hic", "3c", "4c", "5c",
"chromatin conformation",

# RNA binding
"clip-seq", "clipseq", "par-clip", "iclip",
"rip-seq", "ripseq",

# Other NGS
"cage-seq", "cageseq", "cage",
"gro-seq", "groseq",
"net-seq", "netseq",
```

### Phase 2B: Fix Classification Priority (Priority 1)

**Move technique check BEFORE gene check:**

```python
def _classify_entity(self, ent, text_lower: str) -> EntityType:
    # Check techniques EARLY (before gene/chemical/general)
    if self._is_experimental_technique(ent, text_lower):  # ✅ Move up!
        return EntityType.TECHNIQUE
    
    # Then check biological entities
    if self._is_gene_entity(ent, text_lower):
        return EntityType.GENE
    # ... rest
```

### Phase 2C: Enhanced Technique Detector (Priority 2)

**Create specialized genomic technique detector:**

```python
def _is_experimental_technique(self, ent, text_lower: str) -> bool:
    """Enhanced genomic technique detection."""
    
    # Core NGS techniques (high priority)
    ngs_patterns = {
        "rna-seq", "rnaseq", "scrna-seq", "scrnaseq",
        "chip-seq", "chipseq",
        "atac-seq", "atacseq", "atac",
        "dnase-seq", "dnaseseq",
        "wgbs", "rrbs",
        "hi-c", "hic",
    }
    
    # Full technique names
    full_names = {
        "dna methylation",
        "chromatin accessibility",
        "gene expression profiling",
        "bisulfite sequencing",
        "chromatin immunoprecipitation",
        "transcription factor binding",
    }
    
    # Check exact matches (case-insensitive)
    if text_lower in ngs_patterns or text_lower in full_names:
        return True
    
    # Check -seq suffix (most NGS techniques)
    if text_lower.endswith("-seq") or text_lower.endswith("seq"):
        return True
    
    # Check sequencing in name
    if "sequencing" in text_lower:
        return True
    
    # Check chromatin-related
    if "chromatin" in text_lower:
        return True
    
    # Check methylation-related
    if "methylation" in text_lower:
        return True
    
    # ... existing patterns ...
    
    return False
```

---

## Implementation Plan

### Immediate (Today - Phase 2A)

1. **Enhance `_is_experimental_technique()` method**
   - Add 50+ genomic technique patterns
   - Include acronyms and full names
   - Add suffix/keyword detection

2. **Fix classification priority**
   - Move technique check before gene check
   - Prevent misclassification of WGBS/RRBS as genes

3. **Test coverage improvement**
   - Target: 95%+ technique recognition
   - Validate with genomic test suite

### Short-term (Next Sprint - Phase 2B)

4. **Add technique categories**
   - Epigenetics techniques
   - Chromatin accessibility techniques
   - Gene expression techniques
   - 3D genome techniques
   - RNA modification techniques

5. **Query builder enhancement**
   - Map techniques to PubMed MeSH when available
   - Special handling for compound techniques
   - Optimize for GEO database queries

6. **Synonym expansion**
   - RNA-seq → "RNA sequencing", "transcriptome sequencing"
   - ATAC-seq → "chromatin accessibility", "open chromatin profiling"
   - ChIP-seq → "chromatin immunoprecipitation", "TF binding"

### Medium-term (Phase 2C)

7. **Technique ontology integration**
   - Map to EFO (Experimental Factor Ontology)
   - Link to GEO technique terms
   - Connect to NCBI MeSH tree

8. **Context-aware classification**
   - "methylation" + "profiling" → TECHNIQUE
   - "chromatin" + "accessibility" → TECHNIQUE
   - Multi-token technique detection

9. **GEO-specific optimization**
   - Map techniques to GEO platform types
   - Optimize for dataset discovery
   - Add study type inference

---

## Expected Improvements

### Coverage Increase
- **Before:** 70% technique recognition (21/30 queries)
- **After Phase 2A:** 95%+ (28/30 queries)
- **After Phase 2B:** 98%+ (29/30 queries)

### Query Quality
- **Before:** Generic text search for most techniques
- **After:** Database-specific field tags + MeSH terms

### Specific Fixes

**DNA Methylation Queries:**
```python
# BEFORE:
"DNA methylation WGBS breast cancer"
→ Entities: general["DNA methylation"], disease["breast cancer"]
→ PubMed: ("breast cancer"[MeSH]) OR (original)

# AFTER:
"DNA methylation WGBS breast cancer"
→ Entities: technique["DNA methylation", "WGBS"], disease["breast cancer"]
→ PubMed: (("DNA methylation"[Text Word] OR "WGBS"[Text Word]) AND ("breast cancer"[MeSH])) OR (original)
```

**Chromatin Accessibility Queries:**
```python
# BEFORE:
"ATAC-seq chromatin accessibility diabetes"
→ Entities: chemical["ATAC-seq chromatin"], disease["diabetes"]
→ Misclassified!

# AFTER:
"ATAC-seq chromatin accessibility diabetes"
→ Entities: technique["ATAC-seq", "chromatin accessibility"], disease["diabetes"]
→ PubMed: (("ATAC-seq"[Text Word] OR "chromatin accessibility"[Text Word]) AND ("diabetes"[MeSH])) OR (original)
```

**Multi-technique Queries:**
```python
# BEFORE:
"RNA-seq and ATAC-seq integration"
→ Entities: technique["RNA-seq", "ATAC-seq"], organism["integration"] (wrong!)

# AFTER:
"RNA-seq and ATAC-seq integration"
→ Entities: technique["RNA-seq", "ATAC-seq"]
→ PubMed: (("RNA-seq"[Text Word] OR "ATAC-seq"[Text Word])) OR (original)
```

---

## Testing Strategy

### Test Cases to Add

1. **Epigenetics**
   - DNA methylation, WGBS, RRBS, bisulfite-seq
   - Histone modifications, ChIP-seq
   - Chromatin remodeling

2. **Gene Expression**
   - RNA-seq, scRNA-seq, snRNA-seq
   - Microarray, gene chip
   - qPCR, RT-qPCR

3. **Chromatin Accessibility**
   - ATAC-seq, DNase-seq, FAIRE-seq
   - MNase-seq, NOMe-seq

4. **3D Genome**
   - Hi-C, 3C, 4C, 5C
   - ChIA-PET, PLAC-seq

5. **RNA Biology**
   - CLIP-seq, RIP-seq, PAR-CLIP
   - m6A-seq, Ribo-seq

### Success Metrics

- [ ] 95%+ technique recognition rate
- [ ] Zero misclassifications (WGBS, RRBS as genes)
- [ ] All acronyms + full names recognized
- [ ] Multi-word techniques detected
- [ ] Proper PubMed field tags applied

---

## Next Steps

1. ✅ Run genomic test (DONE - identified gaps)
2. ⏳ Enhance technique patterns (NEXT)
3. ⏳ Fix classification priority
4. ⏳ Re-test and validate
5. ⏳ Document improvements
6. ⏳ Commit Phase 2A changes

---

## Files to Modify

1. **`omics_oracle_v2/lib/nlp/biomedical_ner.py`**
   - Lines 420-435: `_is_experimental_technique()` method
   - Lines 190-210: `_classify_entity()` priority order

2. **`test_genomic_terms.py`**
   - Add more test cases
   - Validate improvements

3. **`omics_oracle_v2/lib/publications/pipeline.py`**
   - No changes needed (already uses TECHNIQUE entities)

---

**Status:** Ready to implement Phase 2A enhancements  
**Timeline:** 1-2 hours for Phase 2A  
**Impact:** 70% → 95%+ technique recognition

Let's build robust genomic term handling! 🧬
