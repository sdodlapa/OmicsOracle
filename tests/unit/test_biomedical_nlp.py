"""
Tests for enhanced biomedical NLP functionality.

Tests the BiomedicalNER and EnhancedBiologicalSynonymMapper classes
with mock data to avoid requiring actual model downloads.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omics_oracle.nlp.biomedical_ner import BiomedicalNER, EnhancedBiologicalSynonymMapper

# Add src to path for testing if needed


class TestBiomedicalNER:
    """Test the enhanced biomedical NER processor."""

    @pytest.fixture
    def mock_biomedical_ner(self):
        """Mock biomedical NER without real NLP models."""
        with patch.object(BiomedicalNER, "_initialize_models"):
            ner = BiomedicalNER()
            # Mock the NLP model to avoid requiring spaCy installation
            ner.nlp_model = Mock()
            return ner

    def test_initialization(self):
        """Test BiomedicalNER initialization."""
        with patch.object(BiomedicalNER, "_initialize_models"):
            ner = BiomedicalNER()
            assert ner.model_name == "auto"
            assert ner.config is not None

    def test_initialization_with_specific_model(self):
        """Test BiomedicalNER initialization with specific model."""
        with patch.object(BiomedicalNER, "_initialize_models"):
            ner = BiomedicalNER(model_name="en_core_sci_sm")
            assert ner.model_name == "en_core_sci_sm"

    def test_extract_biomedical_entities_mock(self, mock_biomedical_ner):
        """Test entity extraction with mocked NLP model."""
        # Mock entity with attributes
        mock_entity = Mock()
        mock_entity.text = "BRCA1"
        mock_entity.label_ = "GENE"
        mock_entity.start_char = 0
        mock_entity.end_char = 5
        mock_entity._.confidence = 0.95

        # Mock document with entities
        mock_doc = Mock()
        mock_doc.ents = [mock_entity]

        # Configure mock model to return mock document
        mock_biomedical_ner.nlp_model.return_value = mock_doc

        text = "BRCA1 mutations cause breast cancer"
        entities = mock_biomedical_ner.extract_biomedical_entities(text)

        assert "genes" in entities
        assert len(entities["genes"]) == 1
        assert entities["genes"][0]["text"] == "BRCA1"
        assert entities["genes"][0]["label"] == "GENE"

    def test_extract_biomedical_entities_with_linking(self, mock_biomedical_ner):
        """Test entity extraction with entity linking."""
        # Mock entity with linking information
        mock_entity = Mock()
        mock_entity.text = "diabetes"
        mock_entity.label_ = "DISEASE"
        mock_entity.start_char = 0
        mock_entity.end_char = 8
        mock_entity._.confidence = 0.9
        mock_entity._.kb_id = "MONDO:0005015"

        mock_doc = Mock()
        mock_doc.ents = [mock_entity]

        mock_biomedical_ner.nlp_model.return_value = mock_doc

        text = "diabetes mellitus"
        entities = mock_biomedical_ner.extract_biomedical_entities(text, include_entity_linking=True)

        assert "diseases" in entities
        assert len(entities["diseases"]) == 1
        assert entities["diseases"][0]["kb_id"] == "MONDO:0005015"

    def test_is_gene_entity(self, mock_biomedical_ner):
        """Test gene entity classification."""
        mock_entity = Mock()
        mock_entity.label_ = "GENE"

        assert mock_biomedical_ner._is_gene_entity(mock_entity, "brca1")
        assert mock_biomedical_ner._is_gene_entity(mock_entity, "tp53")
        assert mock_biomedical_ner._is_gene_entity(mock_entity, "EGFR")
        assert not mock_biomedical_ner._is_gene_entity(mock_entity, "diabetes")

    def test_is_disease_entity(self, mock_biomedical_ner):
        """Test disease entity classification."""
        mock_entity = Mock()
        mock_entity.label_ = "DISEASE"

        assert mock_biomedical_ner._is_disease_entity(mock_entity, "cancer")
        assert mock_biomedical_ner._is_disease_entity(mock_entity, "carcinoma")
        assert mock_biomedical_ner._is_disease_entity(mock_entity, "lymphoma")
        assert mock_biomedical_ner._is_disease_entity(mock_entity, "arthritis")
        assert not mock_biomedical_ner._is_disease_entity(mock_entity, "brca1")

    def test_is_organism_entity(self, mock_biomedical_ner):
        """Test organism entity classification."""
        mock_entity = Mock()
        mock_entity.label_ = "ORGANISM"

        assert mock_biomedical_ner._is_organism_entity(mock_entity, "human")
        assert mock_biomedical_ner._is_organism_entity(mock_entity, "mouse")
        assert mock_biomedical_ner._is_organism_entity(mock_entity, "homo sapiens")
        assert not mock_biomedical_ner._is_organism_entity(mock_entity, "cancer")

    def test_is_experimental_technique(self, mock_biomedical_ner):
        """Test experimental technique classification."""
        mock_entity = Mock()

        assert mock_biomedical_ner._is_experimental_technique(mock_entity, "rna-seq")
        assert mock_biomedical_ner._is_experimental_technique(mock_entity, "chip-seq")
        assert mock_biomedical_ner._is_experimental_technique(mock_entity, "pcr")
        assert mock_biomedical_ner._is_experimental_technique(mock_entity, "western blot")
        assert not mock_biomedical_ner._is_experimental_technique(mock_entity, "cancer")

    def test_get_model_info(self, mock_biomedical_ner):
        """Test model information retrieval."""
        mock_biomedical_ner.nlp_model.meta = {
            "name": "test_model",
            "version": "1.0.0",
            "lang": "en",
        }
        mock_biomedical_ner.nlp_model.pipe_names = ["tagger", "parser", "ner"]

        info = mock_biomedical_ner.get_model_info()

        assert info["status"] == "loaded"
        assert info["model_version"] == "1.0.0"
        assert "tagger" in info["pipeline_components"]

    def test_is_available(self, mock_biomedical_ner):
        """Test availability check."""
        assert mock_biomedical_ner.is_available()

        mock_biomedical_ner.nlp_model = None
        assert not mock_biomedical_ner.is_available()


class TestEnhancedBiologicalSynonymMapper:
    """Test the enhanced biological synonym mapper."""

    @pytest.fixture
    def synonym_mapper(self):
        """Create enhanced synonym mapper instance."""
        return EnhancedBiologicalSynonymMapper()

    def test_initialization(self, synonym_mapper):
        """Test synonym mapper initialization."""
        assert hasattr(synonym_mapper, "gene_synonyms")
        assert hasattr(synonym_mapper, "disease_synonyms")
        assert hasattr(synonym_mapper, "organism_synonyms")
        assert hasattr(synonym_mapper, "tissue_synonyms")
        assert hasattr(synonym_mapper, "cell_type_synonyms")
        assert hasattr(synonym_mapper, "technique_synonyms")

    def test_gene_synonyms(self, synonym_mapper):
        """Test gene synonym retrieval."""
        synonyms = synonym_mapper.get_synonyms("brca1", "gene")

        assert "brca1" in synonyms
        assert "breast cancer 1" in synonyms
        assert "brca-1" in synonyms

    def test_disease_synonyms(self, synonym_mapper):
        """Test disease synonym retrieval."""
        synonyms = synonym_mapper.get_synonyms("breast cancer", "disease")

        assert "breast cancer" in synonyms
        assert "breast carcinoma" in synonyms
        assert "mammary cancer" in synonyms

    def test_organism_synonyms(self, synonym_mapper):
        """Test organism synonym retrieval."""
        synonyms = synonym_mapper.get_synonyms("human", "organism")

        assert "human" in synonyms
        assert "homo sapiens" in synonyms
        assert "h. sapiens" in synonyms

    def test_tissue_synonyms(self, synonym_mapper):
        """Test tissue synonym retrieval."""
        synonyms = synonym_mapper.get_synonyms("brain", "tissue")

        assert "brain" in synonyms
        assert "cerebrum" in synonyms
        assert "neural tissue" in synonyms

    def test_cell_type_synonyms(self, synonym_mapper):
        """Test cell type synonym retrieval."""
        synonyms = synonym_mapper.get_synonyms("t cell", "cell_type")

        assert "t cell" in synonyms
        assert "t lymphocyte" in synonyms
        assert "t-cell" in synonyms

    def test_technique_synonyms(self, synonym_mapper):
        """Test experimental technique synonym retrieval."""
        synonyms = synonym_mapper.get_synonyms("rna-seq", "technique")

        assert "rna-seq" in synonyms
        assert "rna sequencing" in synonyms
        assert "transcriptome sequencing" in synonyms

    def test_general_synonym_search(self, synonym_mapper):
        """Test general synonym search across all categories."""
        synonyms = synonym_mapper.get_synonyms("brca1", "general")

        assert "brca1" in synonyms
        assert "breast cancer 1" in synonyms

    def test_normalize_term(self, synonym_mapper):
        """Test term normalization."""
        # Test gene normalization
        assert synonym_mapper.normalize_term("brca-1", "gene") == "BRCA1"
        assert synonym_mapper.normalize_term("p53", "gene") == "TP53"

        # Test disease normalization
        assert synonym_mapper.normalize_term("breast carcinoma", "disease") == "Breast Cancer"

        # Test organism normalization
        assert synonym_mapper.normalize_term("homo sapiens", "organism") == "Human"

    def test_unknown_term(self, synonym_mapper):
        """Test handling of unknown terms."""
        synonyms = synonym_mapper.get_synonyms("unknown_gene", "gene")
        assert synonyms == {"unknown_gene"}

        normalized = synonym_mapper.normalize_term("unknown_gene", "gene")
        assert normalized == "unknown_gene"

    def test_get_entity_relationships(self, synonym_mapper):
        """Test entity relationship retrieval."""
        relationships = synonym_mapper.get_entity_relationships("brca1")

        assert "related_diseases" in relationships
        assert "breast cancer" in relationships["related_diseases"]
        assert "related_techniques" in relationships
        assert "sequencing" in relationships["related_techniques"]

    def test_cancer_relationships(self, synonym_mapper):
        """Test cancer-related entity relationships."""
        relationships = synonym_mapper.get_entity_relationships("breast cancer")

        assert "related_techniques" in relationships
        assert "rna-seq" in relationships["related_techniques"]
        assert "related_genes" in relationships
        assert "tp53" in relationships["related_genes"]

    def test_comprehensive_synonym_coverage(self, synonym_mapper):
        """Test that comprehensive synonyms are available."""
        # Test expanded gene coverage
        gene_keys = list(synonym_mapper.gene_synonyms.keys())
        assert "brca1" in gene_keys
        assert "tp53" in gene_keys
        assert "egfr" in gene_keys
        assert "vegf" in gene_keys
        assert "tnf" in gene_keys

        # Test expanded disease coverage
        disease_keys = list(synonym_mapper.disease_synonyms.keys())
        assert "breast cancer" in disease_keys
        assert "alzheimer" in disease_keys
        assert "diabetes" in disease_keys
        assert "hypertension" in disease_keys

        # Test expanded organism coverage
        organism_keys = list(synonym_mapper.organism_synonyms.keys())
        assert "human" in organism_keys
        assert "mouse" in organism_keys
        assert "zebrafish" in organism_keys
        assert "fruit fly" in organism_keys

    def test_synonym_consistency(self, synonym_mapper):
        """Test that synonyms are consistent and bidirectional."""
        # Test that canonical terms map to themselves
        brca1_synonyms = synonym_mapper.get_synonyms("brca1", "gene")
        assert "brca1" in brca1_synonyms

        # Test that synonyms include the canonical term
        for synonym in ["breast cancer 1", "brca-1"]:
            synonym_set = synonym_mapper.get_synonyms(synonym, "gene")
            assert "brca1" in synonym_set or "breast cancer 1" in synonym_set


class TestBiomedicalNERIntegration:
    """Integration tests for biomedical NLP components."""

    def test_ner_with_synonym_mapper_integration(self):
        """Test integration between NER and synonym mapper."""
        # This test would require actual models, so we'll mock it
        with patch.object(BiomedicalNER, "_initialize_models"):
            ner = BiomedicalNER()
            ner.nlp_model = Mock()

            # Mock extraction of a gene entity
            mock_entity = Mock()
            mock_entity.text = "BRCA1"
            mock_entity.label_ = "GENE"
            mock_entity.start_char = 0
            mock_entity.end_char = 5

            mock_doc = Mock()
            mock_doc.ents = [mock_entity]
            ner.nlp_model.return_value = mock_doc

            # Extract entities
            entities = ner.extract_biomedical_entities("BRCA1 mutations")

            # Use synonym mapper to expand found entities
            mapper = EnhancedBiologicalSynonymMapper()
            if entities["genes"]:
                gene_name = entities["genes"][0]["text"].lower()
                synonyms = mapper.get_synonyms(gene_name, "gene")
                assert len(synonyms) > 1
                assert "breast cancer 1" in synonyms

    def test_comprehensive_text_processing(self):
        """Test processing of complex biomedical text."""
        with patch.object(BiomedicalNER, "_initialize_models"):
            ner = BiomedicalNER()
            ner.nlp_model = Mock()

            # Mock multiple entities in text
            mock_entities = []

            # Gene entity
            gene_entity = Mock()
            gene_entity.text = "BRCA1"
            gene_entity.label_ = "GENE"
            gene_entity.start_char = 0
            gene_entity.end_char = 5
            mock_entities.append(gene_entity)

            # Disease entity
            disease_entity = Mock()
            disease_entity.text = "breast cancer"
            disease_entity.label_ = "DISEASE"
            disease_entity.start_char = 20
            disease_entity.end_char = 33
            mock_entities.append(disease_entity)

            # Organism entity
            organism_entity = Mock()
            organism_entity.text = "human"
            organism_entity.label_ = "ORGANISM"
            organism_entity.start_char = 37
            organism_entity.end_char = 42
            mock_entities.append(organism_entity)

            mock_doc = Mock()
            mock_doc.ents = mock_entities
            ner.nlp_model.return_value = mock_doc

            text = "BRCA1 mutations cause breast cancer in human patients"
            entities = ner.extract_biomedical_entities(text)

            assert len(entities["genes"]) == 1
            assert len(entities["diseases"]) == 1
            assert len(entities["organisms"]) == 1

            # Verify entity categorization
            assert entities["genes"][0]["text"] == "BRCA1"
            assert entities["diseases"][0]["text"] == "breast cancer"
            assert entities["organisms"][0]["text"] == "human"


if __name__ == "__main__":
    # Run basic functionality tests
    mapper = EnhancedBiologicalSynonymMapper()
    print("[PASS] Enhanced synonym mapper created")

    synonyms = mapper.get_synonyms("brca1", "gene")
    print(f"[PASS] BRCA1 synonyms: {synonyms}")

    normalized = mapper.normalize_term("brca-1", "gene")
    print(f"[PASS] Normalized brca-1 -> {normalized}")

    relationships = mapper.get_entity_relationships("brca1")
    print(f"[PASS] BRCA1 relationships: {relationships}")

    print("[PASS] All basic tests passed!")
