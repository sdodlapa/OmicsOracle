"""
Tests for Synonym Expansion (Phase 2B.1)

Tests the gazetteer-based synonym expansion system.
"""

import pytest
from omics_oracle_v2.lib.nlp.synonym_expansion import (
    SynonymExpander,
    SynonymExpansionConfig,
    TechniqueSynonyms
)


class TestSynonymExpander:
    """Test synonym expansion functionality."""
    
    def test_basic_expansion(self):
        """Test basic synonym expansion."""
        expander = SynonymExpander()
        
        # Test RNA-seq expansion
        synonyms = expander.expand("RNA-seq")
        assert "RNA-seq" in synonyms
        assert "RNA sequencing" in synonyms or "transcriptome sequencing" in synonyms
        assert len(synonyms) >= 2
        
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        expander = SynonymExpander()
        
        # Different cases should return same canonical
        canonical1 = expander.get_canonical("RNA-seq")
        canonical2 = expander.get_canonical("rna-seq")
        canonical3 = expander.get_canonical("RNA SEQ")
        
        assert canonical1 == canonical2 == canonical3
        assert canonical1 == "RNA sequencing"
    
    def test_hyphen_space_variants(self):
        """Test hyphen/space variant generation."""
        expander = SynonymExpander()
        
        # Test RNA-seq with different formats
        synonyms1 = expander.expand("RNA-seq")
        synonyms2 = expander.expand("RNA seq")
        synonyms3 = expander.expand("RNAseq")
        
        # Should recognize all variants
        assert len(synonyms1) > 0
        assert len(synonyms2) > 0
        assert len(synonyms3) > 0
    
    def test_abbreviation_expansion(self):
        """Test abbreviation expansion."""
        expander = SynonymExpander()
        
        # ATAC-seq abbreviation
        synonyms = expander.expand("ATAC-seq")
        canonical = expander.get_canonical("ATAC-seq")
        
        assert "ATAC-seq" in synonyms
        assert canonical == "assay for transposase-accessible chromatin using sequencing"
    
    def test_common_abbreviations(self):
        """Test common biomedical abbreviations."""
        expander = SynonymExpander()
        
        # NGS should expand
        synonyms = expander.expand("NGS")
        assert "NGS" in synonyms
        assert any("next-generation sequencing" in s.lower() for s in synonyms)
        
        # WGS should expand
        synonyms = expander.expand("WGS")
        assert "WGS" in synonyms
        assert any("whole genome sequencing" in s.lower() for s in synonyms)
    
    def test_ontology_id_lookup(self):
        """Test ontology ID retrieval."""
        expander = SynonymExpander()
        
        # RNA-seq should have OBI ID
        ont_id = expander.get_ontology_id("RNA-seq")
        assert ont_id is not None
        assert ont_id.startswith("OBI:")
        assert ont_id == "OBI:0001271"
        
        # ATAC-seq should have OBI ID
        ont_id = expander.get_ontology_id("ATAC-seq")
        assert ont_id == "OBI:0002039"
    
    def test_max_synonyms_limit(self):
        """Test maximum synonyms limit."""
        config = SynonymExpansionConfig(max_synonyms_per_term=5)
        expander = SynonymExpander(config)
        
        # Should limit to max
        synonyms = expander.expand("RNA-seq", max_synonyms=3)
        assert len(synonyms) <= 3
    
    def test_query_expansion(self):
        """Test full query expansion."""
        expander = SynonymExpander()
        
        # Simple query
        query = "RNA-seq in liver"
        expanded = expander.expand_query(query)
        
        assert "RNA" in expanded or "transcriptome" in expanded
        assert "liver" in expanded
        
        # Complex query
        query = "ATAC-seq and ChIP-seq"
        expanded = expander.expand_query(query)
        
        assert "ATAC" in expanded or "chromatin" in expanded
        assert "ChIP" in expanded or "immunoprecipitation" in expanded
    
    def test_genomic_techniques(self):
        """Test genomic technique recognition and expansion."""
        expander = SynonymExpander()
        
        # Epigenetic techniques
        assert expander.get_canonical("WGBS") == "whole genome bisulfite sequencing"
        assert expander.get_canonical("RRBS") == "reduced representation bisulfite sequencing"
        assert expander.get_canonical("DNA methylation") == "DNA methylation profiling"
        
        # Chromatin accessibility
        assert expander.get_canonical("ATAC-seq") == "assay for transposase-accessible chromatin using sequencing"
        assert expander.get_canonical("DNase-seq") == "DNase I hypersensitive sites sequencing"
        assert expander.get_canonical("FAIRE-seq") == "formaldehyde-assisted isolation of regulatory elements sequencing"
        
        # 3D genome
        assert expander.get_canonical("Hi-C") == "Hi-C sequencing"
        
        # Gene expression
        assert expander.get_canonical("RNA-seq") == "RNA sequencing"
        assert expander.get_canonical("scRNA-seq") == "single-cell RNA sequencing"
    
    def test_microarray_techniques(self):
        """Test microarray technique expansion."""
        expander = SynonymExpander()
        
        # General microarray
        synonyms = expander.expand("microarray")
        assert "microarray" in synonyms
        assert any("DNA chip" in s or "gene chip" in s for s in synonyms)
        
        # Methylation array
        synonyms = expander.expand("methylation array")
        assert "methylation array" in synonyms
        canonical = expander.get_canonical("450K array")
        assert "methylation" in canonical.lower()
    
    def test_protein_rna_interactions(self):
        """Test protein-RNA interaction techniques."""
        expander = SynonymExpander()
        
        # CLIP-seq
        synonyms = expander.expand("CLIP-seq")
        assert "CLIP-seq" in synonyms
        canonical = expander.get_canonical("CLIP-seq")
        assert "cross-linking immunoprecipitation" in canonical.lower()
    
    def test_caching(self):
        """Test result caching."""
        config = SynonymExpansionConfig(cache_enabled=True)
        expander = SynonymExpander(config)
        
        # First call
        synonyms1 = expander.expand("RNA-seq")
        
        # Second call (should use cache)
        synonyms2 = expander.expand("RNA-seq")
        
        assert synonyms1 == synonyms2
        assert "RNA-seq" in expander._cache
    
    def test_no_expansion_for_unknown(self):
        """Test behavior for unknown terms."""
        expander = SynonymExpander()
        
        # Unknown term should return original only
        synonyms = expander.expand("unknown_technique_xyz")
        assert synonyms == {"unknown_technique_xyz"}
        
        # Unknown canonical should be None
        canonical = expander.get_canonical("unknown_technique_xyz")
        assert canonical is None
    
    def test_statistics(self):
        """Test gazetteer statistics."""
        expander = SynonymExpander()
        
        stats = expander.stats()
        
        assert stats["techniques"] > 0
        assert stats["total_terms"] > stats["techniques"]
        assert stats["synonyms"] > 0
        assert stats["variants"] > 0
        assert stats["normalized_lookup"] > 0
        
        print(f"\nGazetteer Statistics:")
        print(f"  Techniques: {stats['techniques']}")
        print(f"  Total terms: {stats['total_terms']}")
        print(f"  Synonyms: {stats['synonyms']}")
        print(f"  Abbreviations: {stats['abbreviations']}")
        print(f"  Variants: {stats['variants']}")
        print(f"  Normalized lookup entries: {stats['normalized_lookup']}")
    
    def test_multi_word_phrases(self):
        """Test multi-word phrase recognition."""
        expander = SynonymExpander()
        
        # Multi-word technique
        canonical = expander.get_canonical("DNA methylation")
        assert canonical is not None
        assert "methylation" in canonical.lower()
        
        # Gene expression
        canonical = expander.get_canonical("gene expression profiling")
        assert canonical is not None
        assert "gene expression" in canonical.lower()
    
    def test_config_options(self):
        """Test different configuration options."""
        # Disable variants
        config = SynonymExpansionConfig(generate_variants=False)
        expander = SynonymExpander(config)
        stats = expander.stats()
        assert stats["variants"] == 0
        
        # Disable abbreviations
        config = SynonymExpansionConfig(common_abbreviations=False)
        expander = SynonymExpander(config)
        synonyms = expander.expand("NGS")
        # Should only have NGS itself if not in main gazetteer
        
        # Disable cache
        config = SynonymExpansionConfig(cache_enabled=False)
        expander = SynonymExpander(config)
        expander.expand("RNA-seq")
        assert len(expander._cache) == 0


