"""
LLM-powered citation analysis.

Uses LLMs to deeply understand how datasets/papers are being used.
"""

import logging
from typing import List, Optional

from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.llm.prompts import (
    CITATION_CONTEXT_ANALYSIS,
    DATASET_IMPACT_SYNTHESIS,
)
from omics_oracle_v2.lib.citations.models import (
    ApplicationDomain,
    Biomarker,
    CitationContext,
    ClinicalTranslation,
    DatasetImpactReport,
    UsageAnalysis,
)
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class LLMCitationAnalyzer:
    """
    LLM-powered deep analysis of citations and dataset usage.

    Uses large language models to:
    - Understand citation context semantically
    - Classify dataset usage types
    - Extract key findings
    - Identify novel biomarkers
    - Assess clinical relevance
    - Synthesize knowledge across papers

    Example:
        >>> llm_analyzer = LLMCitationAnalyzer(llm_client)
        >>> analysis = llm_analyzer.analyze_citation(context, cited_paper, citing_paper)
        >>> analysis.dataset_reused  # True/False
        >>> analysis.key_findings  # List of findings
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize LLM citation analyzer.

        Args:
            llm_client: LLM client for generation
        """
        self.llm = llm_client

    def analyze_citation_context(
        self,
        citation_context: CitationContext,
        cited_paper: Publication,
        citing_paper: Publication,
    ) -> UsageAnalysis:
        """
        Analyze a single citation using LLM.

        Args:
            citation_context: Citation context
            cited_paper: Paper being cited
            citing_paper: Paper doing the citing

        Returns:
            UsageAnalysis with detailed insights
        """
        logger.info(f"Analyzing citation: {citing_paper.title}")

        # Prepare prompt
        prompt = CITATION_CONTEXT_ANALYSIS.format(
            cited_title=cited_paper.title,
            cited_abstract=cited_paper.abstract or "N/A",
            citing_title=citing_paper.title,
            citing_abstract=citing_paper.abstract or "N/A",
            citation_context=citation_context.context_text,
        )

        # Generate analysis
        try:
            result = self.llm.generate_json(
                prompt,
                system_prompt="You are an expert biomedical research analyst. Provide accurate, evidence-based analysis in valid JSON format.",
            )

            # Convert to UsageAnalysis
            analysis = UsageAnalysis(
                paper_id=citing_paper.doi or citing_paper.title,
                paper_title=citing_paper.title,
                dataset_reused=result.get("dataset_reused", False),
                usage_type=result.get("usage_type", "unknown"),
                confidence=result.get("confidence", 0.5),
                research_question=result.get("research_question", ""),
                application_domain=result.get("application_domain", ""),
                methodology=result.get("methodology", ""),
                sample_info=result.get("sample_info", ""),
                key_findings=result.get("key_findings", []),
                clinical_relevance=result.get("clinical_relevance", "none"),
                clinical_details=result.get("clinical_details", ""),
                novel_biomarkers=result.get("novel_biomarkers", []),
                validation_status=result.get("validation_status", "none"),
                reasoning=result.get("reasoning", ""),
            )

            logger.info(
                f"Analysis complete: dataset_reused={analysis.dataset_reused}, "
                f"usage_type={analysis.usage_type}, confidence={analysis.confidence}"
            )

            return analysis

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Return default analysis on failure
            return UsageAnalysis(
                paper_id=citing_paper.doi or citing_paper.title,
                paper_title=citing_paper.title,
                dataset_reused=False,
                usage_type="unknown",
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
            )

    def analyze_batch(
        self,
        contexts: List[tuple],  # [(context, cited_paper, citing_paper), ...]
        batch_size: int = 5,
    ) -> List[UsageAnalysis]:
        """
        Analyze multiple citations in batch for efficiency.

        Args:
            contexts: List of (context, cited_paper, citing_paper) tuples
            batch_size: Papers to process per LLM call

        Returns:
            List of UsageAnalysis objects
        """
        analyses = []

        for i in range(0, len(contexts), batch_size):
            batch = contexts[i : i + batch_size]

            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} papers")

            # Process each in batch individually for now
            # Could be optimized with better batch prompting
            for context, cited, citing in batch:
                analysis = self.analyze_citation_context(context, cited, citing)
                analyses.append(analysis)

        return analyses

    def synthesize_dataset_impact(
        self,
        dataset_paper: Publication,
        usage_analyses: List[UsageAnalysis],
    ) -> DatasetImpactReport:
        """
        Synthesize comprehensive dataset impact report.

        Args:
            dataset_paper: Original dataset paper
            usage_analyses: List of usage analyses from citing papers

        Returns:
            Comprehensive DatasetImpactReport
        """
        logger.info(f"Synthesizing impact report for: {dataset_paper.title}")

        # Filter to papers that actually reused the dataset
        dataset_users = [a for a in usage_analyses if a.dataset_reused]

        logger.info(f"Found {len(dataset_users)}/{len(usage_analyses)} papers that reused the dataset")

        # Prepare summary for LLM
        papers_summary = self._format_usage_summary(usage_analyses)

        # Generate comprehensive synthesis
        prompt = DATASET_IMPACT_SYNTHESIS.format(
            dataset_title=dataset_paper.title,
            dataset_abstract=dataset_paper.abstract or "N/A",
            dataset_year=dataset_paper.publication_date.year if dataset_paper.publication_date else "Unknown",
            num_papers=len(usage_analyses),
            citing_papers_summary=papers_summary,
        )

        try:
            synthesis = self.llm.generate(
                prompt,
                system_prompt="You are a biomedical research expert. Provide comprehensive, evidence-based analysis.",
                max_tokens=3000,
            )

            # Extract biomarkers
            biomarkers = self._extract_biomarkers(dataset_users)

            # Analyze clinical translation
            clinical_translation = self._analyze_clinical_translation(dataset_users)

            # Build report
            report = DatasetImpactReport(
                dataset_title=dataset_paper.title,
                dataset_year=dataset_paper.publication_date.year if dataset_paper.publication_date else 0,
                total_citations=len(usage_analyses),
                dataset_reuse_count=len(dataset_users),
                time_span_years=self._calculate_time_span(usage_analyses),
                usage_types=self._aggregate_usage_types(dataset_users),
                application_domains=self._aggregate_domains(dataset_users),
                methodologies=self._aggregate_methodologies(dataset_users),
                key_findings=self._aggregate_findings(dataset_users),
                novel_biomarkers=biomarkers,
                clinical_translation=clinical_translation,
                summary=synthesis["content"],
            )

            logger.info("Impact report synthesis complete")
            return report

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            # Return basic report
            return DatasetImpactReport(
                dataset_title=dataset_paper.title,
                dataset_year=0,
                total_citations=len(usage_analyses),
                dataset_reuse_count=len(dataset_users),
                time_span_years=0,
                summary=f"Synthesis failed: {str(e)}",
            )

    def _format_usage_summary(self, analyses: List[UsageAnalysis]) -> str:
        """Format usage analyses for LLM prompt."""
        summary_parts = []

        for i, analysis in enumerate(analyses[:50], 1):  # Limit to 50 to avoid token limits
            if analysis.dataset_reused:
                summary = f"""
Paper {i}: {analysis.paper_title}
- Usage: {analysis.usage_type}
- Domain: {analysis.application_domain}
- Method: {analysis.methodology}
- Findings: {'; '.join(analysis.key_findings[:3])}
- Clinical: {analysis.clinical_relevance}
- Biomarkers: {', '.join(analysis.novel_biomarkers[:5])}
"""
                summary_parts.append(summary.strip())

        return "\n\n".join(summary_parts)

    def _extract_biomarkers(self, analyses: List[UsageAnalysis]) -> List[Biomarker]:
        """Extract all unique biomarkers from analyses."""
        biomarker_dict = {}

        for analysis in analyses:
            for bm_name in analysis.novel_biomarkers:
                if bm_name not in biomarker_dict:
                    biomarker_dict[bm_name] = Biomarker(
                        name=bm_name,
                        type="gene",  # Default
                        sources=[analysis.paper_title],
                        application=analysis.application_domain,
                        validation_level=analysis.validation_status,
                    )
                else:
                    biomarker_dict[bm_name].sources.append(analysis.paper_title)

        return list(biomarker_dict.values())

    def _analyze_clinical_translation(self, analyses: List[UsageAnalysis]) -> Optional[ClinicalTranslation]:
        """Analyze clinical translation from usage analyses."""
        clinical_papers = [a for a in analyses if a.clinical_relevance in ["high", "medium"]]

        if not clinical_papers:
            return None

        # Count trials, validations, etc.
        trials = sum(1 for a in clinical_papers if "trial" in a.clinical_details.lower())
        validated = sum(1 for a in clinical_papers if a.validation_status == "validated")

        return ClinicalTranslation(
            trials_initiated=trials,
            validated_in_patients=validated > 0,
        )

    def _calculate_time_span(self, analyses: List[UsageAnalysis]) -> int:
        """Calculate time span of usage."""
        # Simplified - would need publication dates
        return 5  # Default

    def _aggregate_usage_types(self, analyses: List[UsageAnalysis]) -> dict:
        """Aggregate usage types."""
        types = {}
        for a in analyses:
            types[a.usage_type] = types.get(a.usage_type, 0) + 1
        return types

    def _aggregate_domains(self, analyses: List[UsageAnalysis]) -> List[ApplicationDomain]:
        """Aggregate application domains."""
        domain_dict = {}

        for a in analyses:
            domain = a.application_domain or "Unknown"
            if domain not in domain_dict:
                domain_dict[domain] = ApplicationDomain(
                    name=domain, paper_count=1, example_papers=[a.paper_title]
                )
            else:
                domain_dict[domain].paper_count += 1
                if len(domain_dict[domain].example_papers) < 3:
                    domain_dict[domain].example_papers.append(a.paper_title)

        # Sort by paper count
        domains = sorted(domain_dict.values(), key=lambda d: d.paper_count, reverse=True)
        return domains[:10]  # Top 10

    def _aggregate_methodologies(self, analyses: List[UsageAnalysis]) -> dict:
        """Aggregate methodologies."""
        methods = {}
        for a in analyses:
            method = a.methodology or "Unknown"
            methods[method] = methods.get(method, 0) + 1
        return methods

    def _aggregate_findings(self, analyses: List[UsageAnalysis]) -> List[str]:
        """Aggregate key findings."""
        all_findings = []
        for a in analyses:
            all_findings.extend(a.key_findings)

        # Return unique findings (simplified)
        return list(set(all_findings))[:20]
