#!/usr/bin/env python3
"""
Enhanced    sample_texts = [
        "BRCA1 mutations are associated with breast cancer in humans.",
        ("RNA-seq analysis revealed differential expression of TP53 in "
         "lung carcinoma samples."),
        "Flow cytometry analysis of T cells from mouse spleen tissue.",
        "Western blot analysis confirmed EGFR protein levels in HeLa cells.",
        "Alzheimer's disease patients showed reduced hippocampal volume.",
    ]ical NLP Demonstration

This script demonstrates the capabilities of the enhanced biomedical NLP
functionality in OmicsOracle, including SciSpaCy integration and
comprehensive biomedical entity recognition.
"""

from pathlib import Path

from omics_oracle.nlp.biomedical_ner import BiomedicalNER, EnhancedBiologicalSynonymMapper

# Add src to path for direct execution


def main():
    """Demonstrate enhanced biomedical NLP capabilities."""
    print("=== OmicsOracle Enhanced Biomedical NLP Demonstration ===")
    print("=" * 60)

    # Initialize components
    print("\n1. Initializing Biomedical NLP Components...")
    ner = BiomedicalNER()
    synonym_mapper = EnhancedBiologicalSynonymMapper()

    print(f"[PASS] Loaded NLP model: {ner.get_model_info()['model_name']}")
    print(f"[PASS] Model status: {ner.get_model_info()['status']}")

    # Sample biomedical texts
    sample_texts = [
        "BRCA1 mutations are associated with breast cancer in humans.",
        "RNA-seq analysis revealed differential expression of TP53 in " "lung carcinoma samples.",
        "Flow cytometry analysis of T cells from mouse spleen tissue.",
        "Western blot analysis confirmed EGFR protein levels in HeLa cells.",
        "Alzheimer's disease patients showed reduced hippocampal volume.",
    ]

    print("\n2. Biomedical Entity Recognition...")
    print("-" * 40)

    for i, text in enumerate(sample_texts, 1):
        print(f"\nSample {i}: {text}")
        entities = ner.extract_biomedical_entities(text)

        for entity_type, entity_list in entities.items():
            if entity_list:
                entity_texts = [e["text"] for e in entity_list]
                print(f"  {entity_type.title()}: {entity_texts}")

    print("\n3. Enhanced Synonym Mapping...")
    print("-" * 40)

    # Demonstrate synonym mapping
    test_terms = [
        ("brca1", "gene"),
        ("breast cancer", "disease"),
        ("human", "organism"),
        ("rna-seq", "technique"),
        ("t cell", "cell_type"),
    ]

    for term, entity_type in test_terms:
        synonyms = synonym_mapper.get_synonyms(term, entity_type)
        normalized = synonym_mapper.normalize_term(term, entity_type)
        print(f"\nTerm: {term} ({entity_type})")
        print(f"  Normalized: {normalized}")
        print(f"  Synonyms: {list(synonyms)[:5]}...")  # Show first 5

    print("\n4. Entity Relationships...")
    print("-" * 40)

    relationship_terms = ["brca1", "breast cancer", "alzheimer"]
    for term in relationship_terms:
        relationships = synonym_mapper.get_entity_relationships(term)
        print(f"\n{term.title()} relationships:")
        for rel_type, rel_list in relationships.items():
            if rel_list:
                print(f"  {rel_type}: {rel_list}")

    print("\n5. Advanced Search Query Processing...")
    print("-" * 40)

    # Demonstrate how this could be used for query expansion
    query = "Find BRCA1 studies in breast cancer patients"
    print(f"\nOriginal query: '{query}'")

    entities = ner.extract_biomedical_entities(query)
    expanded_terms = set()

    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            entity_text = entity["text"].lower()
            synonyms = synonym_mapper.get_synonyms(entity_text, entity_type)
            expanded_terms.update(synonyms)

    print(f"Expanded search terms: {sorted(list(expanded_terms))}")

    print("\n6. Model Performance Information...")
    print("-" * 40)

    model_info = ner.get_model_info()
    print(f"Model: {model_info['model_name']} v{model_info['model_version']}")
    print(f"Pipeline: {model_info['pipeline_components']}")
    print(f"SciSpaCy available: {model_info['has_scispacy']}")

    print("\n[PASS] Enhanced Biomedical NLP demonstration complete!")
    print(
        "\nNext steps: Integrate with GEO search and core pipeline for "
        "comprehensive biological data analysis and retrieval."
    )


if __name__ == "__main__":
    main()
