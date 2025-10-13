"""
Query Optimizer for OmicsOracle Unified Pipeline

CORE COMPONENT: Advanced query optimization for better recall.

Features:
- Named Entity Recognition (NER) using production SciSpaCy models
- Medical/biological synonym expansion using SapBERT embeddings + ontologies
- Query term expansion (related concepts)
- Gene/protein name normalization

Uses Existing Production Tools:
- BiomedicalNER (omics_oracle_v2/lib/nlp/biomedical_ner.py) - SciSpaCy NER
- SynonymExpander (omics_oracle_v2/lib/nlp/synonym_expansion.py) - SapBERT + ontologies

Goal: Maximize recall - find ALL relevant results.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List

logger = logging.getLogger(__name__)

# Import existing production tools
try:
    from omics_oracle_v2.lib.query_processing.nlp.biomedical_ner import BiomedicalNER

    HAS_BIOMEDICAL_NER = True
except ImportError:
    logger.warning("BiomedicalNER not available - using fallback pattern matching")
    HAS_BIOMEDICAL_NER = False

try:
    from omics_oracle_v2.lib.query_processing.nlp.synonym_expansion import (
        SynonymExpander,
        SynonymExpansionConfig,
    )

    HAS_SYNONYM_EXPANDER = True
except ImportError:
    logger.warning("SynonymExpander not available - using basic synonyms")
    HAS_SYNONYM_EXPANDER = False


@dataclass
class OptimizedQuery:
    """
    Query optimization result.

    Contains the original query plus enrichments for better search recall.
    """

    primary_query: str
    entities: Dict[str, List[str]] = field(default_factory=dict)
    synonyms: Dict[str, List[str]] = field(default_factory=dict)
    expanded_terms: List[str] = field(default_factory=list)
    normalized_terms: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "primary_query": self.primary_query,
            "entities": self.entities,
            "synonyms": self.synonyms,
            "expanded_terms": self.expanded_terms,
            "normalized_terms": self.normalized_terms,
        }

    def get_all_query_variations(self, max_per_type: int = 3) -> List[str]:
        """
        Get all query variations for comprehensive search.

        Args:
            max_per_type: Maximum variations per synonym type

        Returns:
            List of unique query strings to search
        """
        queries = [self.primary_query]

        # Add synonym variations
        for original_term, synonym_list in self.synonyms.items():
            for synonym in synonym_list[:max_per_type]:
                # Replace original term with synonym in primary query
                variant = self.primary_query.replace(original_term, synonym)
                if variant not in queries:
                    queries.append(variant)

        # Add expanded terms as standalone queries (top N)
        for term in self.expanded_terms[:max_per_type]:
            if term not in queries:
                queries.append(term)

        return queries


class QueryOptimizer:
    """
    Advanced query optimizer for biomedical search.

    CORE COMPONENT - Enhances queries to maximize recall.

    Uses Production Tools:
    - SciSpaCy NER via BiomedicalNER (diseases, genes, proteins, chemicals)
    - SapBERT embeddings for biomedical synonym mining
    - Ontology gazetteers (OBI, EDAM, EFO, MeSH) for technique synonyms
    - Gene/protein name normalization
    - Query expansion with related terms

    Integration Status:
    - ✅ SciSpaCy NER (en_core_sci_md) - replaces regex patterns
    - ✅ SapBERT embeddings - enabled for synonym mining
    - ✅ Ontology gazetteers - fully integrated
    - ⏳ UMLS linker - planned for next sprint
    """

    # Fallback patterns if BiomedicalNER not available
    FALLBACK_DISEASE_PATTERNS = {
        r"\b(cancer|carcinoma|tumor|tumour|neoplasm|malignancy)\b": "cancer",
        r"\b(alzheimer\'?s?|dementia)\b": "alzheimer",
        r"\b(diabetes|diabetic)\b": "diabetes",
        r"\b(parkinson\'?s?)\b": "parkinson",
        r"\b(covid|sars-cov-2|coronavirus)\b": "covid",
    }

    # Fallback gene patterns
    FALLBACK_GENE_PATTERNS = {
        r"\b([A-Z][A-Z0-9]{2,})\b": "gene_symbol",
    }

    # Basic synonym dictionary (fallback - SapBERT is preferred)
    BASIC_SYNONYMS = {
        "alzheimer": ["alzheimer's disease", "alzheimer disease", "AD"],
        "breast cancer": ["mammary carcinoma", "breast neoplasm"],
        "diabetes": ["diabetes mellitus", "diabetic", "DM"],
        "APOE": ["apolipoprotein E", "apoE"],
        "TP53": ["tumor protein p53", "p53"],
    }

    def __init__(
        self,
        enable_ner: bool = True,
        enable_synonyms: bool = True,
        enable_expansion: bool = True,
        enable_normalization: bool = True,
        enable_sapbert: bool = True,  # ✨ NEW: Enable SapBERT embeddings
    ):
        """
        Initialize query optimizer with production tools.

        Args:
            enable_ner: Enable Named Entity Recognition (SciSpaCy)
            enable_synonyms: Enable synonym expansion (SapBERT + ontologies)
            enable_expansion: Enable query expansion
            enable_normalization: Enable term normalization
            enable_sapbert: Enable SapBERT embeddings for synonym mining
        """
        self.enable_ner = enable_ner
        self.enable_synonyms = enable_synonyms
        self.enable_expansion = enable_expansion
        self.enable_normalization = enable_normalization
        self.enable_sapbert = enable_sapbert

        # Initialize BiomedicalNER (production SciSpaCy)
        self.ner_engine = None
        if enable_ner and HAS_BIOMEDICAL_NER:
            try:
                self.ner_engine = BiomedicalNER()
                logger.info("QueryOptimizer: Using production BiomedicalNER (SciSpaCy)")
            except Exception as e:
                logger.warning(f"Failed to load BiomedicalNER: {e}. Using fallback.")
                self.ner_engine = None

        # Initialize SynonymExpander (SapBERT + ontologies)
        self.synonym_expander = None
        if enable_synonyms and HAS_SYNONYM_EXPANDER:
            try:
                # ✨ Enable SapBERT embeddings!
                config = SynonymExpansionConfig(
                    use_ontologies=True,  # Keep ontology gazetteers
                    use_embeddings=enable_sapbert,  # ✨ ENABLE SapBERT!
                    embedding_model="cambridgeltl/SapBERT-from-PubMedBERT-fulltext",
                    similarity_threshold=0.80,
                    detect_abbreviations=True,
                    generate_variants=True,
                    max_synonyms_per_term=10,
                )
                self.synonym_expander = SynonymExpander(config)
                logger.info(
                    f"QueryOptimizer: Using SynonymExpander "
                    f"(SapBERT={'enabled' if enable_sapbert else 'disabled'}, ontologies=enabled)"
                )
            except Exception as e:
                logger.warning(f"Failed to load SynonymExpander: {e}. Using fallback.")
                self.synonym_expander = None

        logger.info(
            f"QueryOptimizer initialized: NER={'SciSpaCy' if self.ner_engine else 'fallback'}, "
            f"Synonyms={'SapBERT+ontologies' if self.synonym_expander else 'basic'}, "
            f"Expansion={enable_expansion}, Normalization={enable_normalization}"
        )

    async def optimize(self, query: str) -> OptimizedQuery:
        """
        Optimize query for better search recall.

        Steps:
        1. Named Entity Recognition (extract diseases, genes, etc.)
        2. Synonym expansion (find medical/biological synonyms)
        3. Query expansion (related terms)
        4. Normalization (standardize gene/protein names)

        Args:
            query: Original user query

        Returns:
            OptimizedQuery with all enhancements
        """
        if not query or not query.strip():
            return OptimizedQuery(primary_query=query)

        result = OptimizedQuery(primary_query=query.strip())

        # Step 1: Named Entity Recognition
        if self.enable_ner:
            entities = await self._extract_entities(query)
            result.entities = entities
            logger.debug(f"Extracted entities: {entities}")

        # Step 2: Synonym expansion
        if self.enable_synonyms:
            synonyms = await self._find_synonyms(result.entities, query)
            result.synonyms = synonyms
            logger.debug(f"Found synonyms: {list(synonyms.keys())}")

        # Step 3: Query expansion
        if self.enable_expansion:
            expanded = await self._expand_query(query, result.entities)
            result.expanded_terms = expanded
            logger.debug(f"Expanded terms: {expanded[:5]}")

        # Step 4: Normalization
        if self.enable_normalization:
            normalized = await self._normalize_terms(query, result.entities)
            result.normalized_terms = normalized
            logger.debug(f"Normalized terms: {normalized}")

        return result

    async def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract biomedical entities using production SciSpaCy NER.

        Uses BiomedicalNER (SciSpacy en_core_sci_md) for accurate entity extraction.
        Falls back to pattern matching if NER unavailable.

        Args:
            query: Query string

        Returns:
            Dictionary mapping entity type to list of entities
            {
                "disease": ["alzheimer's disease", "dementia"],
                "gene": ["APOE", "APP"],
                "protein": ["amyloid beta"],
            }
        """
        entities = {}

        # Use production SciSpaCy NER (preferred)
        if self.ner_engine:
            try:
                ner_result = self.ner_engine.extract_entities(query)

                # Convert NER result to our format
                for entity in ner_result.entities:
                    entity_type = entity.entity_type.value.lower()

                    if entity_type not in entities:
                        entities[entity_type] = []

                    # Store entity text (unique)
                    entity_text = entity.text
                    if entity_text not in entities[entity_type]:
                        entities[entity_type].append(entity_text)

                logger.debug(f"SciSpaCy NER extracted: {entities}")
                return entities

            except Exception as e:
                logger.warning(f"SciSpaCy NER failed: {e}. Using fallback.")

        # Fallback: Pattern-based extraction
        query_lower = query.lower()

        # Extract diseases
        diseases = set()
        for pattern, disease_type in self.FALLBACK_DISEASE_PATTERNS.items():
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                diseases.add(match.lower())

        if diseases:
            entities["disease"] = list(diseases)

        # Extract genes (simple capital letter patterns)
        genes = set()
        for pattern, gene_type in self.FALLBACK_GENE_PATTERNS.items():
            matches = re.findall(pattern, query)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                # Filter out common English words
                if len(match) >= 3 and match.lower() not in ["the", "and", "for", "with"]:
                    genes.add(match.upper())

        if genes:
            entities["gene"] = list(genes)

        logger.debug(f"Fallback pattern extraction: {entities}")
        return entities

    async def _find_synonyms(self, entities: Dict[str, List[str]], query: str) -> Dict[str, List[str]]:
        """
        Find medical/biological synonyms using SapBERT embeddings + ontology gazetteers.

        Uses production SynonymExpander with:
        - SapBERT embeddings (UMLS-trained, biomedical-specific)
        - Ontology gazetteers (OBI, EDAM, EFO, MeSH)
        - Abbreviation detection
        - Variant generation

        Falls back to basic dictionary if expander unavailable.

        Args:
            entities: Extracted entities
            query: Original query for context

        Returns:
            Dictionary mapping original term to list of synonyms
        """
        synonyms = {}

        # Use production SynonymExpander (preferred)
        if self.synonym_expander:
            try:
                # For each entity, get synonyms
                for entity_type, entity_list in entities.items():
                    for entity_text in entity_list:
                        # Query SynonymExpander
                        # Note: SynonymExpander.expand() returns technique-specific synonyms
                        # We'll use it for disease/gene terms too
                        try:
                            expansion_result = self.synonym_expander.expand_query(entity_text)

                            # Extract synonyms from result
                            entity_syns = set()
                            for technique_syns in expansion_result.values():
                                if hasattr(technique_syns, "all_terms"):
                                    entity_syns.update(technique_syns.all_terms())

                            if entity_syns:
                                # Remove original term
                                entity_syns.discard(entity_text)
                                if entity_syns:
                                    synonyms[entity_text] = list(entity_syns)[:10]  # Max 10

                        except Exception as e:
                            logger.debug(f"SynonymExpander failed for '{entity_text}': {e}")
                            continue

                # Also check terms in query directly
                query_lower = query.lower()
                for term, syn_list in self.BASIC_SYNONYMS.items():
                    if term in query_lower and term not in synonyms:
                        synonyms[term] = syn_list

                if synonyms:
                    logger.debug(f"SapBERT+Ontology synonyms found: {list(synonyms.keys())}")
                return synonyms

            except Exception as e:
                logger.warning(f"SynonymExpander failed: {e}. Using fallback.")

        # Fallback: Basic dictionary
        query_lower = query.lower()

        # Check for disease synonyms
        for entity_type, entity_list in entities.items():
            if entity_type == "disease":
                for disease in entity_list:
                    disease_lower = disease.lower()
                    for key, syn_list in self.BASIC_SYNONYMS.items():
                        if disease_lower in key or key in disease_lower:
                            synonyms[disease] = syn_list
                            break

        # Check for gene synonyms
        for entity_type, entity_list in entities.items():
            if entity_type == "gene":
                for gene in entity_list:
                    gene_upper = gene.upper()
                    if gene_upper in self.BASIC_SYNONYMS:
                        synonyms[gene] = self.BASIC_SYNONYMS[gene_upper]

        # Also check query terms
        for term, syn_list in self.BASIC_SYNONYMS.items():
            if term in query_lower and term not in synonyms:
                synonyms[term] = syn_list

        logger.debug(f"Fallback synonyms found: {list(synonyms.keys())}")
        return synonyms

    async def _expand_query(self, query: str, entities: Dict[str, List[str]]) -> List[str]:
        """
        Expand query with related terms.

        Future: Use word embeddings, knowledge graphs, or GO for expansion.

        Args:
            query: Original query
            entities: Extracted entities

        Returns:
            List of expanded/related terms
        """
        expanded = []
        query_lower = query.lower()

        # Disease-specific expansions
        if "alzheimer" in query_lower:
            expanded.extend(
                [
                    "alzheimer's disease pathology",
                    "amyloid beta",
                    "tau protein",
                    "neurodegeneration",
                    "cognitive decline",
                ]
            )

        if "cancer" in query_lower:
            expanded.extend(
                [
                    "oncology",
                    "tumor microenvironment",
                    "metastasis",
                    "carcinogenesis",
                ]
            )

        if "diabetes" in query_lower:
            expanded.extend(
                [
                    "glucose metabolism",
                    "insulin resistance",
                    "hyperglycemia",
                    "pancreatic beta cells",
                ]
            )

        # Gene-specific expansions
        if "gene" in entities:
            for gene in entities["gene"]:
                if gene.upper() == "APOE":
                    expanded.extend(
                        [
                            "lipid metabolism",
                            "cholesterol transport",
                            "apolipoprotein",
                        ]
                    )
                elif gene.upper() == "TP53":
                    expanded.extend(
                        [
                            "tumor suppressor",
                            "cell cycle regulation",
                            "apoptosis",
                        ]
                    )

        # Remove duplicates and limit
        expanded = list(dict.fromkeys(expanded))[:10]

        return expanded

    async def _normalize_terms(self, query: str, entities: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Normalize gene/protein names and other terms.

        Args:
            query: Original query
            entities: Extracted entities

        Returns:
            Dictionary mapping original term to normalized form
        """
        normalized = {}

        # Normalize genes (uppercase)
        if "gene" in entities:
            for gene in entities["gene"]:
                normalized[gene] = gene.upper()

        # Normalize diseases (lowercase, standardized form)
        if "disease" in entities:
            for disease in entities["disease"]:
                # Remove possessive forms
                disease_normalized = disease.replace("'s", "").replace("'s", "").strip()
                normalized[disease] = disease_normalized.lower()

        return normalized


# Example usage and tests
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.DEBUG)

    async def test_optimizer():
        optimizer = QueryOptimizer(
            enable_ner=True,
            enable_synonyms=True,
            enable_expansion=True,
            enable_normalization=True,
        )

        test_queries = [
            "alzheimer's disease",
            "APOE gene expression in Alzheimer's disease",
            "breast cancer treatment",
            "diabetes and insulin resistance",
            "TP53 mutations in cancer",
            "covid-19 vaccine efficacy",
        ]

        print("Query Optimizer Test Results:")
        print("=" * 80)

        for query in test_queries:
            result = await optimizer.optimize(query)

            print(f"\n{'='*80}")
            print(f"Query: '{query}'")
            print(f"\nEntities: {result.entities}")
            print(f"\nSynonyms:")
            for term, syns in result.synonyms.items():
                print(f"  {term}: {syns[:3]}")
            print(f"\nExpanded terms: {result.expanded_terms[:5]}")
            print(f"\nNormalized: {result.normalized_terms}")
            print(f"\nQuery variations (first 5):")
            variations = result.get_all_query_variations(max_per_type=2)
            for i, var in enumerate(variations[:5], 1):
                print(f"  {i}. {var}")

    asyncio.run(test_optimizer())
