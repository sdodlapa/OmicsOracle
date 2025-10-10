#!/usr/bin/env python3
"""
Complete Week 3 Workflow Example

Demonstrates the full Week 3 pipeline:
1. Multi-source search (PubMed + Google Scholar)
2. Deduplication
3. Citation analysis with LLM
4. Advanced analytics (Q&A, trends, knowledge graph)
5. Report generation

This is a comprehensive example showing all Week 3 features working together.
"""

import os
from datetime import datetime
from pathlib import Path

from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.publications.analysis.knowledge_graph import BiomarkerKnowledgeGraph
from omics_oracle_v2.lib.publications.analysis.qa_system import DatasetQASystem
from omics_oracle_v2.lib.publications.analysis.reports import DatasetImpactReportGenerator
from omics_oracle_v2.lib.publications.analysis.trends import TemporalTrendAnalyzer
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.models import Dataset
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline


def print_section(title: str, width: int = 80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def main():
    """Run the complete Week 3 workflow example."""

    print_section("Week 3 Complete Workflow Example")

    # Step 1: Configure the pipeline
    print_section("Step 1: Configure Multi-Source Search Pipeline")

    config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_scholar=True,
        enable_citations=True,
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        max_results=20,
    )

    print("Configuration:")
    print(f"  - PubMed: {'Enabled' if config.enable_pubmed else 'Disabled'}")
    print(f"  - Google Scholar: {'Enabled' if config.enable_scholar else 'Disabled'}")
    print(f"  - Citation Analysis: {'Enabled' if config.enable_citations else 'Disabled'}")
    print(f"  - LLM Provider: {config.llm_provider}")
    print(f"  - Max Results: {config.max_results}")

    # Step 2: Define the dataset we're analyzing
    print_section("Step 2: Define Dataset")

    dataset = Dataset(
        title="The Cancer Genome Atlas (TCGA) Breast Cancer Dataset",
        description="Comprehensive multi-omics breast cancer dataset including genomic, transcriptomic, and clinical data",
        doi="10.1038/nature11412",
        publication_date=datetime(2012, 9, 23),
        url="https://portal.gdc.cancer.gov/projects/TCGA-BRCA",
    )

    print(f"Dataset: {dataset.title}")
    print(f"DOI: {dataset.doi}")
    print(f"Published: {dataset.publication_date.strftime('%Y-%m-%d')}")

    # Step 3: Search for citing papers
    print_section("Step 3: Multi-Source Search")

    pipeline = PublicationSearchPipeline(config)

    print("Searching for papers that cite this dataset...")
    print("  - Querying PubMed...")
    print("  - Querying Google Scholar...")
    print("  - Deduplicating results...")

    search_result = pipeline.search_dataset_citations(dataset, max_results=20)

    print("\nResults:")
    print(f"  - Total papers found: {len(search_result.publications)}")
    print(f"  - Sources used: {', '.join(search_result.metadata.get('sources_used', []))}")
    print(f"  - Duplicates removed: {search_result.metadata.get('duplicates_removed', 0)}")

    if search_result.publications:
        print("\nSample papers:")
        for i, pub in enumerate(search_result.publications[:3], 1):
            print(f"  {i}. {pub.title}")
            print(f"     Authors: {', '.join(a.name for a in pub.authors[:3])}")
            if pub.citation_count:
                print(f"     Citations: {pub.citation_count}")

    # Step 4: LLM Citation Analysis
    print_section("Step 4: LLM Citation Analysis")

    if search_result.citation_analyses:
        print(f"Analyzed {len(search_result.citation_analyses)} citations with LLM")

        # Show statistics
        reused_count = sum(1 for a in search_result.citation_analyses if a.dataset_reused)
        print("\nDataset Usage Statistics:")
        print(f"  - Papers that reused dataset: {reused_count}")
        print(f"  - Reuse rate: {reused_count/len(search_result.citation_analyses)*100:.1f}%")

        # Show usage types
        from collections import Counter

        usage_types = []
        for analysis in search_result.citation_analyses:
            if isinstance(analysis.usage_type, list):
                usage_types.extend(analysis.usage_type)
            else:
                usage_types.append(analysis.usage_type)

        usage_counts = Counter(usage_types)
        print("\nUsage Types:")
        for usage_type, count in usage_counts.most_common(5):
            print(f"  - {usage_type}: {count}")

        # Show biomarkers
        all_biomarkers = set()
        for analysis in search_result.citation_analyses:
            if analysis.biomarkers_studied:
                all_biomarkers.update(analysis.biomarkers_studied)

        print(f"\nBiomarkers Studied ({len(all_biomarkers)} unique):")
        for biomarker in sorted(list(all_biomarkers)[:10]):
            print(f"  - {biomarker}")
        if len(all_biomarkers) > 10:
            print(f"  ... and {len(all_biomarkers) - 10} more")

    # Step 5: Interactive Q&A
    print_section("Step 5: Interactive Q&A System")

    if search_result.citation_analyses:
        llm_client = LLMClient.create(config.llm_provider)
        qa_system = DatasetQASystem(llm_client)

        questions = [
            "What are the main biomarkers studied using this dataset?",
            "How has this dataset been used in cancer research?",
            "What are the key findings from papers using this dataset?",
        ]

        qa_results = []
        for question in questions:
            print(f"\nQ: {question}")
            result = qa_system.ask(dataset, question, search_result.citation_analyses)
            qa_results.append(result)
            print(f"A: {result['answer'][:200]}...")
            if result["evidence"]:
                print(f"   Based on {len(result['evidence'])} pieces of evidence")

    # Step 6: Temporal Trend Analysis
    print_section("Step 6: Temporal Trend Analysis")

    if search_result.citation_analyses and search_result.publications:
        trend_analyzer = TemporalTrendAnalyzer()
        trends = trend_analyzer.analyze_trends(
            dataset, search_result.citation_analyses, search_result.publications
        )

        print("Citation Timeline:")
        if trends.get("citation_timeline"):
            for period in sorted(trends["citation_timeline"].keys()):
                count = trends["citation_timeline"][period]["count"]
                print(f"  {period}: {count} citations")

        print("\nUsage Type Trends:")
        if trends.get("usage_type_trends"):
            for usage_type, data in list(trends["usage_type_trends"].items())[:3]:
                print(f"  {usage_type}: {data['trend']} (growth: {data['overall_growth_rate']:.1f}%)")

        print("\nImpact Trajectory:")
        if trends.get("impact_trajectory"):
            trajectory = trends["impact_trajectory"]
            print(f"  Overall trend: {trajectory['overall_trend']}")
            print(f"  Average citations/year: {trajectory['average_citations_per_year']:.1f}")
            if trajectory.get("peak_impact_year"):
                print(f"  Peak impact year: {trajectory['peak_impact_year']}")

    # Step 7: Biomarker Knowledge Graph
    print_section("Step 7: Biomarker Knowledge Graph")

    if search_result.citation_analyses and search_result.publications:
        graph = BiomarkerKnowledgeGraph()
        graph.build_from_analyses(dataset, search_result.citation_analyses, search_result.publications)

        biomarkers = graph.get_all_biomarkers()
        print(f"Knowledge graph contains {len(biomarkers)} biomarkers")

        # Show top biomarkers
        print("\nTop Biomarkers:")
        for i, biomarker in enumerate(biomarkers[:5], 1):
            connections = graph.get_biomarker_connections(biomarker)
            if connections:
                print(f"  {i}. {biomarker}")
                print(f"     - Papers: {len(connections['discovered_in_papers'])}")
                print(f"     - Diseases: {', '.join(connections['diseases'][:3])}")
                if len(connections["diseases"]) > 3:
                    print(f"       ... and {len(connections['diseases']) - 3} more")

    # Step 8: Generate Comprehensive Report
    print_section("Step 8: Generate Impact Report")

    if search_result.citation_analyses:
        report_gen = DatasetImpactReportGenerator()

        # Generate text report
        text_report = report_gen.generate_report(
            dataset,
            search_result.citation_analyses,
            trends=trends if "trends" in locals() else None,
            graph=graph if "graph" in locals() else None,
            qa_results=qa_results if "qa_results" in locals() else None,
            format="text",
        )

        print("\nText Report Preview (first 500 chars):")
        print("-" * 80)
        print(text_report[:500])
        print("...")
        print("-" * 80)

        # Save reports
        output_dir = Path("data/reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save text report
        text_path = output_dir / f"dataset_impact_{timestamp}.txt"
        text_path.write_text(text_report)
        print(f"\nFull text report saved to: {text_path}")

        # Save markdown report
        markdown_report = report_gen.generate_report(
            dataset,
            search_result.citation_analyses,
            trends=trends if "trends" in locals() else None,
            graph=graph if "graph" in locals() else None,
            format="markdown",
        )
        markdown_path = output_dir / f"dataset_impact_{timestamp}.md"
        markdown_path.write_text(markdown_report)
        print(f"Markdown report saved to: {markdown_path}")

        # Save JSON report
        import json

        json_report = report_gen.generate_report(
            dataset,
            search_result.citation_analyses,
            trends=trends if "trends" in locals() else None,
            graph=graph if "graph" in locals() else None,
            format="json",
        )
        json_path = output_dir / f"dataset_impact_{timestamp}.json"
        json_path.write_text(json.dumps(json_report, indent=2))
        print(f"JSON report saved to: {json_path}")

    # Summary
    print_section("Summary")

    print("Week 3 Workflow Complete!")
    print("\nWhat was demonstrated:")
    print("  [OK] Multi-source search (PubMed + Google Scholar)")
    print("  [OK] Intelligent deduplication")
    print("  [OK] LLM-powered citation analysis")
    print("  [OK] Interactive Q&A system")
    print("  [OK] Temporal trend analysis")
    print("  [OK] Biomarker knowledge graph")
    print("  [OK] Multi-format report generation")

    print("\nKey Metrics:")
    print(f"  - Papers found: {len(search_result.publications)}")
    if search_result.citation_analyses:
        print(f"  - Citations analyzed: {len(search_result.citation_analyses)}")
    if "trends" in locals():
        print(f"  - Time periods tracked: {len(trends.get('citation_timeline', {}))}")
    if "graph" in locals():
        print(f"  - Biomarkers in graph: {len(graph.get_all_biomarkers())}")

    print("\nNext Steps:")
    print("  - Review generated reports")
    print("  - Explore biomarker connections")
    print("  - Ask additional questions")
    print("  - Analyze temporal trends")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
