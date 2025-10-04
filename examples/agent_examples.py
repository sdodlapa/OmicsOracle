"""
Agent Framework Examples

Practical examples demonstrating how to use the OmicsOracle v2 Agent Framework.
Run each example independently to learn different aspects of the system.

Requirements:
    - NCBI email configured (export NCBI_EMAIL="your@email.com")
    - OpenAI API key configured (export OPENAI_API_KEY="sk-...")
    - NLP model downloaded (python -m spacy download en_core_sci_sm)
"""

import os

from omics_oracle_v2.agents import DataAgent, Orchestrator, QueryAgent, ReportAgent, SearchAgent
from omics_oracle_v2.agents.models import QueryInput
from omics_oracle_v2.agents.models.data import DataInput
from omics_oracle_v2.agents.models.orchestrator import OrchestratorInput, WorkflowType
from omics_oracle_v2.agents.models.report import ReportFormat, ReportInput, ReportType
from omics_oracle_v2.agents.models.search import SearchInput
from omics_oracle_v2.core import GEOSettings, Settings
from omics_oracle_v2.lib.nlp.models import EntityType

# ============================================================================
# Example 1: Simple Query Processing
# ============================================================================


def example_1_simple_query():
    """Extract biomedical entities from a natural language query."""
    print("=" * 70)
    print("Example 1: Simple Query Processing")
    print("=" * 70)

    # Create Query Agent
    agent = QueryAgent()

    # Process a complex biomedical query
    query_input = QueryInput(query="Find datasets about TP53 mutations in breast cancer patients")

    result = agent.execute(query_input)

    if result.success:
        output = result.output
        print(f"\nOriginal Query: {output.original_query}")
        print(f"Detected Intent: {output.intent}")
        print(f"Confidence: {output.confidence:.2f}")
        print(f"\nExtracted Entities ({len(output.entities)}):")

        for entity in output.entities[:10]:
            print(f"  - {entity.text} ({entity.entity_type.value})")

        print(f"\nGenerated Search Terms: {output.search_terms}")
        print("\nEntity Counts:")
        for entity_type, count in output.entity_counts.items():
            print(f"  {entity_type}: {count}")
    else:
        print(f"Error: {result.error}")

    print()


# ============================================================================
# Example 2: Dataset Search
# ============================================================================


def example_2_dataset_search():
    """Search GEO database for relevant datasets."""
    print("=" * 70)
    print("Example 2: Dataset Search")
    print("=" * 70)

    # Configure with NCBI email
    settings = Settings(
        geo=GEOSettings(
            ncbi_email=os.getenv("NCBI_EMAIL", "test@example.com"),
            rate_limit=3,
        )
    )

    # Create Search Agent
    agent = SearchAgent(settings=settings)

    # Search for datasets
    search_input = SearchInput(
        search_terms=["TP53", "breast cancer"],
        max_results=10,
        organism="Homo sapiens",
    )

    result = agent.execute(search_input)

    if result.success:
        output = result.output
        print(f"\nTotal Datasets Found: {output.total_found}")
        print(f"Search Terms Used: {output.search_terms_used}")
        print(f"Filters Applied: {output.filters_applied}")
        print("\nTop Results:")

        for i, ranked_ds in enumerate(output.datasets[:5], 1):
            ds = ranked_ds.dataset
            print(f"\n{i}. {ds.geo_id}")
            print(f"   Title: {ds.title[:60]}...")
            print(f"   Organism: {ds.organism}")
            print(f"   Samples: {ds.sample_count}")
            print(f"   Relevance: {ranked_ds.relevance_score:.2f}")
            print(f"   Reasons: {', '.join(ranked_ds.match_reasons[:3])}")
    else:
        print(f"Error: {result.error}")

    print()


# ============================================================================
# Example 3: Data Quality Validation
# ============================================================================


