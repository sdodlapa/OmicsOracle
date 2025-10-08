"""
Example: How to use the integration layer in practice.

This demonstrates the complete workflow with all features.
"""

import asyncio

from omics_oracle_v2.integration import AnalysisClient, DataTransformer, MLClient, SearchClient


async def example_basic_search():
    """Example 1: Basic search."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Search")
    print("=" * 80)

    async with SearchClient(base_url="http://localhost:8000") as client:
        # Execute search
        results = await client.search(query="CRISPR gene editing", max_results=20)

        print(f"\nFound {results.metadata.total_results} papers")
        print(f"Query time: {results.metadata.query_time:.2f}s")
        print(f"Databases: {', '.join(results.metadata.databases_searched)}")

        # Display results
        print("\nTop 5 results:")
        for i, pub in enumerate(results.results[:5], 1):
            print(f"\n{i}. {pub.title}")
            print(f"   Authors: {', '.join(pub.authors[:3])}")
            print(
                f"   Year: {pub.year} | Citations: {pub.citation_metrics.count if pub.citation_metrics else 'N/A'}"
            )
            if pub.quality_score:
                print(f"   Quality: {pub.quality_score.overall:.2f}")


async def example_llm_analysis():
    """Example 2: LLM Analysis (NEW FEATURE!)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: LLM Analysis (Previously Missing!)")
    print("=" * 80)

    async with SearchClient() as search:
        async with AnalysisClient() as analysis:
            # First search
            results = await search.search("cancer immunotherapy", max_results=10)

            # Analyze with LLM
            llm_analysis = await analysis.analyze_with_llm(
                query="cancer immunotherapy", results=results.results, analysis_type="overview"
            )

            print("\nOverview:")
            print(llm_analysis.overview)

            print("\nKey Findings:")
            for finding in llm_analysis.key_findings:
                print(f"  - {finding}")

            print("\nResearch Gaps:")
            for gap in llm_analysis.research_gaps:
                print(f"  - {gap}")

            print("\nRecommendations:")
            for rec in llm_analysis.recommendations:
                print(f"  - {rec}")

            print(f"\nConfidence: {llm_analysis.confidence:.2f}")
            print(f"Model: {llm_analysis.model_used}")


async def example_qa():
    """Example 3: Q&A over papers (NEW FEATURE!)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Q&A Over Papers (Previously Missing!)")
    print("=" * 80)

    async with SearchClient() as search:
        async with AnalysisClient() as analysis:
            # Search
            results = await search.search("mRNA vaccine delivery", max_results=10)

            # Ask questions
            questions = [
                "What delivery mechanisms are most effective?",
                "What are the main challenges?",
                "Which lipid nanoparticles show best results?",
            ]

            for question in questions:
                print(f"\nQ: {question}")

                answer = await analysis.ask_question(question=question, context=results.results)

                print(f"A: {answer.answer}")
                print(f"   Sources: {', '.join(answer.sources[:3])}")
                print(f"   Confidence: {answer.confidence:.2f}")


async def example_trends_and_network():
    """Example 4: Trend analysis and citation network."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Trends & Citation Network")
    print("=" * 80)

    async with SearchClient() as search:
        async with AnalysisClient() as analysis:
            # Search
            results = await search.search("deep learning genomics", max_results=50)

            # Trend analysis
            print("\nTrend Analysis:")
            trends = await analysis.get_trends(results.results)

            print(f"  Growth rate: {trends.growth_rate:.1f}% per year")
            print(f"  Peak year: {trends.peak_year}")
            print(f"  Predicted in 5 years: {trends.prediction_5yr} papers")

            print(f"\n  Recent trends:")
            for point in trends.trends[-5:]:
                print(f"    {point.year}: {point.count} papers (avg citations: {point.citation_avg:.1f})")

            # Citation network
            print("\nCitation Network:")
            network = await analysis.get_network(results=results.results, min_citations=10)

            print(f"  Nodes: {len(network.nodes)}")
            print(f"  Edges: {len(network.edges)}")
            print(f"  Clusters: {len(network.clusters)}")

            if network.clusters:
                print(f"\n  Cluster sizes:")
                for cluster_id, papers in list(network.clusters.items())[:3]:
                    print(f"    Cluster {cluster_id}: {len(papers)} papers")


async def example_recommendations():
    """Example 5: ML recommendations (NEW FEATURE!)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: ML Recommendations (Previously Missing!)")
    print("=" * 80)

    async with SearchClient() as search:
        async with MLClient() as ml:
            # Search for seed papers
            results = await search.search("AlphaFold protein structure", max_results=5)

            # Get recommendations based on top papers
            seed_papers = [pub.id for pub in results.results[:3]]

            print(f"\nSeed papers:")
            for i, pub in enumerate(results.results[:3], 1):
                print(f"  {i}. {pub.title[:80]}...")

            print(f"\nGetting recommendations...")
            recs = await ml.get_recommendations(seed_papers=seed_papers, count=10)

            print(f"\nRecommended papers:")
            for i, rec in enumerate(recs.recommendations, 1):
                print(f"\n  {i}. {rec.publication.title}")
                print(f"     Score: {rec.score:.2f}")
                print(f"     Reason: {rec.reason}")


async def example_citation_prediction():
    """Example 6: Citation prediction (NEW FEATURE!)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Citation Prediction (Previously Missing!)")
    print("=" * 80)

    async with SearchClient() as search:
        async with MLClient() as ml:
            # Search
            results = await search.search("transformer neural networks", max_results=5)

            # Predict citations for top papers
            for i, pub in enumerate(results.results[:3], 1):
                print(f"\n{i}. {pub.title[:80]}...")
                print(
                    f"   Current citations: {pub.citation_metrics.count if pub.citation_metrics else 'N/A'}"
                )

                prediction = await ml.predict_citations(pub_id=pub.id, years_ahead=5)

                print(f"   Predicted in 5 years: {prediction['predicted_count']}")
                print(f"   Confidence: {prediction['confidence']:.2f}")


