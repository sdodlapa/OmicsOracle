"""
Visualization Demo Script

Demonstrates all visualization capabilities for Week 4.
"""

from pathlib import Path

from omics_oracle_v2.lib.visualizations import ColorSchemes, ExportOptions, VisualizationConfig
from omics_oracle_v2.lib.visualizations.network import CitationNetworkVisualizer, visualize_knowledge_graph
from omics_oracle_v2.lib.visualizations.trends import TrendVisualizer, visualize_citation_timeline


def create_sample_knowledge_graph():
    """Create sample knowledge graph for demo."""
    return {
        "nodes": [
            {
                "id": "CA-125",
                "type": "biomarker",
                "label": "CA-125 (Ovarian Cancer Marker)",
                "citations": 850,
                "impact": 9.2,
            },
            {
                "id": "HE4",
                "type": "biomarker",
                "label": "HE4 (Human Epididymis Protein 4)",
                "citations": 620,
                "impact": 8.5,
            },
            {
                "id": "PSA",
                "type": "biomarker",
                "label": "PSA (Prostate-Specific Antigen)",
                "citations": 1200,
                "impact": 9.8,
            },
            {
                "id": "study_2020",
                "type": "paper",
                "label": "Smith et al. (2020): CA-125 Diagnostic Value",
                "citations": 145,
                "impact": 7.8,
            },
            {
                "id": "study_2021",
                "type": "paper",
                "label": "Jones et al. (2021): HE4 in Ovarian Cancer",
                "citations": 98,
                "impact": 6.9,
            },
            {
                "id": "study_2022",
                "type": "paper",
                "label": "Brown et al. (2022): Combined Biomarkers",
                "citations": 76,
                "impact": 7.2,
            },
            {
                "id": "ovarian_cancer",
                "type": "disease",
                "label": "Ovarian Cancer",
                "citations": 2500,
                "impact": 10.0,
            },
            {
                "id": "prostate_cancer",
                "type": "disease",
                "label": "Prostate Cancer",
                "citations": 3200,
                "impact": 10.0,
            },
            {
                "id": "dataset_tcga",
                "type": "dataset",
                "label": "TCGA Ovarian Cancer Dataset",
                "citations": 450,
                "impact": 8.9,
            },
        ],
        "edges": [
            {
                "source": "study_2020",
                "target": "CA-125",
                "relationship": "studies",
                "strength": 0.95,
            },
            {
                "source": "study_2021",
                "target": "HE4",
                "relationship": "studies",
                "strength": 0.92,
            },
            {
                "source": "study_2022",
                "target": "CA-125",
                "relationship": "studies",
                "strength": 0.88,
            },
            {
                "source": "study_2022",
                "target": "HE4",
                "relationship": "studies",
                "strength": 0.85,
            },
            {
                "source": "CA-125",
                "target": "ovarian_cancer",
                "relationship": "associated_with",
                "strength": 0.98,
            },
            {
                "source": "HE4",
                "target": "ovarian_cancer",
                "relationship": "associated_with",
                "strength": 0.94,
            },
            {
                "source": "PSA",
                "target": "prostate_cancer",
                "relationship": "associated_with",
                "strength": 0.99,
            },
            {
                "source": "dataset_tcga",
                "target": "ovarian_cancer",
                "relationship": "contains_data_for",
                "strength": 0.90,
            },
            {
                "source": "study_2020",
                "target": "dataset_tcga",
                "relationship": "uses",
                "strength": 0.75,
            },
        ],
    }


def create_sample_timeline():
    """Create sample citation timeline for demo."""
    return {
        "dates": [
            "2020-01",
            "2020-04",
            "2020-07",
            "2020-10",
            "2021-01",
            "2021-04",
            "2021-07",
            "2021-10",
            "2022-01",
            "2022-04",
            "2022-07",
            "2022-10",
        ],
        "counts": [25, 42, 68, 95, 130, 175, 145, 210, 285, 310, 395, 450],
        "peaks": [
            {"date": "2021-07", "count": 175, "reason": "ASCO Conference"},
            {"date": "2022-07", "count": 395, "reason": "Nature Review Publication"},
        ],
        "forecast": {
            "dates": ["2023-01", "2023-04", "2023-07"],
            "values": [520, 580, 630],
        },
    }


def create_sample_usage_evolution():
    """Create sample usage evolution for demo."""
    return {
        "dates": [
            "2020-Q1",
            "2020-Q2",
            "2020-Q3",
            "2020-Q4",
            "2021-Q1",
            "2021-Q2",
            "2021-Q3",
            "2021-Q4",
            "2022-Q1",
            "2022-Q2",
        ],
        "by_type": {
            "diagnostic": [15, 28, 42, 55, 70, 88, 95, 110, 135, 155],
            "prognostic": [8, 14, 20, 28, 38, 45, 40, 55, 72, 85],
            "therapeutic": [2, 8, 12, 18, 25, 35, 28, 42, 58, 68],
            "research": [5, 8, 12, 18, 25, 32, 38, 48, 62, 78],
        },
    }