def example_3_data_validation():
    """Validate and assess quality of datasets."""
    print("=" * 70)
    print("Example 3: Data Quality Validation")
    print("=" * 70)

    # First get some datasets from search
    settings = Settings(geo=GEOSettings(ncbi_email=os.getenv("NCBI_EMAIL", "test@example.com")))

    search_agent = SearchAgent(settings=settings)
    search_result = search_agent.execute(SearchInput(search_terms=["cancer"], max_results=10))

    if not search_result.success:
        print(f"Search failed: {search_result.error}")
        return

    # Validate datasets
    data_agent = DataAgent(settings=settings)
    data_input = DataInput(
        datasets=search_result.output.datasets[:5],
        min_quality_score=0.0,  # Accept all for demonstration
    )

    result = data_agent.execute(data_input)

    if result.success:
        output = result.output
        print(f"\nTotal Processed: {output.total_processed}")
        print(f"Passed Quality Threshold: {output.total_passed_quality}")
        print(f"Average Quality Score: {output.average_quality_score:.2f}")
        print("\nQuality Distribution:")
        for level, count in output.quality_distribution.items():
            print(f"  {level}: {count}")

        print("\nTop Quality Datasets:")
        for processed_ds in output.processed_datasets[:3]:
            print(f"\n{processed_ds.geo_id}")
            print(f"  Quality Score: {processed_ds.quality_score:.2f}")
            print(f"  Samples: {processed_ds.sample_count}")
            print(f"  Has Publication: {processed_ds.has_publication}")
            print(f"  Has SRA Data: {processed_ds.has_sra_data}")
            print(f"  Age: {processed_ds.age_days} days")
    else:
        print(f"Error: {result.error}")

    print()


# ============================================================================
# Example 4: Report Generation
# ============================================================================


def example_4_report_generation():
    """Generate AI-powered analysis reports."""
    print("=" * 70)
    print("Example 4: Report Generation")
    print("=" * 70)

    # Get processed datasets first
    settings = Settings(geo=GEOSettings(ncbi_email=os.getenv("NCBI_EMAIL", "test@example.com")))

    search_agent = SearchAgent(settings=settings)
    search_result = search_agent.execute(SearchInput(search_terms=["cancer"], max_results=5))

    if not search_result.success:
        print("Search failed")
        return

    data_agent = DataAgent(settings=settings)
    data_result = data_agent.execute(DataInput(datasets=search_result.output.datasets[:3]))

    if not data_result.success:
        print("Data validation failed")
        return

    # Generate report
    report_agent = ReportAgent(settings=settings)
    report_input = ReportInput(
        datasets=data_result.output.processed_datasets,
        query_context="Cancer research datasets",
        report_type=ReportType.BRIEF,
        report_format=ReportFormat.MARKDOWN,
    )

    result = report_agent.execute(report_input)

    if result.success:
        output = result.output
        print(f"\nReport Generated: {output.generated_at}")
        print(f"Report Type: {output.report_type.value}")
        print(f"Format: {output.report_format.value}")
        print(f"Datasets Analyzed: {output.total_datasets_analyzed}")
        print(f"\nReport Title: {output.title}")
        print(f"\nExecutive Summary:\n{output.summary}")
        print(f"\nKey Insights: {len(output.key_insights)}")
        for insight in output.key_insights[:3]:
            print(f"  - {insight.insight}")

        print("\nFull Report Preview:")
        print("-" * 70)
        print(output.full_report[:500] + "...")
    else:
        print(f"Error: {result.error}")

    print()


# ============================================================================
# Example 5: Simple Orchestrated Workflow
# ============================================================================


def example_5_simple_workflow():
    """Execute a simple orchestrated workflow."""
    print("=" * 70)
    print("Example 5: Simple Orchestrated Workflow")
    print("=" * 70)

    # Configure settings
    settings = Settings(
        geo=GEOSettings(
            ncbi_email=os.getenv("NCBI_EMAIL", "test@example.com"),
        )
    )

    # Create orchestrator
    orchestrator = Orchestrator(settings=settings)

    # Execute simple search workflow
    workflow_input = OrchestratorInput(
        query="Find TP53 datasets in cancer research",
        workflow_type=WorkflowType.SIMPLE_SEARCH,
        max_results=10,
    )

    result = orchestrator.execute(workflow_input)

    if result.success:
        output = result.output
        print(f"\nWorkflow Type: {output.workflow_type.value}")
        print(f"Final Stage: {output.final_stage.value}")
        print(f"Stages Completed: {output.stages_completed}")
        print(f"Execution Time: {output.total_execution_time_ms:.2f}ms")

        print(f"\nDatasets Found: {output.total_datasets_found}")

        print("\nStage Results:")
        for stage_result in output.stage_results:
            status = "[OK]" if stage_result.success else "[FAILED]"
            print(f"  {status} {stage_result.stage.value}: " f"{stage_result.execution_time_ms:.2f}ms")

        if output.final_report:
            print("\nReport Preview:")
            print("-" * 70)
            print(output.final_report[:300] + "...")
    else:
        print(f"Error: {result.error}")

    print()


# ============================================================================
# Example 6: Full Analysis Workflow
# ============================================================================


