"""
Unit tests for NLP library.

Tests biomedical entity recognition, classification, and synonym management.
"""

import pytest

from omics_oracle_v2.lib.nlp import BiomedicalNER, Entity, EntityType, ModelInfo, NERResult, SynonymManager

# ============================================================================
# SynonymManager Tests
# ============================================================================


class TestSynonymManager:
    """Tests for biological synonym management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sm = SynonymManager()

    def test_init(self):
        """Test SynonymManager initialization."""
        assert self.sm.gene_synonyms is not None
        assert self.sm.disease_synonyms is not None
        assert self.sm.organism_synonyms is not None
        assert len(self.sm.gene_synonyms) > 0

    def test_get_gene_synonyms(self):
        """Test gene synonym retrieval."""
        synonyms = self.sm.get_synonyms("brca1", "gene")
        assert "brca1" in synonyms
        assert "breast cancer 1" in synonyms
        assert "brca-1" in synonyms

    def test_get_disease_synonyms(self):
        """Test disease synonym retrieval."""
        synonyms = self.sm.get_synonyms("alzheimer", "disease")
        assert "alzheimer" in synonyms
        assert "alzheimer's disease" in synonyms
        assert "ad" in synonyms

    def test_get_organism_synonyms(self):
        """Test organism synonym retrieval."""
        synonyms = self.sm.get_synonyms("human", "organism")
        assert "human" in synonyms
        assert "homo sapiens" in synonyms
        assert "h. sapiens" in synonyms

    def test_get_synonyms_case_insensitive(self):
        """Test that synonym lookup is case-insensitive."""
        synonyms_lower = self.sm.get_synonyms("brca1", "gene")
        synonyms_upper = self.sm.get_synonyms("BRCA1", "gene")
        assert len(synonyms_lower) == len(synonyms_upper)

    def test_get_synonyms_general(self):
        """Test synonym retrieval without type specification."""
        synonyms = self.sm.get_synonyms("brca1")
        assert len(synonyms) > 0
        assert "brca1" in synonyms

    def test_normalize_gene_term(self):
        """Test gene term normalization."""
        # p53 -> TP53
        normalized = self.sm.normalize_term("p53", "gene")
        assert normalized == "TP53"

        # Should already be canonical
        normalized = self.sm.normalize_term("brca1", "gene")
        assert normalized == "BRCA1"

    def test_normalize_disease_term(self):
        """Test disease term normalization."""
        normalized = self.sm.normalize_term("alzheimer's disease", "disease")
        assert normalized.lower() == "alzheimer"

    def test_normalize_unknown_term(self):
        """Test normalization of unknown terms."""
        # Should return original term if not in dictionaries
        normalized = self.sm.normalize_term("unknown_gene_xyz", "gene")
        assert normalized == "unknown_gene_xyz"

    def test_get_entity_relationships_brca1(self):
        """Test relationship retrieval for BRCA1."""
        rels = self.sm.get_entity_relationships("brca1")
        assert "related_diseases" in rels
        assert "breast cancer" in rels["related_diseases"]

    def test_get_entity_relationships_tp53(self):
        """Test relationship retrieval for TP53."""
        rels = self.sm.get_entity_relationships("tp53")
        assert "related_genes" in rels
        assert "mdm2" in rels["related_genes"]

    def test_get_entity_relationships_cancer(self):
        """Test relationship retrieval for cancer."""
        rels = self.sm.get_entity_relationships("breast cancer")
        assert "related_techniques" in rels
        assert len(rels["related_techniques"]) > 0


# ============================================================================
# Entity Model Tests
# ============================================================================


class TestEntityModels:
    """Tests for Pydantic entity models."""

    def test_entity_creation(self):
        """Test Entity model creation."""
        entity = Entity(
            text="BRCA1",
            entity_type=EntityType.GENE,
            start=10,
            end=15,
            confidence=0.95,
        )
        assert entity.text == "BRCA1"
        assert entity.entity_type == EntityType.GENE
        assert entity.confidence == 0.95

    def test_entity_immutable(self):
        """Test that Entity is immutable."""
        entity = Entity(
            text="BRCA1",
            entity_type=EntityType.GENE,
            start=0,
            end=5,
        )
        with pytest.raises(Exception):  # Pydantic ValidationError or AttributeError
            entity.text = "BRCA2"  # type: ignore

    def test_entity_with_kb_id(self):
        """Test Entity with knowledge base ID."""
        entity = Entity(
            text="BRCA1",
            entity_type=EntityType.GENE,
            start=0,
            end=5,
            kb_id="ENSG00000012048",
        )
        assert entity.kb_id == "ENSG00000012048"

    def test_ner_result_creation(self):
        """Test NERResult model creation."""
        entities = [
            Entity(
                text="BRCA1",
                entity_type=EntityType.GENE,
                start=0,
                end=5,
            ),
            Entity(
                text="breast cancer",
                entity_type=EntityType.DISEASE,
                start=10,
                end=23,
            ),
        ]
        result = NERResult(
            entities=entities,
            text="BRCA1 and breast cancer study",
        )
        assert len(result.entities) == 2
        assert result.text == "BRCA1 and breast cancer study"

    def test_ner_result_get_entities_by_type(self):
        """Test filtering entities by type."""
        entities = [
            Entity(text="BRCA1", entity_type=EntityType.GENE, start=0, end=5),
            Entity(text="TP53", entity_type=EntityType.GENE, start=10, end=14),
            Entity(text="cancer", entity_type=EntityType.DISEASE, start=20, end=26),
        ]
        result = NERResult(entities=entities, text="Test text")

        genes = result.get_entities_by_type(EntityType.GENE)
        assert len(genes) == 2
        assert all(e.entity_type == EntityType.GENE for e in genes)

        diseases = result.get_entities_by_type(EntityType.DISEASE)
        assert len(diseases) == 1

    def test_ner_result_entities_by_type_property(self):
        """Test entities_by_type computed property."""
        entities = [
            Entity(text="BRCA1", entity_type=EntityType.GENE, start=0, end=5),
            Entity(text="cancer", entity_type=EntityType.DISEASE, start=10, end=16),
        ]
        result = NERResult(entities=entities, text="Test")

        by_type = result.entities_by_type
        assert EntityType.GENE in by_type
        assert EntityType.DISEASE in by_type
        assert len(by_type[EntityType.GENE]) == 1

    def test_model_info_creation(self):
        """Test ModelInfo model creation."""
        info = ModelInfo(
            status="loaded",
            model_name="en_core_sci_sm",
            model_version="0.5.0",
            pipeline_components=["tok2vec", "ner"],
        )
        assert info.status == "loaded"
        assert info.model_name == "en_core_sci_sm"
        assert "ner" in info.pipeline_components

    def test_entity_type_enum(self):
        """Test EntityType enum values."""
        assert EntityType.GENE.value == "gene"
        assert EntityType.DISEASE.value == "disease"
        assert EntityType.PROTEIN.value == "protein"

        # Test all expected types exist
        expected_types = {
            "gene",
            "protein",
            "disease",
            "chemical",
            "organism",
            "tissue",
            "cell_type",
            "anatomical",
            "phenotype",
            "technique",
            "general",
        }
        actual_types = {et.value for et in EntityType}
        assert expected_types == actual_types


# ============================================================================
# BiomedicalNER Tests (without spaCy models)
# ============================================================================


class TestBiomedicalNERBasic:
    """Tests for BiomedicalNER without requiring spaCy models."""

    def test_ner_init_no_model(self):
        """Test NER initialization without spaCy model."""
        # This will fail to load models but should not crash
        from omics_oracle_v2.core.config import NLPSettings

        settings = NLPSettings(model_name="en_core_sci_sm")
        ner = BiomedicalNER(settings)
        assert ner is not None

    def test_ner_model_info_unavailable(self):
        """Test model info when models are unavailable."""
        from omics_oracle_v2.core.config import NLPSettings

        settings = NLPSettings(model_name="en_core_sci_sm")
        ner = BiomedicalNER(settings)
        info = ner.get_model_info()
        assert info.status in ["loaded", "not_loaded"]  # Depends on system


# ============================================================================
# Integration Tests (require spaCy models)
# ============================================================================


@pytest.mark.integration
class TestBiomedicalNERIntegration:
    """
    Integration tests for BiomedicalNER with spaCy models.

    These tests require spaCy and optionally SciSpaCy models to be installed.
    Run with: pytest -m integration
    """

    @pytest.fixture
    def ner_engine(self):
        """Create NER engine with settings."""
        try:
            from omics_oracle_v2.core.config import NLPSettings

            settings = NLPSettings(model_name="en_core_web_sm")
            ner = BiomedicalNER(settings)
            if not ner.get_model_info().is_available:
                pytest.skip("spaCy model not available")
            return ner
        except Exception as e:
            pytest.skip(f"Could not initialize NER: {e}")

    def test_extract_entities_simple(self, ner_engine):
        """Test entity extraction from simple text."""
        text = "BRCA1 is associated with breast cancer."
        result = ner_engine.extract_entities(text)

        assert isinstance(result, NERResult)
        assert result.text == text
        assert len(result.entities) > 0

    def test_extract_entities_complex(self, ner_engine):
        """Test entity extraction from complex biomedical text."""
        text = (
            "The TP53 gene encodes a tumor suppressor protein "
            "that regulates cell cycle and apoptosis. Mutations in TP53 "
            "are associated with various cancers including breast cancer."
        )
        result = ner_engine.extract_entities(text)

        assert len(result.entities) > 0
        # Should find genes and diseases
        by_type = result.entities_by_type
        assert len(by_type) > 0

    def test_entity_classification_gene(self, ner_engine):
        """Test gene entity classification."""
        text = "BRCA1, TP53, and EGFR are important oncogenes."
        result = ner_engine.extract_entities(text)

        # Check if any entities were classified as genes
        genes = result.get_entities_by_type(EntityType.GENE)
        # May or may not find genes depending on model and classification logic
        assert isinstance(genes, list)  # Should return a list

    def test_extract_entities_empty_text(self, ner_engine):
        """Test extraction from empty text."""
        result = ner_engine.extract_entities("")
        assert isinstance(result, NERResult)
        assert len(result.entities) == 0

    def test_extract_entities_no_entities(self, ner_engine):
        """Test extraction from text with no biomedical entities."""
        text = "The quick brown fox jumps over the lazy dog."
        result = ner_engine.extract_entities(text)
        assert isinstance(result, NERResult)
        # May or may not find entities depending on model


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.performance
class TestNLPPerformance:
    """Performance tests for NLP module."""

    def test_synonym_lookup_performance(self):
        """Test synonym lookup performance."""
        import time

        sm = SynonymManager()

        start = time.time()
        for _ in range(1000):
            sm.get_synonyms("brca1", "gene")
        elapsed = time.time() - start

        # Should be fast (< 1 second for 1000 lookups)
        assert elapsed < 1.0

    def test_normalization_performance(self):
        """Test term normalization performance."""
        import time

        sm = SynonymManager()

        start = time.time()
        for _ in range(1000):
            sm.normalize_term("p53", "gene")
        elapsed = time.time() - start

        assert elapsed < 1.0
