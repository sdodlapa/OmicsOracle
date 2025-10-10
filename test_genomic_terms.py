#!/usr/bin/env python3
"""
Test genomic technique recognition in BiomedicalNER.

Tests whether our NER system recognizes and properly classifies:
- Epigenetic techniques: DNA methylation, WGBS, RRBS
- Gene expression: RNA-seq, microarray
- Chromatin accessibility: ATAC-seq, DNase-seq, ChIP-seq
- Transcription factor binding: TFB, ChIP-seq

Run: python test_genomic_terms.py
"""

import logging
from omics_oracle_v2.lib.nlp.biomedical_ner import BiomedicalNER
from omics_oracle_v2.lib.nlp.models import EntityType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_genomic_techniques():
    """Test recognition of genomic data-related techniques."""
    
    print("=" * 80)
    print("GENOMIC TECHNIQUE RECOGNITION TEST")
    print("=" * 80)
    
    # Initialize NER
    print("\n✓ Loading BiomedicalNER...")
    try:
        ner = BiomedicalNER()
        print(f"  Model loaded: {ner._model_name}")
    except Exception as e:
        print(f"  ❌ Failed to load NER: {e}")
        return
    
    # Test queries with genomic techniques
    test_cases = [
        {
            "category": "Epigenetics - DNA Methylation",
            "queries": [
                "DNA methylation in breast cancer",
                "WGBS analysis of tumor samples",
                "RRBS methylation profiling",
                "bisulfite sequencing methylation",
                "whole genome bisulfite sequencing WGBS",
                "reduced representation bisulfite sequencing RRBS",
            ]
        },
        {
            "category": "Gene Expression",
            "queries": [
                "RNA-seq gene expression analysis",
                "microarray expression profiling",
                "transcriptome sequencing RNA-seq",
                "differential gene expression RNA-seq",
                "Affymetrix microarray gene expression",
            ]
        },
        {
            "category": "Chromatin Accessibility",
            "queries": [
                "ATAC-seq chromatin accessibility",
                "DNase-seq open chromatin regions",
                "FAIRE-seq nucleosome positioning",
                "chromatin accessibility profiled by ATAC-seq",
                "DNase hypersensitivity sequencing",
            ]
        },
        {
            "category": "Transcription Factor Binding",
            "queries": [
                "ChIP-seq transcription factor binding",
                "TF binding sites ChIP-seq",
                "chromatin immunoprecipitation sequencing",
                "transcription factor occupancy ChIP-seq",
                "histone modification ChIP-seq",
            ]
        },
        {
            "category": "Other NGS Techniques",
            "queries": [
                "single-cell RNA-seq analysis",
                "scRNA-seq cell heterogeneity",
                "Hi-C chromatin interaction",
                "CLIP-seq RNA-protein binding",
                "CAGE-seq transcription start sites",
            ]
        },
        {
            "category": "Multi-technique Queries",
            "queries": [
                "RNA-seq and ATAC-seq integration",
                "WGBS and RNA-seq correlation",
                "ChIP-seq and RNA-seq combined analysis",
                "DNA methylation WGBS gene expression microarray",
            ]
        }
    ]
    
    # Summary statistics
    total_queries = 0
    total_entities = 0
    technique_entities = 0
    technique_terms_found = set()
    missing_techniques = []
    
    for test_case in test_cases:
        print("\n" + "=" * 80)
        print(f"Category: {test_case['category']}")
        print("=" * 80)
        
        for query in test_case['queries']:
            total_queries += 1
            print(f"\nQuery: '{query}'")
            
            # Extract entities
            result = ner.extract_entities(query)
            entities_by_type = result.entities_by_type
            
            if result.entities:
                total_entities += len(result.entities)
                print(f"  Entities found: {len(result.entities)}")
                
                # Show all entities with types
                for entity_type, entities in entities_by_type.items():
                    if entities:
                        entity_texts = [e.text for e in entities]
                        print(f"    {entity_type.value}: {entity_texts}")
                        
                        # Track technique entities
                        if entity_type == EntityType.TECHNIQUE:
                            technique_entities += len(entities)
                            technique_terms_found.update(entity_texts)
                
                # Check if technique entities were found
                techniques_in_query = EntityType.TECHNIQUE in entities_by_type
                if techniques_in_query:
                    print("  ✅ Technique entities recognized")
                else:
                    print("  ⚠️  No technique entities found (may be classified differently)")
                    missing_techniques.append(query)
            else:
                print("  ❌ No entities found")
                missing_techniques.append(query)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal queries tested: {total_queries}")
    print(f"Total entities extracted: {total_entities}")
    print(f"Technique entities found: {technique_entities}")
    print(f"Average entities per query: {total_entities/total_queries:.1f}")
    
    print(f"\n✅ Technique terms recognized ({len(technique_terms_found)}):")
    for term in sorted(technique_terms_found):
        print(f"  - {term}")
    
    if missing_techniques:
        print(f"\n⚠️  Queries with no technique entities ({len(missing_techniques)}):")
        for query in missing_techniques[:10]:  # Show first 10
            print(f"  - {query}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 80)
    
    coverage_rate = (technique_entities / total_queries) * 100
    print(f"\nTechnique recognition rate: {coverage_rate:.1f}%")
    
    if coverage_rate < 50:
        print("\n❌ LOW COVERAGE - Need to enhance technique patterns!")
        print("\nMissing patterns to add:")
        print("  - DNA methylation, methylation profiling")
        print("  - WGBS, RRBS (bisulfite sequencing variants)")
        print("  - ATAC-seq, DNase-seq, FAIRE-seq (accessibility)")
        print("  - scRNA-seq, single-cell RNA-seq")
        print("  - Hi-C, CLIP-seq, CAGE-seq")
        print("  - chromatin accessibility, open chromatin")
        print("  - transcription factor binding, TF binding")
    elif coverage_rate < 80:
        print("\n⚠️  MODERATE COVERAGE - Some improvements needed")
        print("\nConsider adding:")
        print("  - More variant spellings (RNA-seq vs RNA seq vs RNAseq)")
        print("  - Full technique names alongside acronyms")
        print("  - Multi-word technique phrases")
    else:
        print("\n✅ GOOD COVERAGE - Technique recognition working well!")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

def test_query_optimization():
    """Test how genomic terms are used in query optimization."""
    
    print("\n\n" + "=" * 80)
    print("QUERY OPTIMIZATION TEST")
    print("=" * 80)
    
    from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
    from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig
    
    # Initialize pipeline with preprocessing
    config = PublicationSearchConfig(
        enable_query_preprocessing=True,
        pubmed_config=PubMedConfig(email="sdodl001@odu.edu"),
    )
    
    pipeline = PublicationSearchPipeline(config)
    pipeline.initialize()
    
    if not hasattr(pipeline, 'ner') or not pipeline.ner:
        print("\n⚠️  Query preprocessing not available")
        return
    
    # Test genomic queries
    test_queries = [
        "DNA methylation WGBS breast cancer",
        "ATAC-seq chromatin accessibility diabetes",
        "RNA-seq gene expression TP53 mutations",
        "ChIP-seq histone modifications H3K27ac",
    ]
    
    print("\nTesting query optimization for genomic techniques:\n")
    
    for query in test_queries:
        print("-" * 80)
        print(f"Query: '{query}'")
        
        # Preprocess
        preprocessed = pipeline._preprocess_query(query)
        
        # Show entities
        if preprocessed.get("entities"):
            print("\nEntities extracted:")
            for entity_type, entities in preprocessed["entities"].items():
                if entities:
                    entity_texts = [e.text for e in entities]
                    print(f"  {entity_type.value}: {entity_texts}")
        
        # Show optimized queries
        pubmed_query = preprocessed.get("pubmed", query)
        openalex_query = preprocessed.get("openalex", query)
        
        print(f"\nPubMed query:")
        if pubmed_query != query:
            print(f"  {pubmed_query}")
        else:
            print(f"  ⚠️  No optimization (using original)")
        
        print(f"\nOpenAlex query:")
        if openalex_query != query:
            print(f"  {openalex_query}")
        else:
            print(f"  ⚠️  No optimization (using original)")
    
    pipeline.cleanup()
    
    print("\n" + "=" * 80)
    print("OPTIMIZATION TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        # Test 1: Entity recognition
        test_genomic_techniques()
        
        # Test 2: Query optimization
        test_query_optimization()
        
        print("\n" + "=" * 80)
        print("🔬 ALL GENOMIC TESTS COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
