"""
Biomedical NLP library.

Provides named entity recognition (NER), entity resolution, and text processing
specifically designed for biomedical and scientific literature.

Key Components:
    - BiomedicalNER: Main NER engine for extracting genes, proteins, diseases, etc.
    - SynonymManager: Entity synonym and alias resolution
    - Entity models: Type-safe data models for entities and results

Example:
    >>> from omics_oracle_v2.lib.nlp import BiomedicalNER
    >>> ner = BiomedicalNER()
    >>> result = ner.extract_entities("TP53 gene mutations in lung cancer")
    >>> for entity in result.entities:
    ...     print(f"{entity.text}: {entity.entity_type}")
    TP53: gene
    lung cancer: disease

Status: Phase 1 Task 3 (In Progress)
"""

# Exports will be added as modules are implemented
# from .biomedical_ner import BiomedicalNER
# from .models import Entity, EntityType, NERResult
# from .synonym_manager import SynonymManager

__all__ = []
