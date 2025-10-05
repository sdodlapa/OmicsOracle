"""Test what entities are extracted from the HiC methylation query."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.agents.models import QueryInput
from omics_oracle_v2.agents.query_agent import QueryAgent
from omics_oracle_v2.core.config import Settings


def test_query_parsing():
    """Test query parsing for HiC methylation query."""

    # Initialize
    settings = Settings()
    agent = QueryAgent(settings)

    # Test query
    query = "dna methylation and HiC joint profiling datasets"
    print(f"\n{'='*80}")
    print(f"Testing Query: {query}")
    print(f"{'='*80}\n")

    # Execute
    query_input = QueryInput(query=query, include_synonyms=False)
    result = agent.execute(query_input)

    # Display results
    print(f"Intent: {result.output.intent}")
    print(f"Confidence: {result.output.confidence:.2f}")
    print(f"\nEntities Extracted ({len(result.output.entities)}):")
    for entity in result.output.entities:
        print(
            f"  - {entity.text:30s} | Type: {entity.entity_type.value:15s} | Confidence: {entity.confidence:.2f}"
        )

    print(f"\nSearch Terms Generated ({len(result.output.search_terms)}):")
    for term in result.output.search_terms:
        print(f"  - {term}")

    print(f"\nEntity Counts by Type:")
    for entity_type, count in result.output.entity_counts.items():
        print(f"  - {entity_type}: {count}")

    print(f"\nSuggestions:")
    for suggestion in result.output.suggestions:
        print(f"  - {suggestion}")

    print(f"\n{'='*80}")
    print("✅ Query parsing completed")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_query_parsing()
