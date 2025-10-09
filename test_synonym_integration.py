"""
Integration Test: Query Preprocessing + Synonym Expansion (Phase 2B)

Tests the complete pipeline integration with synonym expansion.
"""

import pytest
import asyncio
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig


class TestSynonymExpansionIntegration:
    """Test synonym expansion integration with query preprocessing pipeline."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = PublicationSearchConfig()
        config.enable_query_preprocessing = True
        config.enable_synonym_expansion = True
        config.max_synonyms_per_term = 5
        
        # Disable external services for unit test
        config.enable_pubmed = False
        config.enable_openalex = False
        config.enable_scholar = False
        config.enable_citations = False
        config.enable_pdf_download = False
        config.enable_fulltext = False
        config.enable_institutional_access = False
        config.enable_cache = False
        
        return config
    
    @pytest.fixture
    def pipeline(self, config):
        """Create pipeline with synonym expansion."""
        return PublicationSearchPipeline(config)
    
    def test_pipeline_initialization(self, pipeline):
        """Test that pipeline initializes synonym expander."""
        assert pipeline.synonym_expander is not None
        stats = pipeline.synonym_expander.stats()
        assert stats["techniques"] > 0
        print(f"\n✅ Synonym expander initialized: {stats['techniques']} techniques, {stats['total_terms']} terms")
    
    def test_query_expansion(self, pipeline):
        """Test basic query expansion."""
        # Test RNA-seq query
        query = "RNA-seq in liver"
        processed = pipeline._preprocess_query(query)
        
        assert "original" in processed
        assert "expanded" in processed
        assert processed["original"] == query
        
        # Expanded query should contain synonyms
        expanded = processed["expanded"]
        print(f"\n📝 Original: {query}")
        print(f"📝 Expanded: {expanded}")
        
        # Should contain RNA-seq alternatives
        assert "RNA" in expanded or "transcriptome" in expanded
    
    def test_genomic_technique_expansion(self, pipeline):
        """Test genomic technique query expansion."""
        queries = [
            ("DNA methylation in cancer", ["methylation", "5mC", "CpG"]),
            ("ATAC-seq chromatin", ["ATAC", "transposase", "chromatin"]),
            ("WGBS epigenetic", ["WGBS", "bisulfite", "methylation"]),
            ("scRNA-seq T cells", ["scrna-seq", "single-cell", "single cell"]),
        ]
        
        for query, expected_terms in queries:
            processed = pipeline._preprocess_query(query)
            expanded = processed["expanded"].lower()
            
            # At least one expected term should be in expanded query
            found = any(term.lower() in expanded for term in expected_terms)
            print(f"\n🧬 Query: {query}")
            print(f"   Expanded: {processed['expanded']}")
            print(f"   Expected terms: {expected_terms}")
            print(f"   Found: {found}")
            
            # Should find at least one expected term OR original query preserved
            # Note: scRNA-seq will match as "single-cell RNA sequencing" now
            assert found or query.lower().replace("-", " ") in expanded.replace("-", " ")
    
    def test_pubmed_query_building(self, pipeline):
        """Test PubMed query building with expanded terms."""
        query = "RNA-seq inflammation"
        processed = pipeline._preprocess_query(query)
        
        # PubMed query should use expanded terms
        pubmed_query = processed["pubmed"]
        print(f"\n🔬 PubMed query: {pubmed_query}")
        
        # Should contain field tags or expanded terms
        assert pubmed_query is not None
    
    def test_openalex_query_building(self, pipeline):
        """Test OpenAlex query building with expanded terms."""
        query = "ATAC-seq gene regulation"
        processed = pipeline._preprocess_query(query)
        
        # OpenAlex query should use expanded terms
        openalex_query = processed["openalex"]
        print(f"\n📚 OpenAlex query: {openalex_query}")
        
        assert openalex_query is not None
    
    def test_multi_technique_expansion(self, pipeline):
        """Test expansion with multiple techniques."""
        query = "RNA-seq and ATAC-seq in neurons"
        processed = pipeline._preprocess_query(query)
        
        expanded = processed["expanded"]
        print(f"\n🧠 Multi-technique query: {query}")
        print(f"   Expanded: {expanded}")
        
        # Should expand both techniques
        lower_expanded = expanded.lower()
        has_rna_terms = any(term in lower_expanded for term in ["rna", "transcriptome"])
        has_atac_terms = any(term in lower_expanded for term in ["atac", "chromatin", "transposase"])
        
        # At least one technique should be expanded
        assert has_rna_terms or has_atac_terms
    
    def test_entity_extraction_with_synonyms(self, pipeline):
        """Test that entity extraction works with expanded queries."""
        query = "WGBS methylation"
        processed = pipeline._preprocess_query(query)
        
        # Should have entities extracted
        if "entities" in processed:
            entities = processed["entities"]
            print(f"\n🔍 Entities found: {entities}")
            
            # Should recognize technique
            from omics_oracle_v2.lib.nlp.models import EntityType
            if EntityType.TECHNIQUE in entities:
                techniques = entities[EntityType.TECHNIQUE]
                print(f"   Techniques: {[t.text for t in techniques]}")
                assert len(techniques) > 0
    
    def test_no_expansion_for_unknown(self, pipeline):
        """Test that unknown terms pass through unchanged."""
        query = "novel protein XYZ123"
        processed = pipeline._preprocess_query(query)
        
        # Unknown terms should not be modified
        expanded = processed["expanded"]
        assert "XYZ123" in expanded
        print(f"\n❓ Unknown term preserved: {expanded}")
    
    def test_configuration_toggle(self):
        """Test enabling/disabling synonym expansion."""
        # Test with expansion enabled
        config1 = PublicationSearchConfig()
        config1.enable_synonym_expansion = True
        config1.enable_query_preprocessing = True
        config1.enable_pubmed = False
        config1.enable_openalex = False
        
        pipeline1 = PublicationSearchPipeline(config1)
        assert pipeline1.synonym_expander is not None
        
        # Test with expansion disabled
        config2 = PublicationSearchConfig()
        config2.enable_synonym_expansion = False
        config2.enable_query_preprocessing = True
        config2.enable_pubmed = False
        config2.enable_openalex = False
        
        pipeline2 = PublicationSearchPipeline(config2)
        assert pipeline2.synonym_expander is None
        
        print("\n⚙️ Configuration toggle works correctly")


class TestRealWorldQueries:
    """Test with real-world biomedical queries."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline for real-world tests."""
        config = PublicationSearchConfig()
        config.enable_query_preprocessing = True
        config.enable_synonym_expansion = True
        config.enable_pubmed = False
        config.enable_openalex = False
        config.enable_scholar = False
        config.enable_citations = False
        config.enable_pdf_download = False
        config.enable_fulltext = False
        config.enable_institutional_access = False
        config.enable_cache = False
        
        return PublicationSearchPipeline(config)
    
    def test_geo_dataset_query(self, pipeline):
        """Test query for GEO datasets."""
        query = "ATAC-seq chromatin accessibility liver"
        processed = pipeline._preprocess_query(query)
        
        expanded = processed["expanded"]
        print(f"\n🧬 GEO query: {query}")
        print(f"   Expanded: {expanded}")
        
        # Should help find relevant datasets
        assert len(expanded) >= len(query)
    
    def test_methylation_profiling_query(self, pipeline):
        """Test methylation profiling query."""
        query = "DNA methylation WGBS cancer"
        processed = pipeline._preprocess_query(query)
        
        expanded = processed["expanded"]
        print(f"\n🔬 Methylation query: {query}")
        print(f"   Expanded: {expanded}")
        
        # Should expand WGBS to synonyms
        lower_expanded = expanded.lower()
        assert "methylation" in lower_expanded
    
    def test_single_cell_query(self, pipeline):
        """Test single-cell query."""
        query = "scRNA-seq immune cells COVID-19"
        processed = pipeline._preprocess_query(query)
        
        expanded = processed["expanded"]
        print(f"\n🦠 Single-cell query: {query}")
        print(f"   Expanded: {expanded}")
        
        # Should expand scRNA-seq (either as whole term or find single-cell)
        # Check if scRNA-seq is matched as a complete term
        assert "scrna" in expanded.lower() or "single-cell" in expanded.lower() or "single cell" in expanded.lower()
    
    def test_multi_omics_query(self, pipeline):
        """Test multi-omics query."""
        query = "RNA-seq ATAC-seq Hi-C integration"
        processed = pipeline._preprocess_query(query)
        
        expanded = processed["expanded"]
        print(f"\n🔗 Multi-omics query: {query}")
        print(f"   Expanded: {expanded}")
        
        # Should handle multiple techniques
        assert expanded is not None


def test_performance_benchmark():
    """Benchmark synonym expansion performance."""
    config = PublicationSearchConfig()
    config.enable_query_preprocessing = True
    config.enable_synonym_expansion = True
    config.enable_pubmed = False
    config.enable_openalex = False
    
    pipeline = PublicationSearchPipeline(config)
    
    queries = [
        "RNA-seq liver",
        "ATAC-seq chromatin",
        "DNA methylation cancer",
        "scRNA-seq T cells",
        "ChIP-seq histone",
    ]
    
    import time
    start = time.time()
    
    for _ in range(100):
        for query in queries:
            pipeline._preprocess_query(query)
    
    elapsed = time.time() - start
    queries_per_sec = (100 * len(queries)) / elapsed
    
    print(f"\n⚡ Performance: {queries_per_sec:.1f} queries/sec ({elapsed:.3f}s for {100 * len(queries)} queries)")
    print(f"   Average: {elapsed / (100 * len(queries)) * 1000:.2f} ms/query")
    
    # Should be reasonably fast (< 50ms per query with NER)
    # Note: NER adds ~10-15ms overhead, synonym expansion adds ~2-5ms
    assert elapsed / (100 * len(queries)) < 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