def create_sample_impact_trajectory():
    """Create sample impact trajectory for demo."""
    return {
        "dates": [
            "2020-01",
            "2020-04",
            "2020-07",
            "2020-10",
            "2021-01",
            "2021-04",
            "2021-07",
            "2021-10",
            "2022-01",
            "2022-04",
        ],
        "citation_counts": [25, 42, 68, 95, 130, 175, 145, 210, 285, 310],
        "impact_scores": [5.2, 5.8, 6.5, 7.1, 7.8, 8.5, 8.2, 9.0, 9.5, 9.8],
        "growth_rates": [0.0, 0.68, 0.62, 0.40, 0.37, 0.35, -0.17, 0.45, 0.36, 0.09],
    }


def demo_network_visualization():
    """Demonstrate network visualization features."""
    print("\n" + "=" * 80)
    print("CITATION NETWORK VISUALIZATION DEMO")
    print("=" * 80)

    graph_data = create_sample_knowledge_graph()

    # 1. Basic visualization
    print("\n1. Creating basic citation network...")
    viz = CitationNetworkVisualizer()
    viz.create(graph_data)
    print(f"   OK Created network with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")

    # 2. Different layouts
    print("\n2. Testing different layouts...")
    layouts = ["spring", "circular", "kamada_kawai"]
    for layout in layouts:
        viz.create(graph_data, layout=layout)
        print(f"   OK Created {layout} layout")

    # 3. Network statistics
    print("\n3. Calculating network statistics...")
    stats = viz.get_network_stats()
    print(f"   OK Nodes: {stats['num_nodes']}")
    print(f"   OK Edges: {stats['num_edges']}")
    print(f"   OK Density: {stats['density']:.3f}")
    print(f"   OK Average Degree: {stats['avg_degree']:.2f}")
    print(f"   OK Connected Components: {stats['connected_components']}")

    if stats.get("top_nodes_by_centrality"):
        print("\n   Top nodes by centrality:")
        for node_info in stats["top_nodes_by_centrality"][:3]:
            print(f"     - {node_info['node']}: {node_info['centrality']:.3f}")

    # 4. Color schemes
    print("\n4. Testing color schemes...")
    schemes = ["default", "colorblind", "high_contrast"]
    for scheme in schemes:
        config = VisualizationConfig(color_scheme=scheme)
        viz_scheme = CitationNetworkVisualizer(config)
        viz_scheme.create(graph_data)
        print(f"   OK Created visualization with {scheme} color scheme")

    # 5. Export options
    print("\n5. Exporting visualizations...")
    output_dir = Path("data/visualizations")
    output_dir.mkdir(parents=True, exist_ok=True)

    # HTML export
    html_options = ExportOptions(format="html", filename="demo_network.html")
    html_path = viz.export(html_options)
    print(f"   OK Exported HTML: {html_path}")

    # JSON export
    json_options = ExportOptions(format="json", filename="demo_network.json")
    json_path = viz.export(json_options)
    print(f"   OK Exported JSON: {json_path}")

    # 6. Convenience function
    print("\n6. Using convenience function...")
    visualize_knowledge_graph(graph_data, layout="spring", export_path="demo_graph_quick.html")
    print("   OK Created and exported using convenience function")


def demo_trend_visualization():
    """Demonstrate trend visualization features."""
    print("\n" + "=" * 80)
    print("TREND VISUALIZATION DEMO")
    print("=" * 80)

    # 1. Citation timeline
    print("\n1. Creating citation timeline...")
    timeline_data = create_sample_timeline()

    viz = TrendVisualizer()
    viz.create({"citation_timeline": timeline_data})
    print(f"   OK Created timeline with {len(timeline_data['dates'])} data points")

    # 2. Different chart types
    print("\n2. Testing different chart types...")
    chart_types = ["line", "area", "bar"]
    for chart_type in chart_types:
        viz.create({"citation_timeline": timeline_data}, chart_type=chart_type)
        print(f"   OK Created {chart_type} chart")

    # 3. Peak highlighting
    print("\n3. Highlighting peaks...")
    viz.create({"citation_timeline": timeline_data}, show_peaks=True)
    print(f"   OK Highlighted {len(timeline_data['peaks'])} peak periods")
    for peak in timeline_data["peaks"]:
        print(f"     - {peak['date']}: {peak['count']} citations ({peak['reason']})")

    # 4. Forecast
    print("\n4. Adding forecast...")
    viz.create({"citation_timeline": timeline_data}, show_forecast=True)
    forecast = timeline_data["forecast"]
    print(f"   OK Added forecast for {len(forecast['dates'])} periods")

    # 5. Usage evolution (stacked)
    print("\n5. Creating usage evolution chart...")
    usage_data = create_sample_usage_evolution()
    viz.create({"usage_evolution": usage_data}, chart_type="area")
    print(f"   OK Created stacked chart with {len(usage_data['by_type'])} usage types")

    # 6. Impact trajectory
    print("\n6. Creating impact trajectory...")
    impact_data = create_sample_impact_trajectory()
    viz.create({"impact_trajectory": impact_data})
    print("   OK Created dual-axis chart (citations + impact score)")

    # 7. Export options
    print("\n7. Exporting visualizations...")

    # Timeline HTML
    html_options = ExportOptions(format="html", filename="demo_timeline.html")
    html_path = viz.export(html_options)
    print(f"   OK Exported timeline HTML: {html_path}")

    # Usage evolution
    viz.create({"usage_evolution": usage_data}, chart_type="area")
    usage_options = ExportOptions(format="html", filename="demo_usage.html")
    usage_path = viz.export(usage_options)
    print(f"   OK Exported usage HTML: {usage_path}")

    # 8. Convenience function
    print("\n8. Using convenience function...")
    visualize_citation_timeline(timeline_data, chart_type="area", export_path="demo_timeline_quick.html")
    print("   OK Created and exported using convenience function")


