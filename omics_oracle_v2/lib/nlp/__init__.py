"""
Biomedical Natural Language Processing library.

Provides entity recognition, classification, and extraction
for biomedical literature and text.
"""

from .biomedical_ner import BiomedicalNER
from .models import Entity, EntityType, ModelInfo, NERResult
from .synonym_manager import SynonymManager

__all__ = [
    "BiomedicalNER",
    "Entity",
    "EntityType",
    "ModelInfo",
    "NERResult",
    "SynonymManager",
]
