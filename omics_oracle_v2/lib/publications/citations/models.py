"""
Data models for citation analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class CitationContext:
    """
    Citation context extracted from a paper.

    Attributes:
        citing_paper_id: ID of paper doing the citing
        cited_paper_id: ID of paper being cited
        context_text: Text around the citation
        sentence: Sentence containing the citation
        paragraph: Full paragraph containing the citation
        section: Paper section (intro, methods, results, discussion)
    """

    citing_paper_id: str
    cited_paper_id: str
    context_text: str
    sentence: Optional[str] = None
    paragraph: Optional[str] = None
    section: Optional[str] = None


@dataclass
class UsageAnalysis:
    """
    LLM analysis of how a dataset/paper was used.

    Attributes:
        paper_id: ID of the citing paper
        paper_title: Title of citing paper
        dataset_reused: Whether the dataset was actually used
        usage_type: How it was used (validation, novel_application, etc.)
        confidence: Analysis confidence (0-1)
        research_question: Research question investigated
        application_domain: Domain (e.g., "cancer biomarker discovery")
        methodology: Methods used (e.g., "machine learning - random forest")
        sample_info: Sample size and source
        key_findings: List of main findings
        clinical_relevance: Level of clinical relevance (high/medium/low/none)
        clinical_details: Clinical translation details
        novel_biomarkers: Novel biomarkers identified
        validation_status: Validation level (validated/in_progress/proposed/none)
        reasoning: LLM's reasoning
    """

    paper_id: str
    paper_title: str
    dataset_reused: bool
    usage_type: str
    confidence: float
    research_question: str = ""
    application_domain: str = ""
    methodology: str = ""
    sample_info: str = ""
    key_findings: List[str] = field(default_factory=list)
    clinical_relevance: str = "none"
    clinical_details: str = ""
    novel_biomarkers: List[str] = field(default_factory=list)
    validation_status: str = "none"
    reasoning: str = ""


@dataclass
class ApplicationDomain:
    """
    Application domain for dataset usage.

    Attributes:
        name: Domain name (e.g., "breast cancer biomarker discovery")
        paper_count: Number of papers in this domain
        example_papers: Example paper titles
        key_characteristics: Key features of this domain
    """

    name: str
    paper_count: int
    example_papers: List[str] = field(default_factory=list)
    key_characteristics: List[str] = field(default_factory=list)


@dataclass
class TemporalTrend:
    """
    Temporal trend in dataset usage.

    Attributes:
        year: Year
        paper_count: Papers published this year
        usage_types: Distribution of usage types
        domains: Active domains this year
        key_developments: Notable developments
    """

    year: int
    paper_count: int
    usage_types: dict = field(default_factory=dict)
    domains: List[str] = field(default_factory=list)
    key_developments: List[str] = field(default_factory=list)


@dataclass
class Biomarker:
    """
    Novel biomarker discovered using the dataset.

    Attributes:
        name: Biomarker name (gene, protein, etc.)
        type: Type (gene/protein/metabolite/signature)
        sources: Papers that identified it
        application: What it predicts/indicates
        validation_level: Level of validation
        clinical_potential: Clinical utility potential
        details: Additional details
    """

    name: str
    type: str
    sources: List[str] = field(default_factory=list)
    application: str = ""
    validation_level: str = "computational"
    clinical_potential: str = "low"
    details: str = ""


@dataclass
class ClinicalTranslation:
    """
    Clinical translation information.

    Attributes:
        trials_initiated: Clinical trials based on findings
        trials_completed: Completed trials
        fda_submissions: FDA submissions/approvals
        validated_in_patients: Patient validation studies
        clinical_guidelines: Incorporated into guidelines
        time_to_clinic: Years from discovery to clinical use
    """

    trials_initiated: int = 0
    trials_completed: int = 0
    fda_submissions: List[str] = field(default_factory=list)
    validated_in_patients: bool = False
    clinical_guidelines: List[str] = field(default_factory=list)
    time_to_clinic: Optional[float] = None


@dataclass
class DatasetImpactReport:
    """
    Comprehensive dataset impact report.

    Attributes:
        dataset_title: Original dataset paper title
        dataset_year: Publication year
        total_citations: Total citation count
        dataset_reuse_count: Papers that reused the dataset
        time_span_years: Years from publication to present

        usage_types: Distribution of usage types
        application_domains: Primary application domains
        methodologies: Methodologies employed

        key_findings: Aggregated key findings
        novel_biomarkers: Novel biomarkers discovered

        clinical_translation: Clinical translation info
        temporal_trends: Usage over time

        research_gaps: Identified research gaps
        future_opportunities: Future research opportunities

        summary: Natural language summary
        generated_at: Report generation timestamp
    """

    dataset_title: str
    dataset_year: int
    total_citations: int
    dataset_reuse_count: int
    time_span_years: int

    usage_types: dict = field(default_factory=dict)
    application_domains: List[ApplicationDomain] = field(default_factory=list)
    methodologies: dict = field(default_factory=dict)

    key_findings: List[str] = field(default_factory=list)
    novel_biomarkers: List[Biomarker] = field(default_factory=list)

    clinical_translation: Optional[ClinicalTranslation] = None
    temporal_trends: List[TemporalTrend] = field(default_factory=list)

    research_gaps: List[str] = field(default_factory=list)
    future_opportunities: List[str] = field(default_factory=list)

    summary: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