def demo_customization():
    """Demonstrate customization options."""
    print("\n" + "=" * 80)
    print("CUSTOMIZATION OPTIONS DEMO")
    print("=" * 80)

    graph_data = create_sample_knowledge_graph()
    timeline_data = create_sample_timeline()

    # 1. Themes
    print("\n1. Testing themes...")
    themes = ["plotly_white", "plotly_dark", "seaborn"]
    for theme in themes:
        config = VisualizationConfig(theme=theme)

        # Network
        viz_net = CitationNetworkVisualizer(config)
        viz_net.create(graph_data)

        # Trends
        viz_trend = TrendVisualizer(config)
        viz_trend.create({"citation_timeline": timeline_data})

        print(f"   OK Applied {theme} theme to both visualizations")

    # 2. Custom dimensions
    print("\n2. Testing custom dimensions...")
    sizes = [(800, 600), (1200, 800), (1600, 1200)]
    for width, height in sizes:
        config = VisualizationConfig(width=width, height=height)
        viz = CitationNetworkVisualizer(config)
        viz.create(graph_data)
        print(f"   OK Created {width}x{height} visualization")

    # 3. Color schemes
    print("\n3. Testing color schemes...")
    print("\n   Available schemes:")
    for scheme_name in ["default", "colorblind", "high_contrast"]:
        scheme = ColorSchemes.get_scheme(scheme_name)
        print(f"\n   {scheme_name.upper()}:")
        for key, color in list(scheme.items())[:3]:
            print(f"     - {key}: {color}")

    # 4. Font customization
    print("\n4. Testing font customization...")
    config = VisualizationConfig(font_family="Helvetica, Arial, sans-serif", font_size=14)
    viz = CitationNetworkVisualizer(config)
    viz.create(graph_data)
    print("   OK Applied custom font family and size")


def demo_integration_example():
    """Demonstrate integration with Week 3 analytics."""
    print("\n" + "=" * 80)
    print("INTEGRATION WITH WEEK 3 ANALYTICS")
    print("=" * 80)

    print("\nThis demo shows how Week 4 visualizations integrate with Week 3 analytics:")

    print("\n1. Knowledge Graph Analysis -> Network Visualization")
    print("   - Week 3: KnowledgeGraphAnalyzer.analyze(papers)")
    print("   - Week 4: visualize_knowledge_graph(graph_data)")
    print("   OK Interactive network showing citation relationships")

    print("\n2. Trend Analysis -> Timeline Visualization")
    print("   - Week 3: TrendAnalyzer.analyze_trends(papers)")
    print("   - Week 4: visualize_citation_timeline(trend_data)")
    print("   OK Interactive charts showing citation evolution")

    print("\n3. Q&A System -> Custom Visualizations")
    print("   - Week 3: QASystem.answer(question, papers)")
    print("   - Week 4: Create charts from Q&A results")
    print("   OK Data-driven visual answers")

    print("\n4. Report Generation -> Dashboard")
    print("   - Week 3: ReportGenerator.generate_report(papers)")
    print("   - Week 4: Dashboard displays all visualizations")
    print("   OK Complete interactive report interface")


def main():
    """Run all visualization demos."""
    print("\n" + "=" * 80)
    print("OMICSORACLE VISUALIZATION DEMO")
    print("Week 4: Day 21 - Citation Network & Trend Visualization")
    print("=" * 80)

    try:
        # Run demos
        demo_network_visualization()
        demo_trend_visualization()
        demo_customization()
        demo_integration_example()

        print("\n" + "=" * 80)
        print("DEMO COMPLETE!")
        print("=" * 80)
        print("\nGenerated visualizations saved to: data/visualizations/")
        print("\nFiles created:")
        output_dir = Path("data/visualizations")
        if output_dir.exists():
            for file in sorted(output_dir.glob("demo_*.html")):
                print(f"  OK {file.name}")

        print("\nNext steps:")
        print("  1. Open HTML files in browser for interactive exploration")
        print("  2. Continue to Day 22: Additional visualizations")
        print("  3. Integrate with Week 3 analytics pipeline")

    except Exception as e:
        print(f"\nERROR Error during demo: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