def example_6_full_analysis():
    """Execute complete workflow with all agents."""
    print("=" * 70)
    print("Example 6: Full Analysis Workflow")
    print("=" * 70)

    settings = Settings(
        geo=GEOSettings(
            ncbi_email=os.getenv("NCBI_EMAIL", "test@example.com"),
        )
    )

    orchestrator = Orchestrator(settings=settings)

    # Execute full analysis
    workflow_input = OrchestratorInput(
        query="Analyze BRCA1 mutations in breast cancer patients",
        workflow_type=WorkflowType.FULL_ANALYSIS,
        max_results=5,
        organism="Homo sapiens",
        min_samples=50,
    )

    result = orchestrator.execute(workflow_input)

    if result.success:
        output = result.output
        print(f"\nQuery: {output.query}")
        print(f"Workflow: {output.workflow_type.value}")
        print(f"Status: {output.final_stage.value}")

        print("\nExecution Summary:")
        summary = output.get_execution_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")

        print("\nStage-by-Stage Results:")
        for stage_result in output.stage_results:
            print(f"\n  Stage: {stage_result.stage.value}")
            print(f"    Agent: {stage_result.agent_name}")
            print(f"    Success: {stage_result.success}")
            print(f"    Time: {stage_result.execution_time_ms:.2f}ms")
            if stage_result.error:
                print(f"    Error: {stage_result.error}")
    else:
        print(f"Workflow failed: {result.error}")

    print()


# ============================================================================
# Example 7: Manual Multi-Agent Workflow
# ============================================================================


def example_7_manual_workflow():
    """Manually coordinate multiple agents for fine control."""
    print("=" * 70)
    print("Example 7: Manual Multi-Agent Workflow")
    print("=" * 70)

    settings = Settings(
        geo=GEOSettings(
            ncbi_email=os.getenv("NCBI_EMAIL", "test@example.com"),
        )
    )

    # Initialize all agents
    query_agent = QueryAgent(settings=settings)
    search_agent = SearchAgent(settings=settings)
    data_agent = DataAgent(settings=settings)

    # Step 1: Query Processing
    print("\nStep 1: Processing Query...")
    query_result = query_agent.execute(QueryInput(query="Find TP53 datasets in cancer research"))

    if not query_result.success:
        print(f"Query failed: {query_result.error}")
        return

    print(f"  Found {len(query_result.output.entities)} entities")
    print(f"  Generated {len(query_result.output.search_terms)} search terms")

    # Step 2: Dataset Search
    print("\nStep 2: Searching GEO...")
    search_result = search_agent.execute(
        SearchInput(
            search_terms=query_result.output.search_terms,
            max_results=10,
            organism="Homo sapiens",
        )
    )

    if not search_result.success:
        print(f"Search failed: {search_result.error}")
        return

    print(f"  Found {search_result.output.total_found} datasets")

    # Step 3: Quality Validation
    print("\nStep 3: Validating Quality...")
    data_result = data_agent.execute(
        DataInput(
            datasets=search_result.output.datasets[:5],
            min_quality_score=0.7,
        )
    )

    if not data_result.success:
        print(f"Validation failed: {data_result.error}")
        return

    print(f"  Processed {data_result.output.total_processed} datasets")
    print(f"  High quality: {len(data_result.output.get_high_quality_datasets())}")

    # Results Summary
    print("\nWorkflow Complete!")
    print(
        f"  Total execution: ~{query_result.execution_time_ms + search_result.execution_time_ms + data_result.execution_time_ms:.0f}ms"
    )

    print()


# ============================================================================
# Example 8: Entity-Focused Search
# ============================================================================


def example_8_entity_focused():
    """Search focusing on specific biomedical entities."""
    print("=" * 70)
    print("Example 8: Entity-Focused Search")
    print("=" * 70)

    # Process query to extract entities
    query_agent = QueryAgent()
    query_result = query_agent.execute(
        QueryInput(query="Find datasets about BRCA1 and BRCA2 genes in ovarian cancer")
    )

    if not query_result.success:
        print(f"Query failed: {query_result.error}")
        return

    # Extract specific entity types
    genes = query_result.output.get_entities_by_type(EntityType.GENE)
    diseases = query_result.output.get_entities_by_type(EntityType.DISEASE)

    print("\nExtracted Entities:")
    print(f"  Genes: {[g.text for g in genes]}")
    print(f"  Diseases: {[d.text for d in diseases]}")

    # Search using only gene entities
    settings = Settings(geo=GEOSettings(ncbi_email=os.getenv("NCBI_EMAIL", "test@example.com")))

    search_agent = SearchAgent(settings=settings)
    search_result = search_agent.execute(
        SearchInput(
            search_terms=[g.text for g in genes] + [d.text for d in diseases],
            max_results=10,
        )
    )

    if search_result.success:
        print(f"\nFound {search_result.output.total_found} relevant datasets")
        print("\nTop 3 Results:")
        for i, ds in enumerate(search_result.output.datasets[:3], 1):
            print(f"\n{i}. {ds.dataset.geo_id}")
            print(f"   {ds.dataset.title[:70]}...")
            print(f"   Relevance: {ds.relevance_score:.2f}")

    print()


