"""
Interactive Q&A system for dataset analysis.

Allows users to ask natural language questions about datasets and their usage
in scientific literature, powered by LLM analysis of citations.
"""

import logging
from typing import Dict, List

from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.publications.citations.models import UsageAnalysis
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class DatasetQASystem:
    """
    Interactive Q&A system for dataset analysis.

    Uses LLM to answer natural language questions about how datasets
    are being used in scientific literature.

    Example:
        >>> qa = DatasetQASystem(llm_client)
        >>> answer = qa.ask(
        ...     dataset_publication,
        ...     "What novel biomarkers were discovered?",
        ...     citation_analyses
        ... )
        >>> print(answer["answer"])
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Q&A system.

        Args:
            llm_client: LLM client for generating answers
        """
        self.llm = llm_client

    def ask(
        self,
        dataset: Publication,
        question: str,
        citation_analyses: List[UsageAnalysis],
        max_citations: int = 20,
    ) -> Dict:
        """
        Ask a question about a dataset.

        Args:
            dataset: Dataset publication
            question: Natural language question
            citation_analyses: Citation analyses for the dataset
            max_citations: Maximum citations to include in context

        Returns:
            Dictionary with answer, evidence, and metadata
        """
        logger.info(f"Answering question: {question}")

        # Build context from citation analyses
        context = self._build_context(dataset, citation_analyses[:max_citations])

        # Create prompt
        prompt = self._create_qa_prompt(dataset, question, context)

        # Generate answer
        try:
            response = self.llm.generate(
                prompt,
                system_prompt="You are a biomedical research expert. Provide accurate, evidence-based answers with citations.",
                max_tokens=1000,
            )

            answer_text = response.get("content", "")

            # Extract evidence from analyses
            evidence = self._extract_evidence(question, citation_analyses[:max_citations])

            result = {
                "question": question,
                "answer": answer_text,
                "evidence": evidence,
                "num_citations_analyzed": len(citation_analyses),
                "num_citations_used": min(max_citations, len(citation_analyses)),
                "dataset_title": dataset.title,
            }

            logger.info(f"Answer generated with {len(evidence)} evidence citations")
            return result

        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return {
                "question": question,
                "answer": f"Unable to answer question: {str(e)}",
                "evidence": [],
                "error": str(e),
            }

    def ask_batch(
        self,
        dataset: Publication,
        questions: List[str],
        citation_analyses: List[UsageAnalysis],
    ) -> List[Dict]:
        """
        Ask multiple questions about a dataset.

        Args:
            dataset: Dataset publication
            questions: List of questions
            citation_analyses: Citation analyses

        Returns:
            List of answer dictionaries
        """
        answers = []
        for question in questions:
            answer = self.ask(dataset, question, citation_analyses)
            answers.append(answer)
        return answers

    def suggest_questions(
        self,
        dataset: Publication,
        citation_analyses: List[UsageAnalysis],
    ) -> List[str]:
        """
        Suggest relevant questions based on citation analyses.

        Args:
            dataset: Dataset publication
            citation_analyses: Citation analyses

        Returns:
            List of suggested questions
        """
        # Analyze what information is available
        has_biomarkers = any(len(analysis.novel_biomarkers) > 0 for analysis in citation_analyses)
        has_clinical = any(
            analysis.clinical_relevance in ["high", "medium"] for analysis in citation_analyses
        )
        has_validation = any(analysis.validation_status == "validated" for analysis in citation_analyses)

        # Build usage types
        usage_types = set(analysis.usage_type for analysis in citation_analyses)

        # Build domains
        domains = set(
            analysis.application_domain for analysis in citation_analyses if analysis.application_domain
        )

        # Suggest questions based on available data
        suggestions = [
            f"How has {dataset.title} been used in research?",
            "What are the most common applications of this dataset?",
        ]

        if has_biomarkers:
            suggestions.append("What novel biomarkers were discovered using this dataset?")

        if has_clinical:
            suggestions.append("What are the clinical applications of research using this dataset?")

        if has_validation:
            suggestions.append("Which findings have been validated in independent studies?")

        if "novel_application" in usage_types:
            suggestions.append("What novel applications were developed using this dataset?")

        if len(domains) > 1:
            suggestions.append("What research domains have used this dataset?")

        return suggestions[:7]  # Return top 7

    def _build_context(
        self,
        dataset: Publication,
        citation_analyses: List[UsageAnalysis],
    ) -> str:
        """Build context string from citation analyses."""
        context_parts = [
            f"Dataset: {dataset.title}",
            f"Published: {dataset.publication_date.year if dataset.publication_date else 'Unknown'}",
            f"Number of citations analyzed: {len(citation_analyses)}",
            "",
            "Citation Analyses:",
        ]

        for i, analysis in enumerate(citation_analyses[:20], 1):
            analysis_text = f"\n{i}. {analysis.paper_title}"

            if analysis.dataset_reused:
                analysis_text += "\n   - Dataset reused: Yes"
                analysis_text += f"\n   - Usage type: {analysis.usage_type}"
                analysis_text += f"\n   - Domain: {analysis.application_domain}"

                if analysis.key_findings:
                    analysis_text += f"\n   - Key findings: {'; '.join(analysis.key_findings[:3])}"

                if analysis.novel_biomarkers:
                    analysis_text += f"\n   - Biomarkers: {', '.join(analysis.novel_biomarkers[:5])}"

                if analysis.clinical_relevance != "none":
                    analysis_text += f"\n   - Clinical relevance: {analysis.clinical_relevance}"

                if analysis.validation_status != "none":
                    analysis_text += f"\n   - Validation: {analysis.validation_status}"

            context_parts.append(analysis_text)

        return "\n".join(context_parts)

    def _create_qa_prompt(
        self,
        dataset: Publication,
        question: str,
        context: str,
    ) -> str:
        """Create prompt for Q&A."""
        prompt = f"""Based on the following information about how a dataset has been used in scientific literature, please answer the question.

{context}

Question: {question}

Instructions:
1. Provide a clear, evidence-based answer
2. Reference specific papers when possible
3. Quantify findings when available (e.g., "3 papers discovered novel biomarkers")
4. Be specific about domains, methodologies, and findings
5. Acknowledge limitations if data is incomplete

Answer:"""

        return prompt

    def _extract_evidence(
        self,
        question: str,
        citation_analyses: List[UsageAnalysis],
    ) -> List[Dict]:
        """Extract relevant evidence citations for the answer."""
        evidence = []

        # Keywords to look for based on question
        question_lower = question.lower()

        for analysis in citation_analyses:
            relevance_score = 0
            reasons = []

            # Check for biomarker-related questions
            if "biomarker" in question_lower and analysis.novel_biomarkers:
                relevance_score += 3
                reasons.append(f"Discovered {len(analysis.novel_biomarkers)} biomarkers")

            # Check for clinical questions
            if "clinical" in question_lower and analysis.clinical_relevance in ["high", "medium"]:
                relevance_score += 2
                reasons.append(f"Clinical relevance: {analysis.clinical_relevance}")

            # Check for validation questions
            if "validat" in question_lower and analysis.validation_status == "validated":
                relevance_score += 2
                reasons.append("Findings validated")

            # Check for application/usage questions
            if (
                any(word in question_lower for word in ["use", "application", "applied"])
                and analysis.dataset_reused
            ):
                relevance_score += 1
                reasons.append(f"Usage type: {analysis.usage_type}")

            # Check for domain questions
            if "domain" in question_lower or "field" in question_lower:
                if analysis.application_domain:
                    relevance_score += 1
                    reasons.append(f"Domain: {analysis.application_domain}")

            # Add to evidence if relevant
            if relevance_score > 0:
                evidence.append(
                    {
                        "paper_title": analysis.paper_title,
                        "paper_id": analysis.paper_id,
                        "relevance_score": relevance_score,
                        "reasons": reasons,
                        "usage_type": analysis.usage_type,
                        "biomarkers": analysis.novel_biomarkers,
                        "clinical_relevance": analysis.clinical_relevance,
                    }
                )

        # Sort by relevance
        evidence.sort(key=lambda x: x["relevance_score"], reverse=True)

        return evidence[:10]  # Top 10 most relevant

    def get_statistics(self, citation_analyses: List[UsageAnalysis]) -> Dict:
        """
        Get statistics about citation analyses for context.

        Args:
            citation_analyses: List of citation analyses

        Returns:
            Dictionary of statistics
        """
        total = len(citation_analyses)
        reused = sum(1 for a in citation_analyses if a.dataset_reused)

        # Count usage types
        usage_types = {}
        for analysis in citation_analyses:
            if analysis.dataset_reused:
                usage_types[analysis.usage_type] = usage_types.get(analysis.usage_type, 0) + 1

        # Count domains
        domains = {}
        for analysis in citation_analyses:
            if analysis.application_domain:
                domains[analysis.application_domain] = domains.get(analysis.application_domain, 0) + 1

        # Count biomarkers
        all_biomarkers = []
        for analysis in citation_analyses:
            all_biomarkers.extend(analysis.novel_biomarkers)

        # Clinical relevance
        clinical_high = sum(1 for a in citation_analyses if a.clinical_relevance == "high")
        clinical_medium = sum(1 for a in citation_analyses if a.clinical_relevance == "medium")

        # Validation
        validated = sum(1 for a in citation_analyses if a.validation_status == "validated")

        return {
            "total_citations": total,
            "dataset_reused": reused,
            "reuse_rate": reused / total if total > 0 else 0,
            "usage_types": usage_types,
            "domains": domains,
            "unique_biomarkers": len(set(all_biomarkers)),
            "total_biomarkers": len(all_biomarkers),
            "clinical_high": clinical_high,
            "clinical_medium": clinical_medium,
            "validated_findings": validated,
        }
