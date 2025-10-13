"""
Tests for NLP functionality.

Tests the prompt interpreter and biological synonym mapper.
"""

from unittest.mock import Mock, patch

import pytest

try:
    import spacy

    # Try to load a basic model to see if it's installed
    try:
        spacy.load("en_core_web_sm")
        SPACY_MODELS_AVAILABLE = True
    except OSError:
        SPACY_MODELS_AVAILABLE = False
except ImportError:
    SPACY_MODELS_AVAILABLE = False

from omics_oracle.nlp.prompt_interpreter import BiologicalSynonymMapper, PromptInterpreter


class TestPromptInterpreter:
    """Test the prompt interpreter."""

    @pytest.fixture
    def mock_interpreter(self):
        """Mock interpreter without real NLP models."""
        with patch.object(PromptInterpreter, "_initialize_models"):
            interpreter = PromptInterpreter()
            # Mock the NLP model to avoid requiring spaCy installation
            interpreter.nlp_model = Mock()
            return interpreter

    def test_extract_geo_identifiers(self, mock_interpreter):
        """Test GEO ID extraction."""
        text = "Find data for GSE12345 and GSE67890"
        geo_ids = mock_interpreter.extract_geo_identifiers(text)

        assert len(geo_ids) == 2
        assert "GSE12345" in geo_ids
        assert "GSE67890" in geo_ids

    def test_extract_geo_identifiers_case_insensitive(self, mock_interpreter):
        """Test GEO ID extraction is case insensitive."""
        text = "Look for gse123 and Gse456"
        geo_ids = mock_interpreter.extract_geo_identifiers(text)

        assert len(geo_ids) == 2
        assert "GSE123" in geo_ids
        assert "GSE456" in geo_ids

    def test_classify_intent_search(self, mock_interpreter):
        """Test intent classification for search queries."""
        test_cases = [
            "find breast cancer data",
            "search for microarray datasets",
            "get gene expression data",
            "retrieve samples for alzheimer",
        ]

        for text in test_cases:
            result = mock_interpreter.classify_intent(text)
            assert result["intent"] == "search"
            assert result["confidence"] > 0

    def test_classify_intent_summarize(self, mock_interpreter):
        """Test intent classification for summarization."""
        test_cases = [
            "summarize GSE12345",
            "what is this dataset about",
            "describe the experiment",
            "tell me about this study",
        ]

        for text in test_cases:
            result = mock_interpreter.classify_intent(text)
            assert result["intent"] == "summarize"
            assert result["confidence"] > 0

    def test_classify_intent_compare(self, mock_interpreter):
        """Test intent classification for comparison."""
        test_cases = [
            "compare GSE123 vs GSE456",
            "difference between these datasets",
            "similarity analysis",
            "how are these related",
        ]

        for text in test_cases:
            result = mock_interpreter.classify_intent(text)
            assert result["intent"] == "compare"
            assert result["confidence"] > 0

    def test_classify_intent_unknown(self, mock_interpreter):
        """Test unknown intent classification."""
        text = "hello world"
        result = mock_interpreter.classify_intent(text)

        assert result["intent"] == "unknown"
        assert result["confidence"] == 0.0

    def test_is_available_with_mock(self, mock_interpreter):
        """Test availability check with mock model."""
        assert mock_interpreter.is_available() is True

    def test_is_available_without_model(self):
        """Test availability check without model."""
        with patch.object(PromptInterpreter, "_initialize_models"):
            interpreter = PromptInterpreter()
            interpreter.nlp_model = None
            assert interpreter.is_available() is False

    @pytest.mark.skipif(
        not SPACY_MODELS_AVAILABLE,
        reason="Requires spaCy models to be installed",
    )
    def test_extract_entities_real(self):
        """Test entity extraction with real NLP model."""
        # This test requires actual spaCy models
        interpreter = PromptInterpreter()
        if not interpreter.is_available():
            pytest.skip("NLP models not available")

        text = "breast cancer gene expression in human samples"
        entities = interpreter.extract_entities(text)

        assert isinstance(entities, dict)
        assert "genes" in entities
        assert "diseases" in entities
        assert "organisms" in entities


