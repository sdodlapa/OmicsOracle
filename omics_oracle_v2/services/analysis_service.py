"""
AI Analysis Service

Business logic for AI-powered dataset analysis using LLMs.
Extracted from api/routes/agents.py to improve separation of concerns.
"""

import logging
import time
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from omics_oracle_v2.api.models.responses import AIAnalysisResponse

logger = logging.getLogger(__name__)


class AIAnalysisRequest:
    """Request model for AI analysis (imported from routes)."""

    pass  # Will use the one from routes


class AnalysisService:
    """Service for AI-powered dataset analysis."""

    def __init__(self):
        """Initialize analysis service."""
        self.logger = logger

    async def analyze_datasets(
        self,
        request: "AIAnalysisRequest",
        settings,
    ) -> AIAnalysisResponse:
        """
        Generate AI analysis of datasets using LLM.

        Args:
            request: Analysis request with datasets and query
            settings: Application settings with AI configuration

        Returns:
            AIAnalysisResponse with analysis and insights

        Raises:
            HTTPException: If OpenAI not configured or analysis fails
        """
        from fastapi import HTTPException, status

        start_time = time.time()

        # Check OpenAI configuration
        if not settings.ai.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis unavailable: OpenAI API key not configured. "
                "Set OPENAI_API_KEY environment variable.",
            )

        # Get ParsedCache for loading full-text content
        from omics_oracle_v2.lib.pipelines.text_enrichment import \
            get_parsed_cache

        parsed_cache = get_parsed_cache()

        # Limit datasets
        datasets_to_analyze = request.datasets[: request.max_datasets]

        # Check if we have actual content (not just metadata)
        (
            has_content,
            total_fulltext,
            total_with_content,
        ) = self._check_content_availability(datasets_to_analyze)

        if not has_content:
            return self._build_no_content_response(
                request, start_time, total_fulltext, total_with_content
            )

        # Build dataset summaries with full-text
        dataset_summaries, total_fulltext_papers = await self._build_dataset_summaries(
            datasets_to_analyze, parsed_cache
        )

        # Build comprehensive analysis prompt
        analysis_prompt = self._build_analysis_prompt(
            request=request,
            datasets_to_analyze=datasets_to_analyze,
            dataset_summaries=dataset_summaries,
            total_fulltext_papers=total_fulltext_papers,
        )

        # Call LLM
        analysis = self._call_llm(analysis_prompt, settings)

        # Parse insights and recommendations
        insights, recommendations = self._parse_analysis_results(analysis)

        execution_time_ms = (time.time() - start_time) * 1000

        return AIAnalysisResponse(
            success=True,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(timezone.utc),
            query=request.query,
            analysis=analysis,
            insights=insights[:5] if insights else [],
            recommendations=recommendations[:5] if recommendations else [],
            model_used=settings.ai.model,
        )

    def _check_content_availability(self, datasets: List) -> Tuple[bool, int, int]:
        """
        Check if datasets have actual parsed content.

        Returns:
            Tuple of (has_content, total_fulltext_count, total_with_content)
        """
        total_fulltext_count = 0
        total_with_content = 0

        for ds in datasets:
            if ds.fulltext and len(ds.fulltext) > 0:
                total_fulltext_count += len(ds.fulltext)
                for ft in ds.fulltext:
                    has_content = any(
                        [
                            ft.get("methods") and len(ft.get("methods", "")) > 100,
                            ft.get("results") and len(ft.get("results", "")) > 100,
                            ft.get("abstract") and len(ft.get("abstract", "")) > 50,
                        ]
                    )
                    if has_content:
                        total_with_content += 1
                        break

        has_content = total_fulltext_count > 0 and total_with_content > 0
        return has_content, total_fulltext_count, total_with_content

    def _build_no_content_response(
        self,
        request: "AIAnalysisRequest",
        start_time: float,
        total_fulltext: int,
        total_with_content: int,
    ) -> AIAnalysisResponse:
        """Build response when no content is available."""
        reason = (
            "No full-text papers downloaded"
            if total_fulltext == 0
            else "Papers downloaded but not parsed yet (only metadata available)"
        )

        self.logger.warning(
            f"[WARNING] AI Analysis BLOCKED: {reason}. "
            f"Fulltext count: {total_fulltext}, With content: {total_with_content}"
        )

        return AIAnalysisResponse(
            success=False,
            execution_time_ms=(time.time() - start_time) * 1000,
            timestamp=datetime.now(timezone.utc),
            query=request.query,
            analysis=(
                "# [!] AI Analysis Not Available\n\n"
                f"**Reason:** {reason}\n\n"
                "AI analysis requires detailed **Methods**, **Results**, and **Discussion** sections "
                "to provide meaningful insights. Without full-text content, AI would only summarize "
                "the brief GEO metadata - which you can read directly on the dataset cards.\n\n"
                "## Why We Skip Analysis\n\n"
                "- **No value added**: GEO summaries are brief (1-2 paragraphs) and easily readable\n"
                "- **Cost savings**: Each GPT-4 call costs $0.03-0.10 - not worth it for metadata\n"
                "- **Better alternative**: Read the GEO summary directly - it's faster!\n\n"
                "## What You Can Do\n\n"
                "1. **Download Papers First**: Click the 'Download Papers' button on any dataset card\n"
                "2. **Wait for Parsing**: The system will download, parse, and cache the full-text\n"
                "3. **Try AI Analysis Again**: Once papers are downloaded, AI can analyze Methods/Results\n\n"
                "## Manual Review Option\n\n"
                "You can review the GEO summaries manually - they contain:\n"
                "- Basic study description\n"
                "- Sample count and organism\n"
                "- Brief methods overview\n"
                "- Link to full paper (if available)\n\n"
                "For detailed experimental protocols and findings, full-text papers are required."
            ),
            insights=[],
            recommendations=[
                "Click 'Download Papers' button on dataset cards",
                "Wait for download and parsing to complete",
                "Then click 'AI Analysis' for in-depth insights",
                "Or manually read GEO summaries (faster for basic info)",
            ],
            model_used="none (analysis blocked - no content)",
        )

    async def _build_dataset_summaries(
        self, datasets: List, parsed_cache
    ) -> Tuple[List[str], int]:
        """
        Build comprehensive dataset summaries with full-text content.

        Returns:
            Tuple of (dataset_summaries, total_fulltext_papers)
        """
        dataset_summaries = []
        total_fulltext_papers = 0

        for i, ds in enumerate(datasets, 1):
            dataset_info = [
                f"{i}. **{ds.geo_id}** (Relevance: {int(ds.relevance_score * 100)}%)",
                f"   Title: {ds.title}",
                f"   Organism: {ds.organism or 'N/A'}, Samples: {ds.sample_count or 0}",
                f"   GEO Summary: {ds.summary[:200] if ds.summary else 'No summary'}...",
            ]

            # Add full-text content if available
            if ds.fulltext and len(ds.fulltext) > 0:
                # Prioritize papers for analysis
                sorted_papers = sorted(
                    ds.fulltext,
                    key=lambda p: (
                        0
                        if (
                            hasattr(ds, "pubmed_ids")
                            and p.pmid in (ds.pubmed_ids or [])
                        )
                        else 1,
                        0 if (hasattr(p, "has_methods") and p.has_methods) else 1,
                        -int(p.pmid) if p.pmid and p.pmid.isdigit() else 0,
                    ),
                )

                papers_to_analyze = sorted_papers[:2]
                total_papers = len(ds.fulltext)

                dataset_info.append(
                    f"\n   [DOC] Full-text content from {len(papers_to_analyze)} of {total_papers} linked publication(s):"
                )
                if total_papers > 2:
                    dataset_info.append(
                        f"   [INFO] Analyzing {len(papers_to_analyze)} papers (token limit). "
                        f"Prioritized: original dataset papers, papers with parsed content."
                    )
                total_fulltext_papers += len(papers_to_analyze)

                for j, ft in enumerate(papers_to_analyze, 1):
                    # Load content from cache if not in object
                    (
                        abstract_text,
                        methods_text,
                        results_text,
                        discussion_text,
                    ) = await self._load_paper_content(ft, parsed_cache)

                    dataset_info.extend(
                        [
                            f"\n   Paper {j}: {ft.title[:100]}... (PMID: {ft.pmid})",
                            f"   Abstract: {abstract_text[:250] if abstract_text else 'N/A'}...",
                            f"   Methods: {methods_text[:400] if methods_text else 'N/A'}...",
                            f"   Results: {results_text[:400] if results_text else 'N/A'}...",
                            f"   Discussion: {discussion_text[:250] if discussion_text else 'N/A'}...",
                        ]
                    )
            else:
                dataset_info.append(
                    "   [WARNING] No full-text available (analyzing GEO summary only)"
                )

            dataset_summaries.append("\n".join(dataset_info))

        return dataset_summaries, total_fulltext_papers

    async def _load_paper_content(
        self, paper, parsed_cache
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Load paper content from object or cache."""
        abstract_text = (
            paper.abstract if hasattr(paper, "abstract") and paper.abstract else None
        )
        methods_text = (
            paper.methods if hasattr(paper, "methods") and paper.methods else None
        )
        results_text = (
            paper.results if hasattr(paper, "results") and paper.results else None
        )
        discussion_text = (
            paper.discussion
            if hasattr(paper, "discussion") and paper.discussion
            else None
        )

        # Load from cache if not in object
        if not any([abstract_text, methods_text, results_text, discussion_text]):
            if hasattr(paper, "pmid") and paper.pmid:
                try:
                    cached_data = await parsed_cache.get(paper.pmid)
                    if cached_data:
                        content_data = cached_data.get("content", {})
                        abstract_text = content_data.get("abstract", "")
                        methods_text = content_data.get("methods", "")
                        results_text = content_data.get("results", "")
                        discussion_text = content_data.get("discussion", "")
                        self.logger.info(
                            f"[ANALYZE] Loaded parsed content from cache for PMID {paper.pmid}"
                        )
                except Exception as e:
                    self.logger.warning(
                        f"[ANALYZE] Could not load parsed content for PMID {paper.pmid}: {e}"
                    )

        return abstract_text, methods_text, results_text, discussion_text

    def _build_analysis_prompt(
        self,
        request: "AIAnalysisRequest",
        datasets_to_analyze: List,
        dataset_summaries: List[str],
        total_fulltext_papers: int,
    ) -> str:
        """Build comprehensive analysis prompt."""
        fulltext_note = (
            f"\n\nIMPORTANT: You have access to full-text content from {total_fulltext_papers} scientific papers "
            "(Methods, Results, Discussion sections). Use these to provide detailed, specific insights "
            "about experimental design, methodologies, and key findings."
            if total_fulltext_papers > 0
            else "\n\nNote: Analysis based on GEO metadata only (no full-text papers available)."
        )

        # Add query processing context
        query_context_section = ""
        if request.query_processing:
            qp = request.query_processing
            query_context_section = "\n# QUERY ANALYSIS CONTEXT\n"

            if qp.extracted_entities:
                query_context_section += (
                    f"Extracted Entities: {dict(qp.extracted_entities)}\n"
                )
            if qp.expanded_terms:
                query_context_section += (
                    f"Expanded Search Terms: {', '.join(qp.expanded_terms)}\n"
                )
            if qp.geo_search_terms:
                query_context_section += (
                    f"GEO Query Used: {', '.join(qp.geo_search_terms)}\n"
                )
            if qp.search_intent:
                query_context_section += f"Search Intent: {qp.search_intent}\n"
            if qp.query_type:
                query_context_section += f"Query Type: {qp.query_type}\n"

            query_context_section += "\n"

        # Add match explanations
        match_context_section = ""
        if request.match_explanations:
            match_context_section = "\n# WHY THESE DATASETS WERE RETRIEVED\n"
            for geo_id, explanation in request.match_explanations.items():
                match_context_section += (
                    f"- {geo_id}: Matched terms [{', '.join(explanation.matched_terms)}], "
                    f"Relevance: {int(explanation.relevance_score * 100)}%, "
                    f"Match type: {explanation.match_type}\n"
                )
            match_context_section += "\n"

        return f"""
User searched for: "{request.query}"
{query_context_section}{match_context_section}
Found {len(datasets_to_analyze)} relevant datasets:

{chr(10).join(dataset_summaries)}{fulltext_note}

# ANALYSIS TASK (Step-by-Step Reasoning)

**Step 1: Query-Dataset Alignment**
- Review the extracted entities and search intent
- For each dataset, explain HOW it relates to the specific entities (genes, diseases, etc.)
- Reference the matched terms that led to its retrieval

**Step 2: Methodology Assessment**
{"- Compare experimental approaches from Methods sections" if total_fulltext_papers > 0 else "- Assess study design from GEO summaries"}
- Identify strengths and limitations of each approach
- Note unique methodological contributions

**Step 3: Data Quality and Scope**
- Evaluate sample sizes and experimental conditions
{"- Cite specific results and findings from the papers" if total_fulltext_papers > 0 else "- Consider organism and platform information"}
- Assess data completeness and reproducibility

**Step 4: Recommendations**
Based on your analysis, recommend which dataset(s) for:
- **Basic Understanding**: Best introduction to the topic
- **Advanced Analysis**: Most comprehensive data and methods
- **Method Development**: Best experimental protocols

# OUTPUT FORMAT
Provide your analysis in clear sections:
1. Overview (why each dataset is relevant)
2. Comparison (key differences)
3. Key Insights (main findings)
4. Recommendations (specific to use cases)

Be specific. Cite dataset IDs (GSE numbers){" and PMIDs" if total_fulltext_papers > 0 else ""}.
{"Ground your analysis in actual experimental details from the papers." if total_fulltext_papers > 0 else ""}
{"Reference the entities and terms from the query context when explaining relevance." if request.query_processing else ""}
"""

    def _call_llm(self, prompt: str, settings) -> str:
        """Call LLM with analysis prompt."""
        from fastapi import HTTPException, status

        from omics_oracle_v2.api.helpers import call_openai

        system_message = (
            "You are an expert bioinformatics advisor helping researchers understand and select genomics datasets. "
            "You use step-by-step reasoning to analyze datasets based on:\n"
            "1. Query context (extracted entities, search intent)\n"
            "2. Match explanations (why each dataset was retrieved)\n"
            "3. Full-text content (experimental methods, results, discussion)\n"
            "4. Dataset metadata (organism, samples, platform)\n\n"
            "Provide clear, actionable insights that reference specific evidence from the query analysis "
            "and dataset content. Be specific about WHY datasets are relevant and HOW they differ."
        )

        analysis = call_openai(
            prompt=prompt,
            system_message=system_message,
            api_key=settings.ai.openai_api_key,
            model=settings.ai.model,
            max_tokens=800,
            temperature=settings.ai.temperature,
            timeout=settings.ai.timeout,
        )

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI analysis failed to generate response",
            )

        return analysis

    def _parse_analysis_results(self, analysis: str) -> Tuple[List[str], List[str]]:
        """Parse insights and recommendations from analysis text."""
        insights = []
        recommendations = []

        lines = analysis.split("\n")
        current_section = None

        for line in lines:
            line_lower = line.lower().strip()
            if "insight" in line_lower or "finding" in line_lower:
                current_section = "insights"
            elif "recommend" in line_lower:
                current_section = "recommendations"
            elif line.strip() and (
                line.strip()[0].isdigit() or line.strip().startswith("-")
            ):
                if current_section == "insights":
                    insights.append(line.strip().lstrip("0123456789.-) "))
                elif current_section == "recommendations":
                    recommendations.append(line.strip().lstrip("0123456789.-) "))

        return insights, recommendations
