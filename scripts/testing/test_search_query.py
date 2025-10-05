"""Test the full search pipeline to see what query is sent to NCBI."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.core.config import Settings
from omics_oracle_v2.agents.query_agent import QueryAgent
from omics_oracle_v2.agents.search_agent import SearchAgent
from omics_oracle_v2.agents.models import QueryInput
from omics_oracle_v2.agents.models.search import SearchInput


def test_search_query():
    """Test what search query is sent to NCBI."""
    
    # Initialize
    settings = Settings()
    query_agent = QueryAgent(settings)
    search_agent = SearchAgent(settings)
    
    # Test query
    query = "dna methylation and HiC joint profiling datasets"
    print(f"\n{'='*80}")
    print(f"User Query: {query}")
    print(f"{'='*80}\n")
    
    # Step 1: Query processing
    query_input = QueryInput(query=query, include_synonyms=False)
    query_result = query_agent.execute(query_input)
    
    print(f"Extracted Search Terms:")
    for term in query_result.output.search_terms:
        print(f"  - {term}")
    
    # Step 2: Build search input
    search_input = SearchInput(
        search_terms=query_result.output.search_terms,
        max_results=10,
        min_samples=None,
        organism=None,
        study_type=None
    )
    
    # Build the query string (without actually searching)
    search_query = search_agent._build_search_query(search_input)
    
    print(f"\nNCBI Search Query:")
    print(f"  {search_query}")
    
    print(f"\n{'='*80}")
    print("Analysis:")
    print(f"{'='*80}")
    print("The query uses OR logic, so NCBI will return datasets matching:")
    print("  - 'HiC joint profiling' OR")
    print("  - 'datasets' OR")  
    print("  - 'dna methylation'")
    print("\nThis means datasets with ONLY 'dna methylation' (without HiC) will match!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_search_query()
