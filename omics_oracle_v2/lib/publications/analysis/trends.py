"""
Temporal trend analysis for dataset usage patterns.

Analyzes how dataset usage has evolved over time based on citation patterns.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from omics_oracle_v2.lib.citations.models import UsageAnalysis
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class TemporalTrendAnalyzer:
    """
    Analyze temporal trends in dataset usage.

    Tracks how dataset usage, research domains, and methodologies
    have evolved over time based on citation analysis.

    Example:
        >>> analyzer = TemporalTrendAnalyzer()
        >>> trends = analyzer.analyze_trends(dataset, citation_analyses)
        >>> print(trends["citation_timeline"])
    """

    def __init__(self):
        """Initialize trend analyzer."""
        pass

    def analyze_trends(
        self,
        dataset: Publication,
        citation_analyses: List[UsageAnalysis],
        citing_papers: Optional[List[Publication]] = None,
    ) -> Dict:
        """
        Analyze temporal trends in dataset usage.

        Args:
            dataset: Dataset publication
            citation_analyses: Citation analyses
            citing_papers: Optional list of citing publications with dates

        Returns:
            Dictionary with trend analyses
        """
        logger.info(f"Analyzing temporal trends for: {dataset.title}")

        # Build timeline from citing papers if available
        timeline_data = self._build_timeline(citation_analyses, citing_papers)

        # Analyze usage type trends
        usage_trends = self._analyze_usage_trends(timeline_data)

        # Analyze domain evolution
        domain_trends = self._analyze_domain_trends(timeline_data)

        # Analyze biomarker discovery timeline
        biomarker_timeline = self._analyze_biomarker_timeline(timeline_data)

        # Calculate impact trajectory
        impact_trajectory = self._calculate_impact_trajectory(timeline_data)

        # Find peak usage periods
        peak_periods = self._find_peak_periods(timeline_data)

        result = {
            "dataset_title": dataset.title,
            "dataset_year": dataset.publication_date.year if dataset.publication_date else None,
            "analysis_timespan": self._get_timespan(timeline_data),
            "citation_timeline": timeline_data["by_year"],
            "usage_type_trends": usage_trends,
            "domain_evolution": domain_trends,
            "biomarker_timeline": biomarker_timeline,
            "impact_trajectory": impact_trajectory,
            "peak_periods": peak_periods,
            "total_citations_analyzed": len(citation_analyses),
        }

        logger.info(f"Trend analysis complete: {len(timeline_data['by_year'])} years of data")
        return result

    def _build_timeline(
        self,
        citation_analyses: List[UsageAnalysis],
        citing_papers: Optional[List[Publication]] = None,
    ) -> Dict:
        """
        Build timeline data structure.

        Returns:
            Dictionary with data organized by year
        """
        timeline = {
            "by_year": defaultdict(
                lambda: {
                    "count": 0,
                    "reuse_count": 0,
                    "usage_types": defaultdict(int),
                    "domains": defaultdict(int),
                    "biomarkers": [],
                    "papers": [],
                }
            )
        }

        # If we have citing papers with dates, use those
        if citing_papers:
            for paper, analysis in zip(citing_papers, citation_analyses):
                if paper.publication_date:
                    year = paper.publication_date.year
                    self._add_to_year(timeline["by_year"][year], analysis, paper)
        else:
            # Estimate years based on analysis order (less accurate)
            # Assume papers are roughly chronological
            current_year = datetime.now().year
            years_back = min(10, len(citation_analyses) // 5)  # Spread over ~10 years

            for i, analysis in enumerate(citation_analyses):
                # Distribute papers over years (rough estimate)
                year = current_year - (i * years_back // len(citation_analyses))
                self._add_to_year(timeline["by_year"][year], analysis, None)

        return timeline

    def _add_to_year(
        self,
        year_data: Dict,
        analysis: UsageAnalysis,
        paper: Optional[Publication],
    ):
        """Add analysis to year data."""
        year_data["count"] += 1

        if analysis.dataset_reused:
            year_data["reuse_count"] += 1
            year_data["usage_types"][analysis.usage_type] += 1

            if analysis.application_domain:
                year_data["domains"][analysis.application_domain] += 1

            year_data["biomarkers"].extend(analysis.novel_biomarkers)

        if paper:
            year_data["papers"].append(
                {
                    "title": paper.title,
                    "doi": paper.doi,
                    "reused": analysis.dataset_reused,
                }
            )

    def _analyze_usage_trends(self, timeline_data: Dict) -> Dict:
        """
        Analyze how usage types have changed over time.

        Returns:
            Dictionary with usage type trends
        """
        trends = {}
        by_year = timeline_data["by_year"]

        # Get all usage types
        all_usage_types = set()
        for year_data in by_year.values():
            all_usage_types.update(year_data["usage_types"].keys())

        # Build time series for each usage type
        for usage_type in all_usage_types:
            trends[usage_type] = {
                year: year_data["usage_types"].get(usage_type, 0)
                for year, year_data in sorted(by_year.items())
            }

        # Calculate trends (increasing/decreasing)
        trend_directions = {}
        for usage_type, yearly_counts in trends.items():
            if len(yearly_counts) >= 2:
                values = list(yearly_counts.values())
                # Simple trend: compare first half to second half
                mid = len(values) // 2
                first_half_avg = sum(values[:mid]) / mid if mid > 0 else 0
                second_half_avg = sum(values[mid:]) / (len(values) - mid) if len(values) - mid > 0 else 0

                if second_half_avg > first_half_avg * 1.2:
                    trend_directions[usage_type] = "increasing"
                elif second_half_avg < first_half_avg * 0.8:
                    trend_directions[usage_type] = "decreasing"
                else:
                    trend_directions[usage_type] = "stable"

        return {
            "time_series": trends,
            "trend_directions": trend_directions,
        }

    def _analyze_domain_trends(self, timeline_data: Dict) -> Dict:
        """
        Analyze how research domains have evolved.

        Returns:
            Dictionary with domain evolution data
        """
        by_year = timeline_data["by_year"]

        # Get domain distribution by year
        domain_by_year = {}
        for year, year_data in sorted(by_year.items()):
            domain_by_year[year] = dict(year_data["domains"])

        # Find emerging domains (new in recent years)
        all_years = sorted(by_year.keys())
        if len(all_years) >= 3:
            recent_years = all_years[-3:]
            earlier_years = all_years[:-3]

            recent_domains = set()
            for year in recent_years:
                recent_domains.update(by_year[year]["domains"].keys())

            earlier_domains = set()
            for year in earlier_years:
                earlier_domains.update(by_year[year]["domains"].keys())

            emerging_domains = recent_domains - earlier_domains
        else:
            emerging_domains = set()

        # Find most active domains per year
        dominant_domains = {}
        for year, year_data in sorted(by_year.items()):
            if year_data["domains"]:
                dominant = max(year_data["domains"].items(), key=lambda x: x[1])
                dominant_domains[year] = dominant[0]

        return {
            "domain_by_year": domain_by_year,
            "emerging_domains": list(emerging_domains),
            "dominant_by_year": dominant_domains,
        }

    def _analyze_biomarker_timeline(self, timeline_data: Dict) -> Dict:
        """
        Analyze biomarker discovery timeline.

        Returns:
            Dictionary with biomarker discovery trends
        """
        by_year = timeline_data["by_year"]

        biomarker_counts = {}
        cumulative_biomarkers = set()
        cumulative_counts = {}

        for year, year_data in sorted(by_year.items()):
            year_biomarkers = year_data["biomarkers"]
            biomarker_counts[year] = len(year_biomarkers)

            cumulative_biomarkers.update(year_biomarkers)
            cumulative_counts[year] = len(cumulative_biomarkers)

        # Find year with most discoveries
        if biomarker_counts:
            peak_year = max(biomarker_counts.items(), key=lambda x: x[1])
        else:
            peak_year = None

        return {
            "discoveries_per_year": biomarker_counts,
            "cumulative_unique_biomarkers": cumulative_counts,
            "peak_discovery_year": peak_year[0] if peak_year else None,
            "peak_discoveries": peak_year[1] if peak_year else 0,
            "total_unique_biomarkers": len(cumulative_biomarkers),
        }

    def _calculate_impact_trajectory(self, timeline_data: Dict) -> Dict:
        """
        Calculate dataset impact trajectory.

        Returns:
            Dictionary with impact metrics over time
        """
        by_year = timeline_data["by_year"]

        trajectory = {}
        for year, year_data in sorted(by_year.items()):
            total = year_data["count"]
            reused = year_data["reuse_count"]
            reuse_rate = reused / total if total > 0 else 0

            trajectory[year] = {
                "total_citations": total,
                "dataset_reuse": reused,
                "reuse_rate": reuse_rate,
                "unique_biomarkers": len(set(year_data["biomarkers"])),
            }

        # Calculate growth metrics
        years = sorted(trajectory.keys())
        if len(years) >= 2:
            first_year = years[0]
            last_year = years[-1]
            years_span = last_year - first_year

            first_citations = trajectory[first_year]["total_citations"]
            last_citations = trajectory[last_year]["total_citations"]

            if years_span > 0 and first_citations > 0:
                growth_rate = (last_citations - first_citations) / (years_span * first_citations)
            else:
                growth_rate = 0
        else:
            growth_rate = 0

        return {
            "yearly_metrics": trajectory,
            "overall_growth_rate": growth_rate,
            "years_analyzed": len(years),
        }

    def _find_peak_periods(self, timeline_data: Dict) -> List[Dict]:
        """
        Find peak usage periods.

        Returns:
            List of peak periods with details
        """
        by_year = timeline_data["by_year"]

        # Find years with highest citations
        citation_peaks = sorted(by_year.items(), key=lambda x: x[1]["count"], reverse=True)[:3]

        # Find years with highest reuse
        reuse_peaks = sorted(by_year.items(), key=lambda x: x[1]["reuse_count"], reverse=True)[:3]

        # Find years with most biomarkers
        biomarker_peaks = sorted(by_year.items(), key=lambda x: len(x[1]["biomarkers"]), reverse=True)[:3]

        return {
            "highest_citation_years": [
                {"year": year, "count": data["count"]} for year, data in citation_peaks
            ],
            "highest_reuse_years": [
                {"year": year, "count": data["reuse_count"]} for year, data in reuse_peaks
            ],
            "highest_biomarker_years": [
                {"year": year, "count": len(data["biomarkers"])} for year, data in biomarker_peaks
            ],
        }

    def _get_timespan(self, timeline_data: Dict) -> Dict:
        """Get analysis timespan."""
        years = sorted(timeline_data["by_year"].keys())
        if len(years) >= 2:
            return {
                "start_year": years[0],
                "end_year": years[-1],
                "years_covered": years[-1] - years[0] + 1,
            }
        elif len(years) == 1:
            return {
                "start_year": years[0],
                "end_year": years[0],
                "years_covered": 1,
            }
        else:
            return {
                "start_year": None,
                "end_year": None,
                "years_covered": 0,
            }

    def generate_summary(self, trends: Dict) -> str:
        """
        Generate human-readable summary of trends.

        Args:
            trends: Trends dictionary from analyze_trends()

        Returns:
            Text summary
        """
        lines = [
            f"Temporal Analysis: {trends['dataset_title']}",
            f"Dataset published: {trends['dataset_year']}",
            f"Analysis timespan: {trends['analysis_timespan']['years_covered']} years "
            f"({trends['analysis_timespan']['start_year']}-{trends['analysis_timespan']['end_year']})",
            "",
            "Key Findings:",
        ]

        # Citation trend
        trajectory = trends["impact_trajectory"]
        if trajectory["overall_growth_rate"] > 0:
            lines.append(f"- Citations growing at {trajectory['overall_growth_rate']:.1%} per year")
        elif trajectory["overall_growth_rate"] < 0:
            lines.append(f"- Citations declining at {abs(trajectory['overall_growth_rate']):.1%} per year")
        else:
            lines.append("- Citation rate stable")

        # Peak years
        peaks = trends["peak_periods"]
        if peaks["highest_citation_years"]:
            peak_year = peaks["highest_citation_years"][0]
            lines.append(f"- Peak citation year: {peak_year['year']} ({peak_year['count']} citations)")

        # Biomarker discoveries
        biomarker_timeline = trends["biomarker_timeline"]
        if biomarker_timeline["total_unique_biomarkers"] > 0:
            lines.append(f"- Total biomarkers discovered: {biomarker_timeline['total_unique_biomarkers']}")
            if biomarker_timeline["peak_discovery_year"]:
                lines.append(
                    f"- Peak discovery year: {biomarker_timeline['peak_discovery_year']} "
                    f"({biomarker_timeline['peak_discoveries']} biomarkers)"
                )

        # Emerging domains
        domain_trends = trends["domain_evolution"]
        if domain_trends["emerging_domains"]:
            lines.append(f"- Emerging domains: {', '.join(domain_trends['emerging_domains'][:3])}")

        return "\n".join(lines)
