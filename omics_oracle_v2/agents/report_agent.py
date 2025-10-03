"""Report generation agent with AI-powered summarization."""

import json
from collections import Counter
from datetime import datetime
from typing import Dict, List

from omics_oracle_v2.agents.base import Agent
from omics_oracle_v2.agents.models.data import DataQualityLevel, ProcessedDataset
from omics_oracle_v2.agents.models.report import (
    KeyInsight,
    ReportFormat,
    ReportInput,
    ReportOutput,
    ReportSection,
    ReportType,
)
from omics_oracle_v2.lib.ai import SummarizationClient


class ReportAgent(Agent[ReportInput, ReportOutput]):
    """Report Agent for AI-powered report generation.

    Generates comprehensive reports from processed datasets using AI summarization.
    """

    def __init__(self, settings):
        """Initialize Report Agent."""
        super().__init__(settings)
        self._ai_client = None
        if settings.ai:
            try:
                self._ai_client = SummarizationClient(settings.ai)
            except Exception:
                self._ai_client = None

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._ai_client:
            try:
                self._ai_client.cleanup()
            except Exception:
                pass
        super().cleanup()

    def _validate_input(self, input_data: ReportInput) -> ReportInput:
        """Validate report input data."""
        if not input_data.datasets:
            from omics_oracle_v2.agents.exceptions import AgentValidationError

            raise AgentValidationError("At least one dataset is required for report generation")
        return input_data

    def _process(self, input_data: ReportInput, context) -> ReportOutput:
        """Process input to generate report."""
        # Select top datasets by quality and relevance
        datasets = self._select_datasets(input_data)

        # Generate title
        title = self._generate_title(input_data, datasets)

        # Generate summary
        summary = self._generate_summary(input_data, datasets)

        # Generate sections based on report type
        sections = self._generate_sections(input_data, datasets)

        # Extract insights if enabled
        insights = []
        if input_data.include_quality_analysis:
            insights = self._extract_insights(datasets)

        # Generate recommendations if enabled
        recommendations = []
        if input_data.include_recommendations:
            recommendations = self._generate_recommendations(datasets)

        # Calculate quality summary
        quality_summary = self._calculate_quality_summary(datasets)

        # Format full report
        full_report = self._format_report(
            input_data.report_format,
            title,
            summary,
            sections,
            insights,
            recommendations,
            quality_summary,
        )

        return ReportOutput(
            title=title,
            summary=summary,
            sections=sections,
            key_insights=insights,
            recommendations=recommendations,
            total_datasets_analyzed=len(input_data.datasets),
            datasets_included=[d.geo_id for d in datasets],
            quality_summary=quality_summary,
            generated_at=datetime.utcnow().isoformat(),
            report_type=input_data.report_type,
            report_format=input_data.report_format,
            full_report=full_report,
        )

    def _select_datasets(self, input_data: ReportInput) -> List[ProcessedDataset]:
        """Select top datasets by quality and relevance."""
        datasets = sorted(
            input_data.datasets,
            key=lambda d: (d.quality_score * 0.6 + d.relevance_score * 0.4),
            reverse=True,
        )
        return datasets[: input_data.max_datasets]

    def _generate_title(self, input_data: ReportInput, datasets: List[ProcessedDataset]) -> str:
        """Generate report title."""
        if input_data.query_context:
            return f"Biomedical Data Report: {input_data.query_context}"
        return f"Analysis of {len(datasets)} Biomedical Datasets"

    def _generate_summary(self, input_data: ReportInput, datasets: List[ProcessedDataset]) -> str:
        """Generate AI-powered summary with fallback."""
        # Try AI summarization if available
        if self._ai_client:
            try:
                dataset_texts = []
                for ds in datasets[:5]:  # Use top 5 for summary
                    dataset_texts.append(
                        f"Dataset {ds.geo_id}: {ds.title}\n"
                        f"Organism: {ds.organism}, Samples: {ds.sample_count}\n"
                        f"Summary: {ds.summary[:200]}..."
                    )

                combined_text = "\n\n".join(dataset_texts)
                max_length = 200 if input_data.report_type == ReportType.BRIEF else 500

                summary = self._ai_client.summarize(
                    text=combined_text,
                    max_length=max_length,
                )
                if summary:
                    return summary
            except Exception:
                pass

        # Fallback summary
        return self._generate_fallback_summary(datasets)

    def _generate_fallback_summary(self, datasets: List[ProcessedDataset]) -> str:
        """Generate fallback summary without AI."""
        organism_counts = Counter(d.organism for d in datasets)
        total_samples = sum(d.sample_count for d in datasets)
        high_quality = sum(
            1 for d in datasets if d.quality_level in [DataQualityLevel.EXCELLENT, DataQualityLevel.GOOD]
        )

        top_organism = organism_counts.most_common(1)[0] if organism_counts else ("unknown", 0)

        return (
            f"Analysis of {len(datasets)} biomedical datasets, predominantly from {top_organism[0]} "
            f"({top_organism[1]} datasets). Collectively comprising {total_samples} samples, with "
            f"{high_quality} datasets meeting high quality standards."
        )

    def _generate_sections(
        self, input_data: ReportInput, datasets: List[ProcessedDataset]
    ) -> List[ReportSection]:
        """Generate report sections based on type."""
        sections = []

        # Overview section (all report types)
        sections.append(self._generate_overview_section(datasets))

        # Quality analysis (if not brief)
        if input_data.report_type != ReportType.BRIEF and input_data.include_quality_analysis:
            sections.append(self._generate_quality_section(datasets))

        # Detailed section (comprehensive and technical)
        if input_data.report_type in [ReportType.COMPREHENSIVE, ReportType.TECHNICAL]:
            sections.append(self._generate_detailed_section(datasets))

        # Technical details (technical only)
        if input_data.report_type == ReportType.TECHNICAL:
            sections.append(self._generate_technical_section(datasets))

        return sections

    def _generate_overview_section(self, datasets: List[ProcessedDataset]) -> ReportSection:
        """Generate dataset overview section."""
        organism_counts = Counter(d.organism for d in datasets)
        total_samples = sum(d.sample_count for d in datasets)

        content_lines = [
            f"**Total Datasets:** {len(datasets)}",
            f"**Total Samples:** {total_samples}",
            "",
            "**Organism Distribution:**",
        ]
        for organism, count in organism_counts.most_common(5):
            content_lines.append(f"- {organism}: {count} datasets")

        return ReportSection(title="Dataset Overview", content="\n".join(content_lines), order=0)

    def _generate_quality_section(self, datasets: List[ProcessedDataset]) -> ReportSection:
        """Generate quality analysis section."""
        quality_counts = Counter(d.quality_level for d in datasets)
        high_quality = [
            d for d in datasets if d.quality_level in [DataQualityLevel.EXCELLENT, DataQualityLevel.GOOD]
        ]

        content_lines = [
            "**Quality Distribution:**",
            f"- Excellent: {quality_counts.get(DataQualityLevel.EXCELLENT, 0)}",
            f"- Good: {quality_counts.get(DataQualityLevel.GOOD, 0)}",
            f"- Fair: {quality_counts.get(DataQualityLevel.FAIR, 0)}",
            f"- Poor: {quality_counts.get(DataQualityLevel.POOR, 0)}",
            "",
            f"**Top {min(5, len(high_quality))} High-Quality Datasets:**",
        ]

        for ds in high_quality[:5]:
            content_lines.append(
                f"- {ds.geo_id}: {ds.title} (Quality: {ds.quality_score:.2f}, Samples: {ds.sample_count})"
            )

        return ReportSection(title="Quality Analysis", content="\n".join(content_lines), order=1)

    def _generate_detailed_section(self, datasets: List[ProcessedDataset]) -> ReportSection:
        """Generate detailed dataset information."""
        content_lines = []

        for i, ds in enumerate(datasets[:10], 1):
            content_lines.append(f"**{i}. {ds.geo_id}: {ds.title}**")
            content_lines.append(f"- Organism: {ds.organism}")
            content_lines.append(f"- Samples: {ds.sample_count}")
            content_lines.append(f"- Quality Score: {ds.quality_score:.2f} ({ds.quality_level.value})")
            content_lines.append(f"- Relevance Score: {ds.relevance_score:.2f}")
            if ds.has_publication:
                content_lines.append("- Has publication data")
            if ds.has_sra_data:
                content_lines.append(f"- SRA runs available: {ds.sra_run_count}")
            content_lines.append("")

        return ReportSection(title="Detailed Dataset Information", content="\n".join(content_lines), order=2)

    def _generate_technical_section(self, datasets: List[ProcessedDataset]) -> ReportSection:
        """Generate technical details section."""
        sra_datasets = [d for d in datasets if d.has_sra_data]
        published = [d for d in datasets if d.has_publication]
        total_sra_runs = sum(d.sra_run_count or 0 for d in sra_datasets)

        content_lines = [
            f"**SRA Data Availability:** {len(sra_datasets)} datasets ({total_sra_runs} total runs)",
            f"**Published Datasets:** {len(published)}",
            "",
            "**Sample Size Distribution:**",
            f"- Large (>=100 samples): {sum(1 for d in datasets if d.sample_count >= 100)}",
            f"- Medium (50-99 samples): {sum(1 for d in datasets if 50 <= d.sample_count < 100)}",
            f"- Small (<50 samples): {sum(1 for d in datasets if d.sample_count < 50)}",
        ]

        return ReportSection(title="Technical Details", content="\n".join(content_lines), order=3)

    def _extract_insights(self, datasets: List[ProcessedDataset]) -> List[KeyInsight]:
        """Extract key insights from datasets."""
        insights = []

        # Insight 1: Sample size trends
        large_sample_datasets = [d for d in datasets if d.sample_count >= 100]
        if large_sample_datasets:
            insights.append(
                KeyInsight(
                    insight=f"{len(large_sample_datasets)} datasets have >=100 samples, "
                    f"providing robust statistical power for analysis",
                    supporting_datasets=[d.geo_id for d in large_sample_datasets[:5]],
                    confidence=0.9,
                )
            )

        # Insight 2: Published high-quality datasets
        published_quality = [
            d
            for d in datasets
            if d.has_publication and d.quality_level in [DataQualityLevel.EXCELLENT, DataQualityLevel.GOOD]
        ]
        if published_quality:
            insights.append(
                KeyInsight(
                    insight=f"{len(published_quality)} high-quality datasets have associated publications, "
                    f"indicating peer-reviewed methodologies",
                    supporting_datasets=[d.geo_id for d in published_quality[:5]],
                    confidence=0.95,
                )
            )

        # Insight 3: SRA data availability
        sra_datasets = [d for d in datasets if d.has_sra_data]
        if sra_datasets:
            total_runs = sum(d.sra_run_count or 0 for d in sra_datasets)
            insights.append(
                KeyInsight(
                    insight=f"{len(sra_datasets)} datasets have SRA data ({total_runs} total runs), "
                    f"enabling deep reanalysis opportunities",
                    supporting_datasets=[d.geo_id for d in sra_datasets[:5]],
                    confidence=0.85,
                )
            )

        # Insight 4: Recent vs historical
        recent_datasets = [d for d in datasets if d.age_days and d.age_days <= 730]  # 2 years
        if recent_datasets:
            insights.append(
                KeyInsight(
                    insight=f"{len(recent_datasets)} datasets are recent (<=2 years old), "
                    f"reflecting current research trends",
                    supporting_datasets=[d.geo_id for d in recent_datasets[:5]],
                    confidence=0.8,
                )
            )

        return insights

    def _generate_recommendations(self, datasets: List[ProcessedDataset]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Recommendation 1: Focus on high-quality datasets
        high_quality = [d for d in datasets if d.quality_score >= 0.75]
        if high_quality:
            recommendations.append(
                f"Prioritize the {len(high_quality)} high-quality datasets "
                f"(quality score >=0.75) for initial analysis"
            )

        # Recommendation 2: Review published datasets
        published = [d for d in datasets if d.has_publication]
        if published:
            recommendations.append(
                f"Review the {len(published)} published datasets for " f"validated findings and methodology"
            )

        # Recommendation 3: Large sample sizes
        large_sample = [d for d in datasets if d.sample_count >= 50]
        if large_sample:
            recommendations.append(
                f"Focus on datasets with >=50 samples ({len(large_sample)} datasets) "
                f"for more robust statistical analysis"
            )

        # Recommendation 4: SRA reanalysis
        sra_datasets = [d for d in datasets if d.has_sra_data]
        if sra_datasets:
            recommendations.append(
                f"Consider reanalyzing the {len(sra_datasets)} datasets with SRA data " f"for deeper insights"
            )

        # Recommendation 5: Quality issues
        low_quality = [d for d in datasets if d.quality_level == DataQualityLevel.POOR]
        if low_quality:
            recommendations.append(
                f"Exercise caution with {len(low_quality)} low-quality datasets; "
                f"review quality issues before use"
            )

        return recommendations

    def _calculate_quality_summary(self, datasets: List[ProcessedDataset]) -> Dict[str, int]:
        """Calculate quality distribution summary."""
        quality_counts = Counter(d.quality_level for d in datasets)
        return {
            "excellent": quality_counts.get(DataQualityLevel.EXCELLENT, 0),
            "good": quality_counts.get(DataQualityLevel.GOOD, 0),
            "fair": quality_counts.get(DataQualityLevel.FAIR, 0),
            "poor": quality_counts.get(DataQualityLevel.POOR, 0),
        }

    def _format_report(
        self,
        format_type: ReportFormat,
        title: str,
        summary: str,
        sections: List[ReportSection],
        insights: List[KeyInsight],
        recommendations: List[str],
        quality_summary: Dict[str, int],
    ) -> str:
        """Format report in requested format."""
        if format_type == ReportFormat.MARKDOWN:
            return self._format_markdown(title, summary, sections, insights, recommendations, quality_summary)
        elif format_type == ReportFormat.JSON:
            return self._format_json(title, summary, sections, insights, recommendations, quality_summary)
        elif format_type == ReportFormat.HTML:
            return self._format_html(title, summary, sections, insights, recommendations, quality_summary)
        else:  # TEXT
            return self._format_text(title, summary, sections, insights, recommendations, quality_summary)

    def _format_markdown(self, title, summary, sections, insights, recommendations, quality_summary) -> str:
        """Format report as Markdown."""
        lines = [
            f"# {title}",
            "",
            "## Executive Summary",
            summary,
            "",
        ]

        for section in sorted(sections, key=lambda s: s.order):
            lines.append(f"## {section.title}")
            lines.append(section.content)
            lines.append("")

        if insights:
            lines.append("## Key Insights")
            for i, insight in enumerate(insights, 1):
                lines.append(f"{i}. {insight.insight}")
                lines.append(f"   - Confidence: {insight.confidence:.0%}")
            lines.append("")

        if recommendations:
            lines.append("## Recommendations")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        return "\n".join(lines)

    def _format_json(self, title, summary, sections, insights, recommendations, quality_summary) -> str:
        """Format report as JSON."""
        data = {
            "title": title,
            "summary": summary,
            "sections": [
                {"title": s.title, "content": s.content, "order": s.order}
                for s in sorted(sections, key=lambda s: s.order)
            ],
            "insights": [
                {
                    "insight": i.insight,
                    "supporting_datasets": i.supporting_datasets,
                    "confidence": i.confidence,
                }
                for i in insights
            ],
            "recommendations": recommendations,
            "quality_summary": quality_summary,
        }
        return json.dumps(data, indent=2)

    def _format_text(self, title, summary, sections, insights, recommendations, quality_summary) -> str:
        """Format report as plain text."""
        lines = [
            "=" * 80,
            title,
            "=" * 80,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 80,
            summary,
            "",
        ]

        for section in sorted(sections, key=lambda s: s.order):
            lines.append(section.title.upper())
            lines.append("-" * 80)
            lines.append(section.content)
            lines.append("")

        if insights:
            lines.append("KEY INSIGHTS")
            lines.append("-" * 80)
            for i, insight in enumerate(insights, 1):
                lines.append(f"{i}. {insight.insight}")
            lines.append("")

        if recommendations:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 80)
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        return "\n".join(lines)

    def _format_html(self, title, summary, sections, insights, recommendations, quality_summary) -> str:
        """Format report as HTML."""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"    <title>{title}</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }",
            "        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; }",
            "        h2 { color: #34495e; margin-top: 30px; }",
            "        .summary { background: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; }",
            "        .insight { background: #e8f6f3; padding: 10px; margin: 10px 0; border-left: 3px solid #1abc9c; }",
            "        .recommendation { background: #fef9e7; padding: 10px; margin: 10px 0; border-left: 3px solid #f39c12; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <h1>{title}</h1>",
            "    <h2>Executive Summary</h2>",
            f'    <div class="summary">{summary}</div>',
        ]

        for section in sorted(sections, key=lambda s: s.order):
            html_parts.append(f"    <h2>{section.title}</h2>")
            html_parts.append(f"    <div>{section.content}</div>")

        if insights:
            html_parts.append("    <h2>Key Insights</h2>")
            for insight in insights:
                html_parts.append(f'    <div class="insight">{insight.insight}</div>')

        if recommendations:
            html_parts.append("    <h2>Recommendations</h2>")
            for rec in recommendations:
                html_parts.append(f'    <div class="recommendation">{rec}</div>')

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)