# ============================================================================
# Example 9: Batch Processing
# ============================================================================


def example_9_batch_processing():
    """Process multiple queries efficiently."""
    print("=" * 70)
    print("Example 9: Batch Processing")
    print("=" * 70)

    settings = Settings(geo=GEOSettings(ncbi_email=os.getenv("NCBI_EMAIL", "test@example.com")))

    orchestrator = Orchestrator(settings=settings)

    # Multiple related queries
    queries = [
        "TP53 in breast cancer",
        "TP53 mutations",
        "TP53 gene expression",
    ]

    print(f"\nProcessing {len(queries)} queries...")
    results = []

    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}/{len(queries)}: {query}")
        result = orchestrator.execute(
            OrchestratorInput(
                query=query,
                workflow_type=WorkflowType.SIMPLE_SEARCH,
                max_results=5,
            )
        )

        if result.success:
            print(
                f"  [OK] Success: {result.output.total_datasets_found} datasets, "
                f"{result.output.total_execution_time_ms:.0f}ms"
            )
            results.append(result)
        else:
            print(f"  [FAILED] Failed: {result.error}")

    print("\nBatch Summary:")
    print(f"  Successful: {len(results)}/{len(queries)}")
    total_datasets = sum(r.output.total_datasets_found for r in results)
    print(f"  Total datasets found: {total_datasets}")
    avg_time = sum(r.output.total_execution_time_ms for r in results) / len(results)
    print(f"  Average execution time: {avg_time:.0f}ms")

    print()


# ============================================================================
# Example 10: Error Handling
# ============================================================================


def example_10_error_handling():
    """Demonstrate robust error handling."""
    print("=" * 70)
    print("Example 10: Error Handling")
    print("=" * 70)

    orchestrator = Orchestrator()

    # Test 1: Empty query
    print("\nTest 1: Empty Query")
    try:
        result = orchestrator.execute(
            OrchestratorInput(
                query="",  # Invalid
                workflow_type=WorkflowType.SIMPLE_SEARCH,
            )
        )
        print(f"  Result: {'Success' if result.success else 'Failed'}")
    except Exception as e:
        print(f"  Exception caught: {type(e).__name__}")

    # Test 2: Workflow handles failures gracefully
    print("\nTest 2: Minimal Query (might have issues)")
    result = orchestrator.execute(
        OrchestratorInput(
            query="test",  # Very basic query
            workflow_type=WorkflowType.SIMPLE_SEARCH,
            max_results=1,
        )
    )

    print(f"  Success: {result.success}")
    print(f"  Final stage: {result.output.final_stage.value}")
    if result.output.error_message:
        print(f"  Message: {result.output.error_message}")

    # Test 3: Check failed stages
    failed_stages = result.output.get_failed_stages()
    if failed_stages:
        print("\n  Failed stages:")
        for stage in failed_stages:
            print(f"    - {stage.stage.value}: {stage.error}")
    else:
        print("  No failed stages")

    print()


# ============================================================================
# Main
# ============================================================================


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("OmicsOracle v2 Agent Framework - Examples")
    print("=" * 70)

    # Check environment
    ncbi_email = os.getenv("NCBI_EMAIL")
    if not ncbi_email:
        print("\nWARNING: NCBI_EMAIL not set. Some examples may fail.")
        print("  export NCBI_EMAIL='your@email.com'")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("\nWARNING: OPENAI_API_KEY not set. Report generation may fail.")
        print("  export OPENAI_API_KEY='sk-...'")

    print()

    # Run examples
    examples = [
        ("Simple Query Processing", example_1_simple_query),
        ("Dataset Search", example_2_dataset_search),
        ("Data Quality Validation", example_3_data_validation),
        ("Report Generation", example_4_report_generation),
        ("Simple Workflow", example_5_simple_workflow),
        ("Full Analysis", example_6_full_analysis),
        ("Manual Workflow", example_7_manual_workflow),
        ("Entity-Focused", example_8_entity_focused),
        ("Batch Processing", example_9_batch_processing),
        ("Error Handling", example_10_error_handling),
    ]

    for name, func in examples:
        try:
            func()
        except KeyboardInterrupt:
            print(f"\n\nStopped at: {name}")
            break
        except Exception as e:
            print(f"\nExample '{name}' failed: {e}")
            import traceback

            traceback.print_exc()

    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