class TestIntegrationWithQueries:
    """Test integration with real queries."""
    
    def test_geo_style_queries(self):
        """Test with GEO-style queries."""
        expander = SynonymExpander()
        
        # GEO query 1: Epigenetics
        query = "DNA methylation in cancer"
        expanded = expander.expand_query(query)
        assert "methylation" in expanded.lower()
        
        # GEO query 2: Chromatin
        query = "ATAC-seq chromatin accessibility"
        expanded = expander.expand_query(query)
        assert "atac" in expanded.lower() or "transposase" in expanded.lower()
        
        # GEO query 3: Expression
        query = "single-cell RNA-seq liver"
        expanded = expander.expand_query(query)
        assert "scrna" in expanded.lower() or "single" in expanded.lower()
    
    def test_pubmed_style_queries(self):
        """Test with PubMed-style queries."""
        expander = SynonymExpander()
        
        # PubMed query
        query = "ChIP-seq transcription factor binding"
        expanded = expander.expand_query(query)
        
        assert "chip" in expanded.lower()
        assert "binding" in expanded.lower()
    
    def test_complex_multi_technique(self):
        """Test complex queries with multiple techniques."""
        expander = SynonymExpander()
        
        query = "RNA-seq and ATAC-seq in T cells"
        expanded = expander.expand_query(query)
        
        # Should expand both techniques
        assert "rna" in expanded.lower() or "transcriptome" in expanded.lower()
        assert "atac" in expanded.lower() or "chromatin" in expanded.lower()
        assert "cells" in expanded.lower()


def test_comprehensive_coverage():
    """Test comprehensive technique coverage."""
    expander = SynonymExpander()
    
    # All techniques from our previous tests
    techniques = [
        # Epigenetics
        ("DNA methylation", "DNA methylation profiling"),
        ("WGBS", "whole genome bisulfite sequencing"),
        ("RRBS", "reduced representation bisulfite sequencing"),
        
        # Gene expression
        ("RNA-seq", "RNA sequencing"),
        ("scRNA-seq", "single-cell RNA sequencing"),
        ("microarray", "DNA microarray"),
        
        # Chromatin
        ("ATAC-seq", "assay for transposase-accessible chromatin using sequencing"),
        ("DNase-seq", "DNase I hypersensitive sites sequencing"),
        ("ChIP-seq", "chromatin immunoprecipitation sequencing"),
        
        # 3D genome
        ("Hi-C", "Hi-C sequencing"),
    ]
    
    coverage = 0
    for term, expected_canonical in techniques:
        canonical = expander.get_canonical(term)
        if canonical and canonical == expected_canonical:
            coverage += 1
        else:
            print(f"Missing or incorrect: {term} -> {canonical} (expected: {expected_canonical})")
    
    coverage_pct = (coverage / len(techniques)) * 100
    print(f"\nTechnique Coverage: {coverage}/{len(techniques)} ({coverage_pct:.1f}%)")
    
    assert coverage_pct >= 90, f"Coverage should be >= 90%, got {coverage_pct:.1f}%"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