async def example_export():
    """Example 7: Export in multiple formats."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Export Results")
    print("=" * 80)

    async with SearchClient() as client:
        # Search
        results = await client.search("single cell RNA-seq", max_results=10)

        # Transform to different formats
        transformer = DataTransformer()

        # CSV
        csv_data = transformer.to_csv(results)
        print(f"\nCSV export: {len(csv_data)} bytes")
        print("First 200 chars:")
        print(csv_data[:200])

        # BibTeX
        bibtex = transformer.to_bibtex(results.results)
        print(f"\nBibTeX export: {len(bibtex)} bytes")
        print("First entry:")
        print(bibtex.split("\n\n")[0])

        # JSON
        json_data = transformer.to_json(results)
        print(f"\nJSON export: {len(json_data)} bytes")

        # Streamlit format
        streamlit_data = transformer.to_streamlit(results)
        print(f"\nStreamlit format: {len(streamlit_data['results'])} results")

        # React format
        react_data = transformer.to_react(results)
        print(f"React format: {len(react_data['results'])} results")


async def example_multi_frontend():
    """Example 8: Same data, multiple frontends."""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Multi-Frontend Support")
    print("=" * 80)

    async with SearchClient() as client:
        # Single search
        results = await client.search("COVID-19 vaccines", max_results=10)

        transformer = DataTransformer()

        # Same data, different formats
        print("\n1. For Streamlit Dashboard:")
        streamlit_data = transformer.to_streamlit(results)
        print(f"   Format: dict with 'results', 'metadata', 'aggregated_biomarkers'")
        print(f"   Fields: {list(streamlit_data['results'][0].keys())}")

        print("\n2. For React Admin Dashboard:")
        react_data = transformer.to_react(results)
        print(f"   Format: camelCase for JavaScript")
        print(f"   Fields: {list(react_data['results'][0].keys())}")

        print("\n3. For Vue Mobile App:")
        vue_data = transformer.to_vue(results)
        print(f"   Format: Vue-friendly structure")
        print(f"   Fields: {list(vue_data['results'][0].keys())}")

        print("\n[OK] Same backend call, three different frontends!")


async def example_complete_workflow():
    """Example 9: Complete research workflow."""
    print("\n" + "=" * 80)
    print("EXAMPLE 9: Complete Research Workflow")
    print("=" * 80)

    async with SearchClient() as search:
        async with AnalysisClient() as analysis:
            async with MLClient() as ml:
                # 1. Search
                print("\nStep 1: Searching...")
                results = await search.search(
                    query="CRISPR off-target effects",
                    max_results=30,
                    search_mode="hybrid",
                    filters={"year_min": 2020},
                )
                print(f"  Found {results.metadata.total_results} papers")

                # 2. Get overview
                print("\nStep 2: Getting LLM overview...")
                overview = await analysis.analyze_with_llm(
                    query="CRISPR off-target effects", results=results.results[:10]
                )
                print(f"  {overview.overview[:200]}...")

                # 3. Ask specific questions
                print("\nStep 3: Asking questions...")
                answer = await analysis.ask_question(
                    question="What methods detect off-target effects?", context=results.results
                )
                print(f"  Answer: {answer.answer[:200]}...")

                # 4. Analyze trends
                print("\nStep 4: Analyzing trends...")
                trends = await analysis.get_trends(results.results)
                print(f"  Growth: {trends.growth_rate:.1f}% per year")

                # 5. Get recommendations
                print("\nStep 5: Getting recommendations...")
                top_papers = [pub.id for pub in results.results[:3]]
                recs = await ml.get_recommendations(seed_papers=top_papers, count=5)
                print(f"  Found {len(recs.recommendations)} similar papers")

                # 6. Generate report
                print("\nStep 6: Generating comprehensive report...")
                report = await analysis.generate_report(
                    query="CRISPR off-target effects", results=results.results, include_analysis=True
                )
                print(f"  Report: {len(report)} characters")

                # 7. Export
                print("\nStep 7: Exporting results...")
                transformer = DataTransformer()
                csv = transformer.to_csv(results)
                bibtex = transformer.to_bibtex(results.results)
                print(f"  CSV: {len(csv)} bytes")
                print(f"  BibTeX: {len(bibtex)} bytes")

                print("\n[OK] Complete workflow executed!")


async def main():
    """Run all examples."""
    examples = [
        example_basic_search,
        example_llm_analysis,
        example_qa,
        example_trends_and_network,
        example_recommendations,
        example_citation_prediction,
        example_export,
        example_multi_frontend,
        example_complete_workflow,
    ]

    print("\n" + "=" * 80)
    print("OMICSORACLE INTEGRATION LAYER - EXAMPLES")
    print("=" * 80)
    print("\nThese examples demonstrate:")
    print("  1. Basic search")
    print("  2. LLM analysis (NEW!)")
    print("  3. Q&A over papers (NEW!)")
    print("  4. Trends & citation networks")
    print("  5. ML recommendations (NEW!)")
    print("  6. Citation predictions (NEW!)")
    print("  7. Export formats")
    print("  8. Multi-frontend support")
    print("  9. Complete workflow")

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\n[ERROR] Error in {example.__name__}: {e}")
            print("(This is expected if backend is not running)")


if __name__ == "__main__":
    # Make sure backend is running on http://localhost:8000
    print("\n[WARNING] Make sure the backend is running:")
    print("    ./start_omics_oracle.sh")
    print()

    asyncio.run(main())
