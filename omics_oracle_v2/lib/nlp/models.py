"""
Data models for biomedical NLP.

Provides Pydantic models for biomedical entities, NER results, and related
data structures with full type safety and validation.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Supported biomedical entity types."""

    GENE = "gene"
    PROTEIN = "protein"
    DISEASE = "disease"
    CHEMICAL = "chemical"
    ORGANISM = "organism"
    TISSUE = "tissue"
    CELL_TYPE = "cell_type"
    ANATOMICAL = "anatomical"
    PHENOTYPE = "phenotype"
    TECHNIQUE = "technique"
    GENERAL = "general"


class Entity(BaseModel):
    """
    Biomedical named entity.

    Represents a single entity extracted from text with position,
    type, and optional metadata.
    """

    text: str = Field(..., description="Entity text as it appears in document")
    entity_type: EntityType = Field(..., description="Entity category")
    start: int = Field(..., ge=0, description="Start character position")
    end: int = Field(..., gt=0, description="End character position")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    label: Optional[str] = Field(None, description="Original spaCy label")
    kb_id: Optional[str] = Field(None, description="Knowledge base ID (e.g., NCBI Gene ID)")

    class Config:
        frozen = True  # Immutable


class NERResult(BaseModel):
    """
    Result of Named Entity Recognition.

    Contains all extracted entities with their types and positions.

    Example:
        >>> result = NERResult(entities=[], text="Sample text")
        >>> print(len(result.entities))
        0
    """

    model_config = {"protected_namespaces": ()}  # Allow model_* field names

    entities: List[Entity]
    text: str
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")

    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """
        Filter entities by type.

        Args:
            entity_type: Entity type to filter by

        Returns:
            List of entities matching the specified type
        """
        return [e for e in self.entities if e.entity_type == entity_type]

    @property
    def entities_by_type(self) -> Dict[EntityType, List[Entity]]:
        """
        Group entities by type.

        Returns:
            Dictionary mapping entity types to entity lists
        """
        result: Dict[EntityType, List[Entity]] = {}
        for entity in self.entities:
            if entity.entity_type not in result:
                result[entity.entity_type] = []
            result[entity.entity_type].append(entity)
        return result


class ModelInfo(BaseModel):
    """Information about the loaded NLP model."""

    model_config = {"protected_namespaces": ()}  # Allow model_* field names

    status: str = Field(..., description="Model status (loaded/not_loaded)")
    model_name: Optional[str] = Field(None, description="Name of loaded model")
    model_version: Optional[str] = Field(None, description="Model version")
    language: str = Field(default="en", description="Model language")
    has_scispacy: bool = Field(default=False, description="SciSpaCy availability")
    has_spacy: bool = Field(default=False, description="spaCy availability")
    pipeline_components: List[str] = Field(default_factory=list, description="NLP pipeline components")