class TestBiologicalSynonymMapper:
    """Test the biological synonym mapper."""

    @pytest.fixture
    def mapper(self):
        """Synonym mapper instance."""
        return BiologicalSynonymMapper()

    def test_get_gene_synonyms(self, mapper):
        """Test gene synonym retrieval."""
        synonyms = mapper.get_synonyms("brca1", "gene")

        assert "brca1" in synonyms
        assert "breast cancer 1" in synonyms
        assert "brca-1" in synonyms

    def test_get_disease_synonyms(self, mapper):
        """Test disease synonym retrieval."""
        synonyms = mapper.get_synonyms("breast cancer", "disease")

        assert "breast cancer" in synonyms
        assert "breast carcinoma" in synonyms
        assert "mammary cancer" in synonyms

    def test_get_organism_synonyms(self, mapper):
        """Test organism synonym retrieval."""
        synonyms = mapper.get_synonyms("human", "organism")

        assert "human" in synonyms
        assert "homo sapiens" in synonyms
        assert "h. sapiens" in synonyms

    def test_get_synonyms_unknown_term(self, mapper):
        """Test synonym retrieval for unknown terms."""
        synonyms = mapper.get_synonyms("unknown_gene", "gene")

        # Should return just the original term
        assert synonyms == {"unknown_gene"}

    def test_normalize_gene_term(self, mapper):
        """Test gene term normalization."""
        # Test canonical form
        assert mapper.normalize_term("brca1", "gene") == "BRCA1"

        # Test synonym
        assert mapper.normalize_term("breast cancer 1", "gene") == "BRCA1"

        # Test unknown gene
        assert mapper.normalize_term("unknown_gene", "gene") == "unknown_gene"

    def test_normalize_disease_term(self, mapper):
        """Test disease term normalization."""
        # Test canonical form
        expected = "Breast Cancer"
        assert mapper.normalize_term("breast cancer", "disease") == expected

        # Test synonym
        assert mapper.normalize_term("breast carcinoma", "disease") == expected

    def test_normalize_organism_term(self, mapper):
        """Test organism term normalization."""
        # Test canonical form
        assert mapper.normalize_term("human", "organism") == "Human"

        # Test synonym
        assert mapper.normalize_term("homo sapiens", "organism") == "Human"

    def test_normalize_unknown_term(self, mapper):
        """Test normalization of unknown terms."""
        result = mapper.normalize_term("unknown_term", "gene")
        assert result == "unknown_term"


class TestNLPIntegration:
    """Integration tests for NLP components."""

    def test_end_to_end_query_parsing(self):
        """Test complete query parsing pipeline."""
        # Mock the interpreter to avoid requiring NLP models
        with patch.object(PromptInterpreter, "_initialize_models"):
            interpreter = PromptInterpreter()
            interpreter.nlp_model = Mock()

        # Mock entity extraction
        mock_entities = {
            "genes": [{"text": "BRCA1", "label": "GENE"}],
            "diseases": [{"text": "breast cancer", "label": "DISEASE"}],
            "organisms": [{"text": "human", "label": "ORGANISM"}],
            "tissues": [],
            "chemicals": [],
            "general": [],
        }
        interpreter.extract_entities = Mock(return_value=mock_entities)

        query = "Find BRCA1 data for breast cancer in human samples"
        result = interpreter.parse_search_query(query)

        assert result["intent"]["intent"] == "search"
        assert result["entities"] == mock_entities
        assert "BRCA1" in result["search_terms"]
        assert "breast cancer" in result["search_terms"]
        assert result["original_text"] == query

    def test_synonym_expansion_workflow(self):
        """Test workflow with synonym expansion."""
        mapper = BiologicalSynonymMapper()

        # Test workflow: normalize input -> get synonyms -> use for search
        user_input = "breast cancer 1"

        # Step 1: Normalize
        normalized = mapper.normalize_term(user_input, "gene")
        assert normalized == "BRCA1"

        # Step 2: Get synonyms for search expansion
        synonyms = mapper.get_synonyms(normalized.lower(), "gene")
        assert len(synonyms) > 1
        assert "brca1" in synonyms
        assert "breast cancer 1" in synonyms
