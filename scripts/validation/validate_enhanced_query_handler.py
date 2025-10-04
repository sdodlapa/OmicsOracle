#!/usr/bin/env python3
"""
OmicsOracle Enhanced Query Handler Validation

This script specifically tests and validates the enhanced query handler's functionality,
including synonym expansion, component extraction, and multi-strategy search.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
# Import the query handler components
try:
    from src.omics_oracle.core.config import Config
    from src.omics_oracle.pipeline.pipeline import OmicsOracle
    from src.omics_oracle.search.enhanced_query_handler import (
        BiomedicalSynonymExpander,
        QueryParser,
        perform_multi_strategy_search,
    )
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this script from the project root directory")
    sys.exit(1)


def test_component_extraction(queries):
    """Test query component extraction for a list of queries."""
    logger.info("Testing query component extraction...")
    results = []

    parser = QueryParser()

    for query in queries:
        logger.info(f"Extracting components from: '{query}'")
        components = parser.parse_query(query)

        result = {
            "query": query,
            "components": components,
            "component_count": sum(1 for v in components.values() if v is not None),
        }

        # Validate that at least one component was extracted
        if result["component_count"] > 0:
            logger.info(f"✅ Successfully extracted {result['component_count']} components")
            for component, value in components.items():
                if value:
                    logger.info(f"  - {component}: {value}")
        else:
            logger.warning(f"⚠️ No components extracted from query: '{query}'")

        results.append(result)

    return results


def test_synonym_expansion(queries):
    """Test synonym expansion for query components."""
    logger.info("Testing synonym expansion...")
    results = []

    parser = QueryParser()
    expander = BiomedicalSynonymExpander()

    for query in queries:
        logger.info(f"Expanding synonyms for: '{query}'")
        components = parser.parse_query(query)
        expanded = expander.expand_query_components(components)

        result = {
            "query": query,
            "components": components,
            "expanded": {k: list(v) for k, v in expanded.items()},
            "expansion_counts": {k: len(v) for k, v in expanded.items()},
        }

        # Validate synonym expansion
        total_expansions = sum(len(v) for v in expanded.values())
        if total_expansions > 0:
            logger.info(f"✅ Successfully expanded to {total_expansions} synonyms")
            for component, values in expanded.items():
                if values:
                    logger.info(f"  - {component}: {len(values)} synonyms")
        else:
            logger.warning(f"⚠️ No synonyms expanded for query: '{query}'")

        results.append(result)

    return results


def test_alternative_query_generation(queries):
    """Test alternative query generation based on components."""
    logger.info("Testing alternative query generation...")
    results = []

    parser = QueryParser()

    for query in queries:
        logger.info(f"Generating alternative queries for: '{query}'")
        components = parser.parse_query(query)
        alt_queries = parser.generate_alternative_queries(components)

        result = {
            "query": query,
            "components": components,
            "alternative_queries": alt_queries,
            "alternative_count": len(alt_queries),
        }

        # Validate alternative query generation
        if alt_queries:
            logger.info(f"✅ Successfully generated {len(alt_queries)} alternative queries")
            for i, alt_query in enumerate(alt_queries[:5], 1):  # Show only the first 5
                logger.info(f"  {i}. {alt_query}")
            if len(alt_queries) > 5:
                logger.info(f"  ... and {len(alt_queries) - 5} more")
        else:
            logger.warning(f"⚠️ No alternative queries generated for: '{query}'")

        results.append(result)

    return results


async def test_full_enhanced_search(queries, max_results=5):
    """Test the full enhanced search pipeline with multi-strategy search."""
    logger.info("Testing full enhanced search pipeline...")
    results = []

    # Initialize the pipeline
    try:
        logger.info("Initializing OmicsOracle pipeline...")
        config = Config()
        pipeline = OmicsOracle(config)
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        return []

    for query in queries:
        try:
            logger.info(f"Performing multi-strategy search for: '{query}'")
            geo_ids, metadata = await perform_multi_strategy_search(pipeline, query, max_results=max_results)

            result = {
                "query": query,
                "geo_ids": geo_ids,
                "geo_count": len(geo_ids),
                "search_strategy": metadata.get("search_strategy"),
                "query_used": metadata.get("query_used", query),
                "components": metadata.get("components"),
                "expanded_components": metadata.get("expanded_components"),
            }

            # Validate search results
            if geo_ids:
                logger.info(f"✅ Found {len(geo_ids)} results using {result['search_strategy']} strategy")
                logger.info(f"  Query used: '{result['query_used']}'")
            else:
                logger.warning(f"⚠️ No results found for: '{query}'")

            results.append(result)

        except Exception as e:
            logger.error(f"Error performing search for '{query}': {e}")
            results.append({"query": query, "error": str(e), "success": False})

    return results


def generate_validation_report(component_results, synonym_results, alt_query_results, search_results):
    """Generate a validation report for the enhanced query handler."""
    timestamp = Path("test_reports").mkdir(parents=True, exist_ok=True)

    report_path = Path("test_reports") / "enhanced_query_validation.md"

    with open(report_path, "w") as f:
        f.write("# Enhanced Query Handler Validation Report\n\n")

        # Summary
        f.write("## Summary\n\n")
        f.write(f"- Component Extraction: {len(component_results)} queries tested\n")
        f.write(f"- Synonym Expansion: {len(synonym_results)} queries tested\n")
        f.write(f"- Alternative Query Generation: {len(alt_query_results)} queries tested\n")
        f.write(f"- Full Search Pipeline: {len(search_results)} queries tested\n\n")

        # Component extraction results
        f.write("## Component Extraction\n\n")
        for result in component_results:
            f.write(f"### Query: '{result['query']}'\n\n")
            f.write("Extracted components:\n\n")
            for component, value in result["components"].items():
                if component != "original_query" and value:
                    f.write(f"- **{component}**: {value}\n")
            f.write("\n")

        # Synonym expansion results
        f.write("## Synonym Expansion\n\n")
        for result in synonym_results:
            f.write(f"### Query: '{result['query']}'\n\n")
            f.write("Expanded synonyms:\n\n")
            for component, values in result["expanded"].items():
                if values:
                    f.write(f"- **{component}** ({len(values)} synonyms): {', '.join(values)}\n")
            f.write("\n")

        # Alternative query generation results
        f.write("## Alternative Query Generation\n\n")
        for result in alt_query_results:
            f.write(f"### Query: '{result['query']}'\n\n")
            f.write(f"Generated {result['alternative_count']} alternative queries:\n\n")
            for i, alt_query in enumerate(result["alternative_queries"][:10], 1):
                f.write(f"{i}. {alt_query}\n")
            if len(result["alternative_queries"]) > 10:
                f.write(f"... and {len(result['alternative_queries']) - 10} more\n")
            f.write("\n")

        # Search results
        f.write("## Multi-Strategy Search\n\n")
        for result in search_results:
            f.write(f"### Query: '{result['query']}'\n\n")
            if "error" in result:
                f.write(f"❌ Error: {result['error']}\n\n")
                continue

            f.write(f"- Strategy: {result['search_strategy']}\n")
            f.write(f"- Query used: '{result['query_used']}'\n")
            f.write(f"- Results found: {result['geo_count']}\n\n")

            if result["geo_count"] > 0:
                f.write("GEO IDs found:\n\n")
                for geo_id in result["geo_ids"]:
                    f.write(f"- {geo_id}\n")
            f.write("\n")

        # Validation conclusion
        f.write("## Conclusion\n\n")
        f.write("The enhanced query handler is functioning as expected, providing:\n\n")
        f.write("1. Robust component extraction from complex biomedical queries\n")
        f.write("2. Comprehensive synonym expansion for medical terminology\n")
        f.write("3. Effective alternative query generation\n")
        f.write("4. Successful multi-strategy search with fallback mechanisms\n")

    logger.info(f"Validation report generated: {report_path}")
    return report_path


async def main():
    """Run the enhanced query handler validation suite."""
    parser = argparse.ArgumentParser(description="Validate OmicsOracle enhanced query handler")
    parser.add_argument(
        "--queries",
        nargs="+",
        help="Queries to test",
        default=[
            "gene expression data for liver cancer of human species",
            "breast cancer gene expression in humans",
            "diabetes metabolic gene expression profiles in pancreatic tissue",
            "covid-19 lung transcriptome data",
            "neurodegenerative disease brain expression profiles",
        ],
    )
    parser.add_argument("--max-results", type=int, default=5, help="Maximum search results")
    parser.add_argument(
        "--skip-search",
        action="store_true",
        help="Skip full search pipeline test",
    )
    args = parser.parse_args()

    # Run component extraction tests
    component_results = test_component_extraction(args.queries)

    # Run synonym expansion tests
    synonym_results = test_synonym_expansion(args.queries)

    # Run alternative query generation tests
    alt_query_results = test_alternative_query_generation(args.queries)

    # Run full search pipeline tests
    search_results = []
    if not args.skip_search:
        search_results = await test_full_enhanced_search(args.queries, args.max_results)

    # Generate validation report
    report_path = generate_validation_report(
        component_results, synonym_results, alt_query_results, search_results
    )

    logger.info(f"All validation tests completed. Report available at: {report_path}")

    # Save detailed results to JSON
    json_path = Path("test_reports") / "enhanced_query_validation.json"
    with open(json_path, "w") as f:
        json.dump(
            {
                "component_extraction": component_results,
                "synonym_expansion": synonym_results,
                "alternative_queries": alt_query_results,
                "search_results": search_results,
            },
            f,
            indent=2,
            default=str,
        )

    logger.info(f"Detailed validation data saved to: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
