"""
Dataset impact report generation.

Synthesizes Q&A, trends, and knowledge graph data into comprehensive reports.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from omics_oracle_v2.lib.search_engines.citations.models import Publication

logger = logging.getLogger(__name__)


class DatasetImpactReportGenerator:
    """
    Generate comprehensive impact reports for datasets.

    Combines Q&A results, trend analysis, and knowledge graphs into reports.

    Example:
        >>> generator = DatasetImpactReportGenerator()
        >>> report = generator.generate_report(
        ...     dataset=dataset_pub,
        ...     citation_analyses=analyses,
        ...     trends=trend_data,
        ...     graph=knowledge_graph,
        ...     qa_results=qa_answers
        ... )
        >>> print(report["text"])
    """

    def __init__(self):
        """Initialize report generator."""

    def generate_report(
        self,
        dataset: Publication,
        citation_analyses: List,
        trends: Optional[Dict] = None,
        graph: Optional[object] = None,
        qa_results: Optional[List[Dict]] = None,
        format: str = "text",
    ) -> Dict:
        """
        Generate comprehensive impact report.

        Args:
            dataset: Dataset publication
            citation_analyses: List of citation analyses
            trends: Optional trend analysis results
            graph: Optional knowledge graph
            qa_results: Optional Q&A results
            format: Output format (text, markdown, json)

        Returns:
            Report dictionary with content and metadata
        """
        logger.info(f"Generating impact report for: {dataset.title}")

        # Build report sections
        sections = {
            "executive_summary": self._generate_executive_summary(dataset, citation_analyses, trends, graph),
            "dataset_overview": self._generate_dataset_overview(dataset),
            "usage_statistics": self._generate_usage_statistics(citation_analyses),
            "temporal_trends": self._generate_trends_section(trends) if trends else None,
            "biomarker_discoveries": self._generate_biomarker_section(graph) if graph else None,
            "key_findings": self._generate_key_findings(citation_analyses, trends, graph),
            "qa_insights": self._format_qa_results(qa_results) if qa_results else None,
        }

        # Format report
        if format == "text":
            content = self._format_as_text(sections)
        elif format == "markdown":
            content = self._format_as_markdown(sections)
        elif format == "json":
            content = json.dumps(sections, indent=2, default=str)
        else:
            content = self._format_as_text(sections)

        return {
            "content": content,
            "format": format,
            "generated_at": datetime.now().isoformat(),
            "dataset_title": dataset.title,
            "sections": sections,
        }

    def _generate_executive_summary(
        self, dataset: Publication, citation_analyses: List, trends: Optional[Dict], graph: Optional[object]
    ) -> str:
        """Generate executive summary."""
        lines = []

        # Basic stats
        total_citations = len(citation_analyses)
        reused = sum(1 for a in citation_analyses if a.dataset_reused)
        reuse_rate = (reused / total_citations * 100) if total_citations > 0 else 0

        lines.append(f"Dataset: {dataset.title}")
        lines.append(f"Total Citations: {total_citations}")
        lines.append(f"Confirmed Reuse: {reused} ({reuse_rate:.1f}%)")

        # Biomarkers
        if graph:
            stats = graph.get_statistics()
            lines.append(f"Biomarkers Discovered: {stats['total_biomarkers']}")
            lines.append(f"Validated Biomarkers: {stats['validated_biomarkers']}")

        # Trends
        if trends and "impact_trajectory" in trends:
            trajectory = trends["impact_trajectory"]
            if "overall_growth_rate" in trajectory:
                lines.append(f"Impact Growth Rate: {trajectory['overall_growth_rate']:.1f}%/year")

        return "\n".join(lines)

    def _generate_dataset_overview(self, dataset: Publication) -> str:
        """Generate dataset overview section."""
        lines = ["Title: {}".format(dataset.title)]

        if dataset.authors:
            authors = ", ".join(dataset.authors[:3])
            if len(dataset.authors) > 3:
                authors += " et al."
            lines.append(f"Authors: {authors}")

        if dataset.publication_date:
            lines.append(f"Publication Date: {dataset.publication_date.strftime('%Y-%m-%d')}")

        if dataset.doi:
            lines.append(f"DOI: {dataset.doi}")

        if dataset.abstract:
            lines.append(f"\nAbstract:\n{dataset.abstract[:500]}...")

        return "\n".join(lines)

    def _generate_usage_statistics(self, citation_analyses: List) -> Dict:
        """Generate usage statistics."""
        total = len(citation_analyses)
        if total == 0:
            return {}

        # Count usage types
        usage_types = {}
        for analysis in citation_analyses:
            if analysis.dataset_reused:
                usage_type = analysis.usage_type
                usage_types[usage_type] = usage_types.get(usage_type, 0) + 1

        # Count domains
        domains = {}
        for analysis in citation_analyses:
            if analysis.application_domain:
                domains[analysis.application_domain] = domains.get(analysis.application_domain, 0) + 1

        # Count validation
        validated = sum(1 for a in citation_analyses if a.validation_status == "validated")

        return {
            "total_citations": total,
            "confirmed_reuse": sum(1 for a in citation_analyses if a.dataset_reused),
            "usage_types": usage_types,
            "application_domains": domains,
            "validated_studies": validated,
        }

    def _generate_trends_section(self, trends: Dict) -> str:
        """Generate temporal trends section."""
        lines = ["Temporal Trends:"]

        # Citation timeline
        if "citation_timeline" in trends:
            timeline = trends["citation_timeline"]
            if timeline:
                years = sorted(timeline.keys())
                lines.append(f"\nActive Years: {min(years)} - {max(years)}")
                # Find peak year by total_citations in each year's data
                peak_year = max(timeline, key=lambda y: timeline[y].get("total_citations", 0))
                lines.append(f"Peak Year: {peak_year}")

        # Usage trends
        if "usage_type_trends" in trends:
            usage_type_trends = trends["usage_type_trends"]
            if "trend_directions" in usage_type_trends:
                for usage_type, trend in usage_type_trends["trend_directions"].items():
                    lines.append(f"{usage_type}: {trend}")

        # Impact trajectory
        if "impact_trajectory" in trends:
            trajectory = trends["impact_trajectory"]
            if "overall_growth_rate" in trajectory:
                lines.append(f"\nGrowth Rate: {trajectory['overall_growth_rate']:.1f}%/year")

        return "\n".join(lines)

    def _generate_biomarker_section(self, graph: object) -> str:
        """Generate biomarker discoveries section."""
        if not hasattr(graph, "get_statistics"):
            return ""

        stats = graph.get_statistics()

        lines = [
            "Biomarker Discoveries:",
            f"Total Biomarkers: {stats['total_biomarkers']}",
            f"Validated: {stats['validated_biomarkers']}",
        ]

        # Top biomarkers
        if hasattr(graph, "get_validated_biomarkers"):
            validated = graph.get_validated_biomarkers()
            if validated:
                lines.append("\nTop Validated Biomarkers:")
                for bm in sorted(validated, key=lambda b: b.citation_count, reverse=True)[:5]:
                    lines.append(f"  - {bm.name} ({bm.citation_count} citations)")

        return "\n".join(lines)

    def _generate_key_findings(
        self, citation_analyses: List, trends: Optional[Dict], graph: Optional[object]
    ) -> List[str]:
        """Generate key findings."""
        findings = []

        # Reuse rate finding
        total = len(citation_analyses)
        reused = sum(1 for a in citation_analyses if a.dataset_reused)
        reuse_rate = (reused / total * 100) if total > 0 else 0

        if reuse_rate > 70:
            findings.append(f"High reuse rate ({reuse_rate:.1f}%) indicates strong dataset utility")
        elif reuse_rate > 40:
            findings.append(f"Moderate reuse rate ({reuse_rate:.1f}%) shows consistent dataset usage")

        # Usage diversity
        usage_types = set()
        for a in citation_analyses:
            if a.dataset_reused:
                usage_types.add(a.usage_type)

        if len(usage_types) > 5:
            findings.append(f"Diverse usage across {len(usage_types)} different analysis types")

        # Biomarker discoveries
        if graph and hasattr(graph, "get_statistics"):
            stats = graph.get_statistics()
            if stats["total_biomarkers"] > 10:
                findings.append(f"Enabled discovery of {stats['total_biomarkers']} biomarkers")
            if stats["validated_biomarkers"] > 5:
                findings.append(f"{stats['validated_biomarkers']} biomarkers have been validated")

        # Growth trend
        if trends and "impact_trajectory" in trends:
            trajectory = trends["impact_trajectory"]
            if trajectory.get("overall_growth_rate", 0) > 20:
                findings.append("Strong growth in dataset impact over time")

        return findings

    def _format_qa_results(self, qa_results: List[Dict]) -> str:
        """Format Q&A results."""
        if not qa_results:
            return ""

        lines = ["Q&A Insights:"]
        for result in qa_results:
            lines.append(f"\nQ: {result.get('question', 'Unknown')}")
            lines.append(f"A: {result.get('answer', 'No answer')}")
            if result.get("evidence"):
                lines.append(f"   (Based on {len(result['evidence'])} citations)")

        return "\n".join(lines)

    def _format_as_text(self, sections: Dict) -> str:
        """Format report as plain text."""
        lines = [
            "=" * 80,
            "DATASET IMPACT REPORT",
            "=" * 80,
            "",
        ]

        # Executive Summary
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(sections["executive_summary"])
        lines.append("")

        # Dataset Overview
        lines.append("DATASET OVERVIEW")
        lines.append("-" * 80)
        lines.append(sections["dataset_overview"])
        lines.append("")

        # Usage Statistics
        if sections["usage_statistics"]:
            lines.append("USAGE STATISTICS")
            lines.append("-" * 80)
            stats = sections["usage_statistics"]
            lines.append(f"Total Citations: {stats.get('total_citations', 0)}")
            lines.append(f"Confirmed Reuse: {stats.get('confirmed_reuse', 0)}")

            if stats.get("usage_types"):
                lines.append("\nUsage Types:")
                for usage_type, count in sorted(
                    stats["usage_types"].items(), key=lambda x: x[1], reverse=True
                ):
                    lines.append(f"  - {usage_type}: {count}")

            if stats.get("application_domains"):
                lines.append("\nApplication Domains:")
                for domain, count in sorted(
                    stats["application_domains"].items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    lines.append(f"  - {domain}: {count}")
            lines.append("")

        # Temporal Trends
        if sections["temporal_trends"]:
            lines.append("TEMPORAL TRENDS")
            lines.append("-" * 80)
            lines.append(sections["temporal_trends"])
            lines.append("")

        # Biomarker Discoveries
        if sections["biomarker_discoveries"]:
            lines.append("BIOMARKER DISCOVERIES")
            lines.append("-" * 80)
            lines.append(sections["biomarker_discoveries"])
            lines.append("")

        # Key Findings
        if sections["key_findings"]:
            lines.append("KEY FINDINGS")
            lines.append("-" * 80)
            for i, finding in enumerate(sections["key_findings"], 1):
                lines.append(f"{i}. {finding}")
            lines.append("")

        # Q&A Insights
        if sections["qa_insights"]:
            lines.append("Q&A INSIGHTS")
            lines.append("-" * 80)
            lines.append(sections["qa_insights"])
            lines.append("")

        lines.append("=" * 80)
        lines.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _format_as_markdown(self, sections: Dict) -> str:
        """Format report as Markdown."""
        lines = [
            "# Dataset Impact Report",
            "",
            "## Executive Summary",
            "",
            sections["executive_summary"],
            "",
            "## Dataset Overview",
            "",
            sections["dataset_overview"],
            "",
        ]

        # Usage Statistics
        if sections["usage_statistics"]:
            lines.append("## Usage Statistics")
            lines.append("")
            stats = sections["usage_statistics"]
            lines.append(f"- **Total Citations:** {stats.get('total_citations', 0)}")
            lines.append(f"- **Confirmed Reuse:** {stats.get('confirmed_reuse', 0)}")

            if stats.get("usage_types"):
                lines.append("\n### Usage Types")
                for usage_type, count in sorted(
                    stats["usage_types"].items(), key=lambda x: x[1], reverse=True
                ):
                    lines.append(f"- {usage_type}: {count}")

            lines.append("")

        # Temporal Trends
        if sections["temporal_trends"]:
            lines.append("## Temporal Trends")
            lines.append("")
            lines.append(sections["temporal_trends"])
            lines.append("")

        # Biomarker Discoveries
        if sections["biomarker_discoveries"]:
            lines.append("## Biomarker Discoveries")
            lines.append("")
            lines.append(sections["biomarker_discoveries"])
            lines.append("")

        # Key Findings
        if sections["key_findings"]:
            lines.append("## Key Findings")
            lines.append("")
            for i, finding in enumerate(sections["key_findings"], 1):
                lines.append(f"{i}. {finding}")
            lines.append("")

        # Q&A Insights
        if sections["qa_insights"]:
            lines.append("## Q&A Insights")
            lines.append("")
            lines.append(sections["qa_insights"])
            lines.append("")

        lines.append("---")
        lines.append(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)
