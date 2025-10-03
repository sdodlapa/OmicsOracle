"""
Query Agent for natural language query processing.

Processes user queries using NLP to extract biomedical entities,
determine intent, and generate search terms for downstream agents.
"""

import logging
import re
from typing import List, Set

from ..core.config import Settings
from ..lib.nlp import BiomedicalNER
from ..lib.nlp.models import Entity, EntityType
from .base import Agent
from .context import AgentContext
from .exceptions import AgentExecutionError, AgentValidationError
from .models import QueryInput, QueryIntent, QueryOutput

logger = logging.getLogger(__name__)


class QueryAgent(Agent[QueryInput, QueryOutput]):
    """
    Agent that processes natural language queries.

    Uses BiomedicalNER to extract entities from user queries and
    generates structured search terms for dataset retrieval.

    Features:
        - Entity extraction (genes, diseases, chemicals, etc.)
        - Intent classification (search, analyze, summarize, compare)
        - Search term generation with synonyms
        - Query validation and suggestions

    Example:
        >>> from omics_oracle_v2.agents import QueryAgent
        >>> from omics_oracle_v2.agents.models import QueryInput
        >>> from omics_oracle_v2.core import Settings
        >>>
        >>> settings = Settings()
        >>> agent = QueryAgent(settings)
        >>>
        >>> query_input = QueryInput(query="Find TP53 mutations in breast cancer")
        >>> result = agent.execute(query_input)
        >>>
        >>> print(result.output.intent)  # QueryIntent.SEARCH
        >>> print(result.output.entities)  # [Entity(text='TP53', type='GENE'), ...]
    """

    def __init__(self, settings: Settings, agent_name: str = "QueryAgent"):
        """
        Initialize the Query Agent.

        Args:
            settings: Application settings
            agent_name: Custom name for the agent
        """
        super().__init__(settings, agent_name)
        self._ner: BiomedicalNER = None

        # Intent detection keywords
        self._intent_keywords = {
            QueryIntent.SEARCH: ["find", "search", "look for", "get", "retrieve", "show"],
            QueryIntent.ANALYZE: ["analyze", "analysis", "examine", "study", "investigate"],
            QueryIntent.SUMMARIZE: ["summarize", "summary", "overview", "describe"],
            QueryIntent.COMPARE: ["compare", "comparison", "versus", "vs", "difference"],
        }

    def _initialize_resources(self) -> None:
        """Initialize the NER model."""
        try:
            logger.info("Initializing BiomedicalNER for QueryAgent")
            self._ner = BiomedicalNER(self.settings.nlp)
            logger.info("BiomedicalNER initialized successfully")
        except Exception as e:
            raise AgentExecutionError(f"Failed to initialize NER model: {e}") from e

    def _cleanup_resources(self) -> None:
        """Clean up NER resources."""
        if self._ner:
            logger.info("Cleaning up BiomedicalNER resources")
            self._ner = None

    def _validate_input(self, input_data: QueryInput) -> QueryInput:
        """
        Validate query input.

        Args:
            input_data: Query input to validate

        Returns:
            Validated query input

        Raises:
            AgentValidationError: If validation fails
        """
        # Check query is not empty after stripping
        if not input_data.query.strip():
            raise AgentValidationError("Query cannot be empty or whitespace only")

        # Check query is not too long (reasonable limit)
        if len(input_data.query) > 10000:
            raise AgentValidationError("Query is too long (max 10000 characters)")

        return input_data

    def _process(self, input_data: QueryInput, context: AgentContext) -> QueryOutput:
        """
        Process the query and extract entities.

        Args:
            input_data: Validated query input
            context: Agent execution context

        Returns:
            Query analysis results with entities and search terms

        Raises:
            AgentExecutionError: If processing fails
        """
        try:
            query = input_data.query.strip()
            context.set_metric("query_length", len(query))

            # 1. Detect intent
            intent = self._detect_intent(query)
            context.set_metric("detected_intent", intent.value)
            logger.info(f"Detected intent: {intent.value}")

            # 2. Extract entities using NER
            logger.info("Extracting entities from query")
            ner_result = self._ner.extract_entities(
                query,
                include_entity_linking=input_data.include_synonyms,
            )

            entities = ner_result.entities
            context.set_metric("entities_extracted", len(entities))
            logger.info(f"Extracted {len(entities)} entities")

            # 3. Count entities by type
            entity_counts = self._count_entities_by_type(entities)
            context.set_metric("entity_types", len(entity_counts))

            # 4. Generate search terms
            search_terms = self._generate_search_terms(entities, include_synonyms=input_data.include_synonyms)
            context.set_metric("search_terms_generated", len(search_terms))
            logger.info(f"Generated {len(search_terms)} search terms")

            # 5. Calculate confidence
            confidence = self._calculate_confidence(entities, intent)
            context.set_metric("confidence", confidence)

            # 6. Generate suggestions
            suggestions = self._generate_suggestions(query, entities, intent)

            return QueryOutput(
                original_query=query,
                intent=intent,
                entities=entities,
                search_terms=search_terms,
                entity_counts=entity_counts,
                confidence=confidence,
                suggestions=suggestions,
            )

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise AgentExecutionError(f"Failed to process query: {e}") from e

    def _detect_intent(self, query: str) -> QueryIntent:
        """
        Detect the user's intent from the query.

        Args:
            query: User query text

        Returns:
            Detected query intent
        """
        query_lower = query.lower()

        # Check for each intent's keywords using word boundaries
        for intent, keywords in self._intent_keywords.items():
            for keyword in keywords:
                # Use word boundary for single words, substring for phrases
                if " " in keyword:
                    # Multi-word phrase - use substring matching
                    if keyword in query_lower:
                        return intent
                else:
                    # Single word - use word boundary matching
                    if re.search(r"\b" + re.escape(keyword) + r"\b", query_lower):
                        return intent

        # Default to SEARCH if no specific intent detected
        return QueryIntent.SEARCH

    def _count_entities_by_type(self, entities: List[Entity]) -> dict:
        """
        Count entities by type.

        Args:
            entities: List of extracted entities

        Returns:
            Dictionary mapping entity type to count
        """
        counts = {}
        for entity in entities:
            entity_type = entity.entity_type.value
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts

    def _generate_search_terms(self, entities: List[Entity], include_synonyms: bool = True) -> List[str]:
        """
        Generate search terms from extracted entities.

        Args:
            entities: Extracted entities
            include_synonyms: Whether to include entity synonyms

        Returns:
            List of unique search terms
        """
        search_terms: Set[str] = set()

        for entity in entities:
            # Add the entity text
            search_terms.add(entity.text)

            # Add normalized form if available
            if hasattr(entity, "normalized") and entity.normalized:
                search_terms.add(entity.normalized)

            # Add KB ID if available (for precise matching)
            if entity.kb_id:
                search_terms.add(entity.kb_id)

        return sorted(list(search_terms))

    def _calculate_confidence(self, entities: List[Entity], intent: QueryIntent) -> float:
        """
        Calculate confidence in query understanding.

        Args:
            entities: Extracted entities
            intent: Detected intent

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence

        # Increase confidence if entities were found
        if len(entities) > 0:
            confidence += 0.3

        # Increase confidence if specific biomedical entities found
        biomedical_types = {
            EntityType.GENE,
            EntityType.PROTEIN,
            EntityType.DISEASE,
            EntityType.CHEMICAL,
        }
        has_biomedical = any(e.entity_type in biomedical_types for e in entities)
        if has_biomedical:
            confidence += 0.2

        # Intent detection adds small confidence boost
        if intent != QueryIntent.UNKNOWN:
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_suggestions(self, query: str, entities: List[Entity], intent: QueryIntent) -> List[str]:
        """
        Generate query improvement suggestions.

        Args:
            query: Original query
            entities: Extracted entities
            intent: Detected intent

        Returns:
            List of suggestions
        """
        suggestions = []

        # Suggest being more specific if no entities found
        if len(entities) == 0:
            suggestions.append("Try including specific genes, diseases, or biological terms in your query")

        # Suggest query expansion if very short
        if len(query.split()) < 3:
            suggestions.append("Consider adding more details to your query for better results")

        # Suggest specific entity types if missing key ones
        entity_types_present = {e.entity_type for e in entities}
        if EntityType.GENE not in entity_types_present and EntityType.DISEASE in entity_types_present:
            suggestions.append("Consider specifying genes or proteins of interest")
        elif EntityType.DISEASE not in entity_types_present and EntityType.GENE in entity_types_present:
            suggestions.append("Consider specifying the disease or condition of interest")

        return suggestions
