"""
Data transformer for converting backend data to frontend formats.

Enables pluggable frontends (Streamlit, React, Vue, mobile).
"""

import csv
import json
from io import StringIO
from typing import Any, Dict, List, Literal

from .models import AnalysisResponse, NetworkGraph, Publication, SearchResponse, TrendAnalysis


class DataTransformer:
    """
    Transform backend data to various frontend formats.

    Supports:
    - Streamlit format (current dashboard)
    - React format (future admin dashboard)
    - Vue format (future mobile app)
    - Export formats (CSV, JSON, BibTeX, RIS)

    Usage:
        transformer = DataTransformer()

        # For Streamlit
        streamlit_data = transformer.to_streamlit(search_response)

        # For React
        react_data = transformer.to_react(search_response)

        # For export
        csv_data = transformer.to_csv(search_response)
        bibtex = transformer.to_bibtex(search_response.results)
    """

    # ========================================================================
    # STREAMLIT TRANSFORMERS
    # ========================================================================

    @staticmethod
    def to_streamlit(response: SearchResponse) -> Dict[str, Any]:
        """
        Transform to Streamlit-friendly format.

        Current dashboard expects specific structure.
        This maintains compatibility while exposing new fields.
        """
        return {
            "results": [
                {
                    # Core fields (existing dashboard uses these)
                    "title": pub.title,
                    "authors": pub.authors,
                    "year": pub.year,
                    "journal": pub.journal,
                    "abstract": pub.abstract,
                    "citation_count": pub.citation_metrics.count if pub.citation_metrics else 0,
                    "pubmed_url": str(pub.pubmed_url) if pub.pubmed_url else None,
                    "scholar_url": str(pub.scholar_url) if pub.scholar_url else None,
                    # NEW fields (dashboard should start using these!)
                    "quality_score": {
                        "overall": pub.quality_score.overall,
                        "methodology": pub.quality_score.methodology,
                        "impact": pub.quality_score.impact,
                        "explanation": pub.quality_score.explanation,
                    }
                    if pub.quality_score
                    else None,
                    "biomarkers": [
                        {
                            "name": bm.name,
                            "type": bm.type,
                            "confidence": bm.confidence,
                            "context": bm.context,
                        }
                        for bm in pub.biomarkers
                    ],
                    "citation_analysis": {
                        "count": pub.citation_metrics.count,
                        "recent_count": pub.citation_metrics.recent_count,
                        "velocity": pub.citation_metrics.velocity,
                        "predicted_5yr": pub.citation_metrics.predicted_5yr,
                    }
                    if pub.citation_metrics
                    else None,
                    "access": {
                        "has_pdf": pub.access_info.has_pdf,
                        "pdf_url": str(pub.access_info.pdf_url)
                        if pub.access_info and pub.access_info.pdf_url
                        else None,
                        "open_access": pub.access_info.open_access if pub.access_info else False,
                    }
                    if pub.access_info
                    else None,
                    "relevance": {
                        "score": pub.relevance_score,
                        "semantic_similarity": pub.semantic_similarity,
                        "explanation": pub.match_explanation,
                    },
                }
                for pub in response.results
            ],
            "metadata": {
                "total": response.metadata.total_results,
                "query_time": response.metadata.query_time,
                "databases": response.metadata.databases_searched,
                "from_cache": response.metadata.cache_hit,
            },
            "aggregated_biomarkers": response.aggregated_biomarkers,
        }

    @staticmethod
    def analysis_to_streamlit(analysis: AnalysisResponse) -> Dict[str, Any]:
        """Transform LLM analysis for Streamlit display."""
        return {
            "overview": analysis.overview,
            "key_findings": analysis.key_findings,
            "research_gaps": analysis.research_gaps,
            "recommendations": analysis.recommendations,
            "confidence": analysis.confidence,
            "model": analysis.model_used,
        }

    @staticmethod
    def trends_to_streamlit(trends: TrendAnalysis) -> Dict[str, Any]:
        """Transform trend analysis for Streamlit charts."""
        return {
            "data": [
                {
                    "year": point.year,
                    "publications": point.count,
                    "avg_citations": point.citation_avg,
                }
                for point in trends.trends
            ],
            "metrics": {
                "growth_rate": trends.growth_rate,
                "prediction_5yr": trends.prediction_5yr,
                "peak_year": trends.peak_year,
            },
        }

    @staticmethod
    def network_to_streamlit(network: NetworkGraph) -> Dict[str, Any]:
        """Transform network for Streamlit visualization."""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.title[:50] + "...",
                    "year": node.year,
                    "citations": node.citations,
                    "size": node.size,
                }
                for node in network.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "weight": edge.weight,
                }
                for edge in network.edges
            ],
            "clusters": network.clusters,
        }

    # ========================================================================
    # REACT TRANSFORMERS
    # ========================================================================

    @staticmethod
    def to_react(response: SearchResponse) -> Dict[str, Any]:
        """
        Transform to React-friendly format.

        React expects camelCase and specific structure for components.
        """
        return {
            "results": [
                {
                    "id": pub.id,
                    "title": pub.title,
                    "authors": pub.authors,
                    "year": pub.year,
                    "journal": pub.journal,
                    "abstract": pub.abstract,
                    "doi": pub.doi,
                    "pmid": pub.pmid,
                    # URLs
                    "urls": {
                        "pubmed": str(pub.pubmed_url) if pub.pubmed_url else None,
                        "scholar": str(pub.scholar_url) if pub.scholar_url else None,
                    },
                    # Metrics
                    "metrics": {
                        "citations": pub.citation_metrics.count if pub.citation_metrics else 0,
                        "recentCitations": pub.citation_metrics.recent_count if pub.citation_metrics else 0,
                        "citationVelocity": pub.citation_metrics.velocity if pub.citation_metrics else None,
                        "predictedCitations": pub.citation_metrics.predicted_5yr
                        if pub.citation_metrics
                        else None,
                        "quality": {
                            "overall": pub.quality_score.overall,
                            "methodology": pub.quality_score.methodology,
                            "impact": pub.quality_score.impact,
                            "explanation": pub.quality_score.explanation,
                        }
                        if pub.quality_score
                        else None,
                    },
                    # Biomarkers
                    "biomarkers": [
                        {
                            "name": bm.name,
                            "type": bm.type,
                            "confidence": bm.confidence,
                            "context": bm.context,
                        }
                        for bm in pub.biomarkers
                    ],
                    # Access
                    "access": {
                        "hasPdf": pub.access_info.has_pdf if pub.access_info else False,
                        "pdfUrl": str(pub.access_info.pdf_url)
                        if pub.access_info and pub.access_info.pdf_url
                        else None,
                        "openAccess": pub.access_info.open_access if pub.access_info else False,
                    },
                    # Relevance
                    "relevance": {
                        "score": pub.relevance_score,
                        "semanticSimilarity": pub.semantic_similarity,
                        "explanation": pub.match_explanation,
                    },
                }
                for pub in response.results
            ],
            "metadata": {
                "total": response.metadata.total_results,
                "queryTime": response.metadata.query_time,
                "databases": response.metadata.databases_searched,
                "fromCache": response.metadata.cache_hit,
            },
        }

    # ========================================================================
    # VUE TRANSFORMERS
    # ========================================================================

    @staticmethod
    def to_vue(response: SearchResponse) -> Dict[str, Any]:
        """
        Transform to Vue-friendly format.

        Vue expects similar to React but with some differences.
        """
        # Similar to React for now, can customize later
        return DataTransformer.to_react(response)

    # ========================================================================
    # EXPORT FORMATS
    # ========================================================================

    @staticmethod
    def to_csv(response: SearchResponse) -> str:
        """Export search results to CSV."""
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Title",
                "Authors",
                "Year",
                "Journal",
                "DOI",
                "PMID",
                "Citations",
                "Quality Score",
                "PubMed URL",
            ]
        )

        # Rows
        for pub in response.results:
            writer.writerow(
                [
                    pub.title,
                    "; ".join(pub.authors),
                    pub.year,
                    pub.journal or "",
                    pub.doi or "",
                    pub.pmid or "",
                    pub.citation_metrics.count if pub.citation_metrics else 0,
                    pub.quality_score.overall if pub.quality_score else "",
                    str(pub.pubmed_url) if pub.pubmed_url else "",
                ]
            )

        return output.getvalue()

    @staticmethod
    def to_json(response: SearchResponse) -> str:
        """Export search results to JSON."""
        return json.dumps(response.dict(), indent=2, default=str)

    @staticmethod
    def to_bibtex(publications: List[Publication]) -> str:
        """Export publications to BibTeX format."""
        entries = []

        for i, pub in enumerate(publications, 1):
            entry = f"""@article{{pub{i},
  title = {{{pub.title}}},
  author = {{{" and ".join(pub.authors)}}},
  year = {{{pub.year}}},
  journal = {{{pub.journal or "Unknown"}}},
"""
            if pub.doi:
                entry += f"  doi = {{{pub.doi}}},\n"
            if pub.abstract:
                entry += f"  abstract = {{{pub.abstract}}},\n"

            entry += "}\n"
            entries.append(entry)

        return "\n".join(entries)

    @staticmethod
    def to_ris(publications: List[Publication]) -> str:
        """Export publications to RIS format."""
        entries = []

        for pub in publications:
            entry = "TY  - JOUR\n"
            entry += f"TI  - {pub.title}\n"

            for author in pub.authors:
                entry += f"AU  - {author}\n"

            entry += f"PY  - {pub.year}\n"

            if pub.journal:
                entry += f"JO  - {pub.journal}\n"

            if pub.doi:
                entry += f"DO  - {pub.doi}\n"

            if pub.abstract:
                entry += f"AB  - {pub.abstract}\n"

            entry += "ER  - \n\n"
            entries.append(entry)

        return "".join(entries)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @staticmethod
    def to_format(
        response: SearchResponse,
        format: Literal["streamlit", "react", "vue", "csv", "json", "bibtex", "ris"],
    ) -> Any:
        """
        Convert to specified format.

        Args:
            response: SearchResponse to convert
            format: Target format

        Returns:
            Converted data in target format
        """
        transformers = {
            "streamlit": DataTransformer.to_streamlit,
            "react": DataTransformer.to_react,
            "vue": DataTransformer.to_vue,
            "csv": DataTransformer.to_csv,
            "json": DataTransformer.to_json,
            "bibtex": lambda r: DataTransformer.to_bibtex(r.results),
            "ris": lambda r: DataTransformer.to_ris(r.results),
        }

        transformer = transformers.get(format)
        if not transformer:
            raise ValueError(f"Unsupported format: {format}")

        return transformer(response)
